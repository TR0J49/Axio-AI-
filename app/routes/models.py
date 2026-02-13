"""
Model routes - AI model selection and management
"""
import requests
from flask import Blueprint, request, jsonify

from app.config.constants import AI_MODELS
from app.config.settings import LITE_SERVER_URL, LITE_MODEL, CODER_MODEL, MAX_MODEL
from app.services.ai_service import get_current_model, set_current_model

models_bp = Blueprint('models', __name__)


def check_model_available(model_name):
    """Dynamically check if an Ollama model is available by checking model list"""
    try:
        # Use /api/tags to list models - much faster than generation test
        base_url = LITE_SERVER_URL.replace('/api/chat', '')
        response = requests.get(f"{base_url}/api/tags", timeout=10)

        if response.status_code == 200:
            models_data = response.json()
            available_models = [m['name'] for m in models_data.get('models', [])]
            return model_name in available_models
        return False
    except Exception:
        return False


@models_bp.route('/models', methods=['GET'])
def get_models():
    """Get available AI models with dynamic availability check"""
    current_model = get_current_model()
    models_info = []

    # Dynamic availability check for models that were marked unavailable
    dynamic_availability = {
        'gpt': True,  # Always assume GPT is available
        'gemini': AI_MODELS['gemini']['available'] or check_model_available(LITE_MODEL),
        'coder': AI_MODELS['coder']['available'] or check_model_available(CODER_MODEL),
        'max': AI_MODELS['max']['available'] or check_model_available(MAX_MODEL)
    }

    for model_id, model_data in AI_MODELS.items():
        # Use dynamic check if static check said unavailable
        is_available = dynamic_availability.get(model_id, model_data['available'])

        # Update the cached value if now available
        if is_available and not model_data['available']:
            AI_MODELS[model_id]['available'] = True

        models_info.append({
            'id': model_id,
            'name': model_data['name'],
            'description': model_data['description'],
            'available': is_available,
            'active': model_id == current_model
        })

    return jsonify({
        'models': models_info,
        'current': current_model
    })


@models_bp.route('/models/select', methods=['POST'])
def select_model():
    """Select an AI model"""
    data = request.json
    model_id = data.get('model', '')

    print(f"[Model Select] Request to switch to model: '{model_id}'")
    print(f"[Model Select] Available models: {[(k, v['available']) for k, v in AI_MODELS.items()]}")

    if not model_id:
        print("[Model Select] Error: No model specified")
        return jsonify({'error': 'No model specified'}), 400

    if model_id not in AI_MODELS:
        print(f"[Model Select] Error: Invalid model '{model_id}'")
        return jsonify({'error': 'Invalid model'}), 400

    if not AI_MODELS[model_id]['available']:
        print(f"[Model Select] Error: Model '{model_id}' is not available")
        return jsonify({'error': f'{AI_MODELS[model_id]["name"]} is not available. Check API configuration.'}), 400

    if set_current_model(model_id):
        return jsonify({
            'success': True,
            'model': model_id,
            'name': AI_MODELS[model_id]['name'],
            'message': f'Switched to {AI_MODELS[model_id]["name"]}'
        })

    return jsonify({'error': 'Failed to switch model'}), 500
