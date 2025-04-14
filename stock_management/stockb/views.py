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


def report_overview(request):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = today

    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    doanh_thu = StockOut.objects.filter(export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    gia_tri_nhap_kho = StockIn.objects.filter(import_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('total_amount'))['total'] or 0

    gia_tri_xuat_kho = StockOut.objects.filter(export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    no_phai_tra = StockIn.objects.filter(payment_status='UNPAID', import_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('total_amount'))['total'] or 0

    no_phai_thu = StockOut.objects.filter(payment_status='UNPAID', export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    context = {
        'so_don_hang': so_don_hang,
        'doanh_thu': doanh_thu,
        'gia_tri_nhap_kho': gia_tri_nhap_kho,
        'gia_tri_xuat_kho': gia_tri_xuat_kho,
        'no_phai_tra': no_phai_tra,
        'no_phai_thu': no_phai_thu,
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

    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    doanh_thu = StockOut.objects.filter(export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    gia_tri_nhap_kho = StockIn.objects.filter(import_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('total_amount'))['total'] or 0

    gia_tri_xuat_kho = StockOut.objects.filter(export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    no_phai_tra = StockIn.objects.filter(payment_status='UNPAID', import_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('total_amount'))['total'] or 0

    no_phai_thu = StockOut.objects.filter(payment_status='UNPAID', export_date__range=(start_date, end_date)) \
        .aggregate(total=Sum('stockoutdetail__product__selling_price'))['total'] or 0

    return JsonResponse({
        'so_don_hang': so_don_hang,
        'doanh_thu': doanh_thu,
        'gia_tri_nhap_kho': gia_tri_nhap_kho,
        'gia_tri_xuat_kho': gia_tri_xuat_kho,
        'no_phai_tra': no_phai_tra,
        'no_phai_thu': no_phai_thu,
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