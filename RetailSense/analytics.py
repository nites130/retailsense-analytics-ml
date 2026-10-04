"""Data validation, sales analytics, and deterministic demonstration data."""
import numpy as np
import pandas as pd

COLUMNS = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']


def demo_data():
    rng = np.random.default_rng(42)
    products = [('P01', 'Ceramic mug', 12.5), ('P02', 'Desk organiser', 24.0), ('P03', 'Cotton tote', 9.5), ('P04', 'Notebook set', 16.0), ('P05', 'Scented candle', 18.0), ('P06', 'Table lamp', 45.0), ('P07', 'Travel bottle', 22.0), ('P08', 'Plant pot', 14.0)]
    rows, invoice = [], 100000
    start = pd.Timestamp('2025-01-01')
    for customer in range(10001, 10501):
        country = rng.choice(['United Kingdom', 'Germany', 'France', 'Netherlands', 'Spain'], p=[.55,.15,.13,.10,.07])
        rate = rng.choice([.009, .025, .07, .13])
        joined = int(rng.integers(0, 140))
        for day in range(joined, 365):
            if rng.random() > rate * (1.25 if day > 300 else 1):
                continue
            invoice += 1
            for product in rng.choice(len(products), size=int(rng.integers(1, 4)), replace=False):
                sku, desc, price = products[product]
                rows.append([str(invoice), sku, desc, int(rng.integers(1,5)), str(start + pd.Timedelta(days=day)), price, str(customer), country])
    return pd.DataFrame(rows, columns=COLUMNS)


def clean_data(raw):
    raw = raw.copy()
    raw.columns = raw.columns.str.strip()
    if raw.columns.duplicated().any():
        raise ValueError('Duplicate column names are not supported.')
    missing = set(COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    df = raw[COLUMNS].copy()
    original = len(df)
    if original == 0:
        raise ValueError('The file contains no rows.')
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce', format='mixed')
    try:
        df['InvoiceDate'] = df['InvoiceDate'].dt.tz_localize(None)
    except (AttributeError, TypeError):
        raise ValueError('Use timezone-free dates in ISO format: YYYY-MM-DD HH:MM:SS.')
    for col in ['Quantity', 'UnitPrice']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    for col in ['InvoiceNo', 'StockCode', 'Description', 'CustomerID', 'Country']:
        df[col] = df[col].fillna('').astype(str).str.strip()
    df['CustomerID'] = df['CustomerID'].str.replace(r'\.0$', '', regex=True)
    valid = df['InvoiceDate'].notna() & np.isfinite(df['Quantity']) & np.isfinite(df['UnitPrice'])
    valid &= (df['Quantity'] > 0) & (df['UnitPrice'] > 0)
    valid &= ~df['InvoiceNo'].str.upper().str.startswith('C')
    valid &= df['InvoiceNo'].ne('') & df['StockCode'].ne('') & df['CustomerID'].ne('')
    invalid = int((~valid).sum())
    df = df[valid].copy()
    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates()
    df['Country'] = df['Country'].replace('', 'Unknown')
    df['Description'] = df['Description'].replace('', 'Unnamed product')
    df['Revenue'] = df.Quantity * df.UnitPrice
    if not np.isfinite(df.Revenue).all():
        raise ValueError('Quantity × UnitPrice exceeds the supported numeric range.')
    if df.empty:
        raise ValueError('No valid positive purchase rows with customer IDs remain.')
    df = df.sort_values('InvoiceDate').reset_index(drop=True)
    return df, dict(input_rows=original, kept_rows=len(df), excluded_rows=invalid, duplicate_rows=duplicates)


def customer_features(df, cutoff):
    # Only history BEFORE cutoff is visible to the model.
    hist = df[df.InvoiceDate < cutoff]
    grouped = hist.groupby('CustomerID')
    out = grouped.agg(last_purchase=('InvoiceDate','max'), frequency=('InvoiceNo','nunique'), monetary=('Revenue','sum'), first_purchase=('InvoiceDate','min'))
    out['recency'] = (cutoff - out.last_purchase).dt.total_seconds() / 86400
    out['tenure'] = (cutoff - out.first_purchase).dt.total_seconds() / 86400
    out['average_order'] = out.monetary / out.frequency
    recent = hist[hist.InvoiceDate >= cutoff - pd.Timedelta(days=30)].groupby('CustomerID').InvoiceNo.nunique()
    out['orders_30d'] = recent.reindex(out.index, fill_value=0)
    return out[['recency','frequency','monetary','tenure','average_order','orders_30d']]


def customers(df):
    cutoff = df.InvoiceDate.max().normalize() + pd.Timedelta(days=1)
    out = customer_features(df, cutoff)
    # Interpretable rule-based RFM segments, not a fitted clustering algorithm.
    out['segment'] = np.select([(out.recency <= 30) & (out.frequency >= 5), out.recency > 90, out.frequency == 1], ['Loyal', 'Inactive', 'New / one-time'], default='Developing')
    out['CustomerID'] = out.index
    return out.reset_index(drop=True)


def summary(df):
    cust = customers(df)
    orders = int(df.InvoiceNo.nunique())
    monthly = df.groupby(df.InvoiceDate.dt.strftime('%Y-%m')).Revenue.sum()
    top = df.groupby('Description').Revenue.sum().nlargest(8)
    countries = df.groupby('Country').Revenue.sum().sort_values(ascending=False)
    return dict(revenue=round(float(df.Revenue.sum()),2), orders=orders, customers=len(cust), average_order=round(float(df.Revenue.sum()/orders),2), repeat_rate=round(float((cust.frequency > 1).mean()*100),1), start=str(df.InvoiceDate.min().date()), end=str(df.InvoiceDate.max().date()), monthly=[dict(label=k,value=round(float(v),2)) for k,v in monthly.items()], products=[dict(label=k,value=round(float(v),2)) for k,v in top.items()], countries=[dict(label=k,value=round(float(v),2)) for k,v in countries.items()], segments=[dict(label=k,value=int(v)) for k,v in cust.segment.value_counts().items()])
