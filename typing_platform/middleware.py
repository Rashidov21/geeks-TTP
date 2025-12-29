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

