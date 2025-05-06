from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from ..forms import UnitForm
from ..models import StockOut, Unit


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
            messages.success(request, 'Đơn vị đã được cập nhật thành công!')
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
            form.save()
            messages.success(request, 'Đơn vị đã được tạo thành công!')
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
        unit.delete()
        messages.success(request, 'Đơn vị đã được xóa thành công!')
        return redirect('units_list')
    return render(request, 'units/units_list.html', {'unit': unit})