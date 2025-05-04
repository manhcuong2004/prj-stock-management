from datetime import timezone
from django.core.checks import messages
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from unidecode import unidecode
from django.db.models import Sum, F, Q

from ..forms import StockOutForm, StockOutDetailFormSet, StockInForm, StockInDetailFormSet
from ..models import  ProductCategory, Product, ProductDetail, StockIn, Supplier, StockInDetail


@login_required
def stock_in(request):
    stock_ins = StockIn.objects.all().order_by('-import_date')
    stock_in_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    if filter_type == 'in_progress':
        stock_ins = stock_ins.filter(import_status='IN_PROGRESS')
    elif filter_type == 'cancel':
        stock_ins = stock_ins.filter(import_status='CANCELLED')
    elif filter_type == 'paid':
        stock_ins = stock_ins.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_ins = stock_ins.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_ins = stock_ins.filter(
            Q(id__icontains=search_text_ch) |
            Q(supplier__company_name__icontains=search_text_ch)
        ).distinct()

    for stock_in in stock_ins:
        total_amount = StockInDetail.objects.filter(import_record=stock_in).aggregate(
            total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_in_list.append({
            'id': stock_in.id,
            'import_date': stock_in.import_date,
            'supplier': stock_in.supplier.company_name,
            'product_batch': stock_in.product_batch,
            'payment_status': stock_in.payment_status,
            'import_status': stock_in.import_status,
            'total_amount': total_amount,
        })
    context = {
        "title": "Trang nhập kho",
        'filter_type': filter_type,
        "stock_in_list": stock_in_list,
    }
    return render(request, "stock_in/stock_in_list.html", context)

@login_required
def stock_in_update(request, pk=None):
    stock_in = get_object_or_404(StockIn, pk=pk) if pk else None
    form = StockInForm(request.POST or None, instance=stock_in)
    formset = StockInDetailFormSet(request.POST or None, instance=stock_in or StockIn(), prefix='stockindetail_set')

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            stock_in = form.save(commit=False)
            if not stock_in.import_date:
                stock_in.import_date = timezone.now()
            stock_in.employee = request.user
            stock_in.save()

            # Lấy mã lô chung từ form
            product_batch = form.cleaned_data.get('product_batch')

            # Xử lý formset
            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        # Xóa hàng nếu được đánh dấu DELETE
                        if detail_form.instance.pk:
                            detail_form.instance.delete()
                        continue

                    detail = detail_form.save(commit=False)
                    detail.import_record = stock_in
                    detail.save()

                    # Tạo hoặc cập nhật ProductDetail với mã lô chung
                    product_detail, created = ProductDetail.objects.get_or_create(
                        product=detail.product,
                        product_batch=product_batch,
                        defaults={
                            'stock_in_detail': detail,
                            'initial_quantity': detail.quantity,
                            'remaining_quantity': detail.quantity,
                            'import_date': stock_in.import_date,
                        }
                    )
                    if not created:
                        product_detail.initial_quantity += detail.quantity
                        product_detail.remaining_quantity += detail.quantity
                        product_detail.save()

                    # Cập nhật số lượng sản phẩm
                    detail.product.quantity += detail.quantity
                    detail.product.save()

            # Kiểm tra lỗi sau khi xử lý
            if not any(formset.errors):
                messages.success(request, 'Đơn nhập kho đã được lưu thành công!')
                return redirect('stock_in')
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    employees = User.objects.filter(is_superuser=False)

    context = {
        'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'suppliers': suppliers,
        'employees': employees,
    }
    return render(request, 'stock_in/stock_in_update.html', context)