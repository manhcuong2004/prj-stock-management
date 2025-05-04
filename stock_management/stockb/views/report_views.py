import datetime

from django.db.models import DecimalField
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper
from django.utils import timezone

from ..models import StockOut, StockOutDetail, Customer, Product, StockIn, StockInDetail, ProductCategory, ProductDetail

def report_overview(request):
    today = timezone.now()
    start_date = today.replace(day=1)
    end_date = today

    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()
    so_don_hang_last_month = StockOut.objects.filter(
        export_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).count()
    so_don_hang_change = so_don_hang - so_don_hang_last_month

    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_last_month = StockInDetail.objects.filter(
        import_record__import_date__range=(
            (start_date - datetime.timedelta(days=30)).replace(day=1),
            start_date - datetime.timedelta(days=1)
        )
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    gia_tri_nhap_kho_change = gia_tri_nhap_kho - gia_tri_nhap_kho_last_month

    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

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
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    context = {
        'today': today,
        'so_don_hang': so_don_hang,
        'so_don_hang_change': so_don_hang_change,
        'doanh_thu': doanh_thu,
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

def ajax_dashboard_stats(request):
    date_range = request.GET.get('dateRange')
    try:
        start_str, end_str = date_range.split(" to ")
        start_date = datetime.datetime.strptime(start_str.strip(), "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_str.strip(), "%d/%m/%Y")
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    so_don_hang = StockOut.objects.filter(export_date__range=(start_date, end_date)).count()

    doanh_thu = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    gia_tri_nhap_kho = StockInDetail.objects.filter(
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    gia_tri_xuat_kho = StockOutDetail.objects.filter(
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    no_phai_tra = StockInDetail.objects.filter(
        import_record__payment_status='UNPAID',
        import_record__import_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    no_phai_thu = StockOutDetail.objects.filter(
        export_record__payment_status='UNPAID',
        export_record__export_date__range=(start_date, end_date)
    ).aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    no_phai_tra_progress = (no_phai_tra / gia_tri_nhap_kho * 100) if gia_tri_nhap_kho > 0 else 0
    no_phai_thu_progress = (no_phai_thu / gia_tri_xuat_kho * 100) if gia_tri_xuat_kho > 0 else 0

    # Dữ liệu cho biểu đồ phân bổ hàng hóa
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
        months.append({
            'name': f"T{i+1}",
            'nhapKho': StockInDetail.objects.filter(
                import_record__import_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__purchase_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0,
            'xuatKho': StockOutDetail.objects.filter(
                export_record__export_date__range=(month_start, month_end)
            ).aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F('quantity') * F('product__selling_price') * (1 - F('discount') / 100),
                        output_field=DecimalField()
                    )
                )
            )['total'] or 0
        })

    return JsonResponse({
        'so_don_hang': so_don_hang,
        'doanh_thu': float(doanh_thu) if doanh_thu else 0,
        'gia_tri_nhap_kho': float(gia_tri_nhap_kho) if gia_tri_nhap_kho else 0,
        'gia_tri_xuat_kho': float(gia_tri_xuat_kho) if gia_tri_xuat_kho else 0,
        'no_phai_tra': float(no_phai_tra) if no_phai_tra else 0,
        'no_phai_thu': float(no_phai_thu) if no_phai_thu else 0,
        'no_phai_tra_progress': float(no_phai_tra_progress),
        'no_phai_thu_progress': float(no_phai_thu_progress),
        'overview_chart_data': overview_chart_data,
        'inventory_trend_data': months,
    })