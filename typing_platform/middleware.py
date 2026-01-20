import time
from django.core.cache import cache

ONLINE_TIMEOUT = 300  # 5 daqiqa ichida ko'ringanlar "online"


class ActiveUserMiddleware:
    """Track active users by updating their last seen timestamp in cache"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only track authenticated users
        if request.user.is_authenticated:
            now = int(time.time())
            uid = request.user.id
            
            # Store user's last activity timestamp
            cache.set(f"online-user:{uid}", now, ONLINE_TIMEOUT)
            
            # Maintain a roster of online users (set as list for cache compatibility)
            roster = set(cache.get("online-roster", []))
            roster.add(uid)
            cache.set("online-roster", list(roster), ONLINE_TIMEOUT)
        
        return response


class NoCacheMiddleware:
    """HTML sahifalar uchun brauzer cache'ni o'chirish"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Faqat HTML sahifalar uchun cache'ni o'chirish
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response

