import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from products.models import Category, Product
from customers.models import Customer
from sales.models import Order, OrderItem
from accounts.models import AuditLog, SystemNotification

COLUMN_CANDIDATES = {
    'order_id': ['Order ID', 'InvoiceNo', 'order_id', 'OrderID', 'Invoice', 'index'],
    'order_date': ['Date', 'InvoiceDate', 'order_date', 'DATE', 'Order Date'],
    'customer_id': ['Customer ID', 'CustomerID', 'CUSTOMER', 'customer_id', 'Customer Name', 'Buyer'],
    'sku': ['SKU', 'StockCode', 'Style', 'Product ID', 'sku', 'Sku', 'Style Id'],
    'product_name': ['Category', 'Description', 'Product Name', 'Catalog', 'Design No.', 'Style'],
    'category': ['Category', 'Catalog', 'Style'],
    'quantity': ['Qty', 'Quantity', 'PCS', 'quantity'],
    'unit_price': ['Amount', 'UnitPrice', 'RATE', 'Price', 'GROSS AMT'],
    'status': ['Status', 'Courier Status', 'order_status'],
    'city': ['ship-city', 'City', 'city'],
    'state': ['ship-state', 'State', 'state'],
    'postal_code': ['ship-postal-code', 'PostalCode', 'postal_code', 'Zip'],
    'country': ['ship-country', 'Country', 'country'],
    'fulfilment': ['Fulfilment', 'fulfilled-by'],
    'b2b': ['B2B', 'is_b2b'],
}

def detect_column_mapping(df_columns):
    mapping = {}
    normalized_cols = {col.strip().lower(): col for col in df_columns}
    
    for standard_field, candidates in COLUMN_CANDIDATES.items():
        matched = None
        for cand in candidates:
            cand_norm = cand.strip().lower()
            if cand_norm in normalized_cols:
                matched = normalized_cols[cand_norm]
                break
        if not matched:
            # Substring match
            for cand in candidates:
                cand_norm = cand.strip().lower()
                for c_norm, original_col in normalized_cols.items():
                    if cand_norm in c_norm:
                        matched = original_col
                        break
                if matched:
                    break
        mapping[standard_field] = matched
    return mapping


def analyze_dataset_file(filepath):
    """
    Validates file, detects columns, missing values, duplicates, and returns summary.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(filepath, nrows=500, low_memory=False, encoding='utf-8', on_bad_lines='skip')
        # Fast buffer-based row counting
        try:
            with open(filepath, 'rb') as f:
                total_rows = 0
                buf_size = 1024 * 1024
                buf = f.read(buf_size)
                while buf:
                    total_rows += buf.count(b'\n')
                    buf = f.read(buf_size)
                total_rows = max(total_rows - 1, len(df))
        except Exception:
            total_rows = len(df)
    elif ext in ['.xlsx', '.xls']:
        df = pd.read_excel(filepath, nrows=500)
        total_rows = len(df)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Please upload CSV or Excel file.")

    detected_mapping = detect_column_mapping(df.columns.tolist())
    
    # Calculate missing value stats on the preview sample
    missing_summary = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            missing_summary[col] = {
                'count': null_count,
                'pct': round((null_count / len(df)) * 100, 1)
            }

    duplicate_rows = int(df.duplicated().sum())

    preview_rows = df.head(10).replace({np.nan: None}).to_dict(orient='records')

    return {
        'total_rows': max(total_rows, len(df)),
        'total_columns': len(df.columns),
        'columns': df.columns.tolist(),
        'detected_mapping': detected_mapping,
        'missing_summary': missing_summary,
        'duplicate_sample_count': duplicate_rows,
        'preview_rows': preview_rows,
    }


def parse_date_safely(val):
    if pd.isna(val) or val is None or str(val).strip() == '':
        return timezone.now().date()
    val_str = str(val).strip()
    # Try multiple common formats
    for fmt in ('%Y-%m-%d', '%m-%d-%y', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%b-%y'):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            pass
    try:
        dt = pd.to_datetime(val_str)
        return dt.date()
    except Exception:
        return timezone.now().date()


def parse_decimal_safely(val, default=0.00):
    if pd.isna(val) or val is None:
        return Decimal(str(default))
    try:
        val_str = str(val).replace(',', '').replace('$', '').replace('₹', '').strip()
        num = float(val_str)
        if np.isnan(num) or np.isinf(num):
            return Decimal(str(default))
        return Decimal(f"{abs(num):.2f}")
    except Exception:
        return Decimal(str(default))


def parse_int_safely(val, default=1):
    if pd.isna(val) or val is None:
        return default
    try:
        num = int(float(str(val).replace(',', '').strip()))
        return max(1, abs(num))
    except Exception:
        return default


def process_and_import_dataset(upload_record, custom_mapping=None, max_rows=None, user=None):
    """
    Executes data validation, cleaning, transformation and atomic import into database.
    """
    upload_record.status = 'Processing'
    upload_record.save(update_fields=['status'])

    filepath = upload_record.file.path
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.csv':
        if max_rows and max_rows < 15000:
            # Read a broader block and sample evenly to capture full temporal distribution
            sample_pool = pd.read_csv(filepath, nrows=max_rows * 12, low_memory=False, encoding='utf-8', on_bad_lines='skip')
            step = max(1, len(sample_pool) // max_rows)
            df = sample_pool.iloc[::step].head(max_rows).copy()
        else:
            df = pd.read_csv(filepath, nrows=max_rows, low_memory=False, encoding='utf-8', on_bad_lines='skip')
    else:
        df = pd.read_excel(filepath, nrows=max_rows)

    mapping = custom_mapping or upload_record.column_mapping or detect_column_mapping(df.columns.tolist())
    upload_record.column_mapping = mapping

    col_order_id = mapping.get('order_id')
    col_date = mapping.get('order_date')
    col_cust = mapping.get('customer_id')
    col_sku = mapping.get('sku')
    col_name = mapping.get('product_name')
    col_cat = mapping.get('category')
    col_qty = mapping.get('quantity')
    col_price = mapping.get('unit_price')
    col_status = mapping.get('status')
    col_city = mapping.get('city')
    col_state = mapping.get('state')
    col_country = mapping.get('country')
    col_postal = mapping.get('postal_code')
    col_fulfilment = mapping.get('fulfilment')
    col_b2b = mapping.get('b2b')

    # Remove strict duplicates
    initial_count = len(df)
    df = df.drop_duplicates()
    duplicates_removed = initial_count - len(df)

    imported_orders = 0
    imported_products = 0
    imported_customers = 0
    errors = []

    # Cache existing categories and products in memory for speed
    categories_cache = {c.name.lower(): c for c in Category.objects.all()}
    products_cache = {p.sku: p for p in Product.objects.all()}
    customers_cache = {c.customer_id: c for c in Customer.objects.all()}
    orders_cache = set(Order.objects.values_list('order_id', flat=True))

    new_categories = []
    new_products = []
    new_customers = []
    new_orders = []
    new_order_items = []

    with transaction.atomic():
        for idx, row in df.iterrows():
            try:
                # 1. Order ID resolution
                raw_order_id = str(row[col_order_id]).strip() if col_order_id and pd.notna(row[col_order_id]) else f"ORD-{idx+10000}"
                if not raw_order_id or raw_order_id == 'nan':
                    raw_order_id = f"ORD-{idx+10000}"

                # 2. Customer resolution (with intelligent synthesis for seller datasets)
                if col_cust and pd.notna(row[col_cust]) and str(row[col_cust]).strip() not in ('', 'nan'):
                    cust_id = str(row[col_cust]).strip()
                    cust_name = cust_id
                else:
                    # Synthesize customer based on postal code + city to retain realistic cohort behavior
                    postal = str(row[col_postal]).strip().replace('.0', '') if col_postal and pd.notna(row[col_postal]) else 'UNKNOWN'
                    city = str(row[col_city]).strip().upper() if col_city and pd.notna(row[col_city]) else 'LOC'
                    cust_id = f"CUST-{city[:6]}-{postal}"
                    cust_name = f"Customer ({city})"

                if cust_id not in customers_cache:
                    cust_city = str(row[col_city]).strip() if col_city and pd.notna(row[col_city]) else ''
                    cust_state = str(row[col_state]).strip() if col_state and pd.notna(row[col_state]) else ''
                    cust_country = str(row[col_country]).strip() if col_country and pd.notna(row[col_country]) else 'IN'
                    cust_postal = str(row[col_postal]).strip().replace('.0', '') if col_postal and pd.notna(row[col_postal]) else ''
                    
                    customer = Customer(
                        customer_id=cust_id,
                        name=cust_name,
                        city=cust_city,
                        state=cust_state,
                        country=cust_country[:100],
                        postal_code=cust_postal[:50]
                    )
                    customers_cache[cust_id] = customer
                    new_customers.append(customer)
                else:
                    customer = customers_cache[cust_id]

                # 3. Category & Product resolution
                cat_name = str(row[col_cat]).strip().title() if col_cat and pd.notna(row[col_cat]) else 'General'
                if not cat_name or cat_name == 'Nan':
                    cat_name = 'General'
                
                cat_key = cat_name.lower()
                if cat_key not in categories_cache:
                    cat = Category.objects.create(name=cat_name)
                    categories_cache[cat_key] = cat
                else:
                    cat = categories_cache[cat_key]

                sku = str(row[col_sku]).strip() if col_sku and pd.notna(row[col_sku]) else f"SKU-{cat_name[:3].upper()}-{idx}"
                if not sku or sku == 'nan':
                    sku = f"SKU-{cat_name[:3].upper()}-{idx}"

                prod_name = str(row[col_name]).strip() if col_name and pd.notna(row[col_name]) else sku
                if not prod_name or prod_name == 'nan':
                    prod_name = sku

                unit_price = parse_decimal_safely(row[col_price] if col_price else 100.0)
                qty = parse_int_safely(row[col_qty] if col_qty else 1)

                if sku not in products_cache:
                    product = Product(
                        sku=sku,
                        name=prod_name[:255],
                        category=cat,
                        unit_price=unit_price if unit_price > 0 else Decimal('199.00'),
                        cost_price=round(unit_price * Decimal('0.6'), 2),
                        stock_quantity=100
                    )
                    products_cache[sku] = product
                    new_products.append(product)
                else:
                    product = products_cache[sku]

                # 4. Order resolution
                order_date = parse_date_safely(row[col_date] if col_date else None)
                status_raw = str(row[col_status]).strip() if col_status and pd.notna(row[col_status]) else 'Shipped'
                if 'cancel' in status_raw.lower():
                    status = 'Cancelled'
                elif 'deliver' in status_raw.lower():
                    status = 'Delivered'
                elif 'return' in status_raw.lower():
                    status = 'Returned'
                elif 'pend' in status_raw.lower():
                    status = 'Pending'
                else:
                    status = 'Shipped'

                line_amount = unit_price if unit_price > 0 else (Decimal('199.00') * Decimal(str(qty)))

                if raw_order_id not in orders_cache:
                    order = Order(
                        order_id=raw_order_id,
                        customer=customer,
                        order_date=order_date,
                        status=status,
                        fulfilment=str(row[col_fulfilment]).strip()[:50] if col_fulfilment and pd.notna(row[col_fulfilment]) else 'Merchant',
                        total_amount=line_amount,
                        total_quantity=qty,
                        shipping_city=str(row[col_city]).strip()[:100] if col_city and pd.notna(row[col_city]) else '',
                        shipping_state=str(row[col_state]).strip()[:100] if col_state and pd.notna(row[col_state]) else '',
                        shipping_country=str(row[col_country]).strip()[:100] if col_country and pd.notna(row[col_country]) else 'IN',
                        shipping_postal_code=str(row[col_postal]).strip().replace('.0', '')[:50] if col_postal and pd.notna(row[col_postal]) else '',
                        is_b2b=bool(row[col_b2b]) if col_b2b and pd.notna(row[col_b2b]) else False,
                    )
                    orders_cache.add(raw_order_id)
                    new_orders.append(order)
                
                # Order item
                order_item = OrderItem(
                    order=order,
                    product=product,
                    sku=sku,
                    product_name=prod_name[:255],
                    quantity=qty,
                    unit_price=unit_price,
                    total_amount=line_amount
                )
                new_order_items.append(order_item)

            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                if len(errors) > 50:
                    break

        # Bulk create entities
        if new_customers:
            Customer.objects.bulk_create(new_customers, ignore_conflicts=True)
            # Re-fetch into cache
            customers_cache.update({c.customer_id: c for c in Customer.objects.filter(customer_id__in=[c.customer_id for c in new_customers])})

        if new_products:
            Product.objects.bulk_create(new_products, ignore_conflicts=True)
            products_cache.update({p.sku: p for p in Product.objects.filter(sku__in=[p.sku for p in new_products])})

        if new_orders:
            # Attach saved customers
            for o in new_orders:
                o.customer = customers_cache[o.customer.customer_id]
            Order.objects.bulk_create(new_orders, ignore_conflicts=True)
            # Map orders by order_id
            persisted_orders = {o.order_id: o for o in Order.objects.filter(order_id__in=[o.order_id for o in new_orders])}

            for item in new_order_items:
                item.order = persisted_orders.get(item.order.order_id, item.order)
                item.product = products_cache.get(item.sku, item.product)
            OrderItem.objects.bulk_create(new_order_items, ignore_conflicts=True)

    # Recalculate RFM for customers
    from customers.services import calculate_rfm_metrics
    calculate_rfm_metrics()

    upload_record.status = 'Imported'
    upload_record.total_rows = initial_count
    upload_record.valid_rows = len(new_orders)
    upload_record.invalid_rows = len(errors)
    upload_record.cleaning_summary = {
        'duplicates_removed': duplicates_removed,
        'new_customers_created': len(new_customers),
        'new_products_created': len(new_products),
        'orders_imported': len(new_orders),
        'order_items_imported': len(new_order_items),
        'errors_sample': errors[:10]
    }
    upload_record.processed_at = timezone.now()
    upload_record.save()

    if user:
        AuditLog.objects.create(
            user=user,
            action="Imported Dataset",
            target_model="DatasetUpload",
            target_id=str(upload_record.id),
            details=f"Imported {len(new_orders)} orders and {len(new_customers)} customers from {upload_record.name}."
        )
        SystemNotification.objects.create(
            user=user,
            title="Dataset Ingestion Complete",
            message=f"Successfully imported {len(new_orders)} orders from {upload_record.name}.",
            level="success",
            link="/dashboard/"
        )

    return upload_record
