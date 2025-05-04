from django.urls import path
from django.contrib.auth import views as auth_views
from .views import report_views, index, stock_in_views, stock_out_views, check_views, unit_views, product_category_views, product_views

urlpatterns = [
    path('', index.home, name='home'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('login/', index.login_view, name='login'),

    # Nhà cung cấp
    # path('supplier', views.supplier_list_view, name='supplier_list'),
    # path('supplier/create', views.supplier_create_view, name='supplier_create'),

    # Kiểm tra
    path('check/near-expiry', check_views.near_expiry_list_view, name='near_expiry_list'),
    path('check/low-stock', check_views.low_stock_list_view, name='low_stock_list'),

    #Xuất nhập kho
    path('stock-out/', stock_out_views.stock_out, name='stock_out'),
    path('stock-out/create/', stock_out_views.stock_out_update, name='stock_out_create'),
    path('stock-out/update/<int:pk>/', stock_out_views.stock_out_update, name='stock_out_update'),
    path('stock-in/', stock_in_views.stock_in, name='stock_in'),
    path('stock-in/create', stock_in_views.stock_in_update, name='stock_in_create'),
    path('stock-in/update/<int:pk>/', stock_in_views.stock_in_update, name='stock_in_update'),

    #Đơn vị
    path('units/', unit_views.unit_list, name='units_list'),
    path('units/create/', unit_views.create_unit, name='create_unit'),
    path('units/edit/<int:pk>/', unit_views.edit_unit, name='edit_unit'),
    path('units/delete/<int:pk>/', unit_views.delete_unit, name='delete_unit'),

    # Khách hàng
    # path('customers/', views.customer_list, name='customer_list'),
    # path('customers/create/', views.customer_create, name='customer_create'),

    # Sản phẩm
    path('product/', product_views.product_view, name='product'),
    path('product/<int:pk>/', product_views.product_detail, name='product_detail'),
    path('product/create/', product_views.product_update, name='product_create'),
    path('product/<int:pk>/update/', product_views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', product_views.product_delete, name='product_delete'),

    # Danh mục
    path('product-category/', product_category_views.product_category_view, name='product_category'),
    path('product-category/create/', product_category_views.product_category_create, name='product_category_create'),
    path('product-category/<int:pk>/', product_category_views.product_category_detail, name='product_category_detail'),
    path('product-category/<int:pk>/update/', product_category_views.product_category_update, name='product_category_update'),
    path('product-category/<int:pk>/delete/', product_category_views.product_category_delete, name='product_category_delete'),

    # Kiểm kê
    # path('inventory-check/', views.inventory_check_list, name='inventory_check_list'),
    # path('inventory-check/create/', views.inventory_check_create, name='inventory_check_create'),
    # path('inventory-check/update/<int:pk>/', views.inventory_check_update, name='inventory_check_update'),
    # path('inventory-check/delete/<int:pk>/', views.inventory_check_delete, name='inventory_check_delete'),

    # Báo cáo
    path('report/', report_views.report_overview, name='report'),
    path('report/ajax/', report_views.ajax_dashboard_stats, name='ajax_dashboard_stats'),
]
