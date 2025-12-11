from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from battles.models import Battle
import logging

logger = logging.getLogger('typing_platform')


class Command(BaseCommand):
    help = 'Delete battles older than 14 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=14,
            help='Number of days to keep battles (default: 14)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old battles
        old_battles = Battle.objects.filter(
            created_at__lt=cutoff_date
        )
        
        count = old_battles.count()
        
        if count > 0:
            # Delete old battles (cascade will delete participants)
            old_battles.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} battle(s) older than {days} days'
                )
            )
            logger.info(f'Deleted {count} battle(s) older than {days} days')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'No battles older than {days} days found')
            )

