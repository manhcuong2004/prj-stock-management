from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect

from ..models import  Supplier

@login_required
def supplier_list_view(request):
    suppliers = Supplier.objects.all()
    context = {
        "title": "Danh sách nhà cung cấp",
        "suppliers": suppliers,
    }
    return render(request, 'supplier/supplier_list.html', context)
@login_required
def supplier_create_view(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        tax_code = request.POST.get('tax_code')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        notes = request.POST.get('notes')
        company_name = request.POST.get('company_name')

        missing_fields = []
        if not supplier_name:
            missing_fields.append("Tên nhà cung cấp")
        if not tax_code:
            missing_fields.append("Mã số thuế")
        if not email:
            missing_fields.append("Email")
        if not phone:
            missing_fields.append("Số điện thoại")

        if missing_fields:
            messages.error(request, f'Vui lòng điền đầy đủ các trường bắt buộc: {", ".join(missing_fields)}!')
            return render(request, 'supplier/supplier_create.html', {'form_data': request.POST})

        if company_name:
            notes = f"Công ty: {company_name}\n{notes or ''}"

        try:
            Supplier.objects.create(
                supplier_name=supplier_name,
                tax_code=tax_code,
                address=address,
                phone=phone,
                email=email,
                notes=notes,
                company_name=company_name or "",
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            messages.success(request, 'Thêm nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_create.html', {'form_data': request.POST})

    return render(request, 'supplier/supplier_create.html', {"title": "Tạo mới nhà cung cấp", 'form_data': {}})
@login_required
def supplier_update_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.tax_code = request.POST.get('tax_code')
        supplier.address = request.POST.get('address')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        supplier.notes = request.POST.get('notes')
        supplier.company_name = request.POST.get('company_name')

        missing_fields = []
        if not supplier.supplier_name:
            missing_fields.append("Tên nhà cung cấp")
        if not supplier.tax_code:
            missing_fields.append("Mã số thuế")
        if not supplier.email:
            missing_fields.append("Email")
        if not supplier.phone:
            missing_fields.append("Số điện thoại")

        if missing_fields:
            messages.error(request, f'Vui lòng điền đầy đủ các trường bắt buộc: {", ".join(missing_fields)}!')
            return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

        try:
            supplier.updated_at = timezone.now()
            supplier.save()
            messages.success(request, 'Cập nhật nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

    return render(request, 'supplier/supplier_update.html', {'supplier': supplier, 'title': "Chỉnh sửa nhà cung cấp"})
@login_required
def supplier_delete_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Xóa nhà cung cấp thành công!')
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_confirm_delete.html', {'supplier': supplier, 'title': "Xóa nhà cung cấp"})
