"""
Management command to create default badges
"""
from django.core.management.base import BaseCommand
from accounts.models import Badge


class Command(BaseCommand):
    help = 'Create default badges for gamification'

    def handle(self, *args, **options):
        badges_data = [
            # Speed badges
            {
                'name': 'Speed Master',
                'description': '100+ WPM tezlikka erishish',
                'icon': '⚡',
                'badge_type': 'speed',
                'requirement': {'wpm': 100},
                'xp_reward': 100,
            },
            {
                'name': 'Speed Expert',
                'description': '80+ WPM tezlikka erishish',
                'icon': '🚀',
                'badge_type': 'speed',
                'requirement': {'wpm': 80},
                'xp_reward': 75,
            },
            {
                'name': 'Speed Advanced',
                'description': '60+ WPM tezlikka erishish',
                'icon': '💨',
                'badge_type': 'speed',
                'requirement': {'wpm': 60},
                'xp_reward': 50,
            },
            
            # Accuracy badges
            {
                'name': 'Accuracy King',
                'description': '95%+ o\'rtacha aniqlik',
                'icon': '🎯',
                'badge_type': 'accuracy',
                'requirement': {'accuracy': 95},
                'xp_reward': 100,
            },
            {
                'name': 'Accuracy Master',
                'description': '90%+ o\'rtacha aniqlik',
                'icon': '✅',
                'badge_type': 'accuracy',
                'requirement': {'accuracy': 90},
                'xp_reward': 75,
            },
            
            # Streak badges
            {
                'name': 'Streak Warrior',
                'description': '7 kun ketma-ket mashq qilish',
                'icon': '🔥',
                'badge_type': 'streak',
                'requirement': {'days': 7},
                'xp_reward': 50,
            },
            {
                'name': 'Streak Champion',
                'description': '14 kun ketma-ket mashq qilish',
                'icon': '🔥🔥',
                'badge_type': 'streak',
                'requirement': {'days': 14},
                'xp_reward': 100,
            },
            {
                'name': 'Streak Legend',
                'description': '30 kun ketma-ket mashq qilish',
                'icon': '🔥🔥🔥',
                'badge_type': 'streak',
                'requirement': {'days': 30},
                'xp_reward': 200,
            },
            
            # Milestone badges
            {
                'name': 'Marathon Runner',
                'description': '100 ta mashqni yakunlash',
                'icon': '🏃',
                'badge_type': 'milestone',
                'requirement': {'sessions': 100},
                'xp_reward': 150,
            },
            {
                'name': 'Dedicated Typist',
                'description': '50 ta mashqni yakunlash',
                'icon': '💪',
                'badge_type': 'milestone',
                'requirement': {'sessions': 50},
                'xp_reward': 75,
            },
            {
                'name': 'Code Ninja',
                'description': '50 ta kod mashqini yakunlash',
                'icon': '🥷',
                'badge_type': 'milestone',
                'requirement': {'code_sessions': 50},
                'xp_reward': 100,
            },
            {
                'name': 'Text Master',
                'description': '50 ta matn mashqini yakunlash',
                'icon': '📝',
                'badge_type': 'milestone',
                'requirement': {'text_sessions': 50},
                'xp_reward': 100,
            },
            
            # Consistency badges
            {
                'name': 'Consistency Champion',
                'description': '30 kun mashq qilish',
                'icon': '📅',
                'badge_type': 'consistency',
                'requirement': {'practice_days': 30},
                'xp_reward': 150,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for badge_data in badges_data:
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults={
                    'description': badge_data['description'],
                    'icon': badge_data['icon'],
                    'badge_type': badge_data['badge_type'],
                    'requirement': badge_data['requirement'],
                    'xp_reward': badge_data['xp_reward'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created badge: {badge.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated badge: {badge.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nBadge creation complete! Created: {created_count}, Updated: {updated_count}'
        ))

