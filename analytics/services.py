from datetime import timedelta, date
from decimal import Decimal
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from sales.models import Order, OrderItem
from products.models import Product, Category
from customers.models import Customer

def parse_date_filter(period='30d', start_date_str=None, end_date_str=None):
    today = timezone.now().date()
    
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif period == '7d':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == '30d':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == '3m':
        start_date = today - timedelta(days=90)
        end_date = today
    elif period == '6m':
        start_date = today - timedelta(days=180)
        end_date = today
    elif period == '1y':
        start_date = today - timedelta(days=365)
        end_date = today
    elif period == 'prev_year':
        start_date = date(today.year - 1, 1, 1)
        end_date = date(today.year - 1, 12, 31)
    elif period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
    elif period == 'all':
        first_order = Order.objects.order_by('order_date').first()
        start_date = first_order.order_date if first_order else today - timedelta(days=30)
        end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today

    # If dataset dates are historical (e.g. 2021 or 2022), check if orders fall within start_date to end_date.
    # If no orders exist in current calendar window, adjust window relative to latest order date in database!
    latest_order = Order.objects.order_by('-order_date').first()
    if latest_order and period not in ['custom', 'all']:
        max_date = latest_order.order_date
        diff = today - max_date
        if diff.days > 60:
            # Shift window relative to max dataset date
            if period == 'today':
                start_date = max_date
                end_date = max_date
            elif period == 'yesterday':
                start_date = max_date - timedelta(days=1)
                end_date = max_date - timedelta(days=1)
            elif period == '7d':
                start_date = max_date - timedelta(days=7)
                end_date = max_date
            elif period == '30d':
                start_date = max_date - timedelta(days=30)
                end_date = max_date
            elif period == '3m':
                start_date = max_date - timedelta(days=90)
                end_date = max_date
            elif period == '6m':
                start_date = max_date - timedelta(days=180)
                end_date = max_date
            elif period == '1y':
                start_date = max_date - timedelta(days=365)
                end_date = max_date

    return start_date, end_date


def get_dashboard_kpis(start_date, end_date):
    """
    Computes primary business KPIs with prior period comparison & percentage growth.
    """
    days = (end_date - start_date).days + 1
    prior_start = start_date - timedelta(days=days)
    prior_end = start_date - timedelta(days=1)

    curr_qs = Order.objects.filter(order_date__range=[start_date, end_date])
    prior_qs = Order.objects.filter(order_date__range=[prior_start, prior_end])

    # Aggregations
    curr_agg = curr_qs.aggregate(
        total_rev=Sum('total_amount'),
        total_orders=Count('id'),
        avg_order=Avg('total_amount')
    )
    prior_agg = prior_qs.aggregate(
        total_rev=Sum('total_amount'),
        total_orders=Count('id'),
        avg_order=Avg('total_amount')
    )

    curr_rev = float(curr_agg['total_rev'] or 0.0)
    prior_rev = float(prior_agg['total_rev'] or 0.0)
    rev_growth = ((curr_rev - prior_rev) / prior_rev * 100) if prior_rev > 0 else 0.0

    curr_orders = curr_agg['total_orders'] or 0
    prior_orders = prior_agg['total_orders'] or 0
    orders_growth = ((curr_orders - prior_orders) / prior_orders * 100) if prior_orders > 0 else 0.0

    curr_aov = float(curr_agg['avg_order'] or 0.0)
    prior_aov = float(prior_agg['avg_order'] or 0.0)
    aov_growth = ((curr_aov - prior_aov) / prior_aov * 100) if prior_aov > 0 else 0.0

    total_customers = Customer.objects.count()
    active_customers = curr_qs.values('customer_id').distinct().count()
    total_products = Product.objects.count()

    return {
        'total_revenue': curr_rev,
        'prior_revenue': prior_rev,
        'revenue_growth': round(rev_growth, 1),
        'total_orders': curr_orders,
        'prior_orders': prior_orders,
        'orders_growth': round(orders_growth, 1),
        'average_order_value': round(curr_aov, 2),
        'prior_aov': round(prior_aov, 2),
        'aov_growth': round(aov_growth, 1),
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_products': total_products,
        'start_date': start_date,
        'end_date': end_date,
    }


def get_revenue_trends(start_date, end_date):
    """
    Returns daily revenue and order trends for Chart.js
    """
    daily_stats = Order.objects.filter(
        order_date__range=[start_date, end_date]
    ).values('order_date').annotate(
        daily_rev=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('order_date')

    dates = [item['order_date'].strftime('%b %d') for item in daily_stats]
    revenues = [round(float(item['daily_rev'] or 0.0), 2) for item in daily_stats]
    orders = [item['order_count'] for item in daily_stats]

    return {
        'labels': dates,
        'revenues': revenues,
        'orders': orders,
    }


def get_sales_by_category(start_date=None, end_date=None):
    """
    Aggregates revenue and item count by product category.
    """
    items_qs = OrderItem.objects.all()
    if start_date and end_date:
        items_qs = items_qs.filter(order__order_date__range=[start_date, end_date])

    cat_stats = items_qs.values(
        cat_name=F('product__category__name')
    ).annotate(
        total_rev=Sum('total_amount'),
        item_count=Sum('quantity')
    ).order_by('-total_rev')[:8]

    labels = []
    revenues = []
    counts = []

    for item in cat_stats:
        cname = item['cat_name'] or 'Uncategorized'
        labels.append(cname)
        revenues.append(round(float(item['total_rev'] or 0.0), 2))
        counts.append(item['item_count'] or 0)

    return {
        'labels': labels,
        'revenues': revenues,
        'counts': counts,
    }


def get_top_products(start_date=None, end_date=None, limit=7):
    """
    Returns top performing products by revenue.
    """
    items_qs = OrderItem.objects.all()
    if start_date and end_date:
        items_qs = items_qs.filter(order__order_date__range=[start_date, end_date])

    top = items_qs.values(
        'sku', 'product_name'
    ).annotate(
        total_revenue=Sum('total_amount'),
        units_sold=Sum('quantity'),
        orders_count=Count('order_id', distinct=True)
    ).order_by('-total_revenue')[:limit]

    products_list = []
    for item in top:
        products_list.append({
            'sku': item['sku'],
            'name': item['product_name'] or item['sku'],
            'revenue': round(float(item['total_revenue'] or 0.0), 2),
            'units': item['units_sold'] or 0,
            'orders': item['orders_count'] or 0
        })

    return products_list


def get_customer_segment_distribution():
    """
    Returns customer count and monetary share by RFM segment.
    """
    segments = Customer.objects.values('segment').annotate(
        count=Count('id'),
        total_spend=Sum('monetary_total')
    ).order_by('-count')

    labels = [s['segment'] for s in segments]
    counts = [s['count'] for s in segments]
    spend = [round(float(s['total_spend'] or 0.0), 2) for s in segments]

    return {
        'labels': labels,
        'counts': counts,
        'spend': spend
    }


def get_geographic_sales(limit=8):
    """
    Aggregates revenue by shipping state/country.
    """
    geo_stats = Order.objects.exclude(
        shipping_state=''
    ).values('shipping_state').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('-revenue')[:limit]

    labels = [g['shipping_state'] for g in geo_stats]
    revenues = [round(float(g['revenue'] or 0.0), 2) for g in geo_stats]
    orders = [g['orders'] for g in geo_stats]

    return {
        'labels': labels,
        'revenues': revenues,
        'orders': orders
    }
