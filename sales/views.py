from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from sales.models import Order

@login_required
def order_list(request):
    status_filter = request.GET.get('status', '')
    fulfilment_filter = request.GET.get('fulfilment', '')
    search_query = request.GET.get('q', '').strip()

    orders = Order.objects.select_related('customer').order_by('-order_date', '-id')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if fulfilment_filter:
        orders = orders.filter(fulfilment__iexact=fulfilment_filter)
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__customer_id__icontains=search_query) |
            Q(shipping_city__icontains=search_query) |
            Q(shipping_state__icontains=search_query)
        )

    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'status_filter': status_filter,
        'fulfilment_filter': fulfilment_filter,
        'search_query': search_query,
        'total_count': paginator.count,
    }
    return render(request, 'sales/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer').prefetch_related('items__product'), pk=pk)
    items = order.items.all()

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'sales/order_detail.html', context)
