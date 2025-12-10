from django.core.management.base import BaseCommand
from typing_practice.models import Text


class Command(BaseCommand):
    help = 'Fix word_count field for all texts based on actual word count in body'

    def handle(self, *args, **options):
        texts = Text.objects.all()
        fixed_count = 0
        skipped_count = 0
        
        # Word count choices: 10, 25, 60, 100
        word_count_choices = [10, 25, 60, 100]
        
        for text in texts:
            # Calculate actual word count
            actual_word_count = len(text.body.split())
            
            # Find closest word_count choice
            closest_word_count = min(word_count_choices, key=lambda x: abs(x - actual_word_count))
            
            # Only update if different
            if text.word_count != closest_word_count:
                old_word_count = text.word_count
                text.word_count = closest_word_count
                text.save()
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Fixed: "{text.title}" - Actual: {actual_word_count} words, '
                        f'Changed from {old_word_count} to {closest_word_count}'
                    )
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    f'Skipped: "{text.title}" - Already correct ({text.word_count} words, actual: {actual_word_count})'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Fixed: {fixed_count}, Skipped: {skipped_count}, Total: {texts.count()}'
            )
        )

