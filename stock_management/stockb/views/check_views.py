from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from ..models import Product, ProductDetail


@login_required
def near_expiry_list_view(request):
    today = timezone.now()
    end_date = today + timedelta(days=30)
    search_query = request.GET.get('q', '')
    near_expiry_products = ProductDetail.objects.filter(
        expiry_date__range=(today, end_date),
        status = "ACTIVE"
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

    context = {
        "title": "Hàng gần đến ngày hết hạn",
        "near_expiry_products": products_with_days_left,
        "search_query": search_query,
    }
    return render(request, 'check/near_expiry_list.html', context)


def low_stock_list_view(request):
    low_stock_products = []
    products = Product.objects.all().prefetch_related('product_details').select_related('category', 'unit')

    for product in products:
        total_quantity = product.product_details.aggregate(total=Sum('remaining_quantity'))['total'] or 0
        if total_quantity <= product.minimum_stock:
            low_stock_products.append({
                'product': product,
                'total_quantity': total_quantity,
                'minimum_stock': product.minimum_stock,
            })

    context = {
        "title": "Hàng gần hết trong kho",
        "low_stock_products": low_stock_products,
    }
    return render(request, 'check/low_stock_list.html', context)