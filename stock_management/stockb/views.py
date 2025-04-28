from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Supplier

# Create your views here.
def index(request):
    return render(request, "main.html")

def stock_out(request):
    return render(request, "stock_out/stock_out.html")

# View cho danh sách nhà cung cấp
def supplier_list_view(request):
    suppliers = Supplier.objects.all()  # Lấy tất cả nhà cung cấp từ CSDL
    return render(request, 'supplier/supplier_list.html', {'suppliers': suppliers})

# View cho tạo mới nhà cung cấp
def supplier_create_view(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        tax_code = request.POST.get('tax_code')
        address = request.POST.get('address')
        mobile_phone = request.POST.get('mobile_phone')
        email = request.POST.get('email')
        supplier_notes = request.POST.get('supplier_notes')
        company = request.POST.get('company')  # Lấy giá trị từ trường Công ty

        # Kiểm tra dữ liệu đầu vào
        missing_fields = []
        if not supplier_name:
            missing_fields.append("Tên nhà cung cấp")
        if not tax_code:
            missing_fields.append("Mã số thuế")
        if not email:
            missing_fields.append("Email")
        if not mobile_phone:
            missing_fields.append("Số điện thoại di động")

        if missing_fields:
            messages.error(request, f'Vui lòng điền đầy đủ các trường bắt buộc: {", ".join(missing_fields)}!')
            return render(request, 'supplier/supplier_create.html')

        # Kết hợp thông tin Công ty vào ghi chú (vì model không có trường company)
        if company:
            supplier_notes = f"Công ty: {company}\n{supplier_notes or ''}"

        # Tạo nhà cung cấp mới
        try:
            Supplier.objects.create(
                supplier_name=supplier_name,
                tax_code=tax_code,
                address=address,
                mobile_phone=mobile_phone,
                email=email,
                supplier_notes=supplier_notes,
                # Các trường khác để mặc định hoặc trống
                country="Việt Nam",  # Giá trị mặc định
                province="Đà Nẵng",  # Giá trị mặc định
                district="Đà Nẵng",  # Giá trị mặc định
                ward="Đà Nẵng",     # Giá trị mặc định
                landline_phone="",   # Để trống
                manager_name="",     # Để trống
            )
            messages.success(request, 'Thêm nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_create.html')

    return render(request, 'supplier/supplier_create.html')

# View cho chỉnh sửa nhà cung cấp
def supplier_update_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.tax_code = request.POST.get('tax_code')
        supplier.address = request.POST.get('address')
        supplier.mobile_phone = request.POST.get('mobile_phone')
        supplier.email = request.POST.get('email')
        supplier.supplier_notes = request.POST.get('supplier_notes')

        # Kiểm tra dữ liệu đầu vào
        missing_fields = []
        if not supplier.supplier_name:
            missing_fields.append("Tên nhà cung cấp")
        if not supplier.tax_code:
            missing_fields.append("Mã số thuế")
        if not supplier.email:
            missing_fields.append("Email")
        if not supplier.mobile_phone:
            missing_fields.append("Số điện thoại di động")

        if missing_fields:
            messages.error(request, f'Vui lòng điền đầy đủ các trường bắt buộc: {", ".join(missing_fields)}!')
            return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

        # Lưu cập nhật
        try:
            supplier.save()
            messages.success(request, 'Cập nhật nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

    return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

# View cho xóa nhà cung cấp
def supplier_delete_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Xóa nhà cung cấp thành công!')
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_confirm_delete.html', {'supplier': supplier})

# View cho danh sách sản phẩm sắp hết hạn
def near_expiry_list_view(request):
    return render(request, 'inventory/near_expiry_list.html')

# View cho danh sách sản phẩm gần hết trong kho
def low_stock_list_view(request):
    return render(request, 'inventory/low_stock_list.html')