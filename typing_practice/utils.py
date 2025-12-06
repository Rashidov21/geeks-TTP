"""
Utility functions for typing practice calculations
"""
import logging

logger = logging.getLogger('typing_platform')


def calculate_wpm(typed_words, elapsed_seconds):
    """Calculate Words Per Minute"""
    if elapsed_seconds <= 0:
        return 0
    return (typed_words / elapsed_seconds) * 60


def calculate_cpm(typed_chars, elapsed_seconds):
    """Calculate Characters Per Minute"""
    if elapsed_seconds <= 0:
        return 0
    return (typed_chars / elapsed_seconds) * 60


def calculate_accuracy(typed_chars, mistakes):
    """Calculate typing accuracy percentage"""
    if typed_chars <= 0:
        return 100.0
    correct_chars = typed_chars - mistakes
    return max(0, min(100, (correct_chars / typed_chars) * 100))


def validate_wpm(wpm):
    """Validate WPM value (0-1000)"""
    return max(0, min(1000, float(wpm)))


def validate_accuracy(accuracy):
    """Validate accuracy value (0-100)"""
    return max(0, min(100, float(accuracy)))


def get_random_text(difficulty='easy'):
    """Get random text efficiently"""
    from .models import Text
    import random
    
    # Get all IDs first (more efficient)
    text_ids = list(Text.objects.filter(difficulty=difficulty).values_list('id', flat=True))
    if not text_ids:
        return None
    
    random_id = random.choice(text_ids)
    return Text.objects.get(id=random_id)


def get_random_code(language='python', difficulty='easy'):
    """Get random code snippet efficiently"""
    from .models import CodeSnippet
    import random
    
    # Get all IDs first (more efficient)
    code_ids = list(CodeSnippet.objects.filter(
        language=language,
        difficulty=difficulty
    ).values_list('id', flat=True))
    
    if not code_ids:
        return None
    
    random_id = random.choice(code_ids)
    return CodeSnippet.objects.get(id=random_id)

