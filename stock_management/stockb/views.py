
from django.shortcuts import render, redirect


# Create your views here.
def index(request):
    return render(request, "main.html")

def stock_out(request):
    return render(request, "stock_out/stock_out.html")
    context = {"title": "Trang xuất kho"}
    return render(request, "stock_out/stock_out.html", context)

def stock_out_update(request):
    context = {"title": "Trang tạo mới đơn xuất kho"}
    return render(request, "stock_out/stock_out_update.html", context)

def stock_in(request):
    context = {"title": "Trang xuất kho"}
    return render(request, "stock_in/stock_in.html", context)

def stock_in_update(request):
    context = {"title": "Trang tạo mới đơn nhập kho"}
    return render(request, "stock_in/stock_in_update.html", context)


def units_view(request):
    return render(request, 'units/units.html')
def supplier_list_view(request):
    return render(request, 'supplier/supplier_list.html')

def create_unit(request):
    return render(request, 'units/create_unit.html')
def supplier_create_view(request):
    if request.method == 'POST':
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_create.html')

def near_expiry_list_view(request):
    return render(request, 'inventory/near_expiry_list.html')

def low_stock_list_view(request):
    return render(request, 'inventory/low_stock_list.html')

def report_overview(request):
    return render(request, 'report/overview.html')
