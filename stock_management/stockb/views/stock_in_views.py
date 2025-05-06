from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from unidecode import unidecode
from django.db.models import Sum, F, Q
from ..forms import StockInForm, StockInDetailFormSet
from ..models import ProductCategory, Product, ProductDetail, StockIn, Supplier, StockInDetail, Notification

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
    action = "cập nhật" if pk else "thêm"
    form = StockInForm(request.POST or None, instance=stock_in)
    formset = StockInDetailFormSet(request.POST or None, instance=stock_in or StockIn(), prefix='stockindetail_set')

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            stock_in = form.save(commit=False)
            if not stock_in.import_date:
                stock_in.import_date = timezone.now()
            stock_in.save()

            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        if detail_form.instance.pk:
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

                    if detail.pk and detail.product_detail:
                        product_detail = detail.product_detail
                        product_detail.product_batch = product_batch
                        product_detail.initial_quantity = quantity
                        product_detail.remaining_quantity = quantity
                        product_detail.import_date = stock_in.import_date
                        product_detail.save()
                    else:
                        product_detail = ProductDetail(
                            product=product,
                            product_batch=product_batch,
                            initial_quantity=quantity,
                            remaining_quantity=quantity,
                            import_date=stock_in.import_date or timezone.now(),
                            status='ACTIVE'
                        )
                        product_detail.save()

                    detail.product_detail = product_detail
                    detail.save()

            if not any(formset.errors):
                messages.success(request, f'{action.capitalize()} đơn nhập kho thành công!')
                Notification.objects.create(
                    message=f"{request.user.username} đã {action} đơn nhập kho ID {stock_in.id} thành công!",
                    created_at=timezone.now(),
                    is_read=False
                )
                return redirect('stock_in')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")
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
        stock_in_id = stock_in.id
        stock_in.delete()
        messages.success(request, 'Đơn nhập đã được xóa thành công!')
        Notification.objects.create(
            message=f"{request.user.username} đã xóa đơn nhập kho ID {stock_in_id} thành công!",
            created_at=timezone.now(),
            is_read=False
        )
        return redirect('stock_in')
    return render(request, 'stock_in/stock_in_list.html', {'stock_in': stock_in})