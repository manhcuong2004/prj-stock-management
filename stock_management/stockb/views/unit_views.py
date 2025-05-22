from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from ..forms import UnitForm
from ..models import StockOut, Unit, Notification

@login_required
def unit_list(request):
    units = Unit.objects.all()
    query = request.GET.get('q')
    if query:
        units = units.filter(name__icontains=query) | units.filter(symbol__icontains=query)

    paginator = Paginator(units, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Danh sách đơn vị',
        'units': page_obj
    }
    return render(request, 'units/units_list.html', context)

@login_required
def create_unit(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            messages.success(request, 'Đơn vị đã được tạo thành công!')
            Notification.objects.create(
                message=f"Thêm đơn vị {unit.unit_name} thành công!",
                created_at=timezone.now(),
                employee=request.user,
                is_read=False
            )
            return redirect('units_list')
    else:
        form = UnitForm()
    context = {
        'title': 'Tạo đơn vị',
        'form': form,
    }
    return render(request, 'units/create_unit.html', context)

@login_required
def edit_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            unit = form.save()
            messages.success(request, 'Đơn vị đã được cập nhật thành công!')
            Notification.objects.create(
                message=f"Cập nhật đơn vị {unit.unit_name} thành công!",
                created_at=timezone.now(),
                employee=request.user,
                is_read=False
            )
            return redirect('units_list')
    else:
        form = UnitForm(instance=unit)

    context = {
        'title': 'Chỉnh sửa đơn vị',
        'form': form,
        'unit': unit
    }
    return render(request, 'units/edit_unit.html', context)

@login_required
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        messages.success(request, 'Đơn vị đã được xóa thành công!')
        Notification.objects.create(
            message=f"Xóa đơn vị {unit_name} thành công!",
            created_at=timezone.now(),
            employee=request.user,
            is_read=False
        )
        return redirect('units_list')
    return render(request, 'units/units_list.html', {'unit': unit})