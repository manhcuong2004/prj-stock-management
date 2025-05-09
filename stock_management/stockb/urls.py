from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # Nhà cung cấp
    path('supplier/', views.supplier_list_view, name='supplier_list'),
    path('supplier/create/', views.supplier_create_view, name='supplier_create'),
    path('supplier/<int:id>/update/', views.supplier_update_view, name='supplier_update'),
    path('supplier/<int:id>/delete/', views.supplier_delete_view, name='supplier_delete'),
    # Xuất nhập kho
    path('stock-out/', views.stock_out, name='stock_out'),
    path('stock-out/create/', views.stock_out_update, name='stock_out_create'),
    path('stock-out/update/<int:pk>/', views.stock_out_update, name='stock_out_update'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/create/', views.stock_in_update, name='stock_in_create'),
    # Kiểm kê hàng hóa
    path('inventory-check/', views.inventory_check_list, name='inventory_check_list'),
    path('inventory-check/create/', views.inventory_check_create, name='inventory_check_create'),
    path('inventory-check/update/<int:pk>/', views.inventory_check_update, name='inventory_check_update'),
    path('inventory-check/delete/<int:pk>/', views.inventory_check_delete, name='inventory_check_delete'),
    # Hàng hóa
    path('check/near-expiry/', views.near_expiry_list_view, name='near_expiry_list'),
    path('check/low-stock/', views.low_stock_list_view, name='low_stock_list'),
    path('product/', views.product_view, name='product'),
    path('product/create/', views.product_update, name='product_update'),
    path('product/detail/', views.product_detail, name='product_detail'),
    path('product-category/', views.product_category_view, name='product_category'),
    path('product-category/create/', views.product_category_update, name='product_category_create'),
    path('product-category/detail/', views.product_category_detail, name='product_category_detail'),
    # Đơn vị
    path('units/', views.unit_list, name='units_list'),
    path('units/create/', views.create_unit, name='create_unit'),
    path('units/edit/<int:pk>/', views.edit_unit, name='edit_unit'),
    path('units/delete/<int:pk>/', views.delete_unit, name='delete_unit'),
    # Báo cáo
    path('report/', views.report_overview, name='report'),
    path('report/ajax/', views.ajax_dashboard_stats, name='ajax_dashboard_stats'),
    # Khách hàng
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    # Nhân viên
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
]