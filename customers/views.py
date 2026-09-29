from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from customers.models import Customer
from customers.services import calculate_rfm_metrics
from predictions.services import predict_single_customer

@login_required
def customer_list(request):
    segment_filter = request.GET.get('segment', '')
    search_query = request.GET.get('q', '').strip()

    customers = Customer.objects.all().order_by('-monetary_total')

    if segment_filter:
        customers = customers.filter(segment=segment_filter)
    if search_query:
        customers = customers.filter(
            Q(customer_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query)
        )

    # Segment counts summary
    segment_counts = Customer.objects.values('segment').annotate(count=Count('id')).order_by('-count')

    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'customers': page_obj,
        'segment_filter': segment_filter,
        'search_query': search_query,
        'segment_counts': segment_counts,
        'total_count': paginator.count,
    }
    return render(request, 'customers/customer_list.html', context)

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer.objects.prefetch_related('orders__items'), pk=pk)
    orders = customer.orders.all().order_by('-order_date')

    # Get ML repurchase propensity prediction
    prediction = predict_single_customer(customer)

    context = {
        'customer': customer,
        'orders': orders,
        'prediction': prediction,
    }
    return render(request, 'customers/customer_detail.html', context)

@login_required
def rfm_matrix(request):
    if request.method == 'POST' and 'recalculate' in request.POST:
        count = calculate_rfm_metrics()
        messages.success(request, f"Successfully recalculated RFM metrics for {count} customers.")
        return redirect('customers:rfm')

    segment_stats = Customer.objects.values('segment').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'segment_stats': segment_stats,
        'total_customers': Customer.objects.count(),
    }
    return render(request, 'customers/rfm.html', context)
