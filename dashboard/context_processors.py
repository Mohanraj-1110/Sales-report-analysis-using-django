from accounts.models import SystemNotification

def dashboard_context(request):
    if request.user.is_authenticated:
        unread_notifications_count = SystemNotification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = SystemNotification.objects.filter(user=request.user)[:5]
        return {
            'unread_notifications_count': unread_notifications_count,
            'recent_notifications': recent_notifications,
            'is_admin': getattr(request.user, 'is_admin_user', False),
            'is_analyst': getattr(request.user, 'is_analyst_user', False),
            'app_title': 'RetailAnalytics Pro',
            'project_id': '25521 / 5121',
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'is_admin': False,
        'is_analyst': False,
        'app_title': 'RetailAnalytics Pro',
        'project_id': '25521 / 5121',
    }
