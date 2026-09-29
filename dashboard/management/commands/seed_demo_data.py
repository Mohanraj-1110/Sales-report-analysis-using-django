import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from accounts.models import CustomUser, SystemNotification
from datasets.models import DatasetUpload
from datasets.services import process_and_import_dataset, analyze_dataset_file
from customers.services import calculate_rfm_metrics
from predictions.services import train_customer_repurchase_model, execute_bulk_predictions
from forecasting.services import train_and_generate_sales_forecast
from reports.services import generate_report_file

class Command(BaseCommand):
    help = "Seeds realistic demo data or ingests from local Kaggle dataset, trains ML models, and sets up initial users."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1500, help="Number of rows to import from dataset")

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write(self.style.NOTICE(f"=== Initializing RetailAnalytics Pro Demo Setup (Row Limit: {limit}) ==="))

        # 1. Create Default Users
        admin_user, created_adm = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@retailanalytics.local',
                'first_name': 'Chief',
                'last_name': 'Executive',
                'role': CustomUser.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created_adm:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created Administrator user: admin / admin123"))
        else:
            self.stdout.write(self.style.WARNING("[!] Admin user already exists."))

        analyst_user, created_ana = CustomUser.objects.get_or_create(
            username='analyst',
            defaults={
                'email': 'analyst@retailanalytics.local',
                'first_name': 'Sarah',
                'last_name': 'Chen',
                'role': CustomUser.ROLE_ANALYST,
                'is_staff': False
            }
        )
        if created_ana:
            analyst_user.set_password('analyst123')
            analyst_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Created Analyst user: analyst / analyst123"))

        # 2. Check for local dataset file in Dataset/
        dataset_path = os.path.join(settings.DATASETS_DIR, 'Amazon Sale Report.csv')
        if not os.path.exists(dataset_path):
            dataset_path = os.path.join(settings.DATASETS_DIR, 'International sale Report.csv')

        if os.path.exists(dataset_path):
            self.stdout.write(self.style.NOTICE(f"Found source dataset at: {dataset_path}"))
            
            # Copy to media/datasets/raw for persistence
            dest_dir = os.path.join(settings.MEDIA_ROOT, 'datasets', 'raw')
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(dataset_path))
            shutil.copyfile(dataset_path, dest_file)

            analysis = analyze_dataset_file(dest_file)
            
            upload_rec, _ = DatasetUpload.objects.get_or_create(
                name="Amazon E-Commerce Sales Report",
                defaults={
                    'file': f"datasets/raw/{os.path.basename(dataset_path)}",
                    'file_type': 'CSV',
                    'file_size': os.path.getsize(dest_file),
                    'total_rows': analysis['total_rows'],
                    'status': 'Uploaded',
                    'detected_columns': analysis['columns'],
                    'column_mapping': analysis['detected_mapping'],
                    'validation_summary': analysis['missing_summary'],
                    'uploaded_by': admin_user
                }
            )

            self.stdout.write(self.style.NOTICE("Importing and preprocessing records..."))
            process_and_import_dataset(upload_rec, max_rows=limit, user=admin_user)
            self.stdout.write(self.style.SUCCESS(f"[OK] Imported {upload_rec.valid_rows} orders and products successfully."))
        else:
            self.stdout.write(self.style.WARNING("[!] No CSV dataset found in Dataset/ directory. Skipping file import."))

        # 3. Calculate RFM metrics
        self.stdout.write(self.style.NOTICE("Calculating Customer RFM scores and business segments..."))
        count_rfm = calculate_rfm_metrics()
        self.stdout.write(self.style.SUCCESS(f"[OK] Computed RFM segmentation for {count_rfm} customers."))

        # 4. Train Repurchase ML Model
        self.stdout.write(self.style.NOTICE("Training customer repurchase predictive ML models..."))
        model_rec, comp = train_customer_repurchase_model(user=admin_user)
        if model_rec:
            self.stdout.write(self.style.SUCCESS(f"[OK] Trained and activated '{model_rec.algorithm}' with metrics: {model_rec.metrics}"))
            # Execute predictions
            scored = execute_bulk_predictions()
            self.stdout.write(self.style.SUCCESS(f"[OK] Evaluated repurchase likelihood for {scored} customers."))
        else:
            self.stdout.write(self.style.WARNING(f"[!] Model training skipped: {comp}"))

        # 5. Train Sales Forecasting Model
        self.stdout.write(self.style.NOTICE("Training time-series sales forecasting regressor..."))
        forecast_res, err = train_and_generate_sales_forecast(horizon_days=30, user=admin_user)
        if forecast_res:
            self.stdout.write(self.style.SUCCESS(f"[OK] Generated 30-day sales forecast: projected {forecast_res['total_predicted_revenue']:,.2f} INR"))
        else:
            self.stdout.write(self.style.WARNING(f"[!] Forecasting skipped: {err}"))

        # 6. Generate Demo Reports
        self.stdout.write(self.style.NOTICE("Generating sample analytical reports (CSV and Excel)..."))
        generate_report_file('sales', 'csv', user=admin_user)
        generate_report_file('customer', 'excel', user=admin_user)
        self.stdout.write(self.style.SUCCESS("[OK] Sample CSV and Excel reports generated."))

        # 7. Add Notification
        SystemNotification.objects.create(
            user=admin_user,
            title="System Initialization Complete",
            message="The database has been seeded with Kaggle e-commerce data and predictive models have been trained.",
            level="success",
            link="/dashboard/"
        )

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] RetailAnalytics Pro is fully ready!"))
        self.stdout.write(self.style.NOTICE("Admin Login: admin / admin123"))
        self.stdout.write(self.style.NOTICE("Analyst Login: analyst / analyst123"))
