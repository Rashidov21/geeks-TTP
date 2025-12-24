from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from .models import Text, CodeSnippet, UserResult
from .utils import (
    validate_wpm, validate_accuracy,
    get_random_text, get_random_code
)
import json
import logging

logger = logging.getLogger('typing_platform')


@login_required
def index(request):
    return render(request, 'typing_practice/index.html')


@login_required
def text_settings(request):
    return render(request, 'typing_practice/text_settings.html')


@login_required
def text_practice(request, difficulty='easy'):
    # Get settings from query params
    mode = request.GET.get('mode', 'full')
    action = request.GET.get('action', 'random')  # 'random' or 'next'
    current_text_id = request.GET.get('text_id', None)
    
    try:
        words_count = max(0, int(request.GET.get('words_count', 0)))
        time_limit = max(0, int(request.GET.get('time_limit', 0)))
        text_length = int(request.GET.get('text_length', 25))  # Default 25 words
        # Validate text_length is one of allowed values
        if text_length not in [10, 25, 60, 100]:
            text_length = 25
    except (ValueError, TypeError):
        words_count = 0
        time_limit = 0
        text_length = 25
    
    # Select text based on action
    if action == 'next' and current_text_id:
        # Get next text (ordered by ID)
        try:
            current_text = Text.objects.get(id=current_text_id, difficulty=difficulty, word_count=text_length)
            next_text = Text.objects.filter(
                difficulty=difficulty,
                word_count=text_length,
                id__gt=current_text.id
            ).order_by('id').first()
            
            if not next_text:
                # If no next, get first text (wrap around)
                next_text = Text.objects.filter(
                    difficulty=difficulty,
                    word_count=text_length
                ).order_by('id').first()
            
            text = next_text
        except Text.DoesNotExist:
            text = get_random_text(difficulty=difficulty, word_count=text_length)
    else:
        # Random text selection
        text = get_random_text(difficulty=difficulty, word_count=text_length)
    
    if not text:
        from django.contrib import messages
        messages.error(request, f'Bu qiyinchilikda {text_length} so\'zli matnlar topilmadi.')
        return redirect('typing_practice:index')
    
    # Process text based on mode
    words = text.body.split()
    if mode == 'words' and words_count > 0:
        # Take only specified number of words
        text_body = ' '.join(words[:words_count])
    else:
        text_body = text.body
    
    return render(request, 'typing_practice/text_practice.html', {
        'text': text,
        'text_body': text_body,
        'difficulty': difficulty,
        'mode': mode,
        'words_count': words_count,
        'time_limit': time_limit,
        'text_length': text_length,
    })


@login_required
def code_practice(request, language='python'):
    # Validate language
    valid_languages = ['python', 'javascript', 'cpp', 'java']
    if language not in valid_languages:
        from django.contrib import messages
        messages.error(request, 'Noto\'g\'ri dasturlash tili.')
        return redirect('typing_practice:index')
    
    action = request.GET.get('action', 'random')  # 'random' or 'next'
    current_code_id = request.GET.get('code_id', None)
    difficulty = request.GET.get('difficulty', 'easy')
    
    # Select code based on action
    if action == 'next' and current_code_id:
        # Get next code (ordered by ID)
        try:
            current_code = CodeSnippet.objects.get(id=current_code_id, language=language, difficulty=difficulty)
            next_code = CodeSnippet.objects.filter(
                language=language,
                difficulty=difficulty,
                id__gt=current_code.id
            ).order_by('id').first()
            
            if not next_code:
                # If no next, get first code (wrap around)
                next_code = CodeSnippet.objects.filter(
                    language=language,
                    difficulty=difficulty
                ).order_by('id').first()
            
            code = next_code
        except CodeSnippet.DoesNotExist:
            code = get_random_code(language, difficulty=difficulty)
    else:
        # Random code selection
        code = get_random_code(language, difficulty=difficulty)
    
    if not code:
        from django.contrib import messages
        messages.error(request, f'{language} uchun kod topilmadi.')
        return redirect('typing_practice:index')
    
    return render(request, 'typing_practice/code_practice.html', {
        'code': code,
        'language': language,
        'difficulty': difficulty,
    })


@login_required
@require_http_methods(["POST"])
def save_result(request):
    """Save typing practice result with validation"""
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        code_id = data.get('code_id')
        
        # Validate that only one ID is provided
        if not (text_id or code_id) or (text_id and code_id):
            return JsonResponse({'error': 'Invalid request: provide either text_id or code_id'}, status=400)
        
        # Validate and sanitize input
        try:
            wpm = validate_wpm(data.get('wpm', 0))
            accuracy = validate_accuracy(data.get('accuracy', 0))
            mistakes = max(0, int(data.get('mistakes', 0)))
            mistakes_list = data.get('mistakes_list', [])
            if not isinstance(mistakes_list, list):
                mistakes_list = []
            duration_seconds = max(0, int(data.get('duration_seconds', 0)))
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid data in save_result: {e}")
            return JsonResponse({'error': 'Invalid data format'}, status=400)
        
        # Validate text/code exists
        if text_id:
            try:
                text = Text.objects.get(id=text_id)
            except Text.DoesNotExist:
                return JsonResponse({'error': 'Text not found'}, status=404)
            # Ensure user typed the full text unless allowed (e.g., time-limited session)
            typed_text = data.get('typed_text', '')
            allow_incomplete = bool(data.get('allow_incomplete', False))
            if not allow_incomplete:
                # strict check: trimmed typed_text must equal stored text body trimmed
                if not isinstance(typed_text, str) or text.body.strip() != typed_text.strip():
                    return JsonResponse({'error': 'Text not fully typed'}, status=400)
        
        if code_id:
            try:
                code = CodeSnippet.objects.get(id=code_id)
            except CodeSnippet.DoesNotExist:
                return JsonResponse({'error': 'Code snippet not found'}, status=404)
            # Ensure user typed the full code unless allowed
            typed_text = data.get('typed_text', '')
            allow_incomplete = bool(data.get('allow_incomplete', False))
            if not allow_incomplete:
                if not isinstance(typed_text, str) or code.code_body.strip() != typed_text.strip():
                    return JsonResponse({'error': 'Code not fully typed'}, status=400)
        
        session_type = 'text' if text_id else 'code'
        
        # Create result with transaction
        with transaction.atomic():
            result = UserResult.objects.create(
                user=request.user,
                text_id=text_id if text_id else None,
                code_snippet_id=code_id if code_id else None,
                wpm=wpm,
                accuracy=accuracy,
                mistakes=mistakes,
                mistakes_list=mistakes_list,
                duration_seconds=duration_seconds,
                session_type=session_type
            )
            
            # Keep only last 10 results per user, delete older ones
            user_results = UserResult.objects.filter(user=request.user).order_by('-time')
            if user_results.count() > 10:
                # Get IDs of results to delete (all except first 10)
                results_to_delete = user_results[10:].values_list('id', flat=True)
                if results_to_delete:
                    UserResult.objects.filter(id__in=list(results_to_delete)).delete()
                    logger.info(f"Deleted {len(results_to_delete)} old results for user {request.user.username}")
        
        # Clear user stats cache
        cache.delete(f'user_stats_{request.user.id}')
        
        logger.info(f"Result saved: user={request.user.username}, wpm={wpm}, accuracy={accuracy}")
        return JsonResponse({'success': True, 'result_id': result.id})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in save_result request")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error saving result: {e}", exc_info=True)
        return JsonResponse({'error': 'Server error occurred'}, status=500)
