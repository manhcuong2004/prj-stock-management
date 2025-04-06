from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('stock-out/', views.stock_out),
    path('supplier', views.supplier_list_view, name='supplier_list'),
    path('supplier/create', views.supplier_create_view, name='supplier_create'),  # URL cho trang tạo nhà cung cấp
    path('inventory/near-expiry', views.near_expiry_list_view, name='near_expiry_list'),  # URL cho danh sách sản phẩm sắp hết hạn
    path('inventory/low-stock', views.low_stock_list_view, name='low_stock_list'),  # URL cho danh sách sản phẩm gần hết trong kho

    ]
