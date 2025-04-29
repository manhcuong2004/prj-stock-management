import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime

from .forms import UnitForm
from .models import StockOut, StockOutDetail, Unit, StockIn


# Create your views here.
def index(request):
    return render(request, "main.html")
#Xuất nhập kho
def stock_out(request):
    stock_outs = StockOut.objects.all().order_by('-export_date')
    stock_out_list = []

    filter_type = request.GET.get('filter', 'all')
    search_type = request.GET.get('filter', 'all')
    if filter_type == 'in_progress':
        stock_outs = stock_outs.filter(export_status='IN_PROGRESS')
    elif filter_type == 'cancel':
        stock_outs = stock_outs.filter(export_status='CANCELLED')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    for stock_out in stock_outs:
        total_amount = StockOutDetail.objects.filter(export_record=stock_out).aggregate(
            total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_out_list.append({
            'id': stock_out.id,
            'export_date': stock_out.export_date,
            'customer': f"{stock_out.customer.first_name} {stock_out.customer.last_name}",
            'payment_status': stock_out.payment_status,
            'export_status': stock_out.export_status,
            'total_amount': total_amount,
        })
    context = {
        "title": "Trang xuất kho",
        'filter_type': filter_type,
        "stock_out_list" : stock_out_list,
    }
    return render(request, "stock_out/stock_out_list.html", context)

def stock_out_update(request):
    context = {"title": "Trang tạo mới đơn xuất kho"}
    return render(request, "stock_out/stock_out_update.html", context)

def stock_in(request):
    context = {"title": "Trang xuất kho"}
    return render(request, "stock_in/stock_in_list.html", context)

def stock_in_update(request):
    context = {"title": "Trang tạo mới đơn nhập kho"}
    return render(request, "stock_in/stock_in_update.html", context)


def supplier_list_view(request):
    context = {"title": "Danh sách nhà cung cấp"}
    return render(request, 'supplier/supplier_list.html', context)

def supplier_create_view(request):
    context = {"title": "Tạo mới nhà cung cấp"}
    if request.method == 'POST':
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_create.html',context)

def near_expiry_list_view(request):
    context = {"title": "Hàng gần đến ngày khuyến nghị"}
    return render(request, 'inventory/near_expiry_list.html', context)

def low_stock_list_view(request):
    context = {"title": "Hàng gần hết trong kho"}
    return render(request, 'inventory/low_stock_list.html',context)


def unit_list(request):
    units = Unit.objects.all()
    query = request.GET.get('q')
    if query:
        units = units.filter(name__icontains=query) | units.filter(symbol__icontains=query)
    return render(request, 'units/units_list.html', {'units': units})

# Tạo đơn vị
def create_unit(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đơn vị đã được tạo thành công!')
            return redirect('units_list')
    else:
        form = UnitForm()
    return render(request, 'units/create_unit.html', {'form': form})

# Cập nhật đơn vị
def edit_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đơn vị đã được cập nhật thành công!')
            return redirect('units_list')
    else:
        form = UnitForm(instance=unit)
    return render(request, 'units/edit_unit.html', {'form': form, 'unit': unit})

# Xóa đơn vị
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        unit.delete()
        messages.success(request, 'Đơn vị đã được xóa thành công!')
        return redirect('units_list')
    return render(request, 'units/units_list.html', {'unit': unit})


import datetime
from django.shortcuts import render
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.http import JsonResponse
from .models import StockOut, StockOutDetail, StockIn, StockInDetail, ProductCategory

def report_overview(request):
    today = timezone.now()
    start_date = today.replace(day=1)  # Bắt đầu từ ngày đầu tháng
    end_date = today

    # Số đơn hàng
    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()
    so_don_hang_last_month = StockOut.objects.filter(
        export_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).count()
    so_don_hang_change = so_don_hang - so_don_hang_last_month

    # Doanh thu (tính từ StockOutDetail, bao gồm số lượng và chiết khấu)
    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị nhập kho (tính từ StockInDetail, bao gồm số lượng và chiết khấu)
    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_last_month = StockInDetail.objects.filter(
        import_record__import_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_change = gia_tri_nhap_kho - gia_tri_nhap_kho_last_month

    # Giá trị xuất kho (tính từ StockOutDetail, bao gồm số lượng và chiết khấu)
    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải trả (tính từ StockIn với payment_status='UNPAID')
    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải thu (tính từ StockOut với payment_status='UNPAID')
    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Tính tiến trình nợ (progress) - tỷ lệ phần trăm so với tổng giá trị nhập/xuất
    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    # Dữ liệu cho biểu đồ phân bổ hàng hóa
    total_quantity = ProductCategory.objects.aggregate(total=Sum('product__quantity'))['total'] or 1
    categories = ProductCategory.objects.annotate(
        total_quantity=Sum('product__quantity')
    ).values('category_name', 'total_quantity')
    overview_chart_data = [
        {
            'name': cat['category_name'],
            'value': (cat['total_quantity'] or 0) / total_quantity * 100
        }
        for cat in categories
    ]

    # Dữ liệu cho biểu đồ xu hướng nhập/xuất kho
    months = []
    for i in range(3, -1, -1):
        month_start = (today - datetime.timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    context = {
        'today': today,
        'so_don_hang': so_don_hang,
        'so_don_hang_change': so_don_hang_change,
        'doanh_thu': doanh_thu,
        'gia_tri_nhap_kho': gia_tri_nhap_kho,
        'gia_tri_nhap_kho_change': gia_tri_nhap_kho_change,
        'gia_tri_xuat_kho': gia_tri_xuat_kho,
        'no_phai_tra': no_phai_tra,
        'no_phai_thu': no_phai_thu,
        'no_phai_tra_progress': no_phai_tra_progress,
        'no_phai_thu_progress': no_phai_thu_progress,
        'overview_chart_data': overview_chart_data,
        'inventory_trend_data': months,
    }
    return render(request, 'report/overview.html', context)

def ajax_dashboard_stats(request):
    date_range = request.GET.get('dateRange')
    try:
        start_str, end_str = date_range.split(" to ")
        start_date = datetime.strptime(start_str.strip(), "%d/%m/%Y")
        end_date = datetime.strptime(end_str.strip(), "%d/%m/%Y")
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Số đơn hàng
    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    # Doanh thu
    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị nhập kho
    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị xuất kho
    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải trả
    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải thu
    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Tính tiến trình nợ
    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    # Dữ liệu biểu đồ xu hướng
    months = []
    for i in range(3, -1, -1):
        month_start = (start_date - datetime.timedelta(days=30 * i)).replace(dayWise=True)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    return JsonResponse({
        'so_don_hang': so_don_hang,
        'doanh_thu': float(doanh_thu) if doanh_thu else 0,
        'gia_tri_nhap_kho': float(gia_tri_nhap_kho) if gia_tri_nhap_kho else 0,
        'gia_tri_xuat_kho': float(gia_tri_xuat_kho) if gia_tri_xuat_kho else 0,
        'no_phai_tra': float(no_phai_tra) if no_phai_tra else 0,
        'no_phai_thu': float(no_phai_thu) if no_phai_thu else 0,
        'no_phai_tra_progress': float(no_phai_tra_progress),
        'no_phai_thu_progress': float(no_phai_thu_progress),
        'inventory_trend_data': months,
    })

def product_category_view(request):
    context = {"title": "Danh mục sản phẩm"}
    return render(request, 'product_category/product_category_list.html', context)
def product_category_update(request):
    context = {"title": "Tạo mới danh mục sản phẩm"}
    return render(request, 'product_category/product_category_update.html', context)
def product_category_detail(request):
    context = {"title": "Chi tiết sản phẩm"}
    return render(request, 'product_category/product_category_detail.html', context)

def product_view(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_list.html', context)
def product_update(request):
    context = {"title": "Tạo mới sản phẩm"}
    return render(request, 'product/product_update.html', context)
def product_detail(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_detail.html', context)

#Khách hàng
def customer_list(request):
    context = {"title": "Danh sách khách hàng"}
    return render(request, "customer/customer_list.html", context)
def customer_create(request):
    context = {"title": "Thêm mới khách hàng"}
    return render(request, "customer/customer_form.html", context)

#Nhân viên
def  employee_list(request):
    context = {"title": "Danh sách nhân viên"}
    return render(request, "employer/employee_list.html", context)
def employee_create(request):
    context = {"title": "Thêm mới nhân viên"}
    return render(request, "employer/employee_form.html", context)