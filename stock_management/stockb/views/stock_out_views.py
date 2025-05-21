import pandas as pd
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404, redirect
from unidecode import unidecode
from django.db.models import Sum, F, Q
from ..forms import StockOutForm, StockOutDetailFormSet
from ..models import StockOut, Customer, StockOutDetail, ProductCategory, Product, ProductDetail, Notification

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
        "stock_out_list": stock_out_list,
    }
    return render(request, "stock_out/stock_out_list.html", context)

@login_required
def stock_out_update(request, pk=None):
    stock_out = get_object_or_404(StockOut, pk=pk) if pk else None
    action = "Cập nhật" if pk else "Thêm"
    form = StockOutForm(request.POST or None, instance=stock_out)
    formset = StockOutDetailFormSet(request.POST or None, instance=stock_out or StockOut(), prefix='stockoutdetail_set')

    if request.method == "POST":
        print("Formset data:", request.POST)
        if form.is_valid() and formset.is_valid():
            stock_out = form.save(commit=False)
            if not stock_out.export_date:
                stock_out.export_date = timezone.now()
            stock_out.updated_at = timezone.now()
            stock_out.save()

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
                messages.success(request, f"{action.capitalize()} đơn xuất kho thành công!")
                Notification.objects.create(
                    message=f"{action} đơn xuất kho ID {stock_out.id} thành công!",
                    employee=request.user,
                    created_at=timezone.now(),
                    is_read=False
                )
                return redirect('stock_out')
            else:
                messages.error(request, "Có lỗi trong form, vui lòng kiểm tra lại.")
                print("Form errors:", form.errors)
                print("Formset errors:", formset.errors)
        else:
            messages.error(request, "Có lỗi trong form, vui lòng kiểm tra lại.")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    customers = Customer.objects.all()
    employees = User.objects.filter(is_superuser=False)
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
        stock_out_id = stock_out.id
        stock_out.delete()
        messages.success(request, 'Đơn xuất đã được xóa thành công!')
        Notification.objects.create(
            message=f"Xóa đơn xuất kho ID {stock_out_id} thành công!",
            employee=request.user,
            created_at=timezone.now(),
            is_read=False
        )
        return redirect('stock_out')
    return render(request, 'stock_out/stock_out_list.html', {'stock_out': stock_out})

@login_required
def export_all_stockout_excel(request):
    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    # Lấy tất cả các đơn xuất kho, tối ưu hóa truy vấn với select_related và prefetch_related
    stock_outs = StockOut.objects.all().select_related('customer', 'employee').prefetch_related(
        'stockoutdetail_set__product', 'stockoutdetail_set__product_detail'
    )

    # Lọc theo trạng thái thanh toán
    if filter_type == 'partially_paid':
        stock_outs = stock_outs.filter(payment_status='PARTIALLY_PAID')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    # Tìm kiếm theo mã đơn xuất hoặc tên khách hàng
    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_outs = stock_outs.filter(
            Q(id__icontains=search_text_ch) |
            Q(customer__first_name__icontains=search_text_ch) |
            Q(customer__last_name__icontains=search_text_ch)
        ).distinct()

    # Nếu không tìm thấy đơn xuất kho nào, trả về thông báo lỗi
    if not stock_outs.exists():
        return HttpResponse("Không tìm thấy đơn xuất kho nào phù hợp.", status=404)

    # Tạo danh sách dữ liệu
    data = []
    for stock_out in stock_outs:
        details = stock_out.stockoutdetail_set.all()  # Truy cập StockOutDetail
        for detail in details:
            data.append({
                'Mã đơn xuất': stock_out.id,
                'Ngày xuất': stock_out.export_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Khách hàng': f"{stock_out.customer.first_name} {stock_out.customer.last_name}" if stock_out.customer else 'N/A',
                'Trạng thái thanh toán': stock_out.get_payment_status_display(),
                'Tổng tiền': stock_out.total_amount(),
                'Số tiền đã trả': stock_out.amount_paid,
                'Nợ còn lại': stock_out.remaining_debt(),
                'Ghi chú': stock_out.notes or '',
                'Nhân viên': stock_out.employee.username if stock_out.employee else 'N/A',
                'Sản phẩm': detail.product.product_name,
                'Lô sản phẩm': detail.product_detail.product_batch,
                'Số lượng': detail.quantity,
                'Giá bán': detail.product.selling_price,
                'Chiết khấu (%)': detail.discount,
                'Tổng tiền chi tiết': detail.quantity * detail.product.selling_price * (1 - detail.discount / 100),
            })
        if not details:
            data.append({
                'Mã đơn xuất': stock_out.id,
                'Ngày xuất': stock_out.export_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Khách hàng': f"{stock_out.customer.first_name} {stock_out.customer.last_name}" if stock_out.customer else 'N/A',
                'Trạng thái thanh toán': stock_out.get_payment_status_display(),
                'Tổng tiền': stock_out.total_amount(),
                'Số tiền đã trả': stock_out.amount_paid,
                'Nợ còn lại': stock_out.remaining_debt(),
                'Ghi chú': stock_out.notes or '',
                'Nhân viên': stock_out.employee.username if stock_out.employee else 'N/A',
                'Sản phẩm': '',
                'Lô sản phẩm': '',
                'Số lượng': 0,
                'Giá bán': 0,
                'Chiết khấu (%)': 0,
                'Tổng tiền chi tiết': 0,
            })
    df = pd.DataFrame(data)

    # Tạo response Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=stockout_all_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response


@login_required
def export_single_stockout_excel(request, stockout_id):
    stock_out = get_object_or_404(StockOut, id=stockout_id)

    data = []
    details = stock_out.stockoutdetail_set.all().select_related('product', 'product_detail')
    for detail in details:
        data.append({
            'Mã đơn xuất': stock_out.id,
            'Ngày xuất': stock_out.export_date.strftime('%Y-%m-%d %H:%M:%S'),
            'Khách hàng': f"{stock_out.customer.first_name} {stock_out.customer.last_name}" if stock_out.customer else 'N/A',
            'Trạng thái thanh toán': stock_out.get_payment_status_display(),
            'Tổng tiền': stock_out.total_amount(),
            'Số tiền đã trả': stock_out.amount_paid,
            'Nợ còn lại': stock_out.remaining_debt(),
            'Ghi chú': stock_out.notes or '',
            'Nhân viên': stock_out.employee.username if stock_out.employee else 'N/A',
            'Sản phẩm': detail.product.product_name,
            'Lô sản phẩm': detail.product_detail.product_batch,
            'Số lượng': detail.quantity,
            'Giá bán': detail.product.selling_price,
            'Chiết khấu (%)': detail.discount,
            'Tổng tiền chi tiết': detail.quantity * detail.product.selling_price * (1 - detail.discount / 100),
        })
    if not details:
        data.append({
            'Mã đơn xuất': stock_out.id,
            'Ngày xuất': stock_out.export_date.strftime('%Y-%m-%d %H:%M:%S'),
            'Khách hàng': f"{stock_out.customer.first_name} {stock_out.customer.last_name}" if stock_out.customer else 'N/A',
            'Trạng thái thanh toán': stock_out.get_payment_status_display(),
            'Tổng tiền': stock_out.total_amount(),
            'Số tiền đã trả': stock_out.amount_paid,
            'Nợ còn lại': stock_out.remaining_debt(),
            'Ghi chú': stock_out.notes or '',
            'Nhân viên': stock_out.employee.username if stock_out.employee else 'N/A',
            'Sản phẩm': '',
            'Lô sản phẩm': '',
            'Số lượng': 0,
            'Giá bán': 0,
            'Chiết khấu (%)': 0,
            'Tổng tiền chi tiết': 0,
        })
    df = pd.DataFrame(data)

    # Tạo response Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=stockout_{stockout_id}_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response