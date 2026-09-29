from django.core.management.base import BaseCommand
from forecasting.services import train_and_generate_sales_forecast

class Command(BaseCommand):
    help = "Trains time-series sales forecasting regressor and generates multi-day future predictions."

    def add_arguments(self, parser):
        parser.add_argument('--horizon', type=int, default=30, help="Forecast horizon days (7, 30, 90)")

    def handle(self, *args, **options):
        horizon = options['horizon']
        self.stdout.write(self.style.NOTICE(f"Training forecasting model for {horizon}-day horizon..."))
        res, err = train_and_generate_sales_forecast(horizon_days=horizon)
        if err:
            self.stdout.write(self.style.ERROR(f"Error: {err}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Forecast complete!"))
        self.stdout.write(f"Metrics: {res['metrics']}")
        self.stdout.write(self.style.SUCCESS(f"Total Projected Revenue: {res['total_predicted_revenue']:,.2f} INR"))
