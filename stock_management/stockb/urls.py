from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('stock-out/', views.stock_out),


]
