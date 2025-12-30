"""
VizIQ Service - Data Visualization and Analytics
"""
from app.utils.data_processing import (
    parse_csv_data, parse_excel_data, parse_json_data,
    detect_column_types, clean_numeric_value, calculate_statistics
)


def generate_kpis(data, columns, dtypes, stats, filename):
    """Generate KPIs from data"""
    kpis = []

    # Total rows KPI
    kpis.append({
        'label': 'Total Records',
        'value': len(data),
        'icon': 'database',
        'description': f'Total rows in {filename}'
    })

    # Find numeric columns and create KPIs
    for col in columns[:6]:  # Limit to first 6 columns
        if col in stats:
            s = stats[col]
            kpis.append({
                'label': f'Total {col}',
                'value': round(s['sum'], 2),
                'icon': 'trending-up',
                'description': f"Sum of all {col} values",
                'change': None
            })
            kpis.append({
                'label': f'Avg {col}',
                'value': round(s['mean'], 2),
                'icon': 'bar-chart',
                'description': f"Average {col}",
                'change': None
            })
            break  # Just one numeric column for now

    # Count unique values for categorical columns
    for col in columns:
        if dtypes.get(col) == 'categorical':
            unique_vals = set(row.get(col) for row in data if row.get(col))
            kpis.append({
                'label': f'Unique {col}',
                'value': len(unique_vals),
                'icon': 'layers',
                'description': f'Distinct values in {col}'
            })
            break  # Just one categorical column

    return kpis[:6]  # Return max 6 KPIs


def generate_chart_configs(data, columns, dtypes, stats):
    """Generate chart configurations based on data - 3 charts in first row, 1 trend chart in second row"""
    charts = []

    numeric_cols = [c for c in columns if dtypes.get(c) == 'numeric']
    categorical_cols = [c for c in columns if dtypes.get(c) == 'categorical']

    # ============ ROW 1: Column Chart, Distribution Chart, Comparison Chart ============

    # 1. COLUMN CHART - Bar chart for categorical data with numeric values
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]

        # Aggregate data by category
        aggregated = {}
        for row in data:
            cat_val = str(row.get(cat_col, 'Unknown'))
            num_val = clean_numeric_value(row.get(num_col))
            if num_val is not None:
                if cat_val not in aggregated:
                    aggregated[cat_val] = 0
                aggregated[cat_val] += num_val

        # Sort and limit to top 8
        sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:8]

        if sorted_items:
            charts.append({
                'id': 'column-chart',
                'type': 'bar',
                'title': f'Column: {num_col} by {cat_col}',
                'labels': [item[0][:12] for item in sorted_items],  # Truncate labels
                'data': [round(item[1], 2) for item in sorted_items],
                'insight': f"Top: {sorted_items[0][0]} ({round(sorted_items[0][1], 2)})"
            })

    # 2. DISTRIBUTION CHART - Doughnut/Pie chart for categorical distribution
    if categorical_cols:
        cat_col = categorical_cols[0] if len(categorical_cols) == 1 else categorical_cols[1] if len(categorical_cols) > 1 else categorical_cols[0]
        counts = {}
        for row in data:
            val = str(row.get(cat_col, 'Unknown'))
            counts[val] = counts.get(val, 0) + 1

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:6]

        if sorted_counts:
            total = sum(item[1] for item in sorted_counts)
            charts.append({
                'id': 'distribution-chart',
                'type': 'doughnut',
                'title': f'Distribution: {cat_col}',
                'labels': [item[0][:15] for item in sorted_counts],
                'data': [item[1] for item in sorted_counts],
                'insight': f"Largest: {sorted_counts[0][0]} ({round(sorted_counts[0][1]/total*100, 1)}%)"
            })

    # 3. COMPARISON CHART - Compare multiple numeric columns
    if numeric_cols and len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[0], numeric_cols[1]

        if col1 in stats and col2 in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'title': f'Comparison: Metrics',
                'labels': ['Average', 'Maximum', 'Minimum'],
                'datasets': [
                    {
                        'label': col1[:15],
                        'data': [round(stats[col1]['mean'], 2), round(stats[col1]['max'], 2), round(stats[col1]['min'], 2)]
                    },
                    {
                        'label': col2[:15],
                        'data': [round(stats[col2]['mean'], 2), round(stats[col2]['max'], 2), round(stats[col2]['min'], 2)]
                    }
                ],
                'insight': f"Comparing {col1} vs {col2} metrics"
            })
    elif numeric_cols and len(numeric_cols) == 1:
        # Single numeric column - show stats as bar chart
        col = numeric_cols[0]
        if col in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'title': f'Statistics: {col}',
                'labels': ['Average', 'Maximum', 'Minimum'],
                'data': [round(stats[col]['mean'], 2), round(stats[col]['max'], 2), round(stats[col]['min'], 2)],
                'insight': f"Range: {round(stats[col]['min'], 2)} to {round(stats[col]['max'], 2)}"
            })

    # ============ ROW 2: Trend Chart (Full Width) ============

    # 4. TREND CHART - Line chart for time series or sequential data
    if numeric_cols and len(data) > 5:
        num_col = numeric_cols[0]
        values = []
        labels = []

        # Check for date column
        date_cols = [c for c in columns if dtypes.get(c) == 'date']

        for i, row in enumerate(data[:30]):  # Limit to 30 points for clarity
            val = clean_numeric_value(row.get(num_col))
            if val is not None:
                values.append(val)
                if date_cols:
                    labels.append(str(row.get(date_cols[0], i+1))[:10])
                else:
                    labels.append(f'P{i+1}')

        if values and len(values) >= 3:
            # Calculate trend direction
            avg_first_half = sum(values[:len(values)//2]) / (len(values)//2) if len(values) >= 2 else 0
            avg_second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if len(values) >= 2 else 0
            trend = "Upward" if avg_second_half > avg_first_half else "Downward" if avg_second_half < avg_first_half else "Stable"

            charts.append({
                'id': 'trend-chart',
                'type': 'line',
                'title': f'Trend Analysis: {num_col}',
                'labels': labels,
                'data': [round(v, 2) for v in values],
                'insight': f"{trend} trend detected. Range: {round(min(values), 2)} - {round(max(values), 2)}"
            })

    # Ensure we have at least some charts
    if len(charts) < 3 and numeric_cols:
        # Add a simple bar chart if we don't have enough
        col = numeric_cols[0]
        if col in stats and 'column-chart' not in [c['id'] for c in charts]:
            values = []
            for row in data[:10]:
                val = clean_numeric_value(row.get(col))
                if val is not None:
                    values.append(val)
            if values:
                charts.insert(0, {
                    'id': 'column-chart',
                    'type': 'bar',
                    'title': f'Values: {col}',
                    'labels': [f'Row {i+1}' for i in range(len(values))],
                    'data': [round(v, 2) for v in values],
                    'insight': f"Showing first {len(values)} values"
                })

    return charts


def generate_insights(data, columns, dtypes, stats, filename):
    """Generate AI insights from data"""
    insights = []

    # Data quality insight
    null_counts = {}
    for col in columns:
        null_count = sum(1 for row in data if row.get(col) is None or row.get(col) == '')
        if null_count > 0:
            null_counts[col] = null_count

    if null_counts:
        most_nulls = max(null_counts.items(), key=lambda x: x[1])
        insights.append({
            'icon': '⚠️',
            'type': 'warning',
            'title': 'Data Quality Alert',
            'description': f"'{most_nulls[0]}' has {most_nulls[1]} missing values ({round(most_nulls[1]/len(data)*100, 1)}% of data)"
        })

    # Numeric insights
    for col in columns:
        if col in stats:
            s = stats[col]

            # High variance insight
            if s['max'] > s['mean'] * 5:
                insights.append({
                    'icon': '📈',
                    'type': 'trend-up',
                    'title': f'High Variance in {col}',
                    'description': f"Maximum value ({round(s['max'], 2)}) is significantly higher than average ({round(s['mean'], 2)})"
                })

            # Summary insight
            insights.append({
                'icon': '📊',
                'type': 'info',
                'title': f'{col} Summary',
                'description': f"Total: {round(s['sum'], 2)}, Average: {round(s['mean'], 2)}, Median: {round(s['median'], 2)}"
            })
            break

    # Categorical insights
    for col in columns:
        if dtypes.get(col) == 'categorical':
            counts = {}
            for row in data:
                val = row.get(col)
                if val:
                    counts[str(val)] = counts.get(str(val), 0) + 1

            if counts:
                top_item = max(counts.items(), key=lambda x: x[1])
                insights.append({
                    'icon': '🏆',
                    'type': 'trend-up',
                    'title': f'Top {col}',
                    'description': f"'{top_item[0]}' is most frequent with {top_item[1]} occurrences ({round(top_item[1]/len(data)*100, 1)}%)"
                })
            break

    # Row count insight
    insights.append({
        'icon': '📁',
        'type': 'info',
        'title': 'Dataset Size',
        'description': f"Your dataset contains {len(data)} records across {len(columns)} columns"
    })

    return insights[:6]


def generate_dashboard_name(filename, columns):
    """Generate a smart dashboard name"""
    base_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()

    # Try to identify domain from column names
    col_text = ' '.join(columns).lower()

    if any(word in col_text for word in ['sale', 'revenue', 'price', 'amount', 'cost']):
        return f"{base_name} - Sales Analytics"
    elif any(word in col_text for word in ['employee', 'salary', 'department', 'hr']):
        return f"{base_name} - HR Analytics"
    elif any(word in col_text for word in ['customer', 'user', 'client']):
        return f"{base_name} - Customer Analytics"
    elif any(word in col_text for word in ['product', 'inventory', 'stock']):
        return f"{base_name} - Product Analytics"
    elif any(word in col_text for word in ['date', 'time', 'month', 'year']):
        return f"{base_name} - Time Series Analysis"
    else:
        return f"{base_name} Dashboard"


def process_data_file(file_path, file_extension):
    """Process data file and return parsed data with analysis"""
    # Parse file based on type
    if file_extension == 'csv':
        data, columns = parse_csv_data(file_path)
    elif file_extension in ['xlsx', 'xls']:
        data, columns = parse_excel_data(file_path)
        if data is None:
            return None, None, None, columns  # columns contains error message
    elif file_extension == 'json':
        data, columns = parse_json_data(file_path)
    else:
        return None, None, None, 'Unsupported file type'

    if not data:
        return None, None, None, 'No data found in file'

    # Detect column types
    dtypes = detect_column_types(data, columns)

    # Calculate statistics
    stats = calculate_statistics(data, columns, dtypes)

    return data, columns, dtypes, stats


def generate_full_analysis(data, columns, dtypes, stats, filename):
    """Generate complete dashboard analysis"""
    # Generate dashboard name
    dashboard_name = generate_dashboard_name(filename, columns)

    # Generate KPIs
    kpis = generate_kpis(data, columns, dtypes, stats, filename)

    # Generate chart configurations
    charts = generate_chart_configs(data, columns, dtypes, stats)

    # Generate insights
    insights = generate_insights(data, columns, dtypes, stats, filename)

    return {
        'dashboard_name': dashboard_name,
        'kpis': kpis,
        'charts': charts,
        'insights': insights
    }
