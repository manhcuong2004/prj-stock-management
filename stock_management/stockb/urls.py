from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('stock-out/create', views.stock_out_update, name='stock_out_create'),



    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/create', views.stock_in_update, name='stock_in_create'),

    # Khách hàng
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),

    # Nhân viên
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
]
