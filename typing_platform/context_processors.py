from django.core.cache import cache
from django.contrib.auth import get_user_model
from accounts.models import Notification
import time

ONLINE_TIMEOUT = 300  # 5 daqiqa (soniya)


def online_count(request):
    """
    Context processor to provide online user count and total users count.
    Only counts users who were active within ONLINE_TIMEOUT seconds.
    """
    # Get roster of potentially online users
    roster = cache.get("online-roster", [])
    now = int(time.time())
    alive = []
    
    # Check each user's last activity timestamp
    for uid in roster:
        timestamp = cache.get(f"online-user:{uid}")
        if timestamp and (now - timestamp) <= ONLINE_TIMEOUT:
            alive.append(uid)
    
    # Get total registered users count
    User = get_user_model()
    try:
        total_users_count = User.objects.count()
    except Exception:
        total_users_count = 0
    
    # Get unread notifications count for authenticated users
    unread_notifications = 0
    if request.user.is_authenticated:
        try:
            unread_notifications = Notification.get_unread_count(request.user)
        except Exception:
            pass
    
    return {
        "online_count": len(set(alive)),
        "total_users_count": total_users_count,
        "unread_notifications": unread_notifications,
    }

