import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.checks import messages
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q, Max
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from unidecode import unidecode
<<<<<<< HEAD
from .forms import InventoryCheckForm, InventoryCheckDetailFormSet, CustomerForm
from .forms import StockOutForm, StockOutDetailFormSet, StockOutDetailForm
from .models import InventoryCheck, Product, Employee, ProductDetail
from .models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductDetail, Employee, Supplier
from django.contrib import messages
from .forms import UnitForm
from .models import StockOut, StockOutDetail, Unit
# Create your views here.
def index(request):
    return render(request, "main.html")

# Xuất nhập kho
=======
from datetime import timedelta
from .forms import InventoryCheckForm, InventoryCheckDetailFormSet, StockInForm, StockInDetailFormSet, UnitForm
from .models import InventoryCheck, Product, ProductDetail, Supplier, ProductCategory, Unit
from .forms import StockOutForm, StockOutDetailFormSet, StockOutDetailForm
from .models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductDetail


# Create your views here.
def index(request):
    return render(request, "main.html")
#Xuất nhập kho
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def stock_out(request):
    stock_outs = StockOut.objects.all().order_by('-export_date')
    stock_out_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    if filter_type == 'in_progress':
        stock_outs = stock_outs.filter(export_status='IN_PROGRESS')
    elif filter_type == 'cancel':
        stock_outs = stock_outs.filter(export_status='CANCELLED')
    elif filter_type == 'paid':
        stock_outs = stock_outs.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_outs = stock_outs.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_outs_by_id = stock_outs.filter(id__icontains=search_text_ch)
        customers_fn = set()
        customers_ln = set()
        customers_full = set()
        all_customers = Customer.objects.all()
        for customer in all_customers:
            first_name_ch = unidecode(customer.first_name).lower()
            last_name_ch = unidecode(customer.last_name).lower()
            full_name_ch = f"{first_name_ch} {last_name_ch}"

            if search_text_ch in first_name_ch:
                customers_fn.add(customer)
            if search_text_ch in last_name_ch:
                customers_ln.add(customer)
            if search_text_ch in full_name_ch:
                customers_full.add(customer)

        customers = customers_fn | customers_ln | customers_full

        stock_outs_by_customer = stock_outs.filter(customer__in=customers)

        stock_outs = stock_outs_by_id | stock_outs_by_customer

    for stock_out in stock_outs:
        total_amount = StockOutDetail.objects.filter(export_record=stock_out).aggregate(
            total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_out_list.append({
            'id': stock_out.id,
            'export_date': stock_out.export_date,
            'customer': f"{stock_out.customer.first_name} {stock_out.customer.last_name}",
            'payment_status': stock_out.payment_status,
            'export_status': stock_out.export_status,
            'total_amount': total_amount,
        })
    context = {
        "title": "Trang xuất kho",
        'filter_type': filter_type,
        "stock_out_list": stock_out_list,
    }
    return render(request, "stock_out/stock_out_list.html", context)

<<<<<<< HEAD
StockOutDetailFormSet = formset_factory(StockOutDetailForm, extra=0)
def stock_out_update(request, pk=None):
    if pk:
        stock_out = get_object_or_404(StockOut, pk=pk)
        form = StockOutForm(instance=stock_out)
        details = stock_out.stockoutdetail_set.all()
        if details.exists():
            formset = StockOutDetailFormSet(initial=[
                {
                    'product': detail.product.id,
                    'quantity': detail.quantity,
                    'discount': detail.discount,
                    'amount_paid': detail.amount_paid,
                }
                for detail in details
            ], prefix='stockoutdetail_set')
        else:
            formset = StockOutDetailFormSet(prefix='stockoutdetail_set')
    else:
        form = StockOutForm()
        formset = StockOutDetailFormSet(prefix='stockoutdetail_set')

    if request.method == "POST":
        form = StockOutForm(request.POST, instance=stock_out if pk else None)
        formset = StockOutDetailFormSet(request.POST, prefix='stockoutdetail_set')

=======
@login_required
def stock_out_update(request, pk=None):
    stock_out = get_object_or_404(StockOut, pk=pk) if pk else None
    form = StockOutForm(request.POST or None, instance=stock_out)
    formset = StockOutDetailFormSet(request.POST or None, instance=stock_out or StockOut(), prefix='stockoutdetail_set')

    if request.method == "POST":
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
        if form.is_valid() and formset.is_valid():
            stock_out = form.save(commit=False)
            if not stock_out.export_date:
                stock_out.export_date = timezone.now()
            stock_out.employee = request.user
            stock_out.save()

            # Xử lý formset
            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        # Xóa hàng nếu được đánh dấu DELETE
                        if detail_form.instance.pk:
                            detail_form.instance.delete()
                        continue

                    detail = detail_form.save(commit=False)
                    detail.export_record = stock_out
                    detail.product_detail = detail_form.cleaned_data.get('product_detail')

                    if detail.quantity and detail.product and detail.product_detail:
                        if detail.product_detail.product != detail.product:
                            detail_form.add_error(None, f"Lô {detail.product_detail.product_batch} không thuộc sản phẩm đã chọn.")
                            continue
                        if detail.quantity > detail.product_detail.remaining_quantity:
                            detail_form.add_error(None, f"Lô {detail.product_detail.product_batch} chỉ còn {detail.product_detail.remaining_quantity} sản phẩm.")
                            continue
                        detail.save()
                        detail.product_detail.remaining_quantity -= detail.quantity
                        detail.product_detail.save()
                    else:
                        detail_form.add_error(None, "Thông tin sản phẩm hoặc lô không hợp lệ.")
                        continue

            # Kiểm tra lỗi sau khi xử lý
            if not any(formset.errors):
                return redirect('stock_out')
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    customers = Customer.objects.all()
    employees = User.objects.filter(is_superuser=False)
    product_details = ProductDetail.objects.filter(remaining_quantity__gt=0)

    context = {
        'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'product_details': product_details,
        'customers': customers,
        'employees': employees,
    }
    return render(request, 'stock_out/stock_out_update.html', context)

@login_required
def stock_in(request):
<<<<<<< HEAD
    context = {"title": "Trang nhập kho"}
=======
    stock_ins = StockIn.objects.all().order_by('-import_date')
    stock_in_list = []

    filter_type = request.GET.get('filter', 'all')
    search_text = request.GET.get('search', '')

    if filter_type == 'in_progress':
        stock_ins = stock_ins.filter(import_status='IN_PROGRESS')
    elif filter_type == 'cancel':
        stock_ins = stock_ins.filter(import_status='CANCELLED')
    elif filter_type == 'paid':
        stock_ins = stock_ins.filter(payment_status='PAID')
    elif filter_type == 'unpaid':
        stock_ins = stock_ins.filter(payment_status='UNPAID')

    if search_text:
        search_text_ch = unidecode(search_text).lower()
        stock_ins = stock_ins.filter(
            Q(id__icontains=search_text_ch) |
            Q(supplier__company_name__icontains=search_text_ch)
        ).distinct()

    for stock_in in stock_ins:
        total_amount = StockInDetail.objects.filter(import_record=stock_in).aggregate(
            total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
        )['total'] or 0
        stock_in_list.append({
            'id': stock_in.id,
            'import_date': stock_in.import_date,
            'supplier': stock_in.supplier.company_name,
            'product_batch': stock_in.product_batch,
            'payment_status': stock_in.payment_status,
            'import_status': stock_in.import_status,
            'total_amount': total_amount,
        })
    context = {
        "title": "Trang nhập kho",
        'filter_type': filter_type,
        "stock_in_list": stock_in_list,
    }
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
    return render(request, "stock_in/stock_in_list.html", context)

@login_required
def stock_in_update(request, pk=None):
    stock_in = get_object_or_404(StockIn, pk=pk) if pk else None
    form = StockInForm(request.POST or None, instance=stock_in)
    formset = StockInDetailFormSet(request.POST or None, instance=stock_in or StockIn(), prefix='stockindetail_set')

<<<<<<< HEAD
# View cho danh sách nhà cung cấp
=======
    if request.method == "POST":
        if form.is_valid() and formset.is_valid():
            stock_in = form.save(commit=False)
            if not stock_in.import_date:
                stock_in.import_date = timezone.now()
            stock_in.employee = request.user
            stock_in.save()

            # Lấy mã lô chung từ form
            product_batch = form.cleaned_data.get('product_batch')

            # Xử lý formset
            for detail_form in formset:
                if detail_form.cleaned_data:
                    if detail_form.cleaned_data.get('DELETE', False):
                        # Xóa hàng nếu được đánh dấu DELETE
                        if detail_form.instance.pk:
                            detail_form.instance.delete()
                        continue

                    detail = detail_form.save(commit=False)
                    detail.import_record = stock_in
                    detail.save()

                    # Tạo hoặc cập nhật ProductDetail với mã lô chung
                    product_detail, created = ProductDetail.objects.get_or_create(
                        product=detail.product,
                        product_batch=product_batch,
                        defaults={
                            'stock_in_detail': detail,
                            'initial_quantity': detail.quantity,
                            'remaining_quantity': detail.quantity,
                            'import_date': stock_in.import_date,
                        }
                    )
                    if not created:
                        product_detail.initial_quantity += detail.quantity
                        product_detail.remaining_quantity += detail.quantity
                        product_detail.save()

                    # Cập nhật số lượng sản phẩm
                    detail.product.quantity += detail.quantity
                    detail.product.save()

            # Kiểm tra lỗi sau khi xử lý
            if not any(formset.errors):
                messages.success(request, 'Đơn nhập kho đã được lưu thành công!')
                return redirect('stock_in')
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)

    categories = ProductCategory.objects.all()
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    employees = User.objects.filter(is_superuser=False)

    context = {
        'title': 'Chỉnh sửa đơn nhập kho' if pk else 'Tạo mới đơn nhập kho',
        'form': form,
        'formset': formset,
        'categories': categories,
        'products': products,
        'suppliers': suppliers,
        'employees': employees,
    }
    return render(request, 'stock_in/stock_in_update.html', context)
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def supplier_list_view(request):
    suppliers = Supplier.objects.all()
    context = {
        "title": "Danh sách nhà cung cấp",
        "suppliers": suppliers,
    }
    return render(request, 'supplier/supplier_list.html', context)

<<<<<<< HEAD
# View cho tạo mới nhà cung cấp
=======
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def supplier_create_view(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        tax_code = request.POST.get('tax_code')
        address = request.POST.get('address')
        mobile_phone = request.POST.get('phone')
        email = request.POST.get('email')
        supplier_notes = request.POST.get('notes')
        company_name = request.POST.get('company_name')

        missing_fields = []
        if not supplier_name:
            missing_fields.append("Tên nhà cung cấp")
        if not tax_code:
            missing_fields.append("Mã số thuế")
        if not email:
            missing_fields.append("Email")
        if not mobile_phone:
            missing_fields.append("Số điện thoại")

        if missing_fields:
            messages.error(request, f'Vui lòng điền đầy đủ các trường bắt buộc: {", ".join(missing_fields)}!')
            return render(request, 'supplier/supplier_create.html', {'form_data': request.POST})

        if company_name:
            supplier_notes = f"Công ty: {company_name}\n{supplier_notes or ''}"

        try:
            Supplier.objects.create(
                supplier_name=supplier_name,
                tax_code=tax_code,
                address=address,
                phone=mobile_phone,
                email=email,
                notes=supplier_notes,
                company_name=company_name or "",
                created_at=timezone.now(),
                update_at=timezone.now(),
            )
            messages.success(request, 'Thêm nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_create.html', {'form_data': request.POST})

    return render(request, 'supplier/supplier_create.html', {"title": "Tạo mới nhà cung cấp", 'form_data': {}})

# View cho chỉnh sửa nhà cung cấp
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
            supplier.update_at = timezone.now()
            supplier.save()
            messages.success(request, 'Cập nhật nhà cung cấp thành công!')
            return redirect('supplier_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'supplier/supplier_update.html', {'supplier': supplier})

    return render(request, 'supplier/supplier_update.html', {'supplier': supplier, 'title': "Chỉnh sửa nhà cung cấp"})

# View cho xóa nhà cung cấp
def supplier_delete_view(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Xóa nhà cung cấp thành công!')
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_confirm_delete.html', {'supplier': supplier, 'title': "Xóa nhà cung cấp"})

@login_required
def near_expiry_list_view(request):
    today = timezone.now()
    end_date = today + timedelta(days=30)
    search_query = request.GET.get('q', '')
    near_expiry_products = ProductDetail.objects.filter(
        expiry_date__range=(today, end_date),
        remaining_quantity__gt=0
    ).select_related('product__category', 'product__unit').order_by('expiry_date')

    if search_query:
        near_expiry_products = near_expiry_products.filter(product__product_name__icontains=search_query)

    products_with_days_left = []
    for detail in near_expiry_products:
        days_left = (detail.expiry_date - today).days
        products_with_days_left.append({
            'detail': detail,
            'days_left': max(0, days_left),
        })

    context = {
        "title": "Hàng gần đến ngày hết hạn",
        "near_expiry_products": products_with_days_left,
        "search_query": search_query,
    }
    return render(request, 'check/near_expiry_list.html', context)

@login_required
def low_stock_list_view(request):
<<<<<<< HEAD
    context = {"title": "Hàng gần hết trong kho"}
    return render(request, 'check/low_stock_list.html', context)

def unit_list(request):
    units = Unit.objects.all()
    query = request.GET.get('q')
    if query:
        units = units.filter(name__icontains=query) | units.filter(symbol__icontains=query)
    return render(request, 'units/units_list.html', {'units': units})

# Tạo đơn vị
=======
    search_query = request.GET.get('q', '')
    low_stock_products = []
    products = Product.objects.all().prefetch_related('product_details').select_related('category', 'unit')

    if search_query:
        products = products.filter(product_name__icontains=search_query)

    for product in products:
        total_quantity = product.product_details.aggregate(total=Sum('remaining_quantity'))['total'] or 0
        if total_quantity <= product.minimum_stock:
            low_stock_products.append({
                'product': product,
                'total_quantity': total_quantity,
                'minimum_stock': product.minimum_stock,
            })

    context = {
        "title": "Hàng gần hết trong kho",
        "low_stock_products": low_stock_products,
        "search_query": search_query,
    }
    return render(request, 'check/low_stock_list.html', context)

@login_required
def unit_list(request):
    units = Unit.objects.all()
    query = request.GET.get('q')
    if query:
        units = units.filter(name__icontains=query) | units.filter(symbol__icontains=query)
    return render(request, 'units/units_list.html', {'units': units})

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
    return render(request, 'units/edit_unit.html', {'form': form, 'unit': unit})

@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def create_unit(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đơn vị đã được tạo thành công!')
            return redirect('units_list')
    else:
        form = UnitForm()
    return render(request, 'units/create_unit.html', {'form': form})

<<<<<<< HEAD
# Cập nhật đơn vị
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
    return render(request, 'units/edit_unit.html', {'form': form, 'unit': unit})

# Xóa đơn vị
=======
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        unit.delete()
        messages.success(request, 'Đơn vị đã được xóa thành công!')
        return redirect('units_list')
    return render(request, 'units/units_list.html', {'unit': unit})

<<<<<<< HEAD
import datetime
from django.shortcuts import render
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.http import JsonResponse
from .models import StockOut, StockOutDetail, StockIn, StockInDetail, ProductCategory

=======
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def report_overview(request):
    today = timezone.now()
    start_date = today.replace(day=1)  # Bắt đầu từ ngày đầu tháng
    end_date = today

    # Số đơn hàng
    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()
    so_don_hang_last_month = StockOut.objects.filter(
        export_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).count()
    so_don_hang_change = so_don_hang - so_don_hang_last_month

    # Doanh thu (tính từ StockOutDetail, bao gồm số lượng và chiết khấu)
    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị nhập kho (tính từ StockInDetail, bao gồm số lượng và chiết khấu)
    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_last_month = StockInDetail.objects.filter(
        import_record__import_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_change = gia_tri_nhap_kho - gia_tri_nhap_kho_last_month

    # Giá trị xuất kho (tính từ StockOutDetail, bao gồm số lượng và chiết khấu)
    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải trả (tính từ StockIn với payment_status='UNPAID')
    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải thu (tính từ StockOut với payment_status='UNPAID')
    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Tính tiến trình nợ (progress) - tỷ lệ phần trăm so với tổng giá trị nhập/xuất
    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    # Dữ liệu cho biểu đồ phân bổ hàng hóa
    total_quantity = ProductCategory.objects.aggregate(total=Sum('product__quantity'))['total'] or 1
    categories = ProductCategory.objects.annotate(
        total_quantity=Sum('product__quantity')
    ).values('category_name', 'total_quantity')
    overview_chart_data = [
        {
            'name': cat['category_name'],
            'value': (cat['total_quantity'] or 0) / total_quantity * 100
        }
        for cat in categories
    ]

    # Dữ liệu cho biểu đồ xu hướng nhập/xuất kho
    months = []
    for i in range(3, -1, -1):
        month_start = (today - datetime.timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    context = {
        'today': today,
        'so_don_hang': so_don_hang,
        'so_don_hang_change': so_don_hang_change,
        'doanh_thu': doanh_thu,
        'gia_tri_nhap_kho': gia_tri_nhap_kho,
        'gia_tri_nhap_kho_change': gia_tri_nhap_kho_change,
        'gia_tri_xuat_kho': gia_tri_xuat_kho,
        'no_phai_tra': no_phai_tra,
        'no_phai_thu': no_phai_thu,
        'no_phai_tra_progress': no_phai_tra_progress,
        'no_phai_thu_progress': no_phai_thu_progress,
        'overview_chart_data': overview_chart_data,
        'inventory_trend_data': months,
    }
    return render(request, 'report/overview.html', context)

def ajax_dashboard_stats(request):
    date_range = request.GET.get('dateRange')
    try:
        start_str, end_str = date_range.split(" to ")
        start_date = datetime.datetime.strptime(start_str.strip(), "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_str.strip(), "%d/%m/%Y")
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Số đơn hàng
    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    # Doanh thu
    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị nhập kho
    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Giá trị xuất kho
    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải trả
    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Nợ phải thu
    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    # Tính tiến trình nợ
    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    # Dữ liệu biểu đồ xu hướng
    months = []
    for i in range(3, -1, -1):
        month_start = (start_date - datetime.timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    return JsonResponse({
        'so_don_hang': so_don_hang,
        'doanh_thu': float(doanh_thu) if doanh_thu else 0,
        'gia_tri_nhap_kho': float(gia_tri_nhap_kho) if gia_tri_nhap_kho else 0,
        'gia_tri_xuat_kho': float(gia_tri_xuat_kho) if gia_tri_xuat_kho else 0,
        'no_phai_tra': float(no_phai_tra) if no_phai_tra else 0,
        'no_phai_thu': float(no_phai_thu) if no_phai_thu else 0,
        'no_phai_tra_progress': float(no_phai_tra_progress),
        'no_phai_thu_progress': float(no_phai_thu_progress),
        'inventory_trend_data': months,
    })


@login_required
def product_category_view(request):
    context = {"title": "Danh mục sản phẩm"}
    return render(request, 'product_category/product_category_list.html', context)
<<<<<<< HEAD

def product_category_update(request):
    context = {"title": "Tạo mới danh mục sản phẩm"}
    return render(request, 'product_category/product_category_update.html', context)

=======
@login_required
def product_category_update(request):
    context = {"title": "Tạo mới danh mục sản phẩm"}
    return render(request, 'product_category/product_category_update.html', context)
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def product_category_detail(request):
    context = {"title": "Chi tiết sản phẩm"}
    return render(request, 'product_category/product_category_detail.html', context)

@login_required
def product_view(request):
    products = Product.objects.all().order_by('product_name')
    search_text = request.GET.get('search', '').strip()
    filter_category = request.GET.get('category', '')
    filter_supplier = request.GET.get('supplier', '')
    filter_stock_status = request.GET.get('stock_status', '')

    if search_text:
        products = products.filter(
            Q(product_name__icontains=search_text) |
            Q(category__category_name__icontains=search_text) |
            Q(supplier__company_name__icontains=search_text)
        )

    if filter_category:
        products = products.filter(category__id=filter_category)

    # Lọc theo nhà cung cấp
    if filter_supplier:
        products = products.filter(supplier__id=filter_supplier)

    # Lọc theo trạng thái tồn kho
    if filter_stock_status == 'low_stock':
        products = products.filter(quantity__lte=F('minimum_stock'))
    elif filter_stock_status == 'out_of_stock':
        products = products.filter(quantity=0)

    categories = ProductCategory.objects.all()
    suppliers = Supplier.objects.all()
    context = {
        "title": "Danh sách sản phẩm",
        "products": products,
        "search_text": search_text,
        "categories": categories,
        "suppliers": suppliers,
        "filter_category": filter_category,
        "filter_supplier": filter_supplier,
        "filter_stock_status": filter_stock_status,
    }
    return render(request, 'product/product_list.html', context)

<<<<<<< HEAD
def product_update(request):
    context = {"title": "Tạo mới sản phẩm"}
    return render(request, 'product/product_update.html', context)

=======
@login_required
def product_update(request):
    context = {"title": "Tạo mới sản phẩm"}
    return render(request, 'product/product_update.html', context)
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def product_detail(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_detail.html', context)

<<<<<<< HEAD
# Khách hàng
from django.db import connection

=======
#Khách hàng
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def customer_list(request):
    # Chỉ chọn các trường hiện có trong database
    customers = Customer.objects.only(
        'id', 'first_name', 'last_name', 'email', 'phone', 'address', 'created_at', 'update_at'
    ).order_by('-created_at')

    # Xử lý tìm kiếm
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # Phân trang
    paginator = Paginator(customers, 10)  # Hiển thị 10 khách hàng trên mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "title": "Danh sách khách hàng",
        'customers': page_obj
    }
    return render(request, "customer/customer_list.html", context)
<<<<<<< HEAD


=======
@login_required
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
def customer_create(request):
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        # Kiểm tra dữ liệu
        if not first_name or not last_name or not phone or not address:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc!')
            return render(request, "customer/customer_form.html", {
                'title': 'Thêm mới khách hàng',
                'form_data': request.POST
            })

        # Tạo khách hàng mới
        try:
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                created_at=timezone.now(),
                update_at=timezone.now()
            )
            customer.save()
            messages.success(request, 'Thêm khách hàng thành công!')
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    context = {
        "title": "Thêm mới khách hàng",
        "form_data": {}
    }
    return render(request, "customer/customer_form.html", context)

<<<<<<< HEAD

def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        customer.first_name = request.POST.get('first_name')
        customer.last_name = request.POST.get('last_name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')

        # Kiểm tra dữ liệu
        if not customer.first_name or not customer.last_name or not customer.phone or not customer.address:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc!')
            return render(request, "customer/customer_update.html", {
                'title': 'Cập nhật khách hàng',
                'customer': customer
            })

        # Cập nhật khách hàng
        try:
            customer.update_at = timezone.now()
            customer.save()
            messages.success(request, 'Cập nhật khách hàng thành công!')
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')

    # Lấy thông tin đơn hàng của khách hàng
    customer_orders = StockOut.objects.filter(customer=customer).order_by('-export_date')

    # Tính tổng chi tiêu
    total_spent = StockOutDetail.objects.filter(
        export_record__customer=customer,
        export_record__export_status='COMPLETED'
    ).aggregate(
        total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
    )['total'] or 0

    # Tính nợ phải thu
    debt_amount = StockOutDetail.objects.filter(
        export_record__customer=customer,
        export_record__payment_status__in=['UNPAID', 'PARTIALLY_PAID']
    ).aggregate(
        total=Sum(F('quantity') * F('product__selling_price') * (1 - F('discount') / 100))
    )['total'] or 0

    # Lấy ngày đơn hàng gần nhất
    last_order = StockOut.objects.filter(customer=customer).order_by('-export_date').first()
    last_order_date = last_order.export_date.strftime('%d/%m/%Y') if last_order else None

    context = {
        "title": "Cập nhật thông tin khách hàng",
        "customer": customer,
        "customer_orders": customer_orders[:5],  # Chỉ hiển thị 5 đơn hàng gần nhất
        "order_count": customer_orders.count(),
        "total_spent": total_spent,
        "debt_amount": debt_amount,
        "last_order_date": last_order_date
    }
    return render(request, "customer/customer_update.html", context)


def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        try:
            # Kiểm tra xem khách hàng có đơn hàng liên quan không
            related_orders = StockOut.objects.filter(customer=customer).exists()

            if related_orders and not request.POST.get('force_delete') == 'true':
                messages.error(request, 'Không thể xóa khách hàng này vì có đơn hàng liên quan!')
                return redirect('customer_list')

            # Lưu ID của khách hàng để sử dụng sau khi xóa
            customer_id = customer.id
            customer_name = f"{customer.last_name} {customer.first_name}"

            # Xóa đơn hàng liên quan nếu có và được yêu cầu xóa cưỡng bức
            if related_orders and request.POST.get('force_delete') == 'true':
                StockOut.objects.filter(customer=customer).delete()

            # Xóa khách hàng
            customer.delete()

            # Đặt lại bộ đếm tự động tăng trong SQLite
            reset_autoincrement_for_customer(customer_id)

            # Thêm thông báo thành công
            messages.success(request, f'Đã xóa khách hàng {customer_name} thành công và đặt lại ID!')

            # Chuyển hướng về trang danh sách khách hàng
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa khách hàng: {str(e)}')
            return redirect('customer_list')

    # Nếu là GET request, hiển thị trang xác nhận xóa
    # Kiểm tra xem khách hàng có đơn hàng liên quan không
    related_orders = StockOut.objects.filter(customer=customer)
    has_related_orders = related_orders.exists()
    order_count = related_orders.count() if has_related_orders else 0

    context = {
        "title": "Xóa khách hàng",
        "customer": customer,
        "has_related_orders": has_related_orders,
        "order_count": order_count,
        "allow_force_delete": request.user.is_superuser  # Chỉ admin mới có thể xóa cưỡng bức
    }
    return render(request, "customer/customer_confirm_delete.html", context)


def reset_autoincrement_for_customer(deleted_id):
    """
    Đặt lại bộ đếm tự động tăng cho bảng Customer trong SQLite
    để có thể tái sử dụng ID đã xóa.
    """
    try:
        with connection.cursor() as cursor:
            # Lấy ID lớn nhất hiện tại trong bảng Customer
            max_id = Customer.objects.aggregate(Max('id'))['id__max'] or 0

            # Nếu không còn bản ghi nào, đặt sequence về 0
            # Nếu còn bản ghi, đặt sequence về max_id
            new_seq_value = max_id

            # Đặt lại giá trị sequence trong SQLite
            cursor.execute(f"UPDATE sqlite_sequence SET seq = {new_seq_value} WHERE name = 'stockb_customer'")

            # Log thông tin để debug
            print(f"Đã đặt lại sequence cho bảng Customer: {new_seq_value}")
    except Exception as e:
        print(f"Lỗi khi đặt lại sequence: {str(e)}")
=======
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0


@login_required
def inventory_check_list(request):
    inventory_checks = InventoryCheck.objects.all().order_by('-check_date')
    if request.GET.get('search'):
        search_text = unidecode(request.GET['search'].lower())
        inventory_checks = inventory_checks.filter(
            Q(employee__first_name__icontains=search_text) |
            Q(employee__last_name__icontains=search_text) |
            Q(id__icontains=search_text)
        )
    paginator = Paginator(inventory_checks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'inventory_checks': page_obj,
        'title': "Danh sách kiểm kê hàng hóa",
    }
    return render(request, 'inventory/inventory_check_list.html', context)
@login_required
def inventory_check_create(request):
    return inventory_check_update(request)
@login_required
def inventory_check_update(request, pk=None):
    if pk:
        inventory_check = get_object_or_404(InventoryCheck, pk=pk)
    else:
        inventory_check = InventoryCheck()

    form = InventoryCheckForm(instance=inventory_check)
    formset = InventoryCheckDetailFormSet(instance=inventory_check, prefix='inventorycheckdetail_set')

    if request.method == "POST":
        form = InventoryCheckForm(request.POST, instance=inventory_check)
        formset = InventoryCheckDetailFormSet(request.POST, instance=inventory_check, prefix='inventorycheckdetail_set')

        print("POST Data:", request.POST)
        if form.is_valid() and formset.is_valid():
            print("Form Cleaned Data:", form.cleaned_data)
            print("Formset Cleaned Data:", [f.cleaned_data for f in formset])

            inventory_check = form.save(commit=False)
            if not inventory_check.check_date:
                inventory_check.check_date = timezone.now()
            inventory_check.save()

            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
                # Cập nhật remaining_quantity nếu thực tế > lý thuyết
                if instance.actual_quantity > instance.theoretical_quantity:
                    product_details = ProductDetail.objects.filter(product=instance.product)
                    for detail in product_details:
                        if detail.remaining_quantity < instance.actual_quantity - instance.theoretical_quantity:
                            detail.remaining_quantity = instance.actual_quantity - instance.theoretical_quantity
                            detail.save()
                        break  # Chỉ cập nhật lô đầu tiên để đơn giản, có thể tối ưu thêm
            formset.save()

            print("InventoryCheckDetails in DB:", inventory_check.details.all())
            return redirect('inventory_check_list')
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)

    products = Product.objects.all()
    employees = User.objects.all()

    product_details = {}
    for product in products:
        total_remaining = ProductDetail.objects.filter(product=product).aggregate(total=Sum('remaining_quantity'))['total'] or product.quantity
        product_details[product.id] = {
            'product_batch': ProductDetail.objects.filter(product=product).first().product_batch if ProductDetail.objects.filter(product=product).exists() else f'LOT00{product.id}',
            'remaining_quantity': total_remaining,
            'import_date': ProductDetail.objects.filter(product=product).first().import_date if ProductDetail.objects.filter(product=product).exists() else product.created_at,
        }

    context = {
        'title': 'Chỉnh sửa kiểm kê hàng hóa' if pk else 'Tạo mới kiểm kê hàng hóa',
        'form': form,
        'formset': formset,
        'products': products,
        'product_details': product_details,
        'employees': employees,
    }
    return render(request, 'inventory/inventory_check_update.html', context)

@login_required
def inventory_check_delete(request, pk):
    inventory_check = get_object_or_404(InventoryCheck, pk=pk)
    if request.method == "POST":
<<<<<<< HEAD
        try:
            inventory_check.delete()
            messages.success(request, "Xóa kiểm kê thành công!")
            return redirect('inventory_check_list')
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra khi xóa kiểm kê: {str(e)}")
            return redirect('inventory_check_list')
    return render(request, 'inventory/inventory_check_confirm_delete.html', {
        'inventory_check': inventory_check,
        'title': "Xóa kiểm kê hàng hóa",
    })
=======
        inventory_check.delete()
        return redirect('inventory_check_list')
    return render(request, 'inventory/inventory_check_list.html', {
        'inventory_checks': InventoryCheck.objects.all().order_by('-check_date')
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu. Vui lòng thử lại.")

    return render(request, 'login.html')
>>>>>>> d3698f53c449ea7292de40625f825062f8b78ce0
