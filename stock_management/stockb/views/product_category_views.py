from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from ..forms import ProductCategoryForm
from ..models import Product, StockIn, StockInDetail, ProductCategory, ProductDetail, Notification
from django.db.models import Sum, F, Q, Count

@login_required
def product_category_view(request):
    categories = ProductCategory.objects.all().order_by('category_name')
    search_text = request.GET.get('search', '').strip()
    filter_product_status = request.GET.get('product_status', '')

    if search_text:
        categories = categories.filter(
            Q(category_name__icontains=search_text) |
            Q(description__icontains=search_text)
        )

    if filter_product_status == 'has_products':
        categories = categories.annotate(product_count=Count('product')).filter(product_count__gt=0)
    elif filter_product_status == 'no_products':
        categories = categories.annotate(product_count=Count('product')).filter(product_count=0)

    context = {
        "title": "Danh sách danh mục sản phẩm",
        "categories": categories,
        "search_text": search_text,
        "filter_product_status": filter_product_status,
    }
    return render(request, 'product_category/product_category_list.html', context)

@login_required
def product_category_create(request):
    form = ProductCategoryForm()

    if request.method == "POST":
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Đã tạo danh mục thành công!")
            Notification.objects.create(
                message=f"{request.user.username} đã thêm danh mục {category.category_name} thành công!",
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('product_category')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")

    context = {
        "title": "Thêm danh mục mới",
        "form": form,
    }
    return render(request, 'product_category/product_category_update.html', context)

@login_required
def product_category_detail(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    products = Product.objects.filter(category=category)
    context = {
        "title": f"Danh sách sản phẩm trong danh mục - {category.category_name}",
        "category": category,
        "products": products,
    }
    return render(request, 'product_category/product_category_detail.html', context)

@login_required
def product_category_update(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    form = ProductCategoryForm(instance=category)

    if request.method == "POST":
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, "Đã cập nhật danh mục thành công!")
            Notification.objects.create(
                message=f"{request.user.username} đã cập nhật danh mục {category.category_name} thành công!",
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('product_category')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")

    context = {
        "title": f"Chỉnh sửa danh mục - {category.category_name}",
        "form": form,
        "category": category,
    }
    return render(request, 'product_category/product_category_update.html', context)

@login_required
def product_category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    if request.method == "POST":
        if Product.objects.filter(category=category).exists():
            messages.error(request, "Không thể xóa danh mục vì vẫn còn sản phẩm liên kết!")
        else:
            category_name = category.category_name
            category.delete()
            messages.success(request, "Đã xóa danh mục thành công!")
            Notification.objects.create(
                message=f"{request.user.username} đã xóa danh mục {category_name} thành công!",
                created_at=timezone.now(),
                is_read=False
            )
        return redirect('product_category')
    return redirect('product_category')