"""
Model routes - AI model selection and management
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.config.constants import AI_MODELS
from app.services.ai_service import get_current_model, set_current_model
from app.middleware.session import get_session

models_router = APIRouter(tags=["models"])


@models_router.get('/models')
async def get_models(session: dict = Depends(get_session)):
    """Get available AI models"""
    current_model = get_current_model(session)
    models_info = []

    for model_id, model_data in AI_MODELS.items():
        models_info.append({
            'id': model_id,
            'name': model_data['name'],
            'description': model_data['description'],
            'available': model_data['available'],
            'active': model_id == current_model
        })

    return {
        'models': models_info,
        'current': current_model
    }


@models_router.post('/models/select')
async def select_model(request: Request, session: dict = Depends(get_session)):
    """Select an AI model"""
    data = await request.json()
    model_id = data.get('model', '')

    print(f"[Model Select] Request to switch to model: '{model_id}'")
    print(f"[Model Select] Available models: {[(k, v['available']) for k, v in AI_MODELS.items()]}")

    if not model_id:
        print("[Model Select] Error: No model specified")
        return JSONResponse({'error': 'No model specified'}, status_code=400)

    if model_id not in AI_MODELS:
        print(f"[Model Select] Error: Invalid model '{model_id}'")
        return JSONResponse({'error': 'Invalid model'}, status_code=400)

    if not AI_MODELS[model_id]['available']:
        print(f"[Model Select] Error: Model '{model_id}' is not available")
        return JSONResponse(
            {'error': f'{AI_MODELS[model_id]["name"]} is not available. Check API configuration.'},
            status_code=400
        )

    if set_current_model(session, model_id):
        return {
            'success': True,
            'model': model_id,
            'name': AI_MODELS[model_id]['name'],
            'message': f'Switched to {AI_MODELS[model_id]["name"]}'
        }

    return JSONResponse({'error': 'Failed to switch model'}, status_code=500)
