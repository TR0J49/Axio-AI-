"""
Data processing utilities for VizIQ
"""
import json


def parse_csv_data(file_path):
    """Parse CSV file and return data"""
    import csv
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        for row in reader:
            data.append(row)
    return data, columns


def parse_excel_data(file_path):
    """Parse Excel file and return data"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active

        data = []
        columns = []

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                columns = [str(cell) if cell else f'Column_{j}' for j, cell in enumerate(row)]
            else:
                row_data = {}
                for j, cell in enumerate(row):
                    col_name = columns[j] if j < len(columns) else f'Column_{j}'
                    row_data[col_name] = cell
                data.append(row_data)

        return data, columns
    except ImportError:
        return None, "Error: openpyxl library not installed"


def parse_json_data(file_path):
    """Parse JSON file and return data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Handle different JSON structures
    if isinstance(raw_data, list):
        data = raw_data
        if data and isinstance(data[0], dict):
            columns = list(data[0].keys())
        else:
            columns = ['value']
            data = [{'value': item} for item in raw_data]
    elif isinstance(raw_data, dict):
        # Check if it's a records-style dict
        if all(isinstance(v, list) for v in raw_data.values()):
            columns = list(raw_data.keys())
            max_len = max(len(v) for v in raw_data.values())
            data = []
            for i in range(max_len):
                row = {}
                for col in columns:
                    row[col] = raw_data[col][i] if i < len(raw_data[col]) else None
                data.append(row)
        else:
            data = [raw_data]
            columns = list(raw_data.keys())
    else:
        data = [{'value': raw_data}]
        columns = ['value']

    return data, columns


def detect_column_types(data, columns):
    """Detect data types for each column"""
    dtypes = {}

    for col in columns:
        values = [row.get(col) for row in data[:100] if row.get(col) is not None]

        if not values:
            dtypes[col] = 'unknown'
            continue

        # Try to detect type
        numeric_count = 0
        date_count = 0

        for val in values:
            if isinstance(val, (int, float)):
                numeric_count += 1
            elif isinstance(val, str):
                try:
                    float(val.replace(',', '').replace('$', '').replace('%', ''))
                    numeric_count += 1
                except:
                    # Check for date patterns
                    if any(sep in val for sep in ['-', '/', '.']):
                        date_count += 1

        if numeric_count > len(values) * 0.7:
            dtypes[col] = 'numeric'
        elif date_count > len(values) * 0.5:
            dtypes[col] = 'date'
        else:
            dtypes[col] = 'categorical'

    return dtypes


def clean_numeric_value(val):
    """Clean and convert value to numeric"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            cleaned = val.replace(',', '').replace('$', '').replace('%', '').strip()
            return float(cleaned)
        except:
            return None
    return None


def calculate_statistics(data, columns, dtypes):
    """Calculate statistics for numeric columns"""
    stats = {}

    for col in columns:
        if dtypes.get(col) == 'numeric':
            values = [clean_numeric_value(row.get(col)) for row in data]
            values = [v for v in values if v is not None]

            if values:
                stats[col] = {
                    'min': min(values),
                    'max': max(values),
                    'sum': sum(values),
                    'mean': sum(values) / len(values),
                    'count': len(values)
                }

                # Calculate median
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                if n % 2 == 0:
                    stats[col]['median'] = (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
                else:
                    stats[col]['median'] = sorted_vals[n//2]

    return stats
