"""
VizIQ Service - Data Visualization and Analytics
"""
from app.utils.data_processing import (
    parse_csv_data, parse_excel_data, parse_json_data,
    detect_column_types, clean_numeric_value, calculate_statistics
)


def _trend_direction(data, col):
    """Compare first-half vs second-half average to compute trend direction and %."""
    half = max(1, len(data) // 2)
    first_vals = [v for v in (clean_numeric_value(r.get(col)) for r in data[:half]) if v is not None]
    second_vals = [v for v in (clean_numeric_value(r.get(col)) for r in data[half:]) if v is not None]
    if not first_vals or not second_vals:
        return 'neutral', None
    first_avg = sum(first_vals) / len(first_vals)
    second_avg = sum(second_vals) / len(second_vals)
    if first_avg == 0:
        return ('positive' if second_avg > 0 else 'neutral'), None
    pct = round((second_avg - first_avg) / abs(first_avg) * 100, 1)
    trend = 'positive' if pct > 1 else 'negative' if pct < -1 else 'neutral'
    return trend, pct


def generate_kpis(data, columns, dtypes, stats, filename):
    """Generate rich KPIs with trend indicators across all numeric columns."""
    kpis = []
    numeric_cols = [c for c in columns if c in stats]
    categorical_cols = [c for c in columns if dtypes.get(c) == 'categorical']

    total_cells = len(data) * len(columns)
    null_cells = sum(1 for r in data for c in columns if r.get(c) in (None, ''))
    completeness = round((1 - null_cells / max(1, total_cells)) * 100, 1)

    kpis.append({
        'label': 'Total Records',
        'value': len(data),
        'icon': 'database',
        'description': f'{len(numeric_cols)} numeric cols · {completeness}% complete',
        'trend': 'neutral',
        'trend_pct': None
    })

    for col in numeric_cols[:3]:
        s = stats[col]
        trend, trend_pct = _trend_direction(data, col)

        kpis.append({
            'label': f'Total {col}',
            'value': round(s['sum'], 2),
            'icon': 'trending-up',
            'description': f'Max: {round(s["max"], 2):,}',
            'trend': trend,
            'trend_pct': trend_pct
        })

        kpis.append({
            'label': f'Avg {col}',
            'value': round(s['mean'], 2),
            'icon': 'bar-chart',
            'description': f'Median: {round(s["median"], 2):,}',
            'trend': trend,
            'trend_pct': trend_pct
        })

        if len(kpis) >= 7:
            break

    for col in categorical_cols[:1]:
        unique_vals = len(set(str(r.get(col)) for r in data if r.get(col)))
        kpis.append({
            'label': f'Unique {col}',
            'value': unique_vals,
            'icon': 'layers',
            'description': f'Distinct {col} values',
            'trend': 'neutral',
            'trend_pct': None
        })

    return kpis[:8]


def generate_chart_configs(data, columns, dtypes, stats):
    """Generate chart configurations with type-toggle options and richer data coverage."""
    charts = []

    numeric_cols = [c for c in columns if dtypes.get(c) == 'numeric']
    categorical_cols = [c for c in columns if dtypes.get(c) == 'categorical']

    # 1. Bar chart — top categories by numeric value
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        aggregated = {}
        for row in data:
            cat_val = str(row.get(cat_col, 'Unknown'))
            num_val = clean_numeric_value(row.get(num_col))
            if num_val is not None:
                aggregated[cat_val] = aggregated.get(cat_val, 0) + num_val

        sorted_items = sorted(aggregated.items(), key=lambda x: x[1], reverse=True)[:12]

        if sorted_items:
            charts.append({
                'id': 'column-chart',
                'type': 'bar',
                'chartTypes': ['bar', 'line', 'doughnut'],
                'title': f'{num_col} by {cat_col}',
                'labels': [item[0][:15] for item in sorted_items],
                'data': [round(item[1], 2) for item in sorted_items],
                'insight': f"Top: {sorted_items[0][0]} ({round(sorted_items[0][1], 2):,})"
            })

    # 2. Doughnut — category distribution
    if categorical_cols:
        cat_col = categorical_cols[min(1, len(categorical_cols) - 1)]
        counts = {}
        for row in data:
            val = str(row.get(cat_col, 'Unknown'))
            counts[val] = counts.get(val, 0) + 1
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]

        if sorted_counts:
            total = sum(item[1] for item in sorted_counts)
            charts.append({
                'id': 'distribution-chart',
                'type': 'doughnut',
                'chartTypes': ['doughnut', 'bar'],
                'title': f'Distribution: {cat_col}',
                'labels': [item[0][:18] for item in sorted_counts],
                'data': [item[1] for item in sorted_counts],
                'insight': f"Top: {sorted_counts[0][0]} — {round(sorted_counts[0][1]/total*100, 1)}% of total"
            })

    # 3. Multi-series bar — compare two numeric columns across stats
    if len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[0], numeric_cols[1]
        if col1 in stats and col2 in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'chartTypes': ['bar', 'line'],
                'title': f'{col1} vs {col2}',
                'labels': ['Average', 'Maximum', 'Minimum', 'Median'],
                'datasets': [
                    {
                        'label': col1[:20],
                        'data': [round(stats[col1]['mean'], 2), round(stats[col1]['max'], 2),
                                 round(stats[col1]['min'], 2), round(stats[col1]['median'], 2)]
                    },
                    {
                        'label': col2[:20],
                        'data': [round(stats[col2]['mean'], 2), round(stats[col2]['max'], 2),
                                 round(stats[col2]['min'], 2), round(stats[col2]['median'], 2)]
                    }
                ],
                'insight': f"Comparing {col1} and {col2} across key statistics"
            })
    elif len(numeric_cols) == 1:
        col = numeric_cols[0]
        if col in stats:
            charts.append({
                'id': 'comparison-chart',
                'type': 'bar',
                'chartTypes': ['bar', 'line'],
                'title': f'Statistics: {col}',
                'labels': ['Average', 'Maximum', 'Minimum', 'Median'],
                'data': [round(stats[col]['mean'], 2), round(stats[col]['max'], 2),
                         round(stats[col]['min'], 2), round(stats[col]['median'], 2)],
                'insight': f"Range: {round(stats[col]['min'], 2):,} to {round(stats[col]['max'], 2):,}"
            })

    # 4. Scatter plot — correlation between two numeric columns
    if len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[0], numeric_cols[1]
        scatter_pts = []
        for row in data[:300]:
            x = clean_numeric_value(row.get(col1))
            y = clean_numeric_value(row.get(col2))
            if x is not None and y is not None:
                scatter_pts.append({'x': round(x, 2), 'y': round(y, 2)})
        if len(scatter_pts) >= 5:
            charts.append({
                'id': 'scatter-chart',
                'type': 'scatter',
                'chartTypes': ['scatter'],
                'title': f'Correlation: {col1} vs {col2}',
                'scatterData': scatter_pts,
                'insight': f"{len(scatter_pts)} data points — {col1} (x-axis) vs {col2} (y-axis)"
            })

    # 5. Trend line — full width, up to 100 data points
    if numeric_cols and len(data) > 5:
        num_col = numeric_cols[0]
        date_cols = [c for c in columns if dtypes.get(c) == 'date']
        values, labels = [], []

        for i, row in enumerate(data[:100]):
            val = clean_numeric_value(row.get(num_col))
            if val is not None:
                values.append(round(val, 2))
                labels.append(str(row.get(date_cols[0], i + 1))[:10] if date_cols else f'#{i + 1}')

        if len(values) >= 3:
            half = len(values) // 2
            avg1 = sum(values[:half]) / half
            avg2 = sum(values[half:]) / (len(values) - half)
            trend_label = "Upward ↑" if avg2 > avg1 * 1.01 else "Downward ↓" if avg2 < avg1 * 0.99 else "Stable →"

            charts.append({
                'id': 'trend-chart',
                'type': 'line',
                'chartTypes': ['line', 'bar'],
                'title': f'Trend: {num_col}',
                'labels': labels,
                'data': values,
                'insight': f"{trend_label}  ·  Min {min(values):,}  ·  Max {max(values):,}  ·  Range {round(max(values)-min(values),2):,}"
            })

    # Fallback: simple bar when no charts generated
    if not charts and numeric_cols:
        col = numeric_cols[0]
        values = [clean_numeric_value(r.get(col)) for r in data[:15]]
        values = [round(v, 2) for v in values if v is not None]
        if values:
            charts.append({
                'id': 'column-chart',
                'type': 'bar',
                'chartTypes': ['bar', 'line'],
                'title': f'Values: {col}',
                'labels': [f'#{i+1}' for i in range(len(values))],
                'data': values,
                'insight': f'First {len(values)} values of {col}'
            })

    return charts


def generate_insights(data, columns, dtypes, stats, filename):
    """Generate rich insights: data quality, growth, outliers, summaries, category leaders."""
    insights = []
    numeric_cols = [c for c in columns if c in stats]
    categorical_cols = [c for c in columns if dtypes.get(c) == 'categorical']

    # 1. Data completeness
    total_cells = len(data) * len(columns)
    null_cells = sum(1 for r in data for c in columns if r.get(c) in (None, ''))
    completeness = round((1 - null_cells / max(1, total_cells)) * 100, 1)

    if null_cells > 0:
        worst_col = max(
            ((c, sum(1 for r in data if r.get(c) in (None, ''))) for c in columns),
            key=lambda x: x[1]
        )
        insights.append({
            'icon': '⚠️', 'type': 'warning',
            'title': 'Data Quality',
            'description': f'{completeness}% complete. "{worst_col[0]}" has {worst_col[1]} missing values ({round(worst_col[1]/len(data)*100,1)}%)'
        })
    else:
        insights.append({
            'icon': '✅', 'type': 'trend-up',
            'title': 'Clean Dataset',
            'description': f'100% data completeness — no missing values across {len(data):,} records and {len(columns)} columns'
        })

    # 2. Growth rate: first 10% vs last 10% of rows
    for col in numeric_cols[:2]:
        window = max(1, len(data) // 10)
        first_vals = [v for v in (clean_numeric_value(r.get(col)) for r in data[:window]) if v is not None]
        last_vals = [v for v in (clean_numeric_value(r.get(col)) for r in data[-window:]) if v is not None]
        if first_vals and last_vals:
            first_avg = sum(first_vals) / len(first_vals)
            last_avg = sum(last_vals) / len(last_vals)
            if first_avg != 0:
                growth = round((last_avg - first_avg) / abs(first_avg) * 100, 1)
                direction = "grew" if growth > 0 else "declined"
                insights.append({
                    'icon': '📈' if growth > 0 else '📉',
                    'type': 'trend-up' if growth > 0 else 'warning',
                    'title': f'{col} Growth',
                    'description': f'{col} {direction} by {abs(growth)}% from the start to the end of the dataset'
                })

    # 3. Outlier detection (IQR method) for first numeric column
    for col in numeric_cols[:1]:
        values = sorted(v for v in (clean_numeric_value(r.get(col)) for r in data) if v is not None)
        if len(values) >= 8:
            q1 = values[len(values) // 4]
            q3 = values[3 * len(values) // 4]
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = [v for v in values if v < lower or v > upper]
            if outliers:
                insights.append({
                    'icon': '🎯', 'type': 'warning',
                    'title': f'Outliers in {col}',
                    'description': f'{len(outliers)} outlier(s) detected outside the expected range ({round(lower,1):,} – {round(upper,1):,})'
                })

    # 4. Summary for each numeric column (up to 3)
    for col in numeric_cols[:3]:
        s = stats[col]
        insights.append({
            'icon': '📊', 'type': 'info',
            'title': f'{col} Summary',
            'description': f'Sum: {round(s["sum"],2):,}  ·  Mean: {round(s["mean"],2):,}  ·  Median: {round(s["median"],2):,}  ·  Range: {round(s["min"],2):,} – {round(s["max"],2):,}'
        })

    # 5. Top and bottom category leaders
    for col in categorical_cols[:1]:
        counts = {}
        for row in data:
            val = row.get(col)
            if val:
                counts[str(val)] = counts.get(str(val), 0) + 1
        if counts:
            top = max(counts.items(), key=lambda x: x[1])
            bottom = min(counts.items(), key=lambda x: x[1])
            insights.append({
                'icon': '🏆', 'type': 'trend-up',
                'title': f'Top {col}',
                'description': f'"{top[0]}" leads with {top[1]:,} records ({round(top[1]/len(data)*100,1)}%). "{bottom[0]}" is lowest at {bottom[1]:,}.'
            })

    # 6. Dataset overview
    insights.append({
        'icon': '📁', 'type': 'info',
        'title': 'Dataset Overview',
        'description': f'{len(data):,} records  ·  {len(numeric_cols)} numeric columns  ·  {len(categorical_cols)} categorical columns'
    })

    return insights[:8]


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
