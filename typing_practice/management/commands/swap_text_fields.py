from django.core.management.base import BaseCommand
from typing_practice.models import Text


class Command(BaseCommand):
    help = 'Swap title and body fields for all texts (title -> body, body -> title)'

    def handle(self, *args, **options):
        texts = Text.objects.all()
        swapped_count = 0
        
        for text in texts:
            # Swap title and body
            old_title = text.title
            old_body = text.body
            
            text.title = old_body
            text.body = old_title
            text.save()
            
            swapped_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Swapped: ID {text.id} - Old title: "{old_title[:50]}..." -> New title: "{text.title[:50]}..."'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Swapped {swapped_count} texts.'
            )
        )

