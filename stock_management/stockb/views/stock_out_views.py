import datetime

import pandas as pd
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, get_object_or_404, redirect
from unidecode import unidecode
from django.db.models import Sum, F, Q
from ..forms import StockOutForm, StockOutDetailFormSet, StockOutImportForm
from ..models import StockOut, Customer, StockOutDetail, ProductCategory, Product, ProductDetail, Notification

@login_required
def stock_out(request):
    stock_outs = StockOut.objects.all().order_by('-export_date')
    stock_out_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if filter_type == 'partially_paid':
        stock_outs = stock_outs.filter(payment_status='PARTIALLY_PAID')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_outs = stock_outs.filter(
            Q(id__icontains=search_text_ch) |
            Q(customer__first_name__icontains=search_text_ch) |
            Q(customer__last_name__icontains=search_text_ch)
        ).distinct()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end_date_obj < start_date_obj:
                messages.warning(request, "Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")
            else:
                end_date_obj = end_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
                stock_outs = stock_outs.filter(export_date__range=(start_date_obj, end_date_obj))
        except ValueError:
            stock_outs = StockOut.objects.none()
    elif start_date or end_date:
        messages.warning(request, "Vui lòng nhập cả ngày bắt đầu và ngày kết thúc.")

    for stock_out in stock_outs:
        stock_out_list.append({
            'id': stock_out.id,
            'export_date': stock_out.export_date,
            'customer': f"{stock_out.customer.first_name} {stock_out.customer.last_name}",
            'payment_status': stock_out.payment_status,
            'total_amount': stock_out.total_amount(),
        })

    paginator = Paginator(stock_out_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "title": "Trang xuất kho",
        'filter_type': filter_type,
        "stock_out_list": page_obj,
        "search_text": search_text,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "stock_out/stock_out_list.html", context)

@login_required
def stock_out_update(request, pk=None):
    stock_out = get_object_or_404(StockOut, pk=pk) if pk else None
    action = "Cập nhật" if pk else "Thêm"
    form = StockOutForm(request.POST or None, instance=stock_out)
    formset = StockOutDetailFormSet(request.POST or None, instance=stock_out or StockOut(), prefix='stockoutdetail_set')

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            stock_out = form.save(commit=False)
            if not stock_out.export_date:
                stock_out.export_date = timezone.now().date()
            stock_out.created_by = request.user if not stock_out else stock_out.created_by
            stock_out.updated_by = request.user
            stock_out.updated_at = timezone.now()
            stock_out.save()

            for detail_form in formset:
                if detail_form.cleaned_data.get('DELETE', False) and detail_form.instance.pk:
                    try:
                        detail_form.instance.delete()
                    except Exception as e:
                        messages.error(request, f"Lỗi khi xóa chi tiết: {str(e)}")
                        return render(request, 'stock_out/stock_out_update.html', {
                            'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
                            'form': form,
                            'formset': formset,
                            'categories': ProductCategory.objects.all(),
                            'products': Product.objects.all(),
                            'product_details': ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE"),
                            'customers': Customer.objects.all(),
                        })
                elif detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                    detail = detail_form.save(commit=False)
                    detail.export_record = stock_out
                    detail.product_detail = detail_form.cleaned_data.get('product_detail')
                    detail.product = detail_form.cleaned_data.get('product')

                    if not detail.pk and not detail.selling_price:
                        detail.selling_price = detail.product.selling_price

                    if detail.quantity and detail.product and detail.product_detail:
                        try:
                            detail.save()
                        except ValueError as e:
                            messages.error(request, f"Lỗi khi lưu chi tiết: {str(e)}")
                            return render(request, 'stock_out/stock_out_update.html', {
                                'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
                                'form': form,
                                'formset': formset,
                                'categories': ProductCategory.objects.all(),
                                'products': Product.objects.all(),
                                'product_details': ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE"),
                                'customers': Customer.objects.all(),
                            })
                    else:
                        messages.error(request, "Thông tin sản phẩm, lô hoặc số lượng không hợp lệ.")
                        return render(request, 'stock_out/stock_out_update.html', {
                            'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
                            'form': form,
                            'formset': formset,
                            'categories': ProductCategory.objects.all(),
                            'products': Product.objects.all(),
                            'product_details': ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE"),
                            'customers': Customer.objects.all(),
                        })

            messages.success(request, f"{action.capitalize()} đơn xuất kho ID {stock_out.id} thành công!")
            Notification.objects.create(
                message=f"{action} đơn xuất kho ID {stock_out.id} thành công!",
                employee=request.user,
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('stock_out')
        else:
            error_messages = []
            if form.errors:
                error_text = form.errors.as_text().replace('\n', ' ')
                error_messages.append(f"Lỗi trong form chính: {error_text}")
            for i, detail_form in enumerate(formset.forms):
                if detail_form.errors:
                    error_text = detail_form.errors.as_text().replace('\n', ' ')
                    error_messages.append(f"Lỗi trong chi tiết {error_text}")
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại: " + " ".join(error_messages))

    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    customers = Customer.objects.all()
    product_details = ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE")

    context = {
        'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'product_details': product_details,
        'customers': customers,
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
def delete_stockout_detail(request, pk):
    stock_out_detail = get_object_or_404(StockOutDetail, pk=pk)
    stock_out_id = stock_out_detail.export_record.id
    stock_out_detail.delete()
    if request.method == 'POST':
        try:
            stock_out_detail.delete()
            messages.success(request, 'Chi tiết xuất kho đã được xóa thành công!')
            Notification.objects.create(
                message=f"Xóa chi tiết xuất kho ID {pk} thành công!",
                employee=request.user,
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('stock_out_update', pk=stock_out_id)
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa chi tiết xuất kho: {str(e)}')
            return redirect('stock_out_update', pk=stock_out_id)
    return redirect('stock_out_update', pk=stock_out_id)

@login_required
def export_all_stockout_excel(request):
    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    stock_outs = StockOut.objects.all().select_related('customer', 'created_by').prefetch_related(
        'stockoutdetail_set__product', 'stockoutdetail_set__product_detail'
    )

    if filter_type == 'partially_paid':
        stock_outs = stock_outs.filter(payment_status='PARTIALLY_PAID')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_outs = stock_outs.filter(
            Q(id__icontains=search_text_ch) |
            Q(customer__first_name__icontains=search_text_ch) |
            Q(customer__last_name__icontains=search_text_ch)
        ).distinct()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end_date_obj < start_date_obj:
                messages.warning(request, "Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")
            else:
                end_date_obj = end_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
                stock_outs = stock_outs.filter(export_date__range=(start_date_obj, end_date_obj))
        except ValueError:
            stock_outs = StockOut.objects.none()
    elif start_date or end_date:
        messages.warning(request, "Vui lòng nhập cả ngày bắt đầu và ngày kết thúc.")

    if not stock_outs.exists():
        return HttpResponse("Không tìm thấy đơn xuất kho nào phù hợp.", status=404)

    data = []
    for stock_out in stock_outs:
        details = stock_out.stockoutdetail_set.all()
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
                'Nhân viên': stock_out.created_by.username if stock_out.created_by else 'N/A',
                'Sản phẩm': detail.product.product_name,
                'Lô sản phẩm': detail.product_detail.product_batch,
                'Số lượng': detail.quantity,
                'Giá bán': detail.selling_price,
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
            'Nhân viên': stock_out.created_by.username if stock_out.created_by else 'N/A',
            'Sản phẩm': detail.product.product_name,
            'Lô sản phẩm': detail.product_detail.product_batch,
            'Số lượng': detail.quantity,
            'Giá bán': detail.selling_price,
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
            'Nhân viên': stock_out.created_by.username if stock_out.created_by else 'N/A',
            'Sản phẩm': '',
            'Lô sản phẩm': '',
            'Số lượng': 0,
            'Giá bán': 0,
            'Chiết khấu (%)': 0,
            'Tổng tiền chi tiết': 0,
        })
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=stockout_{stockout_id}_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response



@login_required
def import_stockout(request):
    if request.method == 'POST':
        form = StockOutImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file, engine='openpyxl')

                required_columns = [
                    'Mã đơn xuất', 'Ngày xuất', 'ID Khách hàng', 'Trạng thái thanh toán',
                    'Số tiền đã trả', 'Ghi chú', 'ID Nhân viên', 'ID Sản phẩm',
                    'Lô sản phẩm', 'Số lượng', 'Chiết khấu (%)'
                ]
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, "File Excel không đúng định dạng. Vui lòng kiểm tra các cột.")
                    return render(request, 'stock_out/import_stockout.html', {'form': form})

                numeric_columns = ['Số tiền đã trả', 'Số lượng', 'Chiết khấu (%)']
                for col in numeric_columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                        df[col] = df[col].astype(float)
                    except Exception as e:
                        messages.error(request, f"Lỗi định dạng cột '{col}': {str(e)}")
                        return render(request, 'stock_out/import_stockout.html', {'form': form})

                grouped = df.groupby('Mã đơn xuất')

                with transaction.atomic():
                    for stockout_id, group in grouped:
                        stockout_data = group.iloc[0]

                        customer_id = stockout_data['ID Khách hàng']
                        customer = None
                        if pd.notna(customer_id):
                            customer = Customer.objects.filter(id=customer_id).first()
                            if not customer:
                                messages.error(request, f"Khách hàng với ID '{customer_id}' không tồn tại.")
                                return render(request, 'stock_out/import_stockout.html', {'form': form})

                        employee_id = stockout_data['ID Nhân viên']
                        employee = User.objects.filter(id=employee_id).first()
                        if not employee:
                            messages.error(request, f"Nhân viên với ID '{employee_id}' không tồn tại.")
                            return render(request, 'stock_out/import_stockout.html', {'form': form})

                        stockout, created = StockOut.objects.get_or_create(
                            id=stockout_id,
                            defaults={
                                'export_date': pd.to_datetime(stockout_data['Ngày xuất']),
                                'amount_paid': float(stockout_data['Số tiền đã trả']),
                                'payment_status': stockout_data['Trạng thái thanh toán'].upper(),
                                'notes': stockout_data['Ghi chú'] if pd.notna(stockout_data['Ghi chú']) else '',
                                'customer': customer,
                                'created_by': employee,
                            }
                        )

                        if not created:
                            stockout.export_date = pd.to_datetime(stockout_data['Ngày xuất'])
                            stockout.amount_paid = float(stockout_data['Số tiền đã trả'])  # Ép thành float
                            stockout.payment_status = stockout_data['Trạng thái thanh toán'].upper()
                            stockout.notes = stockout_data['Ghi chú'] if pd.notna(stockout_data['Ghi chú']) else ''
                            stockout.customer = customer
                            stockout.created_by = employee
                            stockout.updated_by = employee
                            stockout.save()

                        for _, row in group.iterrows():
                            product_id = row['ID Sản phẩm']
                            product = Product.objects.filter(id=product_id).first()
                            if not product:
                                messages.error(request, f"Sản phẩm với ID '{product_id}' không tồn tại.")
                                return render(request, 'stock_out/import_stockout.html', {'form': form})

                            product_batch = row['Lô sản phẩm']
                            quantity = float(row['Số lượng'])
                            discount = float(row['Chiết khấu (%)'])

                            product_detail = ProductDetail.objects.filter(
                                product=product,
                                product_batch=product_batch
                            ).first()
                            if not product_detail:
                                messages.error(request, f"Lô sản phẩm '{product_batch}' cho sản phẩm ID '{product_id}' không tồn tại.")
                                return render(request, 'stock_out/import_stockout.html', {'form': form})

                            if quantity > product_detail.remaining_quantity:
                                messages.error(
                                    request,
                                    f"Số lượng xuất ({quantity}) vượt quá số lượng tồn kho "
                                    f"({product_detail.remaining_quantity}) cho lô '{product_batch}'."
                                )
                                return render(request, 'stock_out/import_stockout.html', {'form': form})

                            StockOutDetail.objects.create(
                                export_record=stockout,
                                product=product,
                                quantity=quantity,
                                product_detail=product_detail,
                                discount=discount,
                                amount_paid=0,
                            )

                        Notification.objects.create(
                            message=f"Nhập đơn xuất kho ID {stockout.id} từ Excel thành công!",
                            employee=request.user,
                            created_at=timezone.now(),
                            is_read=False
                        )

                messages.success(request, "Nhập dữ liệu từ Excel thành công!")
                return redirect('stock_out')

            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi nhập Excel: {str(e)}")
                return render(request, 'stock_out/import_stockout.html', {'form': form})
    else:
        form = StockOutImportForm()

    context = {
        'title': 'Nhập đơn xuất kho từ Excel',
        'form': form,
    }
    return render(request, 'stock_out/import_stockout.html', context)