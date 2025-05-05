document.addEventListener('DOMContentLoaded', function() {
    // Cấu hình toastr
    toastr.options = {
        "positionClass": "toast-top-right",
        "timeOut": "3000",
        "closeButton": true,
        "progressBar": true
    };

    // Hiển thị thông báo từ Django messages
    {% for message in messages %}
        toastr["{{ message.tags }}"]("{{ message }}");
    {% endfor %}

    const notificationDropdown = document.getElementById('notificationDropdown');
    const unreadIndicator = document.getElementById('unreadIndicator');
    const notificationList = document.getElementById('notificationList');

    // Hàm lấy CSRF token từ cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // Lấy danh sách thông báo từ API
    function fetchNotifications() {
        fetch('/notifications/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            notificationList.innerHTML = '';
            let unreadCount = data.unread_count || 0;
            if (!data.notifications || data.notifications.length === 0) {
                notificationList.innerHTML = '<div class="dropdown-item text-muted">Không có thông báo nào.</div>';
            } else {
                data.notifications.forEach(notification => {
                    const div = document.createElement('div');
                    div.className = 'notification-item' + (notification.is_read ? '' : ' unread');
                    div.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <span>${notification.message}</span>
                            <small class="text-muted">${notification.created_at}</small>
                        </div>
                    `;
                    notificationList.appendChild(div);
                });
            }
            // Hiển thị/ẩn dấu chấm đỏ
            unreadIndicator.style.display = unreadCount > 0 ? 'inline-block' : 'none';
        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
            notificationList.innerHTML = '<div class="dropdown-item text-danger">Không thể tải thông báo.</div>';
        });
    }

    // Đánh dấu tất cả thông báo là đã đọc
    function markNotificationsAsRead() {
        fetch('/notifications/mark-as-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                fetchNotifications();
            }
        })
        .catch(error => console.error('Error marking notifications as read:', error));
    }

    // Khi nhấn vào icon chuông, đánh dấu đã đọc và ẩn dấu chấm đỏ
    notificationDropdown.addEventListener('click', function() {
        if (unreadIndicator.style.display !== 'none') {
            markNotificationsAsRead();
        }
    });

    // Cập nhật định kỳ (mỗi 30 giây)
    setInterval(fetchNotifications, 30000);

    // Lấy thông báo lần đầu khi tải trang
    fetchNotifications();
});