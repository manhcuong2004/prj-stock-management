from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('stock-out/', views.stock_out),
    path('units/', views.units_view, name='units'),
    path('units/create/', views.create_unit, name='create_unit'),
    path('report/', views.report_overview, name='report'),
    path('report/overview', views.report_overview, name='report_overview'),
]
