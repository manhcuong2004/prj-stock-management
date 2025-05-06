from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.checks import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Q

from ..forms import InventoryCheckForm, InventoryCheckDetailFormSet
from ..models import Product, ProductDetail, InventoryCheck, ProductCategory


@login_required
def inventory_check_list(request):
    inventory_checks = InventoryCheck.objects.all().order_by('-check_date')

    search_query = request.GET.get('search', '')
    if search_query:
        inventory_checks = inventory_checks.filter(
            Q(id__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(employee__username__icontains=search_query)
        )

    context = {
        'title': "Kiểm kê hàng hóa",
        'inventory_checks': inventory_checks,
        'search_query': search_query
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
                if not instance.product or not instance.product_batch:
                    continue
                instance.inventory_check = inventory_check
                instance.save()

            for obj in formset.deleted_objects:
                obj.delete()

            return redirect('inventory_check_list')
        else:
            error_messages = []
            if form.errors:
                error_messages.append(f"Form errors: {form.errors}")
            if formset.errors:
                error_messages.append(f"Formset errors: {formset.errors}")
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    categories = ProductCategory.objects.all()
    products = Product.objects.select_related('category').all()
    employees = User.objects.filter(is_superuser=False)
    product_details = ProductDetail.objects.filter(remaining_quantity__gt=0, status="ACTIVE")

    context = {
        'title': 'Chỉnh sửa kiểm kê hàng hóa' if pk else 'Tạo mới kiểm kê hàng hóa',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'product_details': product_details,
        'employees': employees,
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
