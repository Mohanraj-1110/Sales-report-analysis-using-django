from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from forecasting.models import SalesForecastRecord
from predictions.models import MLModelRecord
from forecasting.services import train_and_generate_sales_forecast
from sales.models import Order

@login_required
def forecast_view(request):
    horizon = int(request.GET.get('horizon', 30))
    if horizon not in [7, 30, 90]:
        horizon = 30

    forecasts = SalesForecastRecord.objects.filter(horizon_days=horizon).order_by('forecast_date')

    # Historical 30-day run-rate
    hist_orders = Order.objects.values('order_date').annotate(
        revenue=Sum('total_amount')
    ).order_by('-order_date')[:30]
    hist_orders = list(reversed(hist_orders))

    hist_labels = [h['order_date'].strftime('%b %d') for h in hist_orders]
    hist_values = [round(float(h['revenue'] or 0.0), 2) for h in hist_orders]

    forecast_labels = [f.forecast_date.strftime('%b %d') for f in forecasts]
    forecast_values = [round(float(f.predicted_revenue or 0.0), 2) for f in forecasts]
    lower_bounds = [round(float(f.lower_bound or 0.0), 2) for f in forecasts]
    upper_bounds = [round(float(f.upper_bound or 0.0), 2) for f in forecasts]

    total_projected = sum(forecast_values)

    active_model = MLModelRecord.objects.filter(model_type='sales_forecaster', is_active=True).first()

    context = {
        'horizon': horizon,
        'forecasts': forecasts,
        'total_projected': total_projected,
        'hist_labels': hist_labels,
        'hist_values': hist_values,
        'forecast_labels': forecast_labels,
        'forecast_values': forecast_values,
        'lower_bounds': lower_bounds,
        'upper_bounds': upper_bounds,
        'active_model': active_model,
    }
    return render(request, 'forecasting/forecast.html', context)

@login_required
def train_forecast(request):
    if request.method == 'POST':
        horizon = int(request.POST.get('horizon', 30))
        res, err = train_and_generate_sales_forecast(horizon_days=horizon, user=request.user)
        if res:
            messages.success(request, f"Generated {horizon}-day sales forecast successfully! Projected revenue: INR {res['total_predicted_revenue']:,.2f}")
        else:
            messages.error(request, f"Forecasting failed: {err}")
        return redirect(f"/forecasting/?horizon={horizon}")

    return redirect('forecasting:forecast')
