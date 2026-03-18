"""
VizIQ routes - Data Intelligence and Visualization endpoints
"""
import os
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse

from app.config.settings import USE_MONGODB, UPLOAD_FOLDER
from app.utils.session import get_session_id
from app.utils.file_helpers import secure_filename
from app.utils.data_processing import (
    parse_csv_data, parse_excel_data, parse_json_data,
    detect_column_types, calculate_statistics
)
from app.services.viziq_service import (
    generate_kpis, generate_chart_configs, generate_insights,
    generate_dashboard_name
)
from app.middleware.session import get_session

viziq_router = APIRouter(tags=["viziq"])

# In-memory storage for VizIQ data
viziq_storage = {
    'data': None,
    'columns': [],
    'dtypes': {},
    'filename': '',
    'analysis': None
}


@viziq_router.post('/upload')
async def viziq_upload(file: UploadFile = File(...), session: dict = Depends(get_session)):
    """Upload and process data file for VizIQ"""
    global viziq_storage

    if not file.filename:
        return JSONResponse({'error': 'No file selected'}, status_code=400)

    filename = secure_filename(file.filename)
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if file_extension not in ['csv', 'xlsx', 'xls', 'json']:
        return JSONResponse({'error': 'Unsupported file type. Use CSV, XLSX, or JSON.'}, status_code=400)

    try:
        # Save file temporarily
        file_path = os.path.join(UPLOAD_FOLDER, f"viziq_{uuid.uuid4()}_{filename}")
        file_bytes = await file.read()
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        # Parse file based on type
        if file_extension == 'csv':
            data, columns = parse_csv_data(file_path)
        elif file_extension in ['xlsx', 'xls']:
            data, columns = parse_excel_data(file_path)
            if data is None:
                return JSONResponse({'error': columns}, status_code=500)
        elif file_extension == 'json':
            data, columns = parse_json_data(file_path)
        else:
            return JSONResponse({'error': 'Unsupported file type'}, status_code=400)

        # Clean up temp file
        os.remove(file_path)

        if not data:
            return JSONResponse({'error': 'No data found in file'}, status_code=400)

        # Detect column types
        dtypes = detect_column_types(data, columns)

        # Calculate statistics
        stats = calculate_statistics(data, columns, dtypes)

        # Generate dashboard name
        dashboard_name = generate_dashboard_name(filename, columns)

        # Generate KPIs
        kpis = generate_kpis(data, columns, dtypes, stats, filename)

        # Generate chart configurations
        charts = generate_chart_configs(data, columns, dtypes, stats)

        # Generate insights
        insights = generate_insights(data, columns, dtypes, stats, filename)

        # Store data in memory for immediate use
        viziq_storage = {
            'data': data,
            'columns': columns,
            'dtypes': dtypes,
            'stats': stats,
            'filename': filename
        }

        # Prepare preview data (first 100 rows)
        preview_data = data[:100]

        # Save to MongoDB for persistence
        if USE_MONGODB:
            from database import get_database
            db = get_database()
            if db.is_connected():
                session_id = get_session_id(session)
                viziq_data_info = {
                    'filename': filename,
                    'columns': columns,
                    'dtypes': dtypes,
                    'stats': stats,
                    'row_count': len(data),
                    'kpis': kpis,
                    'charts': charts,
                    'insights': insights,
                    'preview_data': preview_data,
                    'dashboard_name': dashboard_name
                }
                db.save_viziq_data(session_id, viziq_data_info)
                print(f"[VizIQ] Data saved to MongoDB: {filename}")

        return {
            'success': True,
            'dashboard_name': dashboard_name,
            'description': f'AI-generated analytics from {filename}',
            'rows': len(data),
            'cols': len(columns),
            'columns': columns,
            'dtypes': dtypes,
            'kpis': kpis,
            'charts': charts,
            'insights': insights,
            'preview': preview_data
        }

    except Exception as e:
        print(f"VizIQ upload error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({'error': f'Failed to process file: {str(e)}'}, status_code=500)


@viziq_router.post('/clear')
async def viziq_clear(session: dict = Depends(get_session)):
    """Clear VizIQ data"""
    global viziq_storage

    # Clear from MongoDB
    if USE_MONGODB:
        from database import get_database
        db = get_database()
        if db.is_connected():
            session_id = get_session_id(session)
            db.clear_viziq_data(session_id)

    # Clear in-memory storage
    viziq_storage = {
        'data': None,
        'columns': [],
        'dtypes': {},
        'filename': '',
        'analysis': None
    }
    return {'success': True}


@viziq_router.get('/data')
async def viziq_get_data(session: dict = Depends(get_session)):
    """Get current VizIQ data"""
    # Try to get from in-memory first
    if viziq_storage['data'] is not None:
        return {
            'filename': viziq_storage['filename'],
            'columns': viziq_storage['columns'],
            'dtypes': viziq_storage['dtypes'],
            'rows': len(viziq_storage['data']),
            'preview': viziq_storage['data'][:50]
        }

    # Try to get from MongoDB
    if USE_MONGODB:
        from database import get_database
        db = get_database()
        if db.is_connected():
            session_id = get_session_id(session)
            viziq_data = db.get_viziq_data(session_id)
            if viziq_data:
                return {
                    'filename': viziq_data.get('filename'),
                    'columns': viziq_data.get('columns', []),
                    'dtypes': viziq_data.get('dtypes', {}),
                    'rows': viziq_data.get('row_count', 0),
                    'preview': viziq_data.get('preview_data', [])[:50],
                    'kpis': viziq_data.get('kpis', []),
                    'charts': viziq_data.get('charts', []),
                    'insights': viziq_data.get('insights', []),
                    'dashboard_name': viziq_data.get('dashboard_name')
                }

    return JSONResponse({'error': 'No data loaded'}, status_code=404)
