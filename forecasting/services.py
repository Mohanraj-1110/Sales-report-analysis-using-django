import os
import joblib
import numpy as np
import pandas as pd
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sales.models import Order
from forecasting.models import SalesForecastRecord
from predictions.models import MLModelRecord

def generate_daily_sales_series():
    """
    Extracts complete daily aggregated revenue and order counts.
    """
    daily_stats = Order.objects.values('order_date').annotate(
        revenue=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('order_date')

    if not daily_stats:
        return pd.DataFrame()

    df = pd.DataFrame(list(daily_stats))
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['revenue'] = df['revenue'].astype(float)
    df = df.set_index('order_date').asfreq('D', fill_value=0.0)
    return df


def train_and_generate_sales_forecast(horizon_days=30, user=None):
    """
    Trains time-series regression model on daily historical sales and forecasts
    future revenue over 7, 30, or 90 day horizons with confidence intervals.
    """
    df = generate_daily_sales_series()
    if len(df) < 14:
        return None, "Not enough daily sales history to generate forecast (minimum 14 days required)."

    # Build lag and calendar features
    series = df['revenue'].copy()
    feature_df = pd.DataFrame(index=series.index)
    feature_df['revenue'] = series
    
    # Lags
    feature_df['lag_1'] = series.shift(1)
    feature_df['lag_7'] = series.shift(7)
    feature_df['lag_14'] = series.shift(14)
    
    # Rolling averages
    feature_df['rolling_mean_7'] = series.shift(1).rolling(window=7).mean()
    feature_df['rolling_mean_14'] = series.shift(1).rolling(window=14).mean()
    
    # Calendar features
    feature_df['day_of_week'] = feature_df.index.dayofweek
    feature_df['is_weekend'] = feature_df['day_of_week'].isin([5, 6]).astype(int)
    feature_df['day_of_month'] = feature_df.index.day
    feature_df['month'] = feature_df.index.month

    # Drop NA rows caused by lagging
    clean_df = feature_df.dropna()
    if len(clean_df) < 7:
        clean_df = feature_df.fillna(0.0)

    feature_cols = ['lag_1', 'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_14', 'day_of_week', 'is_weekend', 'day_of_month', 'month']
    X = clean_df[feature_cols]
    y = clean_df['revenue']

    # Train Ridge Regressor for stable time-series trend extrapolation
    model = Ridge(alpha=1.0)
    model.fit(X, y)

    preds = model.predict(X)
    mae = round(float(mean_absolute_error(y, preds)), 2)
    rmse = round(float(np.sqrt(mean_squared_error(y, preds))), 2)
    r2 = round(float(r2_score(y, preds)), 4)

    residuals = y - preds
    std_error = float(np.std(residuals)) if len(residuals) > 0 else 50.0

    # Persist model
    os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
    model_path = os.path.join(settings.ML_MODELS_DIR, 'sales_forecaster.joblib')
    joblib.dump(model, model_path)

    metrics = {
        'mae': mae,
        'rmse': rmse,
        'r2_score': r2,
        'std_error': round(std_error, 2)
    }

    MLModelRecord.objects.filter(model_type='sales_forecaster').update(is_active=False)
    record = MLModelRecord.objects.create(
        name="Time-Series Sales Forecaster",
        model_type='sales_forecaster',
        algorithm="Ridge Time-Series Regression",
        version="1.0.0",
        file_path=model_path,
        is_active=True,
        metrics=metrics,
        training_sample_count=len(clean_df),
        feature_names=feature_cols,
        trained_by=user
    )

    # Iterative multi-step forecasting
    last_date = series.index[-1]
    last_series = list(series.values)
    forecast_results = []
    
    # Delete old forecasts for this horizon
    SalesForecastRecord.objects.filter(horizon_days=horizon_days).delete()
    db_records = []

    for step in range(1, horizon_days + 1):
        target_date = last_date + timedelta(days=step)
        
        # Build features for this step
        lag_1 = last_series[-1]
        lag_7 = last_series[-7] if len(last_series) >= 7 else lag_1
        lag_14 = last_series[-14] if len(last_series) >= 14 else lag_7
        roll_7 = float(np.mean(last_series[-7:]))
        roll_14 = float(np.mean(last_series[-14:]))
        dow = target_date.dayofweek
        is_wk = 1 if dow in [5, 6] else 0
        dom = target_date.day
        mon = target_date.month

        step_features = pd.DataFrame([[lag_1, lag_7, lag_14, roll_7, roll_14, dow, is_wk, dom, mon]], columns=feature_cols)
        pred_rev = max(0.0, float(model.predict(step_features)[0]))
        
        lower_bound = max(0.0, pred_rev - (1.96 * std_error))
        upper_bound = pred_rev + (1.96 * std_error)

        last_series.append(pred_rev)

        forecast_record = SalesForecastRecord(
            model_record=record,
            forecast_date=target_date.date(),
            horizon_days=horizon_days,
            predicted_revenue=Decimal(f"{pred_rev:.2f}"),
            predicted_orders=max(1, int(pred_rev / 500)),
            lower_bound=Decimal(f"{lower_bound:.2f}"),
            upper_bound=Decimal(f"{upper_bound:.2f}")
        )
        db_records.append(forecast_record)
        forecast_results.append({
            'date': target_date.strftime('%Y-%m-%d'),
            'label': target_date.strftime('%b %d'),
            'revenue': round(pred_rev, 2),
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2)
        })

    SalesForecastRecord.objects.bulk_create(db_records)

    return {
        'model_record': record,
        'metrics': metrics,
        'forecast_points': forecast_results,
        'total_predicted_revenue': round(sum(p['revenue'] for p in forecast_results), 2),
        'horizon_days': horizon_days
    }, None
