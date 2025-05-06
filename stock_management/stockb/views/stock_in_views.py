from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from unidecode import unidecode
from django.db.models import Sum, F, Q

from ..forms import   StockInForm, StockInDetailFormSet
from ..models import  ProductCategory, Product, ProductDetail, StockIn, Supplier, StockInDetail


@login_required
def stock_in(request):
    stock_ins = StockIn.objects.all().order_by('-import_date')
    stock_in_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    if filter_type == 'partially_paid':
        stock_ins = stock_ins.filter(payment_status='PARTIALLY_PAID')
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
            total=Sum(F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_in_list.append({
            'id': stock_in.id,
            'import_date': stock_in.import_date,
            'supplier': stock_in.supplier.company_name,
            'payment_status': stock_in.payment_status,
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
            # Lưu StockIn
            stock_in = form.save(commit=False)
            if not stock_in.import_date:
                stock_in.import_date = timezone.now()
            stock_in.employee = request.user
            stock_in.save()

            # Xử lý formset
            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        if detail_form.instance.pk:
                            # Xóa ProductDetail liên quan nếu có
                            if detail_form.instance.product_detail:
                                detail_form.instance.product_detail.delete()
                            detail_form.instance.delete()
                        continue

                    detail = detail_form.save(commit=False)
                    detail.import_record = stock_in
                    product = detail_form.cleaned_data.get('product')
                    product_batch = detail_form.cleaned_data.get('product_batch')
                    quantity = detail_form.cleaned_data.get('quantity')

                    if not (product and product_batch and quantity):
                        detail_form.add_error(None, "Thông tin sản phẩm, mã lô hoặc số lượng không hợp lệ.")
                        continue

                    # Kiểm tra nếu đang cập nhật
                    if detail.pk and detail.product_detail:
                        product_detail = detail.product_detail
                        product_detail.product_batch = product_batch
                        product_detail.initial_quantity = quantity
                        product_detail.remaining_quantity = quantity  # Cập nhật lại
                        product_detail.import_date = stock_in.import_date
                        product_detail.save()
                    else:
                        # Tạo ProductDetail mới
                        product_detail = ProductDetail(
                            product=product,
                            product_batch=product_batch,
                            initial_quantity=quantity,
                            remaining_quantity=quantity,
                            import_date=stock_in.import_date or timezone.now(),
                            status='ACTIVE'
                        )
                        product_detail.save()

                    # Gán ProductDetail vào StockInDetail
                    detail.product_detail = product_detail
                    detail.save()

            # Kiểm tra lỗi sau khi xử lý
            if not any(formset.errors):
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

@login_required
def stock_in_delete(request, pk):
    stock_in = get_object_or_404(StockIn, pk=pk)
    if request.method == 'POST':
        stock_in.delete()
        messages.success(request, 'Đơn nhập đã được xóa thành công!')
        return redirect('stock_in')
    return render(request, 'stock_in/stock_in_list.html', {'stock_in': stock_in})