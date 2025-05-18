from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Notification

@login_required
def get_notifications(request):
    unread_count = Notification.objects.filter(is_read=False).count()
    notifications = Notification.objects.all().order_by('-created_at')[:50]
    data = [
        {
            'message': notification.message,
            'employee': {'username': notification.employee.username} if notification.employee else None,
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

@login_required
def activity_log_list(request):
    action_filter = request.GET.get('action_filter', 'all')
    employee_filter = request.GET.get('employee_filter', 'all')
    search_text = request.GET.get('search', '')

    logs = Notification.objects.all()

    if action_filter != 'all':
        if action_filter == 'create':
            logs = logs.filter(message__icontains='thêm')
        elif action_filter == 'update':
            logs = logs.filter(message__icontains='cập nhật')
        elif action_filter == 'delete':
            logs = logs.filter(message__icontains='xóa')

    # Lọc theo nhân viên
    if employee_filter != 'all':
        logs = logs.filter(employee_id=employee_filter)

    if search_text:
        logs = logs.filter(
            Q(message__icontains=search_text) |
            Q(employee__username__icontains=search_text)
        )

    employees = User.objects.filter(is_active=True).order_by('username')

    context = {
        'title': 'Lịch sử hoạt động',
        'logs': logs,
        'action_filter': action_filter,
        'employee_filter': employee_filter,
        'search_text': search_text,
        'employees': employees,
    }
    return render(request, 'activity_log/activity_log.html', context)





















@login_required
def notification_list(request):
    search_text = request.GET.get('search', '').strip()
    filter_read_status = request.GET.get('read_status', '')
    notifications = Notification.objects.all().order_by('-created_at')
    if search_text:
        notifications = notifications.filter(message__icontains=search_text)
    if filter_read_status:
        notifications = notifications.filter(is_read=filter_read_status == 'read')
    unread_notifications = Notification.objects.filter(is_read=False).count()
    context = {
        'title': 'Danh sách thông báo',
        'notifications': notifications,
        'unread_count': unread_notifications,
        'search_text': search_text,
        'filter_read_status': filter_read_status,
    }
    return render(request, 'notification/notification_list.html', context)

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == 'POST':
        notification.is_read = True
        notification.save()
        messages.success(request, 'Thông báo đã được đánh dấu là đã đọc.')
        return redirect('notification_list')
    return redirect('notification_list')

@login_required
def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Thông báo đã được xóa.')
        return redirect('notification_list')
    return redirect('notification_list')