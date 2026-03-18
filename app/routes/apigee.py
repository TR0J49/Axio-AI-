"""
Apigee routes - API Proxy Bundle Generation endpoints
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime

from app.services.apigee_service import process_apigee_request

apigee_router = APIRouter(tags=["apigee"])


@apigee_router.post('/generate')
async def generate_apigee_bundle(request: Request):
    """Generate an Apigee proxy bundle from natural language description"""
    data = await request.json()
    message = data.get('message', '')

    print(f"[Apigee Route] Received request: {message[:100]}...")

    if not message:
        return JSONResponse({'error': 'No message provided'}, status_code=400)

    # Process the request
    zip_buffer, details, error = process_apigee_request(message)

    if error:
        # Check if we have partial details that need confirmation
        if details:
            return JSONResponse({
                'needs_confirmation': True,
                'extracted': details,
                'error': error,
                'message': f"I extracted some details but {error}. Please provide the missing information."
            }, status_code=400)

        return JSONResponse({
            'error': error,
            'tips': [
                'Specify the proxy name (e.g., "weather-api")',
                'Include the target domain (e.g., "api.weather.com")',
                'Optionally specify the endpoint path (e.g., "/v1/forecast")'
            ]
        }, status_code=400)

    if not zip_buffer:
        return JSONResponse({'error': 'Failed to generate proxy bundle'}, status_code=500)

    # Return the ZIP file
    filename = f"{details['proxy_name']}-bundle.zip"

    return StreamingResponse(
        zip_buffer,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@apigee_router.post('/preview')
async def preview_apigee_bundle(request: Request):
    """Preview the extracted proxy details without generating the bundle"""
    data = await request.json()
    message = data.get('message', '')

    if not message:
        return JSONResponse({'error': 'No message provided'}, status_code=400)

    from app.services.apigee_service import extract_proxy_details, validate_proxy_details

    # Extract details
    details, error = extract_proxy_details(message)

    if error:
        return JSONResponse({'error': error}, status_code=400)

    if not details:
        return JSONResponse({'error': 'Could not extract proxy details from the message'}, status_code=400)

    # Validate and set defaults
    valid, validation_error = validate_proxy_details(details)

    return {
        'valid': valid,
        'details': details,
        'validation_error': validation_error,
        'bundle_structure': [
            f"apiproxy/{details.get('proxy_name', 'proxy')}.xml",
            "apiproxy/proxies/default.xml",
            "apiproxy/targets/default.xml",
            "apiproxy/policies/.gitkeep",
            "apiproxy/resources/.gitkeep"
        ]
    }
