import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from unidecode import unidecode
from django.db.models import Sum, F, Q
from ..forms import StockInForm, StockInDetailFormSet, StockInImportForm
from ..models import ProductCategory, Product, ProductDetail, StockIn, Supplier, StockInDetail, Notification
import datetime

@login_required
def stock_in(request):
    stock_ins = StockIn.objects.all().order_by('-import_date')
    stock_in_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

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
            Q(supplier__supplier_name__icontains=search_text_ch)
        ).distinct()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end_date_obj < start_date_obj:
                messages.warning(request, "Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")
            else:
                end_date_obj = end_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
                stock_ins = stock_ins.filter(import_date__range=(start_date_obj, end_date_obj))
        except ValueError:
            stock_ins = StockIn.objects.none()
    elif start_date or end_date:
        messages.warning(request, "Vui lòng nhập cả ngày bắt đầu và ngày kết thúc.")

    for stock_in in stock_ins:
        stock_in_list.append({
            'id': stock_in.id,
            'import_date': stock_in.import_date,
            'supplier': stock_in.supplier.supplier_name,
            'payment_status': stock_in.payment_status,
            'total_amount': stock_in.total_amount(),
        })
    paginator = Paginator(stock_in_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "title": "Trang nhập kho",
        'filter_type': filter_type,
        "stock_in_list": page_obj,
        "search_text": search_text,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "stock_in/stock_in_list.html", context)

@login_required
def stock_in_update(request, pk=None):
    stock_in = get_object_or_404(StockIn, pk=pk) if pk else None
    action = "Cập nhật" if pk else "Thêm"
    form = StockInForm(request.POST or None, instance=stock_in)
    formset = StockInDetailFormSet(request.POST or None, instance=stock_in or StockIn(), prefix='stockindetail_set')

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            stock_in = form.save(commit=False)

            stock_in.created_by = request.user if not stock_in else stock_in.created_by
            stock_in.updated_by = request.user
            stock_in.updated_at = timezone.now()
            stock_in.save()

            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        if detail_form.instance.pk:
                            try:
                                if detail_form.instance.product_detail:
                                    detail_form.instance.product_detail.delete()
                                detail_form.instance.delete()
                            except Exception as e:
                                messages.error(request, f"Lỗi khi xóa chi tiết: {str(e)}")
                                return render(request, 'stock_in/stock_in_update.html', {
                                    'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
                                    'form': form,
                                    'formset': formset,
                                    'categories': ProductCategory.objects.all(),
                                    'products': Product.objects.all(),
                                    'suppliers': Supplier.objects.all(),
                                })
                        continue

                    detail = detail_form.save(commit=False)
                    detail.import_record = stock_in
                    product = detail_form.cleaned_data.get('product')
                    product_batch = detail_form.cleaned_data.get('product_batch')
                    quantity = detail_form.cleaned_data.get('quantity')

                    if not (product and product_batch and quantity):
                        messages.error(request, "Thông tin sản phẩm, mã lô hoặc số lượng không hợp lệ.")
                        return render(request, 'stock_in/stock_in_update.html', {
                            'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
                            'form': form,
                            'formset': formset,
                            'categories': ProductCategory.objects.all(),
                            'products': Product.objects.all(),
                            'suppliers': Supplier.objects.all(),
                        })


                    if detail.pk and detail.product_detail:
                        product_detail = detail.product_detail
                        product_detail.product_batch = product_batch
                        product_detail.initial_quantity = quantity
                        product_detail.remaining_quantity = quantity
                        product_detail.import_date = stock_in.import_date or timezone.now().date()
                        product_detail.save()
                    else:
                        product_detail = ProductDetail(
                            product=product,
                            product_batch=product_batch,
                            initial_quantity=quantity,
                            remaining_quantity=quantity,
                            import_date=stock_in.import_date or timezone.now().date(),
                            status='ACTIVE'
                        )
                        product_detail.save()

                    detail.product_detail = product_detail
                    try:
                        detail.save()
                    except ValueError as e:
                        messages.error(request, f"Lỗi khi lưu chi tiết: {str(e)}")
                        return render(request, 'stock_in/stock_in_update.html', {
                            'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
                            'form': form,
                            'formset': formset,
                            'categories': ProductCategory.objects.all(),
                            'products': Product.objects.all(),
                            'suppliers': Supplier.objects.all(),
                        })

            messages.success(request, f'{action.capitalize()} đơn nhập kho ID {stock_in.id} thành công!')
            Notification.objects.create(
                message=f"{action} đơn nhập kho ID {stock_in.id} thành công!",
                employee=request.user,
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('stock_in')
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
    suppliers = Supplier.objects.all()

    context = {
        'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'suppliers': suppliers,
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
            message=f"Xóa đơn nhập kho ID {stock_in_id} thành công!",
            employee=request.user,
            created_at=timezone.now(),
            is_read=False
        )
        return redirect('stock_in')
    return render(request, 'stock_in/stock_in_list.html', {'stock_in': stock_in})

@login_required
def export_all_stockin_excel(request):
    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    stock_ins = StockIn.objects.all().select_related('supplier', 'created_by').prefetch_related('details__product', 'details__product_detail')

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
            Q(supplier__supplier_name__icontains=search_text_ch)
        ).distinct()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            if end_date_obj < start_date_obj:
                messages.warning(request, "Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")
            else:
                end_date_obj = end_date_obj + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
                stock_ins = stock_ins.filter(import_date__range=(start_date_obj, end_date_obj))
        except ValueError:
            stock_ins = StockIn.objects.none()

    elif start_date or end_date:
        messages.warning(request, "Vui lòng nhập cả ngày bắt đầu và ngày kết thúc.")

    if not stock_ins.exists():
        return HttpResponse("Không tìm thấy đơn nhập kho nào phù hợp.", status=404)

    data = []
    for stock_in in stock_ins:
        details = stock_in.details.all()
        for detail in details:
            data.append({
                'Mã đơn nhập': stock_in.id,
                'Ngày nhập': stock_in.import_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Nhà cung cấp': stock_in.supplier.supplier_name,
                'Trạng thái thanh toán': stock_in.get_payment_status_display(),
                'Tổng tiền': stock_in.total_amount(),
                'Số tiền đã trả': stock_in.amount_paid,
                'Nợ còn lại': stock_in.remaining_debt(),
                'Ghi chú': stock_in.notes or '',
                'Nhân viên': stock_in.created_by.username if stock_in.created_by else 'N/A',
                'Sản phẩm': detail.product.product_name,
                'Lô sản phẩm': detail.product_detail.product_batch,
                'Số lượng': detail.quantity,
                'Giá nhập': detail.purchase_price,
                'Chiết khấu (%)': detail.discount,
                'Tổng tiền chi tiết': detail.quantity * detail.product.purchase_price * (1 - detail.discount / 100),
            })
        if not details:
            data.append({
                'Mã đơn nhập': stock_in.id,
                'Ngày nhập': stock_in.import_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Nhà cung cấp': stock_in.supplier.supplier_name,
                'Trạng thái thanh toán': stock_in.get_payment_status_display(),
                'Tổng tiền': stock_in.total_amount(),
                'Số tiền đã trả': stock_in.amount_paid,
                'Nợ còn lại': stock_in.remaining_debt(),
                'Ghi chú': stock_in.notes or '',
                'Nhân viên': stock_in.created_by.username if stock_in.created_by else 'N/A',
                'Sản phẩm': '',
                'Lô sản phẩm': '',
                'Số lượng': 0,
                'Giá nhập': 0,
                'Chiết khấu (%)': 0,
                'Tổng tiền chi tiết': 0,
            })
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=stockin_all_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response

@login_required
def export_single_stockin_excel(request, stockin_id):
    stock_in = get_object_or_404(StockIn, id=stockin_id)

    data = []
    details = stock_in.details.all().select_related('product', 'product_detail')
    for detail in details:
        data.append({
            'Mã đơn nhập': stock_in.id,
            'Ngày nhập': stock_in.import_date.strftime('%Y-%m-%d %H:%M:%S'),
            'Nhà cung cấp': stock_in.supplier.supplier_name,
            'Trạng thái thanh toán': stock_in.get_payment_status_display(),
            'Tổng tiền': stock_in.total_amount(),
            'Số tiền đã trả': stock_in.amount_paid,
            'Nợ còn lại': stock_in.remaining_debt(),
            'Ghi chú': stock_in.notes or '',
            'Nhân viên': stock_in.created_by.username if stock_in.created_by else 'N/A',
            'Sản phẩm': detail.product.product_name,
            'Lô sản phẩm': detail.product_detail.product_batch,
            'Số lượng': detail.quantity,
            'Giá nhập': detail.purchase_price,
            'Chiết khấu (%)': detail.discount,
            'Tổng tiền chi tiết': detail.quantity * detail.product.purchase_price * (1 - detail.discount / 100),
        })
    if not details:
        data.append({
            'Mã đơn nhập': stock_in.id,
            'Ngày nhập': stock_in.import_date.strftime('%Y-%m-%d %H:%M:%S'),
            'Nhà cung cấp': stock_in.supplier.supplier_name,
            'Trạng thái thanh toán': stock_in.get_payment_status_display(),
            'Tổng tiền': stock_in.total_amount(),
            'Số tiền đã trả': stock_in.amount_paid,
            'Nợ còn lại': stock_in.remaining_debt(),
            'Ghi chú': stock_in.notes or '',
            'Nhân viên': stock_in.created_by.username if stock_in.created_by else 'N/A',
            'Sản phẩm': '',
            'Lô sản phẩm': '',
            'Số lượng': 0,
            'Giá nhập': 0,
            'Chiết khấu (%)': 0,
            'Tổng tiền chi tiết': 0,
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=stockin_{stockin_id}_report.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response


@login_required
def import_stockin(request):
    if request.method == 'POST':
        form = StockInImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                df = pd.read_excel(excel_file, engine='openpyxl')

                required_columns = [
                    'Mã đơn nhập', 'Ngày nhập', 'ID Nhà cung cấp', 'Trạng thái thanh toán',
                    'Số tiền đã trả', 'Ghi chú', 'ID Nhân viên', 'ID Sản phẩm',
                    'Lô sản phẩm', 'Số lượng', 'Chiết khấu (%)'
                ]
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, "File Excel không đúng định dạng. Vui lòng kiểm tra các cột.")
                    return render(request, 'stock_in/import_stockin.html', {'form': form})

                numeric_columns = ['Số tiền đã trả', 'Số lượng', 'Chiết khấu (%)']
                for col in numeric_columns:
                    try:
                        # Ép kiểu thành số (numeric), thay thế giá trị không hợp lệ bằng 0
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                        # Chuyển đổi thành float để đảm bảo định dạng thập phân
                        df[col] = df[col].astype(float)
                    except Exception as e:
                        messages.error(request, f"Lỗi định dạng cột '{col}': {str(e)}")
                        return render(request, 'stock_in/import_stockin.html', {'form': form})

                grouped = df.groupby('Mã đơn nhập')

                with transaction.atomic():
                    for stockin_id, group in grouped:
                        stockin_data = group.iloc[0]

                        supplier_id = stockin_data['ID Nhà cung cấp']
                        supplier = Supplier.objects.filter(id=supplier_id).first()
                        if not supplier:
                            messages.error(request, f"Nhà cung cấp với ID '{supplier_id}' không tồn tại.")
                            return render(request, 'stock_in/import_stockin.html', {'form': form})

                        employee_id = stockin_data['ID Nhân viên']
                        employee = User.objects.filter(id=employee_id).first()
                        if not employee:
                            messages.error(request, f"Nhân viên với ID '{employee_id}' không tồn tại.")
                            return render(request, 'stock_in/import_stockin.html', {'form': form})

                        stockin, created = StockIn.objects.get_or_create(
                            id=stockin_id,
                            defaults={
                                'import_date': pd.to_datetime(stockin_data['Ngày nhập']),
                                'amount_paid': float(stockin_data['Số tiền đã trả']),  # Ép thành float
                                'payment_status': stockin_data['Trạng thái thanh toán'].upper(),
                                'notes': stockin_data['Ghi chú'] if pd.notna(stockin_data['Ghi chú']) else '',
                                'supplier': supplier,
                                'created_by': employee,  # Thay employee thành created_by
                            }
                        )

                        if not created:
                            stockin.import_date = pd.to_datetime(stockin_data['Ngày nhập'])
                            stockin.amount_paid = float(stockin_data['Số tiền đã trả'])  # Ép thành float
                            stockin.payment_status = stockin_data['Trạng thái thanh toán'].upper()
                            stockin.notes = stockin_data['Ghi chú'] if pd.notna(stockin_data['Ghi chú']) else ''
                            stockin.supplier = supplier
                            stockin.created_by = employee  # Thay employee thành created_by
                            stockin.updated_by = employee  # Thêm updated_by nếu model có trường này
                            stockin.save()

                        for _, row in group.iterrows():
                            product_id = row['ID Sản phẩm']
                            product = Product.objects.filter(id=product_id).first()
                            if not product:
                                messages.error(request, f"Sản phẩm với ID '{product_id}' không tồn tại.")
                                return render(request, 'stock_in/import_stockin.html', {'form': form})

                            product_batch = row['Lô sản phẩm']
                            quantity = float(row['Số lượng'])  # Ép thành float
                            discount = float(row['Chiết khấu (%)'])  # Ép thành float

                            product_detail, _ = ProductDetail.objects.get_or_create(
                                product=product,
                                product_batch=product_batch,
                                defaults={
                                    'initial_quantity': quantity,
                                    'remaining_quantity': quantity,
                                    'import_date': stockin.import_date,
                                    'status': 'ACTIVE',
                                }
                            )

                            StockInDetail.objects.create(
                                import_record=stockin,
                                product=product,
                                quantity=quantity,
                                product_detail=product_detail,
                                discount=discount,
                            )

                        Notification.objects.create(
                            message=f"Nhập đơn nhập kho ID {stockin.id} từ Excel thành công!",
                            employee=request.user,
                            created_at=timezone.now(),
                            is_read=False
                        )

                messages.success(request, "Nhập dữ liệu từ Excel thành công!")
                return redirect('stock_in')

            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi nhập Excel: {str(e)}")
                return render(request, 'stock_in/import_stockin.html', {'form': form})
    else:
        form = StockInImportForm()

    context = {
        'title': 'Nhập đơn nhập kho từ Excel',
        'form': form,
    }
    return render(request, 'stock_in/import_stockin.html', context)