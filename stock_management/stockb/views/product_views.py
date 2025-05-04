from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F, Q, Count
from ..forms import ProductForm
from ..models import Product, StockIn, StockInDetail, ProductCategory, ProductDetail, Supplier


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

    # Lọc theo trạng thái tồn kho
    if filter_stock_status == 'low_stock':
        products = products.filter(quantity__lte=F('minimum_stock'))
    elif filter_stock_status == 'out_of_stock':
        products = products.filter(quantity=0)

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
    product_details = ProductDetail.objects.filter(product=product).select_related('product__category', 'product__unit')
    total_remaining_quantity = product_details.aggregate(total=Sum('remaining_quantity'))['total'] or 0

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
            messages.success(request, "Đã lưu sản phẩm thành công!")
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
        product.delete()
        messages.success(request, "Đã xóa sản phẩm thành công!")
        return redirect('product')
    return redirect('product')