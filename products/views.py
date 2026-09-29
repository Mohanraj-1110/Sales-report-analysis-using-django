from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from products.models import Product, Category

@login_required
def product_list(request):
    category_id = request.GET.get('category', '')
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.select_related('category').annotate(
        total_units_sold=Sum('order_items__quantity'),
        total_rev_generated=Sum('order_items__total_amount')
    ).order_by('-total_rev_generated')

    if category_id:
        products = products.filter(category_id=category_id)
    if search_query:
        products = products.filter(
            Q(sku__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(style__icontains=search_query)
        )

    categories = Category.objects.all()

    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'total_count': paginator.count,
    }
    return render(request, 'products/product_list.html', context)
