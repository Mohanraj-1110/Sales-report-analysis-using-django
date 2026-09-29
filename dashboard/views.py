from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from analytics.services import (
    parse_date_filter,
    get_dashboard_kpis,
    get_revenue_trends,
    get_sales_by_category,
    get_customer_segment_distribution
)
from sales.models import Order
from predictions.models import MLModelRecord

@login_required
def index(request):
    period = request.GET.get('period', '30d')
    start_date, end_date = parse_date_filter(period=period)

    kpis = get_dashboard_kpis(start_date, end_date)
    trends = get_revenue_trends(start_date, end_date)
    category_data = get_sales_by_category(start_date, end_date)
    rfm_data = get_customer_segment_distribution()

    recent_orders = Order.objects.select_related('customer').order_by('-order_date', '-id')[:6]

    active_classifier = MLModelRecord.objects.filter(model_type='repurchase_classifier', is_active=True).first()
    active_forecaster = MLModelRecord.objects.filter(model_type='sales_forecaster', is_active=True).first()

    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'kpis': kpis,
        'trends': trends,
        'category_data': category_data,
        'rfm_data': rfm_data,
        'recent_orders': recent_orders,
        'active_classifier': active_classifier,
        'active_forecaster': active_forecaster,
    }
    return render(request, 'dashboard/index.html', context)
