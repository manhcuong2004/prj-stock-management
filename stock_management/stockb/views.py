
from django.shortcuts import render, redirect
from django.db.models import Sum, F
from .models import StockOut, StockOutDetail


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


def units_view(request):
    context = {"title": "Danh sách đơn vị"}
    return render(request, 'units/units_list.html', context)
def create_unit(request):
    context = {"title": "Tạo mới đơn vị"}
    return render(request, 'units/create_unit.html',context)
def report_overview(request):
    context = {"title": "Báo cáo"}
    return render(request, 'report/overview.html', context)


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