"""
Sitemap configuration for SEO
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from competitions.models import Competition


class StaticViewSitemap(Sitemap):
    """Static pages sitemap"""
    priority = 1.0
    changefreq = 'daily'
    
    def items(self):
        return [
            'home',
            'dashboard',
            'typing_practice:index',
            'competitions:list',
            'battles:list',
            'leaderboard:index',
            'accounts:login',
            'accounts:register',
            'contact',
            'privacy_policy',
            'terms_of_service',
        ]
    
    def location(self, item):
        return reverse(item)


class CompetitionSitemap(Sitemap):
    """Competitions sitemap"""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Competition.objects.filter(is_public=True, status='active')
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at
    
    def location(self, obj):
        from django.urls import reverse
        return reverse('competitions:detail', args=[obj.id])
