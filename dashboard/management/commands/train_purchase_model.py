from django.core.management.base import BaseCommand
from predictions.services import train_customer_repurchase_model, execute_bulk_predictions

class Command(BaseCommand):
    help = "Trains the customer repurchase classification model, persists it with Joblib, and calculates bulk predictions."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Training customer repurchase classification models..."))
        record, comp = train_customer_repurchase_model()
        if not record:
            self.stdout.write(self.style.ERROR(f"Failed to train model: {comp}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Successfully trained {record.algorithm} v{record.version}."))
        self.stdout.write(f"Metrics: {record.metrics}")
        
        self.stdout.write(self.style.NOTICE("Calculating customer predictions..."))
        count = execute_bulk_predictions()
        self.stdout.write(self.style.SUCCESS(f"Scored {count} customers."))
