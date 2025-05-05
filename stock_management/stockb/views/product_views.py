from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F, Q, Count
from django.utils import timezone

from ..forms import ProductForm
from ..models import Product, ProductCategory, ProductDetail, Supplier, Notification


def product_view(request):
    products = Product.objects.all().order_by('product_name')



    search_text = request.GET.get('search', '').strip()
    filter_category = request.GET.get('category', '')
    filter_supplier = request.GET.get('supplier', '')
    filter_stock_status = request.GET.get('stock_status', '')

    # Tìm kiếm
    if search_text:
        products = products.filter(
            Q(product_name__icontains=search_text) |
            Q(category__category_name__icontains=search_text) |
            Q(supplier__company_name__icontains=search_text)
        )
    # Lọc theo danh mục
    if filter_category:
        products = products.filter(category__id=filter_category)

    # Lọc theo nhà cung cấp
    if filter_supplier:
        products = products.filter(supplier__id=filter_supplier)

    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    context = {
        "title": "Danh sách sản phẩm",
        "products": products,
        "search_text": search_text,
        "categories": categories,
        "suppliers": suppliers,
        "filter_category": filter_category,
        "filter_supplier": filter_supplier,
        "filter_stock_status": filter_stock_status,
    }
    return render(request, 'product/product_list.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product_details = ProductDetail.objects.filter(product=product).select_related('product__category', 'product__unit').order_by('status')
    total_remaining_quantity = ProductDetail.objects.filter(
        product=product, status='ACTIVE'
    ).aggregate(total=Sum('remaining_quantity'))['total'] or 0

    context = {
        "title": f"Chi tiết sản phẩm - {product.product_name}",
        "product": product,
        "product_details": product_details,
        "total_remaining_quantity": total_remaining_quantity,
    }
    return render(request, 'product/product_detail.html', context)

def product_update(request, pk=None):
    if pk:
        product = get_object_or_404(Product, pk=pk)
        title = f"Chỉnh sửa sản phẩm - {product.product_name}"
    else:
        product = None
        title = "Thêm sản phẩm mới"

    form = ProductForm(instance=product)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if not product.created_at:
                product.created_at = timezone.now()
            product.save()
            action = "thêm" if not pk else "cập nhật"
            messages.success(request, "Đã lưu sản phẩm thành công!")
            message = f"NV001 đã {action} sản phẩm {product.product_name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('product')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")

    context = {
        "title": title,
        "form": form,
    }
    return render(request, 'product/product_update.html', context)

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product_name = product.product_name
        product.delete()
        messages.success(request, "Đã xóa sản phẩm thành công!")
        message = f"NV001 đã xóa sản phẩm {product_name} thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('product')
    return redirect('product')

def toggle_product_detail_status(request, pk):
    if request.method == 'POST':
        product_detail = get_object_or_404(ProductDetail, pk=pk)
        # Toggle trạng thái
        if product_detail.status == 'ACTIVE':
            product_detail.status = 'UNACTIVE'
            messages.success(request, f'Lô hàng {product_detail.product_batch} đã được tắt kích hoạt.')
        else:
            product_detail.status = 'ACTIVE'
            messages.success(request, f'Lô hàng {product_detail.product_batch} đã được kích hoạt.')
        product_detail.save()
        return redirect('product_detail', pk=product_detail.product.id)
    messages.error(request, 'Yêu cầu không hợp lệ.')
    product_detail = get_object_or_404(ProductDetail, pk=pk)
    return redirect('product_detail', pk=product_detail.product.id)

def edit_product_detail(request, pk):
    if request.method == 'POST':
        product_detail = get_object_or_404(ProductDetail, pk=pk)
        try:
            new_quantity = float(request.POST.get('remaining_quantity'))
            if new_quantity >= 0:
                product_detail.remaining_quantity = new_quantity
                product_detail.save()
                messages.success(request, f'Cập nhật số lượng lô {product_detail.product_batch} thành công.')
            else:
                messages.error(request, 'Số lượng không được âm.')
        except (ValueError, TypeError):
            messages.error(request, 'Số lượng không hợp lệ.')
        return redirect('product_detail', pk=product_detail.product.id)
    messages.error(request, 'Yêu cầu không hợp lệ.')
    product_detail = get_object_or_404(ProductDetail, pk=pk)
    return redirect('product_detail', pk=product_detail.product.id)

def delete_product_detail(request, pk):
    if request.method == 'POST':
        product_detail = get_object_or_404(ProductDetail, pk=pk)
        product_id = product_detail.product.id
        try:
            product_detail.delete()
            messages.success(request, f'Lô hàng {product_detail.product_batch} đã được xóa.')
        except Exception as e:
            messages.error(request, f'Không thể xóa lô hàng {product_detail.product_batch}: {str(e)}')
        return redirect('product_detail', pk=product_id)
    messages.error(request, 'Yêu cầu không hợp lệ.')
    product_detail = get_object_or_404(ProductDetail, pk=pk)
    return redirect('product_detail', pk=product_detail.product.id)