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

# View cho thông tin nhà cung cấp
def supplier_list_view(request):
    return render(request, 'supplier/supplier_list.html')

# View cho tạo mới nhà cung cấp
def supplier_create_view(request):
    if request.method == 'POST':
        return redirect('supplier_list')  # Quay lại danh sách nhà cung cấp sau khi lưu
    return render(request, 'supplier/supplier_create.html')

# View mới cho danh sách sản phẩm sắp hết hạn
def near_expiry_list_view(request):
    return render(request, 'inventory/near_expiry_list.html')

# View mới cho danh sách sản phẩm gần hết trong kho
def low_stock_list_view(request):
    return render(request, 'inventory/low_stock_list.html')

