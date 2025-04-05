from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('stock-out/', views.stock_out, name='stock_out'),
    path('stock-out/create', views.stock_out_update, name='stock_out_create'),



    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/create', views.stock_in_update, name='stock_in_create'),


]
