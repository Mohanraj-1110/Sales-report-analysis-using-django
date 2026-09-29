from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from analytics.services import (
    parse_date_filter,
    get_dashboard_kpis,
    get_revenue_trends,
    get_sales_by_category,
    get_top_products,
    get_geographic_sales
)

@login_required
def sales_analytics(request):
    period = request.GET.get('period', '30d')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date, end_date = parse_date_filter(period=period, start_date_str=start_date_str, end_date_str=end_date_str)
    kpis = get_dashboard_kpis(start_date, end_date)
    trends = get_revenue_trends(start_date, end_date)
    top_products = get_top_products(start_date, end_date, limit=10)

    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'kpis': kpis,
        'trends': trends,
        'top_products': top_products,
    }
    return render(request, 'analytics/sales.html', context)

@login_required
def category_analytics(request):
    period = request.GET.get('period', 'all')
    start_date, end_date = parse_date_filter(period=period)
    cat_data = get_sales_by_category(start_date, end_date)

    # Calculate percentages
    total_rev = sum(cat_data['revenues']) if cat_data['revenues'] else 1.0
    combined = []
    for lbl, rev, count in zip(cat_data['labels'], cat_data['revenues'], cat_data['counts']):
        pct = round((rev / total_rev) * 100, 1) if total_rev > 0 else 0
        combined.append({
            'name': lbl,
            'revenue': rev,
            'count': count,
            'share_pct': pct
        })

    context = {
        'period': period,
        'cat_data': cat_data,
        'categories': combined,
        'total_revenue': total_rev,
    }
    return render(request, 'analytics/categories.html', context)

@login_required
def geography_analytics(request):
    geo_data = get_geographic_sales(limit=15)
    
    total_rev = sum(geo_data['revenues']) if geo_data['revenues'] else 1.0
    regions = []
    for state, rev, orders in zip(geo_data['labels'], geo_data['revenues'], geo_data['orders']):
        pct = round((rev / total_rev) * 100, 1) if total_rev > 0 else 0
        regions.append({
            'state': state,
            'revenue': rev,
            'orders': orders,
            'share_pct': pct
        })

    context = {
        'geo_data': geo_data,
        'regions': regions,
        'total_revenue': total_rev,
    }
    return render(request, 'analytics/geography.html', context)

@login_required
def api_revenue_trends(request):
    period = request.GET.get('period', '30d')
    start_date, end_date = parse_date_filter(period=period)
    trends = get_revenue_trends(start_date, end_date)
    return JsonResponse(trends)

@login_required
def api_category_distribution(request):
    period = request.GET.get('period', '30d')
    start_date, end_date = parse_date_filter(period=period)
    cat_data = get_sales_by_category(start_date, end_date)
    return JsonResponse(cat_data)
