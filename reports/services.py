import os
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from sales.models import Order, OrderItem
from customers.models import Customer
from products.models import Product
from predictions.models import CustomerPrediction
from reports.models import GeneratedReport

def generate_report_file(report_type, file_format='csv', user=None):
    """
    Builds data table and writes to CSV or Excel (.xlsx) file in media/reports/.
    """
    timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{report_type}_report_{timestamp_str}.{file_format}"
    
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)

    headers = []
    rows = []

    if report_type == 'sales':
        headers = ['Order ID', 'Date', 'Customer ID', 'Status', 'Fulfilment', 'City', 'State', 'Quantity', 'Amount (INR)']
        orders = Order.objects.all().order_by('-order_date')[:500]
        for o in orders:
            rows.append([
                o.order_id,
                o.order_date.strftime('%Y-%m-%d'),
                o.customer.customer_id,
                o.status,
                o.fulfilment,
                o.shipping_city,
                o.shipping_state,
                o.total_quantity,
                float(o.total_amount)
            ])
        report_title = "E-Commerce Sales Summary Report"

    elif report_type == 'customer':
        headers = ['Customer ID', 'Name', 'City', 'State', 'Segment', 'Recency (Days)', 'Orders Count', 'Total Spend (INR)', 'AOV (INR)', 'RFM Score']
        customers = Customer.objects.all().order_by('-monetary_total')[:500]
        for c in customers:
            rows.append([
                c.customer_id,
                c.name,
                c.city,
                c.state,
                c.segment,
                c.recency_days,
                c.frequency_orders,
                float(c.monetary_total),
                float(c.average_order_value),
                c.rfm_score
            ])
        report_title = "Customer RFM & Value Segmentation Report"

    elif report_type == 'product':
        headers = ['SKU', 'Product Name', 'Category', 'Unit Price (INR)', 'Stock', 'Status']
        products = Product.objects.select_related('category').all()[:500]
        for p in products:
            rows.append([
                p.sku,
                p.name,
                p.category.name if p.category else 'General',
                float(p.unit_price),
                p.stock_quantity,
                p.status
            ])
        report_title = "Product Catalog & Performance Report"

    elif report_type == 'prediction':
        headers = ['Customer ID', 'Customer Segment', 'Purchase Probability', 'Likely to Purchase', 'Risk Level', 'Date Evaluated']
        preds = CustomerPrediction.objects.select_related('customer').all()[:500]
        for p in preds:
            rows.append([
                p.customer.customer_id,
                p.customer.segment,
                f"{p.purchase_probability * 100:.1f}%",
                'Yes' if p.is_likely_to_purchase else 'No',
                p.risk_segment,
                p.predicted_at.strftime('%Y-%m-%d')
            ])
        report_title = "Customer Repurchase Prediction Analysis Report"
    else:
        raise ValueError(f"Unknown report type: {report_type}")

    # Generate File
    if file_format == 'csv':
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    elif file_format == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Analytics Data"

        # Styling
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Calibri", size=10)
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        ws.append(headers)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r_idx, row_data in enumerate(rows, start=2):
            ws.append(row_data)
            for c_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=r_idx, column=c_idx)
                cell.font = regular_font
                cell.border = thin_border

        # Adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(filepath)

    # Save to database
    rel_path = f"reports/{filename}"
    report_record = GeneratedReport.objects.create(
        name=report_title,
        report_type=report_type,
        format=file_format,
        file=rel_path,
        row_count=len(rows),
        generated_by=user
    )

    return report_record, filepath
