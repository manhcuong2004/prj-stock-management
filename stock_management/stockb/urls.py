from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('supplier', views.supplier_list_view, name='supplier_list'),
    path('supplier/create', views.supplier_create_view, name='supplier_create'),
    path('inventory/near-expiry', views.near_expiry_list_view, name='near_expiry_list'),
    path('inventory/low-stock', views.low_stock_list_view, name='low_stock_list'),

    path('stock-out/', views.stock_out, name='stock_out'),
    path('stock-out/create', views.stock_out_update, name='stock_out_create'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/create', views.stock_in_update, name='stock_in_create'),

    path('units/', views.units_view, name='units'),
    path('units/create/', views.create_unit, name='create_unit'),
    path('report/', views.report_overview, name='report'),

    path('product-category/', views.product_category_view, name='product_category'),


]
