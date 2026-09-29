import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from datasets.models import DatasetUpload
from datasets.services import process_and_import_dataset, analyze_dataset_file

class Command(BaseCommand):
    help = "Imports an e-commerce CSV or Excel dataset from a specified file path."

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help="Absolute or relative file path to CSV/Excel")
        parser.add_argument('--limit', type=int, default=2000, help="Max rows to process")

    def handle(self, *args, **options):
        path = options['path']
        limit = options['limit']
        if not os.path.isabs(path):
            path = os.path.join(settings.BASE_DIR, path)

        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"File does not exist: {path}"))
            return

        dest_dir = os.path.join(settings.MEDIA_ROOT, 'datasets', 'raw')
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = os.path.join(dest_dir, os.path.basename(path))
        shutil.copyfile(path, dest_file)

        analysis = analyze_dataset_file(dest_file)
        rec = DatasetUpload.objects.create(
            name=os.path.basename(path),
            file=f"datasets/raw/{os.path.basename(path)}",
            file_type='CSV' if path.endswith('.csv') else 'EXCEL',
            file_size=os.path.getsize(dest_file),
            total_rows=analysis['total_rows'],
            detected_columns=analysis['columns'],
            column_mapping=analysis['detected_mapping'],
            validation_summary=analysis['missing_summary']
        )

        self.stdout.write(self.style.NOTICE(f"Processing and importing {path}..."))
        process_and_import_dataset(rec, max_rows=limit)
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {rec.valid_rows} orders."))
