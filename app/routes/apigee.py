"""
Apigee routes - API Proxy Bundle Generation endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime

from app.services.apigee_service import process_apigee_request

apigee_bp = Blueprint('apigee', __name__)


@apigee_bp.route('/generate', methods=['POST'])
def generate_apigee_bundle():
    """Generate an Apigee proxy bundle from natural language description"""
    data = request.json
    message = data.get('message', '')

    print(f"[Apigee Route] Received request: {message[:100]}...")

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Process the request
    zip_buffer, details, error = process_apigee_request(message)

    if error:
        # Check if we have partial details that need confirmation
        if details:
            return jsonify({
                'needs_confirmation': True,
                'extracted': details,
                'error': error,
                'message': f"I extracted some details but {error}. Please provide the missing information."
            }), 400

        return jsonify({
            'error': error,
            'tips': [
                'Specify the proxy name (e.g., "weather-api")',
                'Include the target domain (e.g., "api.weather.com")',
                'Optionally specify the endpoint path (e.g., "/v1/forecast")'
            ]
        }), 400

    if not zip_buffer:
        return jsonify({'error': 'Failed to generate proxy bundle'}), 500

    # Return the ZIP file
    filename = f"{details['proxy_name']}-bundle.zip"

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


@apigee_bp.route('/preview', methods=['POST'])
def preview_apigee_bundle():
    """Preview the extracted proxy details without generating the bundle"""
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    from app.services.apigee_service import extract_proxy_details, validate_proxy_details

    # Extract details
    details, error = extract_proxy_details(message)

    if error:
        return jsonify({'error': error}), 400

    if not details:
        return jsonify({'error': 'Could not extract proxy details from the message'}), 400

    # Validate and set defaults
    valid, validation_error = validate_proxy_details(details)

    return jsonify({
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
    })
