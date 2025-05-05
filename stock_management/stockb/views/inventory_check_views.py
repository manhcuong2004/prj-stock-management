from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.checks import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from ..forms import InventoryCheckForm, InventoryCheckDetailFormSet
from ..models import Product, ProductDetail, Supplier, InventoryCheck, ProductCategory


@login_required
def inventory_check_list(request):
    inventory_checks = InventoryCheck.objects.all().order_by('-check_date')
    context = {
        'title': "Kiểm kê hàng hóa",
        'inventory_checks': inventory_checks,
    }
    return render(request, 'inventory/inventory_check_list.html', context)


@login_required
def inventory_check_update(request, pk=None):
    if pk:
        inventory_check = get_object_or_404(InventoryCheck, pk=pk)
    else:
        inventory_check = InventoryCheck()

    form = InventoryCheckForm(request.POST or None, instance=inventory_check)
    formset = InventoryCheckDetailFormSet(request.POST or None, instance=inventory_check, prefix='inventorycheckdetail_set')

    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            inventory_check = form.save(commit=False)
            if not inventory_check.check_date:
                inventory_check.check_date = timezone.now()
            inventory_check.save()

            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()

            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Kiểm kê đã được lưu thành công!")
            return redirect('inventory_check_list')
        else:
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại dữ liệu.")

    categories = ProductCategory.objects.all()
    products = Product.objects.select_related('category').all()
    employees = User.objects.all()
    product_details = {}
    for product in products:
        details = ProductDetail.objects.filter(product=product, remaining_quantity__gt=0)
        product_details[product.id] = [
            {
                'id': detail.id,
                'product_batch': detail.product_batch,
                'remaining_quantity': detail.remaining_quantity,
                'import_date': detail.import_date,
            } for detail in details
        ]

    context = {
        'title': 'Chỉnh sửa kiểm kê hàng hóa' if pk else 'Tạo mới kiểm kê hàng hóa',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'employees': employees,
        'product_details': product_details,
    }
    return render(request, 'inventory/inventory_check_update.html', context)

@login_required
def inventory_check_delete(request, pk):
    inventory_check = get_object_or_404(InventoryCheck, pk=pk)
    if request.method == "POST":
        inventory_check.delete()
        return redirect('inventory_check_list')
    return render(request, 'inventory/inventory_check_list.html', {
        'inventory_checks': InventoryCheck.objects.all().order_by('-check_date')
    })
