from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Max
from django.shortcuts import render, redirect, get_object_or_404
from stockb.models import Customer, StockOutDetail, StockOut
from django.contrib import messages
from django.utils import timezone
from django.db import connection
@login_required
def customer_list(request):
    # Chỉ chọn các trường hiện có trong database
    customers = Customer.objects.only(
        'id', 'first_name', 'last_name', 'email', 'phone', 'address', 'created_at', 'updated_at'
    ).order_by('-created_at')

    # Xử lý tìm kiếm
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # Phân trang
    paginator = Paginator(customers, 10)  # Hiển thị 10 khách hàng trên mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Danh sách khách hàng",
        'customers': page_obj
    }
    return render(request, "customer/customer_list.html", context)

@login_required
def customer_create(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        # Kiểm tra dữ liệu
        if not first_name or not last_name or not phone or not address:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc!')
            return render(request, "customer/customer_form.html", {
                'title': 'Thêm mới khách hàng',
                'form_data': request.POST
            })

        # Tạo khách hàng mới
        try:
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            customer.save()
            messages.success(request, 'Thêm khách hàng thành công!')
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    context = {
        "title": "Thêm mới khách hàng",
        "form_data": {}
    }
    return render(request, "customer/customer_form.html", context)

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        customer.first_name = request.POST.get('first_name')
        customer.last_name = request.POST.get('last_name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')

        # Kiểm tra dữ liệu
        if not customer.first_name or not customer.last_name or not customer.phone or not customer.address:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc!')
            return render(request, "customer/customer_update.html", {
                'title': 'Cập nhật khách hàng',
                'customer': customer
            })

        # Cập nhật khách hàng
        try:
            customer.updated_at = timezone.now()
            customer.save()
            messages.success(request, 'Cập nhật khách hàng thành công!')
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    # Lấy thông tin đơn hàng của khách hàng
    customer_orders = StockOut.objects.filter(customer=customer).order_by('-export_date')

    # Tính tổng chi tiêu
    total_spent = StockOutDetail.objects.filter(
        export_record__customer=customer,
        export_record__export_status='COMPLETED'
    ).aggregate(
        total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
    )['total'] or 0

    # Tính nợ phải thu
    debt_amount = StockOutDetail.objects.filter(
        export_record__customer=customer,
        export_record__payment_status__in=['UNPAID', 'PARTIALLY_PAID']
    ).aggregate(
        total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
    )['total'] or 0

    last_order = StockOut.objects.filter(customer=customer).order_by('-export_date').first()
    last_order_date = last_order.export_date.strftime('%d/%m/%Y') if last_order else None

    context = {
        "title": "Cập nhật thông tin khách hàng",
        "customer": customer,
        "customer_orders": customer_orders[:5],
        "order_count": customer_orders.count(),
        "total_spent": total_spent,
        "debt_amount": debt_amount,
        "last_order_date": last_order_date
    }
    return render(request, "customer/customer_update.html", context)

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        try:
            related_orders = StockOut.objects.filter(customer=customer).exists()

            if related_orders and not request.POST.get('force_delete') == 'true':
                messages.error(request, 'Không thể xóa khách hàng này vì có đơn hàng liên quan!')
                return redirect('customer_list')

            customer_id = customer.id
            customer_name = f"{customer.last_name} {customer.first_name}"

            if related_orders and request.POST.get('force_delete') == 'true':
                StockOut.objects.filter(customer=customer).delete()

            # Xóa khách hàng
            customer.delete()

            reset_autoincrement_for_customer(customer_id)

            messages.success(request, f'Đã xóa khách hàng {customer_name} thành công và đặt lại ID!')

            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa khách hàng: {str(e)}')
            return redirect('customer_list')

    related_orders = StockOut.objects.filter(customer=customer)
    has_related_orders = related_orders.exists()
    order_count = related_orders.count() if has_related_orders else 0

    context = {
        "title": "Xóa khách hàng",
        "customer": customer,
        "has_related_orders": has_related_orders,
        "order_count": order_count,
        "allow_force_delete": request.user.is_superuser
    }
    return render(request, "customer/customer_confirm_delete.html", context)

def reset_autoincrement_for_customer(deleted_id):

    try:
        with connection.cursor() as cursor:
            max_id = Customer.objects.aggregate(Max('id'))['id__max'] or 0


            new_seq_value = max_id

            cursor.execute(f"UPDATE sqlite_sequence SET seq = {new_seq_value} WHERE name = 'stockb_customer'")

            print(f"Đã đặt lại sequence cho bảng Customer: {new_seq_value}")
    except Exception as e:
        print(f"Lỗi khi đặt lại sequence: {str(e)}")