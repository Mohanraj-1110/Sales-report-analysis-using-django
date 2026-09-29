from django.core.management.base import BaseCommand
from reports.services import generate_report_file

class Command(BaseCommand):
    help = "Generates sample CSV or Excel reports for sales, customers, products, or predictions."

    def add_arguments(self, parser):
        parser.add_argument('--type', type=str, default='sales', choices=['sales', 'customer', 'product', 'prediction'], help="Report type")
        parser.add_argument('--format', type=str, default='csv', choices=['csv', 'excel'], help="File format")

    def handle(self, *args, **options):
        rep_type = options['type']
        fmt = options['format']
        self.stdout.write(self.style.NOTICE(f"Generating {rep_type} report in {fmt.upper()} format..."))
        rec, path = generate_report_file(rep_type, fmt)
        self.stdout.write(self.style.SUCCESS(f"Report generated: {path} ({rec.row_count} rows)"))
