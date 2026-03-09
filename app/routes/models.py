"""
Model routes - AI model selection and management
"""
from flask import Blueprint, request, jsonify

from app.config.constants import AI_MODELS
from app.services.ai_service import get_current_model, set_current_model

models_bp = Blueprint('models', __name__)


@models_bp.route('/models', methods=['GET'])
def get_models():
    """Get available AI models"""
    current_model = get_current_model()
    models_info = []

    for model_id, model_data in AI_MODELS.items():
        models_info.append({
            'id': model_id,
            'name': model_data['name'],
            'description': model_data['description'],
            'available': model_data['available'],
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
