"""
Chat routes - AI conversation endpoints
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone


def _utcnow_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'

from app.config.constants import AI_MODELS
from app.services.ai_service import get_current_model, generate_ai_response
from app.services.chat_service import (
    chat_with_ai, get_conversation, save_conversation,
    clear_conversation, get_debug_info, parse_suggestions,
    create_new_chat, list_chats, load_chat, delete_chat
)
from app.middleware.session import get_session

chat_router = APIRouter(tags=["chat"])


@chat_router.post('/chat')
async def chat(request: Request, session: dict = Depends(get_session)):
    """Handle chat messages"""
    from app.utils.usage import check_and_increment
    exceeded, used, limit = check_and_increment(session)
    if exceeded:
        return JSONResponse(
            {'error': 'free_tier_limit_reached', 'payment_required': True, 'used': used, 'limit': limit},
            status_code=402
        )

    data = await request.json()
    user_message = data.get('message', '')
    force_search = data.get('search', False)
    image_data = data.get('image', None)  # { base64, mime_type }

    if not user_message and not image_data:
        return JSONResponse({'error': 'No message provided'}, status_code=400)

    if not user_message:
        user_message = 'Analyze this image'

    ai_response, user_idx, ai_idx, searched, suggestions, search_images = chat_with_ai(session, user_message, force_search, image_data)
    current_model = get_current_model(session)

    return {
        'response': ai_response,
        'user_index': user_idx,
        'ai_index': ai_idx,
        'searched': searched,
        'suggestions': suggestions,
        'search_images': search_images,
        'model': current_model,
        'model_name': AI_MODELS[current_model]['name'],
        'timestamp': _utcnow_iso()
    }


@chat_router.post('/chat/edit')
async def edit_chat(request: Request, session: dict = Depends(get_session)):
    """Edit a message and regenerate response"""
    data = await request.json()

    # Debug logging
    print(f"Edit request data: {data}")

    # Handle index
    index_value = data.get('index')
    if index_value is None:
        return JSONResponse({'error': 'Invalid index - index is None'}, status_code=400)

    try:
        message_index = int(index_value)
    except (ValueError, TypeError) as e:
        return JSONResponse({'error': f'Invalid index - cannot convert: {index_value}'}, status_code=400)

    new_content = data.get('content')
    if not new_content:
        return JSONResponse({'error': 'No content provided'}, status_code=400)

    conversation = get_conversation(session)

    # Debug logging
    print(f"Conversation length: {len(conversation)}, Requested index: {message_index}")
    for i, msg in enumerate(conversation):
        print(f"  [{i}] {msg['role']}: {msg['content'][:50]}...")

    # Validate index (must be >= 1 because index 0 is system message)
    if message_index < 1 or message_index >= len(conversation):
        return JSONResponse(
            {'error': f'Invalid index - out of range. Index: {message_index}, Conversation length: {len(conversation)}'},
            status_code=400
        )

    # Verify we're editing a user message
    if conversation[message_index]['role'] != 'user':
        return JSONResponse({'error': 'Can only edit user messages'}, status_code=400)

    # Update the message
    conversation[message_index]['content'] = new_content

    # Remove everything after this message (truncate history)
    del conversation[message_index+1:]

    # Generate new response based on updated history
    ai_response_text = generate_ai_response(conversation, session=session)

    # Parse follow-up suggestions from the response
    clean_response, suggestions = parse_suggestions(ai_response_text)

    # Append new AI response (clean, without suggestion markers)
    conversation.append({"role": "assistant", "content": clean_response})
    ai_index = len(conversation) - 1

    save_conversation(session, conversation)

    return {
        'response': clean_response,
        'user_index': message_index,
        'ai_index': ai_index,
        'suggestions': suggestions,
        'timestamp': _utcnow_iso()
    }


@chat_router.post('/chat/reset')
async def reset_chat(session: dict = Depends(get_session)):
    """Reset conversation (creates a new chat)"""
    chat_id = create_new_chat(session)
    return {'status': 'success', 'message': 'Conversation reset', 'chat_id': chat_id}


@chat_router.get('/chat/history')
async def chat_history(session: dict = Depends(get_session)):
    """Get all chat sessions for this user"""
    chats = list_chats(session)
    return {'chats': chats}


@chat_router.post('/chat/new')
async def new_chat(session: dict = Depends(get_session)):
    """Create a new chat session"""
    chat_id = create_new_chat(session)
    return {'status': 'success', 'chat_id': chat_id}


@chat_router.post('/chat/load')
async def load_chat_endpoint(request: Request, session: dict = Depends(get_session)):
    """Load an existing chat session"""
    data = await request.json()
    chat_id = data.get('chat_id')
    if not chat_id:
        return JSONResponse({'error': 'No chat_id provided'}, status_code=400)

    result, error = load_chat(session, chat_id)
    if error:
        return JSONResponse({'error': error}, status_code=404)
    return result


@chat_router.delete('/chat/{chat_id}')
async def delete_chat_endpoint(chat_id: str, session: dict = Depends(get_session)):
    """Delete a chat session"""
    success = delete_chat(session, chat_id)
    if not success:
        return JSONResponse({'error': 'Chat not found'}, status_code=404)
    return {'status': 'success'}


@chat_router.get('/chat/debug')
async def debug_chat(session: dict = Depends(get_session)):
    """Debug endpoint to check conversation state"""
    return get_debug_info(session)
