from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Prefetch
from datetime import timedelta
from ..models import Product, ProductDetail

@login_required
def near_expiry_list_view(request):
    today = timezone.now()
    end_date = today + timedelta(days=30)
    search_query = request.GET.get('q', '')
    status = request.GET.get('status', 'unchecked')

    if request.method == 'POST' and 'check_id' in request.POST:
        detail_id = request.POST.get('check_id')
        try:
            product_detail = ProductDetail.objects.get(id=detail_id)
            inspection_time = product_detail.product.inspection_time
            if inspection_time is None:
                messages.error(request, "Không thể cập nhật: Thời gian kiểm tra (inspection_time) không hợp lệ!")
            else:
                product_detail.checked_at = timezone.now()
                product_detail.expiry_date = product_detail.checked_at + timedelta(days=inspection_time)
                product_detail.save()
                messages.success(request, f"Đã cập nhật trạng thái kiểm tra và ngày hết hạn thành công! Mới: {product_detail.expiry_date}")
        except ProductDetail.DoesNotExist:
            messages.error(request, "Không tìm thấy sản phẩm để cập nhật!")

    if status == 'checked':
        near_expiry_products = ProductDetail.objects.filter(
            status="ACTIVE",
            checked_at__isnull=False
        ).select_related('product__category', 'product__unit').order_by('expiry_date')
    else:
        near_expiry_products = ProductDetail.objects.filter(
            expiry_date__lte=end_date,
            status="ACTIVE",
            checked_at__isnull=True
        ).select_related('product__category', 'product__unit').order_by('expiry_date')

    if search_query:
        near_expiry_products = near_expiry_products.filter(product__product_name__icontains=search_query)

    products_with_days_left = []
    for detail in near_expiry_products:
        days_left = (detail.expiry_date - today).days
        products_with_days_left.append({
            'detail': detail,
            'days_left': max(0, days_left),
        })

    paginator = Paginator(products_with_days_left, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    title = "Hàng gần đến ngày kiểm tra - Đã kiểm tra" if status == 'checked' else "Hàng gần đến ngày kiểm tra - Chưa kiểm tra"

    context = {
        "title": title,
        "products_with_days_left": page_obj,
        "search_query": search_query,
        "status": status,
    }
    return render(request, 'check/near_expiry_list.html', context)


def low_stock_list_view(request):
    search_query = request.GET.get('q', '')
    low_stock_products = []

    product_details_active = ProductDetail.objects.filter(status="ACTIVE")
    products = Product.objects.all().prefetch_related(
        Prefetch('product_details', queryset=product_details_active)
    ).select_related('category', 'unit')

    if search_query:
        products = products.filter(product_name__icontains=search_query)

    for product in products:
        total_quantity = product.product_details.aggregate(total=Sum('remaining_quantity'))['total'] or 0
        if total_quantity <= product.minimum_stock:
            low_stock_products.append({
                'product': product,
                'total_quantity': total_quantity,
                'minimum_stock': product.minimum_stock,
            })

    paginator = Paginator(low_stock_products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Hàng gần hết trong kho",
        "low_stock_products": page_obj,
        "search_query": search_query,
    }
    return render(request, 'check/low_stock_list.html', context)