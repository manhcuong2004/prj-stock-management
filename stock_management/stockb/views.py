from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "main.html")

def stock_out(request):
    context = {"title": "Trang xuất kho"}
    return render(request, "stock_out/stock_out.html", context)

def stock_out_update(request):
    context = {"title": "Trang tạo mới đơn xuất kho"}
    return render(request, "stock_out/stock_out_update.html", context)

def stock_in(request):
    context = {"title": "Trang nhập kho"}
    return render(request, "stock_in/stock_in.html", context )
def stock_in_update(request):
    context = {"title": "Trang tạo mới đơn nhập kho"}
    return render(request, "stock_in/stock_in_update.html", context)

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