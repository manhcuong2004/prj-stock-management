from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import Notification

@login_required
def get_notifications(request):
    unread_count = Notification.objects.filter(is_read=False).count()
    notifications = Notification.objects.all().order_by('-created_at')[:50]
    data = [
        {
            'message': notification.message,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_read': notification.is_read,
        }
        for notification in notifications
    ]
    return JsonResponse({'notifications': data, 'unread_count': unread_count})
@login_required
def mark_notifications_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)