import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper
from django.utils import timezone

from ..models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductCategory, ProductDetail


@login_required
def report_overview(request):
    today = timezone.now()
    start_date = today.replace(day=1)
    end_date = today

    so_don_hang_xuat = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()
    so_don_hang_xuat_last_month = StockOut.objects.filter(
        export_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).count()
    so_don_hang_xuat_change = so_don_hang_xuat - so_don_hang_xuat_last_month

    so_don_hang_nhap = StockIn.objects.filter(import_date__range=(start_date, end_date)).count()
    so_don_hang_nhap_last_month = StockIn.objects.filter(
        import_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).count()
    so_don_hang_nhap_change = so_don_hang_nhap - so_don_hang_nhap_last_month

    stock_ins = StockIn.objects.filter(
        import_date__range=(start_date, end_date)
    ).prefetch_related('details')
    gia_tri_nhap_kho = sum(stock_in.total_amount() for stock_in in stock_ins) or 0

    stock_ins_last_month = StockIn.objects.filter(
        import_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).prefetch_related('details')
    gia_tri_nhap_kho_last_month = sum(stock_in.total_amount() for stock_in in stock_ins_last_month) or 0
    gia_tri_nhap_kho_change = gia_tri_nhap_kho - gia_tri_nhap_kho_last_month

    stock_outs = StockOut.objects.filter(
        export_date__range=(start_date, end_date)
    ).prefetch_related('stockoutdetail_set')
    gia_tri_xuat_kho = sum(stock_out.total_amount() for stock_out in stock_outs) or 0

    no_phai_tra = 0
    stock_ins_unpaid = StockIn.objects.filter(
        payment_status__in=['UNPAID', 'PARTIALLY_PAID'],
        import_date__range=(start_date, end_date)
    ).prefetch_related('details')
    for stock_in in stock_ins_unpaid:
        total = stock_in.total_amount()
        no_phai_tra += total - stock_in.amount_paid

    no_phai_thu = 0
    stock_outs_unpaid = StockOut.objects.filter(
        payment_status__in=['UNPAID', 'PARTIALLY_PAID'],
        export_date__range=(start_date, end_date)
    ).prefetch_related('stockoutdetail_set')
    for stock_out in stock_outs_unpaid:
        total = stock_out.total_amount()
        no_phai_thu += total - stock_out.amount_paid

    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    total_quantity = ProductDetail.objects.aggregate(total=Sum('remaining_quantity'))['total'] or 1
    categories = ProductCategory.objects.prefetch_related('product__product_details').annotate(
        total_quantity=Sum('product__product_details__remaining_quantity')
    ).values('category_name', 'total_quantity')
    overview_chart_data = [
        {
            'name': cat['category_name'],
            'value': (cat['total_quantity'] or 0) / total_quantity * 100
        }
        for cat in categories
    ]

    months = []
    for i in range(3, -1, -1):
        month_start = (today - datetime.timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        stock_ins_month = StockIn.objects.filter(
            import_date__range=(month_start, month_end)
        ).prefetch_related('details')
        stock_outs_month = StockOut.objects.filter(
            export_date__range=(month_start, month_end)
        ).prefetch_related('stockoutdetail_set')
        months.append({
            'name': f"T{i+1}",
            'nhapKho': sum(stock_in.total_amount() for stock_in in stock_ins_month) or 0,
            'xuatKho': sum(stock_out.total_amount() for stock_out in stock_outs_month) or 0
        })

    context = {
        'today': today,
        'so_don_hang_xuat': so_don_hang_xuat,
        'so_don_hang_xuat_change': so_don_hang_xuat_change,
        'so_don_hang_nhap': so_don_hang_nhap,
        'so_don_hang_nhap_change': so_don_hang_nhap_change,
        'gia_tri_nhap_kho': gia_tri_nhap_kho,
        'gia_tri_nhap_kho_change': gia_tri_nhap_kho_change,
        'gia_tri_xuat_kho': gia_tri_xuat_kho,
        'no_phai_tra': no_phai_tra,
        'no_phai_thu': no_phai_thu,
        'no_phai_tra_progress': no_phai_tra_progress,
        'no_phai_thu_progress': no_phai_thu_progress,
        'overview_chart_data': overview_chart_data,
        'inventory_trend_data': months,
    }
    return render(request, 'report/overview.html', context)

@login_required
def ajax_dashboard_stats(request):
    date_range = request.GET.get('dateRange')
    try:
        start_str, end_str = date_range.split(" to ")
        start_date = datetime.datetime.strptime(start_str.strip(), "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_str.strip(), "%d/%m/%Y")
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    so_don_hang_xuat = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    so_don_hang_nhap = StockIn.objects.filter(import_date__range=(start_date, end_date)).count()

    stock_ins = StockIn.objects.filter(
        import_date__range=(start_date, end_date)
    ).prefetch_related('details')
    gia_tri_nhap_kho = sum(stock_in.total_amount() for stock_in in stock_ins) or 0

    stock_outs = StockOut.objects.filter(
        export_date__range=(start_date, end_date)
    ).prefetch_related('stockoutdetail_set')
    gia_tri_xuat_kho = sum(stock_out.total_amount() for stock_out in stock_outs) or 0

    no_phai_tra = 0
    stock_ins_unpaid = StockIn.objects.filter(
        payment_status__in=['UNPAID', 'PARTIALLY_PAID'],
        import_date__range=(start_date, end_date)
    ).prefetch_related('details')
    for stock_in in stock_ins_unpaid:
        total = stock_in.total_amount()
        no_phai_tra += total - stock_in.amount_paid

    no_phai_thu = 0
    stock_outs_unpaid = StockOut.objects.filter(
        payment_status__in=['UNPAID', 'PARTIALLY_PAID'],
        export_date__range=(start_date, end_date)
    ).prefetch_related('stockoutdetail_set')
    for stock_out in stock_outs_unpaid:
        total = stock_out.total_amount()
        no_phai_thu += total - stock_out.amount_paid

    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    total_quantity = ProductDetail.objects.aggregate(total=Sum('remaining_quantity'))['total'] or 1
    categories = ProductCategory.objects.prefetch_related('product__product_details').annotate(
        total_quantity=Sum('product__product_details__remaining_quantity')
    ).values('category_name', 'total_quantity')
    overview_chart_data = [
        {
            'name': cat['category_name'],
            'value': (cat['total_quantity'] or 0) / total_quantity * 100
        }
        for cat in categories
    ]

    months = []
    for i in range(3, -1, -1):
        month_start = (start_date - datetime.timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        stock_ins_month = StockIn.objects.filter(
            import_date__range=(month_start, month_end)
        ).prefetch_related('details')
        stock_outs_month = StockOut.objects.filter(
            export_date__range=(month_start, month_end)
        ).prefetch_related('stockoutdetail_set')
        months.append({
            'name': f"T{i+1}",
            'nhapKho': sum(stock_in.total_amount() for stock_in in stock_ins_month) or 0,
            'xuatKho': sum(stock_out.total_amount() for stock_out in stock_outs_month) or 0
        })

    return JsonResponse({
        'so_don_hang_xuat': so_don_hang_xuat,
        'so_don_hang_nhap': so_don_hang_nhap,
        'gia_tri_nhap_kho': float(gia_tri_nhap_kho) if gia_tri_nhap_kho else 0,
        'gia_tri_xuat_kho': float(gia_tri_xuat_kho) if gia_tri_xuat_kho else 0,
        'no_phai_tra': float(no_phai_tra) if no_phai_tra else 0,
        'no_phai_thu': float(no_phai_thu) if no_phai_thu else 0,
        'no_phai_tra_progress': float(no_phai_tra_progress),
        'no_phai_thu_progress': float(no_phai_thu_progress),
        'overview_chart_data': overview_chart_data,
        'inventory_trend_data': months,
    })