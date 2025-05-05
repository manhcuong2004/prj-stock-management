from .models import Notification

def notifications(request):
    return {
        'notifications': Notification.objects.all()[:50]  # Lấy 50 thông báo mới nhất
    }