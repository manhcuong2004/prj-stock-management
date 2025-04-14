import datetime

from django.core.checks import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.db.models import Sum, F, Q
from unidecode import unidecode

from .forms import StockOutForm, StockOutDetailFormSet
from .models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductDetail


# Create your views here.
def index(request):
    return render(request, "main.html")
#Xuất nhập kho
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


def stock_out_update(request):
    if request.method == 'POST':
        form = StockOutForm(request.POST)
        formset = StockOutDetailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    stock_out = form.save(commit=False)
                    stock_out.export_date = datetime.now()
                    stock_out.save()

                    for detail_form in formset:
                        if detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                            detail = detail_form.save(commit=False)
                            detail.export_record = stock_out
                            product = detail.product

                            if product.quantity < detail.quantity:
                                raise ValueError(f'Sản phẩm {product.product_name} không đủ số lượng. Tồn kho: {product.quantity}')

                            product.quantity -= detail.quantity
                            product.save()

                            detail.save()

                            product_detail = ProductDetail.objects.filter(product=product).order_by('-import_date').first()
                            if product_detail:
                                product_detail.remaining_quantity -= detail.quantity
                                product_detail.save()

                    if not stock_out.stockoutdetail_set.exists():
                        stock_out.delete()
                        messages.error(request, 'Phải có ít nhất một sản phẩm.')
                        return redirect('stock_out_create')

                    messages.success(request, f'Đơn hàng xuất kho đã được tạo thành công!')
                    return redirect('stock_out')

            except Exception as e:
                messages.error(request, f'Có lỗi xảy ra: {str(e)}')
                return redirect('stock_out_create')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = StockOutForm()
        formset = StockOutDetailFormSet()

    products = Product.objects.all()
    product_details = {}
    for product in products:
        detail = ProductDetail.objects.filter(product=product).order_by('-import_date').first()
        if detail:
            product_details[product.id] = {
                'product_batch': detail.product_batch,
                'remaining_quantity': detail.remaining_quantity,
                'import_date': detail.import_date,
            }
        else:
            product_details[product.id] = {
                'product_batch': "Không có lô",
                'remaining_quantity': 0,
                'import_date': None,
                'status': "OUT_OF_STOCK",
            }

    context = {
        "title": "Trang tạo mới đơn xuất kho",
        "form": form,
        "formset": formset,
        "products": products,
        "product_details": product_details,  # Truyền product_details vào context
    }
    return render(request, "stock_out/stock_out_update.html", context)

def stock_in(request):
    context = {"title": "Trang xuất kho"}
    return render(request, "stock_in/stock_in_list.html", context)

def stock_in_update(request):
    context = {"title": "Trang tạo mới đơn nhập kho"}
    return render(request, "stock_in/stock_in_update.html", context)


def supplier_list_view(request):
    context = {"title": "Danh sách nhà cung cấp"}
    return render(request, 'supplier/supplier_list.html', context)

def supplier_create_view(request):
    context = {"title": "Tạo mới nhà cung cấp"}
    if request.method == 'POST':
        return redirect('supplier_list')
    return render(request, 'supplier/supplier_create.html',context)

def near_expiry_list_view(request):
    context = {"title": "Hàng gần đến ngày khuyến nghị"}
    return render(request, 'inventory/near_expiry_list.html', context)

def low_stock_list_view(request):
    context = {"title": "Hàng gần hết trong kho"}
    return render(request, 'inventory/low_stock_list.html',context)


def units_view(request):
    context = {"title": "Danh sách đơn vị"}
    return render(request, 'units/units_list.html', context)
def create_unit(request):
    context = {"title": "Tạo mới đơn vị"}
    return render(request, 'units/create_unit.html',context)
def report_overview(request):
    context = {"title": "Báo cáo"}
    return render(request, 'report/overview.html', context)


def product_category_view(request):
    context = {"title": "Danh mục sản phẩm"}
    return render(request, 'product_category/product_category_list.html', context)
def product_category_update(request):
    context = {"title": "Tạo mới danh mục sản phẩm"}
    return render(request, 'product_category/product_category_update.html', context)
def product_category_detail(request):
    context = {"title": "Chi tiết sản phẩm"}
    return render(request, 'product_category/product_category_detail.html', context)

def product_view(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_list.html', context)
def product_update(request):
    context = {"title": "Tạo mới sản phẩm"}
    return render(request, 'product/product_update.html', context)
def product_detail(request):
    context = {"title": "Danh sách sản phẩm"}
    return render(request, 'product/product_detail.html', context)

#Khách hàng
def customer_list(request):
    context = {"title": "Danh sách khách hàng"}
    return render(request, "customer/customer_list.html", context)
def customer_create(request):
    context = {"title": "Thêm mới khách hàng"}
    return render(request, "customer/customer_form.html", context)

#Nhân viên
def  employee_list(request):
    context = {"title": "Danh sách nhân viên"}
    return render(request, "employer/employee_list.html", context)
def employee_create(request):
    context = {"title": "Thêm mới nhân viên"}
    return render(request, "employer/employee_form.html", context)