from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "main.html")

def stock_out(request):
    return render(request, "stock_out.html")
