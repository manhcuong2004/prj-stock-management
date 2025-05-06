from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from ..forms import UnitForm
from ..models import StockOut, Unit, Notification

@login_required
def unit_list(request):
    units = Unit.objects.all()
    query = request.GET.get('q')
    if query:
        units = units.filter(name__icontains=query) | units.filter(symbol__icontains=query)

    context = {
        'title': 'Danh sách đơn vị',
        'units': units
    }
    return render(request, 'units/units_list.html', context)

@login_required
def edit_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            username = request.user.username
            message = f"{username} đã cập nhật đơn vị {unit.name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
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
def create_unit(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            username = request.user.username
            message = f"{username} đã tạo đơn vị {unit.name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('units_list')
    else:
        form = UnitForm()
    context = {
        'title': 'Tạo đơn vị',
        'form': form,
    }
    return render(request, 'units/create_unit.html', context)

@login_required
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        username = request.user.username
        message = f"{username} đã xóa đơn vị {unit_name} thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('units_list')
    return render(request, 'units/units_list.html', {'unit': unit})