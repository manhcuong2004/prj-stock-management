from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from ..models import Supplier, Notification, StockIn


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

        try:
            messages.success(request, 'Thêm nhà cung cấp thành công!')
            Notification.objects.create(
                message=f"Thêm nhà cung cấp {supplier_name} thành công!",
                employee=request.user,
                created_at=timezone.now(),
                is_read=False
            )
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_create.html', {'form_data': request.POST})

    return render(request, 'supplier/supplier_create.html', {"title": "Tạo mới nhà cung cấp", 'form_data': {}})

def supplier_update_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    purchase_order = StockIn.objects.filter(supplier=supplier).order_by('-import_date')

    all_orders = StockIn.objects.filter(supplier=supplier)
    # Tổng tiền
    total_spend = sum(order.total_amount() for order in all_orders)
    # Tổng đã trả
    total_paid = all_orders.aggregate(total=Sum('amount_paid'))['total'] or 0
    # Tổng nợ
    debt_amount = total_spend - total_paid

    last_purchase = StockIn.objects.filter(supplier=supplier).order_by('-import_date').first()
    last_purchase_date = last_purchase.import_date.strftime('%d/%m/%Y') if last_purchase else None

    if request.method == 'POST':
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.tax_code = request.POST.get('tax_code')
        supplier.address = request.POST.get('address')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        notes = request.POST.get('notes')


        supplier.notes = notes

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
            return render(request, 'supplier/supplier_update.html', {
                'supplier': supplier,
                'title': "Chỉnh sửa nhà cung cấp",
                "purchase_order": purchase_order,
                "import_count": purchase_order.count(),
                "total_spend": total_spend,
                "debt_amount": debt_amount,
                "last_purchase_date": last_purchase_date
            })

        try:
            supplier.update_at = timezone.now()
            supplier.save()
            Notification.objects.create(
                message=f"Cập nhật nhà cung cấp {supplier.supplier_name} thành công!",
                created_at=timezone.now(),
                employee=request.user,
                is_read=False
            )

            messages.success(request, 'Cập nhật nhà cung cấp thành công!')
            return redirect('supplier_list')

        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    return render(request, 'supplier/supplier_update.html', {
        'supplier': supplier,
        'title': "Chỉnh sửa nhà cung cấp",
        "purchase_order": purchase_order,
        "import_count": purchase_order.count(),
        "total_spend": total_spend,
        "debt_amount": debt_amount,
        "last_purchase_date": last_purchase_date
    })

@login_required
def supplier_delete_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier_name = supplier.supplier_name
        supplier.delete()
        messages.success(request, 'Xóa nhà cung cấp thành công!')
        Notification.objects.create(
            message=f"Xóa nhà cung cấp {supplier_name} thành công!",
            created_at=timezone.now(),
            employee=request.user,
            is_read=False
        )
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_confirm_delete.html', {'supplier': supplier, 'title': "Xóa nhà cung cấp"})