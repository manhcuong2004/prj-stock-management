from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('supplier/', views.supplier_list_view, name='supplier_list'),
    path('supplier/create/', views.supplier_create_view, name='supplier_create'),
    path('supplier/<int:id>/update/', views.supplier_update_view, name='supplier_update'),  # URL cho chỉnh sửa nhà cung cấp
    path('supplier/<int:id>/delete/', views.supplier_delete_view, name='supplier_delete'),  # URL cho xóa nhà cung cấp
    path('inventory/near-expiry/', views.near_expiry_list_view, name='near_expiry_list'),
    path('inventory/low-stock/', views.low_stock_list_view, name='low_stock_list'),
]