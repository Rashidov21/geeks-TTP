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
from django.views.decorators.csrf import csrf_exempt
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
        
        # Validate text/code exists and perform server-side normalization/validation
        typed_text = data.get('typed_text', '')
        allow_incomplete = bool(data.get('allow_incomplete', False))
        mode = data.get('mode', 'full')
        try:
            time_limit_sent = int(data.get('time_limit', 0))
        except (TypeError, ValueError):
            time_limit_sent = 0

        def normalize_text(s: str) -> str:
            if not isinstance(s, str):
                return ''
            # Normalize whitespace for plain texts: collapse all whitespace to single spaces
            return ' '.join(s.replace('\r\n', '\n').split())

        def normalize_code(s: str) -> str:
            if not isinstance(s, str):
                return ''
            # Normalize line endings and strip trailing spaces per line
            return '\n'.join([line.rstrip() for line in s.replace('\r\n', '\n').split('\n')])

        if text_id:
            try:
                text = Text.objects.get(id=text_id)
            except Text.DoesNotExist:
                return JsonResponse({'error': 'Text not found'}, status=404)

            original_norm = normalize_text(text.body)
            typed_norm = normalize_text(typed_text)

            # If not time-mode allowed, require full match
            if not (allow_incomplete and mode == 'time' and duration_seconds >= time_limit_sent):
                if typed_norm != original_norm:
                    return JsonResponse({'error': 'Text not fully typed'}, status=400)

            # compute server-side metrics
            typed_chars = len(typed_norm)
            typed_words = len(typed_norm.split()) if typed_norm.strip() else 0
            mismatches = 0
            # per-char mismatch counting against original
            for i, ch in enumerate(typed_norm):
                if i >= len(original_norm) or ch != original_norm[i]:
                    mismatches += 1
            mismatches += max(0, len(original_norm) - len(typed_norm))
            server_accuracy = round(((typed_chars - mismatches) / typed_chars) * 100, 2) if typed_chars > 0 else 100.0
            server_wpm = round((typed_words / duration_seconds) * 60, 2) if duration_seconds > 0 else 0.0

            # override client values if they differ significantly
            if abs(server_wpm - wpm) / (server_wpm + 1e-6) > 0.2:
                logger.info(f"WPM mismatch for user {request.user.username}: client={wpm}, server={server_wpm}")
                wpm = server_wpm
            if abs(server_accuracy - accuracy) > 10:
                logger.info(f"Accuracy mismatch for user {request.user.username}: client={accuracy}, server={server_accuracy}")
                accuracy = server_accuracy

        if code_id:
            try:
                code = CodeSnippet.objects.get(id=code_id)
            except CodeSnippet.DoesNotExist:
                return JsonResponse({'error': 'Code snippet not found'}, status=404)

            original_norm = normalize_code(code.code_body)
            typed_norm = normalize_code(typed_text)

            # If not time-mode allowed, require full match
            if not (allow_incomplete and mode == 'time' and duration_seconds >= time_limit_sent):
                if typed_norm != original_norm:
                    return JsonResponse({'error': 'Code not fully typed'}, status=400)

            # compute server-side metrics for code (chars based)
            typed_chars = len(typed_norm)
            mismatches = 0
            for i, ch in enumerate(typed_norm):
                if i >= len(original_norm) or ch != original_norm[i]:
                    mismatches += 1
            mismatches += max(0, len(original_norm) - len(typed_norm))
            server_accuracy = round(((typed_chars - mismatches) / typed_chars) * 100, 2) if typed_chars > 0 else 100.0
            server_wpm = round(((typed_chars / 5.0) / duration_seconds) * 60, 2) if duration_seconds > 0 else 0.0

            if abs(server_wpm - wpm) / (server_wpm + 1e-6) > 0.2:
                logger.info(f"Code WPM mismatch for user {request.user.username}: client={wpm}, server={server_wpm}")
                wpm = server_wpm
            if abs(server_accuracy - accuracy) > 10:
                logger.info(f"Code accuracy mismatch for user {request.user.username}: client={accuracy}, server={server_accuracy}")
                accuracy = server_accuracy
        
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

            # Keep only last 10 results per user, delete older ones (avoid extra count())
            ids_to_delete = list(UserResult.objects.filter(user=request.user).order_by('-time').values_list('id', flat=True)[10:])
            if ids_to_delete:
                UserResult.objects.filter(id__in=ids_to_delete).delete()
                logger.info(f"Deleted {len(ids_to_delete)} old results for user {request.user.username}")
        
        # Clear user stats cache
        cache.delete(f'user_stats_{request.user.id}')
        
        # Get motivational message
        motivational_message = get_motivational_message(request.user, result)
        
        logger.info(f"Result saved: user={request.user.username}, wpm={wpm}, accuracy={accuracy}")
        return JsonResponse({
            'success': True, 
            'result_id': result.id,
            'message': motivational_message['message'],
            'type': motivational_message['type'],
            'icon': motivational_message['icon']
        })
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in save_result request")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error saving result: {e}", exc_info=True)
        return JsonResponse({'error': 'Server error occurred'}, status=500)


@login_required
def achievements(request):
    """Return a small achievements payload for the user (simple)."""
    # Minimal achievements: last_wpm, best_wpm, streak placeholder
    last = UserResult.objects.filter(user=request.user).order_by('-time').first()
    best = UserResult.objects.filter(user=request.user).order_by('-wpm').first()
    data = {
        'last_wpm': last.wpm if last else 0,
        'best_wpm': best.wpm if best else 0,
        'streak_days': 0,
    }
    return JsonResponse({'success': True, 'achievements': data})


def get_motivational_message(user, result):
    """Get motivational message based on user's performance"""
    try:
        # Get previous best
        previous_best = UserResult.objects.filter(user=user).exclude(id=result.id).aggregate(max_wpm=Max('wpm'))['max_wpm'] or 0
        
        # Check if new record
        if result.wpm > previous_best:
            return {
                'message': f'🎉 Yangi rekord! {result.wpm:.1f} WPM - Ajoyib ish!',
                'type': 'success',
                'icon': '🎉'
            }
        
        # High performance messages
        if result.wpm >= 100:
            return {
                'message': '🔥 Elite tezlik! 100+ WPM - Siz professional darajadasiz!',
                'type': 'success',
                'icon': '🔥'
            }
        elif result.wpm >= 80:
            return {
                'message': '💪 Expert daraja! 80+ WPM - A\'lo natija!',
                'type': 'success',
                'icon': '💪'
            }
        elif result.wpm >= 60:
            return {
                'message': '⭐ Advanced daraja! 60+ WPM - Yaxshi ish!',
                'type': 'info',
                'icon': '⭐'
            }
        
        # Accuracy messages
        if result.accuracy >= 95:
            return {
                'message': '🎯 Mukammal aniqlik! 95%+ - Ajoyib!',
                'type': 'success',
                'icon': '🎯'
            }
        elif result.accuracy < 80:
            return {
                'message': '💪 Aniqlikni yaxshilashga harakat qiling!',
                'type': 'warning',
                'icon': '💪'
            }
        
        # Improvement messages
        profile = UserProfile.objects.get(user=user)
        if profile.current_streak >= 7:
            return {
                'message': f'🔥 {profile.current_streak} kun ketma-ketlik! Ajoyib izchillik!',
                'type': 'success',
                'icon': '🔥'
            }
        
        # Default encouraging message
        messages = [
            'Yaxshi ish! Davom eting! 💪',
            'Ajoyib natija! Keyingi mashqda yanada yaxshiroq bo\'ling! ⭐',
            'Yaxshi! Har bir mashq sizni yanada yaxshiroq qiladi! 🚀',
        ]
        return {
            'message': random.choice(messages),
            'type': 'info',
            'icon': '👍'
        }
    except Exception as e:
        logger.error(f"Error getting motivational message: {e}")
        return {
            'message': 'Natija saqlandi!',
            'type': 'info',
            'icon': '✅'
        }


@csrf_exempt
@require_http_methods(["POST"])
def telemetry(request):
    """Receive small telemetry events from frontend (non-sensitive)."""
    try:
        payload = json.loads(request.body)
        event = payload.get('event')
        details = payload.get('details', {})
        logger.info(f"Telemetry event: {event} details={details}")
        return JsonResponse({'success': True})
    except Exception as e:
        logger.warning(f"Telemetry error: {e}")
        return JsonResponse({'error': 'Bad telemetry'}, status=400)
