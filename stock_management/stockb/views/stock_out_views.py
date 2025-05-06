from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404, redirect
from unidecode import unidecode
from django.db.models import Sum, F, Q

from ..forms import StockOutForm, StockOutDetailFormSet
from ..models import StockOut, Customer, StockOutDetail, ProductCategory, Product, ProductDetail


@login_required
def stock_out(request):
    stock_outs = StockOut.objects.all().order_by('-export_date')
    stock_out_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    if filter_type == 'partially_paid':
        stock_outs = stock_outs.filter(payment_status='PARTIALLY_PAID')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_outs_by_id = stock_outs.filter(id__icontains=search_text_ch)
        customers_fn = set()
        customers_ln = set()
        customers_full = set()
        all_customers = Customer.objects.all()
        for customer in all_customers:
            first_name_ch = unidecode(customer.first_name).lower()
            last_name_ch = unidecode(customer.last_name).lower()
            full_name_ch = f"{first_name_ch} {last_name_ch}"

            if search_text_ch in first_name_ch:
                customers_fn.add(customer)
            if search_text_ch in last_name_ch:
                customers_ln.add(customer)
            if search_text_ch in full_name_ch:
                customers_full.add(customer)

        customers = customers_fn | customers_ln | customers_full

        stock_outs_by_customer = stock_outs.filter(customer__in=customers)

        stock_outs = stock_outs_by_id | stock_outs_by_customer


    for stock_out in stock_outs:
        total_amount = StockOutDetail.objects.filter(export_record=stock_out).aggregate(
            total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_out_list.append({
            'id': stock_out.id,
            'export_date': stock_out.export_date,
            'customer': f"{stock_out.customer.first_name} {stock_out.customer.last_name}",
            'payment_status': stock_out.payment_status,
            'total_amount': total_amount,
        })
    context = {
        "title": "Trang xuất kho",
        'filter_type': filter_type,
        "stock_out_list" : stock_out_list,
    }
    return render(request, "stock_out/stock_out_list.html", context)

@login_required
def stock_out_update(request, pk=None):
    stock_out = get_object_or_404(StockOut, pk=pk) if pk else None
    form = StockOutForm(request.POST or None, instance=stock_out)
    formset = StockOutDetailFormSet(request.POST or None, instance=stock_out or StockOut(), prefix='stockoutdetail_set')

    if request.method == "POST":
        print("Formset data:", request.POST)
        if form.is_valid() and formset.is_valid():
            # Lưu StockOut
            stock_out = form.save(commit=False)
            if not stock_out.export_date:
                stock_out.export_date = timezone.now()
            stock_out.updated_at = timezone.now()
            stock_out.save()

            # Xử lý formset
            for detail_form in formset:
                if detail_form.cleaned_data.get('DELETE', False) and detail_form.instance.pk:
                    try:
                        detail_form.instance.delete()
                        print("Deleted StockOutDetail with id:", detail_form.instance.pk)
                    except Exception as e:
                        print("Error deleting StockOutDetail:", e)
                        detail_form.add_error(None, f"Lỗi khi xóa chi tiết: {str(e)}")
                        continue
                elif detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                    detail = detail_form.save(commit=False)
                    detail.export_record = stock_out
                    detail.product_detail = detail_form.cleaned_data.get('product_detail')

                    if detail.quantity and detail.product and detail.product_detail:
                        try:
                            detail.save()
                        except ValueError as e:
                            detail_form.add_error(None, str(e))
                            continue
                    else:
                        detail_form.add_error(None, "Thông tin sản phẩm hoặc lô không hợp lệ.")
                        continue

            if not any(formset.errors):
                messages.success(request, f"{'Cập nhật' if pk else 'Tạo mới'} đơn xuất kho thành công!")
                return redirect('stock_out')
            else:
                messages.error(request, "Có lỗi trong form, vui lòng kiểm tra lại.")
                print("Form errors:", form.errors)
                print("Formset errors:", formset.errors)
        else:
            messages.error(request, "Có lỗi trong form, vui lòng kiểm tra lại.")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    group = Group.objects.get(name="Quan ly")
    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    customers = Customer.objects.all()
    employees = User.objects.filter(is_superuser=False, groups=group)
    product_details = ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE")

    context = {
        'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'product_details': product_details,
        'customers': customers,
        'employees': employees,
    }
    return render(request, 'stock_out/stock_out_update.html', context)

@login_required
def stock_out_delete(request, pk):
    stock_out = get_object_or_404(StockOut, pk=pk)
    if request.method == 'POST':
        stock_out.delete()
        messages.success(request, 'Đơn xuất đã được xóa thành công!')
        return redirect('stock_out')
    return render(request, 'stock_out/stock_out_list.html', {'stock_out': stock_out})