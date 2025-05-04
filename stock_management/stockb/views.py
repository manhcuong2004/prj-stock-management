import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.checks import messages
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q
from django.utils import timezone
from unidecode import unidecode
from .forms import InventoryCheckForm, InventoryCheckDetailFormSet, StockInForm, StockInDetailFormSet
from .models import InventoryCheck, Product, ProductDetail, Supplier, ProductCategory
from .forms import StockOutForm, StockOutDetailFormSet, StockOutDetailForm
from .models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductDetail


# Create your views here.
def index(request):
    return render(request, "main.html")
#Xuất nhập kho
@login_required
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
        "stock_out_list" : stock_out_list,
    }
    return render(request, "stock_out/stock_out_list.html", context)

@login_required
def stock_out_update(request, pk=None):
    stock_out = get_object_or_404(StockOut, pk=pk) if pk else None
    form = StockOutForm(request.POST or None, instance=stock_out)
    formset = StockOutDetailFormSet(request.POST or None, instance=stock_out or StockOut(), prefix='stockoutdetail_set')

    if request.method == "POST":
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
    return render(request, "stock_in/stock_in_list.html", context)

@login_required
def stock_in_update(request, pk=None):
    stock_in = get_object_or_404(StockIn, pk=pk) if pk else None
    form = StockInForm(request.POST or None, instance=stock_in)
    formset = StockInDetailFormSet(request.POST or None, instance=stock_in or StockIn(), prefix='stockindetail_set')

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
def supplier_list_view(request):
    context = {"title": "Danh sách nhà cung cấp"}
    return render(request, 'supplier/supplier_list.html', context)

@login_required
def supplier_create_view(request):
    context = {"title": "Tạo mới nhà cung cấp"}
    if request.method == 'POST':
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_create.html',context)

@login_required
def near_expiry_list_view(request):
    context = {"title": "Hàng gần đến ngày khuyến nghị"}
    return render(request, 'check/near_expiry_list.html', context)

@login_required
def low_stock_list_view(request):
    context = {"title": "Hàng gần hết trong kho"}
    return render(request, 'check/low_stock_list.html',context)


@login_required
def units_view(request):
    context = {"title": "Danh sách đơn vị"}
    return render(request, 'units/units_list.html', context)
@login_required
def create_unit(request):
    context = {"title": "Tạo mới đơn vị"}
    return render(request, 'units/create_unit.html',context)
@login_required
def report_overview(request):
    context = {"title": "Báo cáo"}
    return render(request, 'report/overview.html', context)


@login_required
def product_category_view(request):
    context = {"title": "Danh mục sản phẩm"}
    return render(request, 'product_category/product_category_list.html', context)
@login_required
def product_category_update(request):
    context = {"title": "Tạo mới danh mục sản phẩm"}
    return render(request, 'product_category/product_category_update.html', context)
@login_required
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

    # Tìm kiếm
    if search_text:
        products = products.filter(
            Q(product_name__icontains=search_text) |
            Q(category__category_name__icontains=search_text) |
            Q(supplier__company_name__icontains=search_text)
        )

    # Lọc theo danh mục
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

@login_required
def product_update(request):
    context = {"title": "Tạo mới sản phẩm"}
    return render(request, 'product/product_update.html', context)
@login_required
def product_detail(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_detail.html', context)

#Khách hàng
@login_required
def customer_list(request):
    context = {"title": "Danh sách khách hàng"}
    return render(request, "customer/customer_list.html", context)
@login_required
def customer_create(request):
    context = {"title": "Thêm mới khách hàng"}
    return render(request, "customer/customer_form.html", context)



@login_required
def inventory_check_list(request):
    inventory_checks = InventoryCheck.objects.all().order_by('-check_date')
    context = {
        'inventory_checks': inventory_checks,
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

            # Lưu formset
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save()
                print(f"Saved InventoryCheckDetail: {instance}")

            # Xử lý các chi tiết bị xóa
            for obj in formset.deleted_objects:
                obj.delete()

            print("InventoryCheckDetails in DB:", inventory_check.details.all())
            return redirect('inventory_check_list')
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)

    products = Product.objects.all()
    employees = User.objects.all()

    product_details = {}
    for product in products:
        details = ProductDetail.objects.filter(product=product).first()
        if details:
            product_details[product.id] = {
                'product_batch': details.product_batch,
                'remaining_quantity': details.remaining_quantity,
                'import_date': details.import_date,
            }
        else:
            product_details[product.id] = {
                'product_batch': f'LOT00{product.id}',
                'remaining_quantity': product.quantity,
                'import_date': product.created_at,
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
        inventory_check.delete()
        return redirect('inventory_check_list')
    return render(request, 'inventory/inventory_check_list.html', {
        'inventory_checks': InventoryCheck.objects.all().order_by('-check_date')
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Xác thực người dùng
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Đăng nhập thành công
            login(request, user)
            messages.success(request, "Đăng nhập thành công!")
            return redirect('')
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu. Vui lòng thử lại.")

    return render(request, 'login.html')