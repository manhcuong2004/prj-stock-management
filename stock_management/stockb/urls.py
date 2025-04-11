from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('supplier', views.supplier_list_view, name='supplier_list'),
    path('supplier/create', views.supplier_create_view, name='supplier_create'),
    path('inventory/near-expiry', views.near_expiry_list_view, name='near_expiry_list'),
    path('inventory/low-stock', views.low_stock_list_view, name='low_stock_list'),
    #Xuất nhập kho
    path('stock-out/', views.stock_out, name='stock_out'),
    path('stock-out/create', views.stock_out_update, name='stock_out_create'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/create', views.stock_in_update, name='stock_in_create'),

    path('units/', views.units_view, name='units'),
    path('units/create/', views.create_unit, name='create_unit'),
    path('report/', views.report_overview, name='report'),
    # Khách hàng
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),

    path('product-category/', views.product_category_view, name='product_category'),
    path('product-category/create', views.product_category_update, name='product_category_create'),
    path('product-category/detail', views.product_category_detail, name='product_category_detail'),

    path('product/', views.product_view, name='product'),
    path('product/create', views.product_update, name='product_update'),
    path('product/detail', views.product_detail, name='product_detail'),

    # Nhân viên
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
]
