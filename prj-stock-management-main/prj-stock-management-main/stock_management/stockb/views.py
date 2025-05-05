import datetime
import json
from django.core.checks import messages
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, Q, Count
from django.utils import timezone
from django.http import JsonResponse
from .forms import InventoryCheckForm, InventoryCheckDetailFormSet
from .forms import StockOutForm, StockOutDetailFormSet, StockOutDetailForm
from .models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductDetail, Employee, ProductCategory, Supplier, Notification
from django.contrib import messages
from .forms import ProductForm, ProductCategoryForm

# Hàm index
def index(request):
    context = {"title": "Trang chủ"}
    return render(request, "main.html", context)

# API để lấy danh sách thông báo
def get_notifications(request):
    # Lấy tổng số thông báo chưa đọc từ queryset gốc
    unread_count = Notification.objects.filter(is_read=False).count()
    # Lấy danh sách 50 thông báo mới nhất
    notifications = Notification.objects.all().order_by('-created_at')[:50]
    data = [
        {
            'message': notification.message,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_read': notification.is_read,
        }
        for notification in notifications
    ]
    return JsonResponse({'notifications': data, 'unread_count': unread_count})

# API để đánh dấu tất cả thông báo là đã đọc
def mark_notifications_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

# View cho Product
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

    if filter_supplier:
        products = products.filter(supplier__id=filter_supplier)

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

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product_details = ProductDetail.objects.filter(product=product)
    context = {
        "title": f"Chi tiết sản phẩm - {product.product_name}",
        "product": product,
        "product_details": product_details,
    }
    return render(request, 'product/product_detail.html', context)

def product_update(request, pk=None):
    if pk:
        product = get_object_or_404(Product, pk=pk)
        title = f"Chỉnh sửa sản phẩm - {product.product_name}"
    else:
        product = None
        title = "Thêm sản phẩm mới"

    form = ProductForm(instance=product)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if not product.created_at:
                product.created_at = timezone.now()
            product.save()
            action = "thêm" if not pk else "cập nhật"
            message = f"NV001 đã {action} sản phẩm {product.product_name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('product')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")

    context = {
        "title": title,
        "form": form,
    }
    return render(request, 'product/product_update.html', context)

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product_name = product.product_name
        product.delete()
        message = f"NV001 đã xóa sản phẩm {product_name} thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('product')
    return redirect('product')

# View cho ProductCategory
def product_category_view(request):
    categories = ProductCategory.objects.all().order_by('category_name')
    search_text = request.GET.get('search', '').strip()
    filter_product_status = request.GET.get('product_status', '')

    if search_text:
        categories = categories.filter(
            Q(category_name__icontains=search_text) |
            Q(description__icontains=search_text)
        )

    if filter_product_status == 'has_products':
        categories = categories.annotate(product_count=Count('product')).filter(product_count__gt=0)
    elif filter_product_status == 'no_products':
        categories = categories.annotate(product_count=Count('product')).filter(product_count=0)

    context = {
        "title": "Danh sách danh mục sản phẩm",
        "categories": categories,
        "search_text": search_text,
        "filter_product_status": filter_product_status,
    }
    return render(request, 'product_category/product_category_list.html', context)

def product_category_detail(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    products = Product.objects.filter(category=category)
    context = {
        "title": f"Danh sách sản phẩm trong danh mục - {category.category_name}",
        "category": category,
        "products": products,
    }
    return render(request, 'product_category/product_category_detail.html', context)

def product_category_update(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    form = ProductCategoryForm(instance=category)

    if request.method == "POST":
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            message = f"NV001 đã cập nhật danh mục {category.category_name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('product_category')
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin nhập vào.")

    context = {
        "title": f"Chỉnh sửa danh mục - {category.category_name}",
        "form": form,
        "category": category,
    }
    return render(request, 'product_category/product_category_update.html', context)

def product_category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    if request.method == "POST":
        if Product.objects.filter(category=category).exists():
            messages.error(request, "Không thể xóa danh mục vì vẫn còn sản phẩm liên kết!")
        else:
            category_name = category.category_name
            category.delete()
            message = f"NV001 đã xóa danh mục {category_name} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('product_category')
    return redirect('product_category')

# Các view khác
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

        if form.is_valid() and formset.is_valid():
            stock_out = form.save(commit=False)
            if not stock_out.export_date:
                stock_out.export_date = timezone.now()
            stock_out.save()

            if pk:
                stock_out.stockoutdetail_set.all().delete()

            for detail_form in formset:
                if detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                    detail = detail_form.save(commit=False)
                    detail.export_record = stock_out
                    if detail.quantity and detail.product:
                        detail.amount_paid = (
                            detail.quantity * detail.product.selling_price * (1 - detail.discount / 100)
                        )
                    detail.save()

            action = "cập nhật" if pk else "tạo"
            message = f"NV001 đã {action} đơn xuất kho {stock_out.id} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('stock_out')

    products = Product.objects.all()
    customers = Customer.objects.all()
    employees = Employee.objects.all()

    product_details = {}
    for product in products:
        product_details[product.id] = {
            'product_batch': f'LOT00{product.id}',
            'remaining_quantity': 10,
            'import_date': product.created_at if hasattr(product, 'created_at') else None,
            'selling_price': int(product.selling_price) if hasattr(product, 'selling_price') else 0,
        }

    context = {
        'title': 'Chỉnh sửa đơn xuất kho' if pk else 'Tạo mới đơn xuất kho',
        'form': form,
        'formset': formset,
        'products': products,
        'product_details': product_details,
        'customers': customers,
        'employees': employees,
    }
    return render(request, 'stock_out/stock_out_update.html', context)

def stock_in(request):
    context = {"title": "Trang nhập kho"}
    return render(request, "stock_in/stock_in_list.html", context)

def stock_in_update(request):
    context = {"title": "Trang tạo mới đơn nhập kho"}
    if request.method == 'POST':
        message = "NV001 đã tạo đơn nhập kho thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('stock_in')
    return render(request, "stock_in/stock_in_update.html", context)

def supplier_list_view(request):
    context = {"title": "Danh sách nhà cung cấp"}
    return render(request, 'supplier/supplier_list.html', context)

def supplier_create_view(request):
    context = {"title": "Tạo mới nhà cung cấp"}
    if request.method == 'POST':
        message = "NV001 đã tạo nhà cung cấp thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_create.html', context)

def near_expiry_list_view(request):
    context = {"title": "Hàng gần đến ngày khuyến nghị"}
    return render(request, 'check/near_expiry_list.html', context)

def low_stock_list_view(request):
    context = {"title": "Hàng gần hết trong kho"}
    return render(request, 'check/low_stock_list.html', context)

def units_view(request):
    context = {"title": "Danh sách đơn vị"}
    return render(request, 'units/units_list.html', context)

def create_unit(request):
    context = {"title": "Tạo mới đơn vị"}
    if request.method == 'POST':
        message = "NV001 đã tạo đơn vị thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('units')
    return render(request, 'units/create_unit.html', context)

def report_overview(request):
    context = {"title": "Báo cáo"}
    return render(request, 'report/overview.html', context)

def customer_list(request):
    context = {"title": "Danh sách khách hàng"}
    return render(request, "customer/customer_list.html", context)

def customer_create(request):
    context = {"title": "Thêm mới khách hàng"}
    if request.method == 'POST':
        message = "NV001 đã tạo khách hàng thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('customer_list')
    return render(request, "customer/customer_form.html", context)

def employee_list(request):
    context = {"title": "Danh sách nhân viên"}
    return render(request, "employer/employee_list.html", context)

def employee_create(request):
    context = {"title": "Thêm mới nhân viên"}
    if request.method == 'POST':
        message = "NV001 đã tạo nhân viên thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('employee_list')
    return render(request, "employer/employee_form.html", context)

def inventory_check_list(request):
    inventory_checks = InventoryCheck.objects.all().order_by('-check_date')
    context = {
        'inventory_checks': inventory_checks,
    }
    return render(request, 'inventory/inventory_check_list.html', context)

def inventory_check_create(request):
    return inventory_check_update(request)

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
                print(f"Saved InventoryCheckDetail: {instance}")

            for obj in formset.deleted_objects:
                obj.delete()

            print("InventoryCheckDetails in DB:", inventory_check.details.all())
            action = "cập nhật" if pk else "tạo"
            message = f"NV001 đã {action} kiểm kê {inventory_check.id} thành công!"
            messages.success(request, message)
            Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
            return redirect('inventory_check_list')
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.")

    products = Product.objects.all()
    employees = Employee.objects.all()

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

def inventory_check_delete(request, pk):
    inventory_check = get_object_or_404(InventoryCheck, pk=pk)
    if request.method == "POST":
        inventory_check_id = inventory_check.id
        inventory_check.delete()
        message = f"NV001 đã xóa kiểm kê {inventory_check_id} thành công!"
        messages.success(request, message)
        Notification.objects.create(message=message, created_at=timezone.now(), is_read=False)
        return redirect('inventory_check_list')
    return render(request, 'inventory/inventory_check_list.html', {
        'inventory_checks': InventoryCheck.objects.all().order_by('-check_date')
    })