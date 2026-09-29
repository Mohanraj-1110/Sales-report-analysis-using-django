from datetime import date
from django.db.models import Count, Sum, Max, Min, Avg
from django.utils import timezone
from customers.models import Customer
from sales.models import Order

def calculate_rfm_metrics(reference_date=None):
    """
    Computes Recency, Frequency, and Monetary (RFM) metrics for every customer
    based on their order history, assigns quintile scores and business segments.
    """
    if reference_date is None:
        latest_order = Order.objects.order_by('-order_date').first()
        reference_date = latest_order.order_date if latest_order else timezone.now().date()

    # Aggregate customer order metrics
    customer_stats = Order.objects.filter(
        status__in=['Shipped', 'Delivered']
    ).values('customer_id').annotate(
        order_count=Count('id', distinct=True),
        total_spend=Sum('total_amount'),
        avg_order=Avg('total_amount'),
        latest_date=Max('order_date'),
        first_date=Min('order_date')
    )

    if not customer_stats:
        return 0

    customers_to_update = []
    
    # Calculate raw R, F, M
    raw_data = []
    for stat in customer_stats:
        c_id = stat['customer_id']
        latest_dt = stat['latest_date']
        recency = (reference_date - latest_dt).days if latest_dt else 999
        freq = stat['order_count'] or 1
        monetary = float(stat['total_spend'] or 0.0)
        aov = float(stat['avg_order'] or 0.0)

        raw_data.append({
            'customer_id': c_id,
            'recency': max(0, recency),
            'frequency': freq,
            'monetary': monetary,
            'aov': aov,
            'first_date': stat['first_date'],
            'latest_date': latest_dt
        })

    # Quantile binning for RFM scoring (1 to 5)
    r_vals = [d['recency'] for d in raw_data]
    f_vals = [d['frequency'] for d in raw_data]
    m_vals = [d['monetary'] for d in raw_data]

    def get_score(val, sorted_unique, reverse=False):
        if not sorted_unique:
            return 3
        # Rank by percentile
        count = len(sorted_unique)
        pos = sum(1 for x in sorted_unique if x < val)
        pct = pos / count if count > 0 else 0.5
        if reverse:
            # For recency, lower value means higher score
            pct = 1.0 - pct
        if pct >= 0.8:
            return 5
        elif pct >= 0.6:
            return 4
        elif pct >= 0.4:
            return 3
        elif pct >= 0.2:
            return 2
        else:
            return 1

    r_sorted = sorted(r_vals)
    f_sorted = sorted(f_vals)
    m_sorted = sorted(m_vals)

    customer_map = {c.id: c for c in Customer.objects.filter(id__in=[d['customer_id'] for d in raw_data])}

    for item in raw_data:
        c = customer_map.get(item['customer_id'])
        if not c:
            continue

        r_score = get_score(item['recency'], r_sorted, reverse=True)
        f_score = get_score(item['frequency'], f_sorted, reverse=False)
        m_score = get_score(item['monetary'], m_sorted, reverse=False)

        rfm_str = f"{r_score}{f_score}{m_score}"

        # Assign Customer Segment according to standard RFM rules
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            segment = 'Champions'
        elif f_score >= 3 and m_score >= 3:
            segment = 'Loyal Customers'
        elif r_score >= 3 and f_score >= 2:
            segment = 'Potential Loyalists'
        elif r_score >= 4 and f_score <= 2:
            segment = 'Recent Customers'
        elif r_score <= 2 and f_score >= 3:
            segment = 'At Risk'
        elif r_score <= 2 and f_score <= 2 and m_score <= 2:
            segment = 'Lost'
        else:
            segment = 'Potential Loyalists'

        c.recency_days = item['recency']
        c.frequency_orders = item['frequency']
        c.monetary_total = item['monetary']
        c.average_order_value = item['aov']
        c.rfm_score = rfm_str
        c.segment = segment
        c.first_order_date = item['first_date']
        c.last_order_date = item['latest_date']
        customers_to_update.append(c)

    if customers_to_update:
        Customer.objects.bulk_update(
            customers_to_update,
            ['recency_days', 'frequency_orders', 'monetary_total', 'average_order_value', 'rfm_score', 'segment', 'first_order_date', 'last_order_date']
        )

    return len(customers_to_update)
