from django.core.management.base import BaseCommand
from datasets.models import DatasetUpload
from datasets.services import process_and_import_dataset

class Command(BaseCommand):
    help = "Cleans and re-processes an existing uploaded dataset record."

    def add_arguments(self, parser):
        parser.add_argument('--upload-id', type=int, required=True, help="ID of DatasetUpload")
        parser.add_argument('--limit', type=int, default=2000, help="Max rows")

    def handle(self, *args, **options):
        upload_id = options['upload-id']
        try:
            rec = DatasetUpload.objects.get(id=upload_id)
        except DatasetUpload.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"DatasetUpload with ID {upload_id} not found."))
            return

        self.stdout.write(self.style.NOTICE(f"Re-processing dataset {rec.name}..."))
        process_and_import_dataset(rec, max_rows=options['limit'])
        self.stdout.write(self.style.SUCCESS(f"Cleaned and imported {rec.valid_rows} records."))
