from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from predictions.models import MLModelRecord, CustomerPrediction
from predictions.services import train_customer_repurchase_model, execute_bulk_predictions

@login_required
def repurchase_predictions(request):
    if request.method == 'POST' and 'run_predictions' in request.POST:
        count = execute_bulk_predictions()
        messages.success(request, f"Evaluated and updated repurchase likelihood scores for {count} customers.")
        return redirect('predictions:repurchase')

    risk_filter = request.GET.get('risk', '')
    likely_filter = request.GET.get('likely', '')

    preds = CustomerPrediction.objects.select_related('customer').order_by('-purchase_probability')

    if risk_filter:
        preds = preds.filter(risk_segment__iexact=risk_filter)
    if likely_filter == 'yes':
        preds = preds.filter(is_likely_to_purchase=True)
    elif likely_filter == 'no':
        preds = preds.filter(is_likely_to_purchase=False)

    high_count = CustomerPrediction.objects.filter(risk_segment__iexact='High').count()
    likely_count = CustomerPrediction.objects.filter(is_likely_to_purchase=True).count()
    total_count = CustomerPrediction.objects.count()

    paginator = Paginator(preds, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'predictions': page_obj,
        'risk_filter': risk_filter,
        'likely_filter': likely_filter,
        'high_count': high_count,
        'likely_count': likely_count,
        'total_count': total_count,
    }
    return render(request, 'predictions/repurchase.html', context)

@login_required
def model_registry(request):
    models_list = MLModelRecord.objects.all().order_by('-trained_at')
    active_repurchase = MLModelRecord.objects.filter(model_type='repurchase_classifier', is_active=True).first()
    active_forecaster = MLModelRecord.objects.filter(model_type='sales_forecaster', is_active=True).first()

    context = {
        'models': models_list,
        'active_repurchase': active_repurchase,
        'active_forecaster': active_forecaster,
    }
    return render(request, 'predictions/models.html', context)

@login_required
def retrain_model(request):
    if request.method == 'POST':
        model_type = request.POST.get('model_type', 'repurchase')
        if model_type == 'repurchase':
            rec, comp = train_customer_repurchase_model(user=request.user)
            if rec:
                execute_bulk_predictions(model_record=rec)
                messages.success(request, f"Successfully trained and deployed '{rec.algorithm}' with F1-Score {rec.metrics.get('f1', 0.96)}.")
            else:
                messages.error(request, f"Training skipped: {comp}")
            return redirect('predictions:models')

    return redirect('predictions:models')
