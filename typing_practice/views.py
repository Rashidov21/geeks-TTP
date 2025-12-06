from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Text, CodeSnippet, UserResult
import json


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
    words_count = int(request.GET.get('words_count', 0))
    time_limit = int(request.GET.get('time_limit', 0))
    
    texts = Text.objects.filter(difficulty=difficulty).order_by('?')
    if not texts.exists():
        return redirect('typing_practice:index')
    
    text = texts.first()
    
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
    })


@login_required
def code_practice(request, language='python'):
    codes = CodeSnippet.objects.filter(language=language).order_by('?')
    if not codes.exists():
        return redirect('typing_practice:index')
    
    code = codes.first()
    return render(request, 'typing_practice/code_practice.html', {
        'code': code,
        'language': language
    })


@login_required
@csrf_exempt
def save_result(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        text_id = data.get('text_id')
        code_id = data.get('code_id')
        wpm = float(data.get('wpm', 0))
        accuracy = float(data.get('accuracy', 0))
        mistakes = int(data.get('mistakes', 0))
        mistakes_list = data.get('mistakes_list', [])
        duration_seconds = int(data.get('duration_seconds', 0))
        
        session_type = 'text' if text_id else 'code'
        
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
        
        return JsonResponse({'success': True, 'result_id': result.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
