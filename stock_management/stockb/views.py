from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "main.html")

def stock_out(request):
    return render(request, "stock_out/stock_out.html")

def units_view(request):
    return render(request, 'units/units.html')

def create_unit(request):
    return render(request, 'units/create_unit.html')

def report_overview(request):
    return render(request, 'report/overview.html')
