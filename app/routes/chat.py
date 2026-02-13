"""
Chat routes - AI conversation endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from app.config.constants import AI_MODELS
from app.services.ai_service import get_current_model, generate_ai_response
from app.services.chat_service import (
    chat_with_ai, get_conversation, save_conversation,
    clear_conversation, get_debug_info, parse_suggestions
)
from app.utils.session import get_session_id

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    force_search = data.get('search', False)

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    ai_response, user_idx, ai_idx, searched, suggestions = chat_with_ai(user_message, force_search)
    current_model = get_current_model()

    return jsonify({
        'response': ai_response,
        'user_index': user_idx,
        'ai_index': ai_idx,
        'searched': searched,
        'suggestions': suggestions,
        'model': current_model,
        'model_name': AI_MODELS[current_model]['name'],
        'timestamp': datetime.now().isoformat()
    })


@chat_bp.route('/chat/edit', methods=['POST'])
def edit_chat():
    """Edit a message and regenerate response"""
    data = request.json

    # Debug logging
    print(f"Edit request data: {data}")

    # Handle index
    index_value = data.get('index')
    if index_value is None:
        return jsonify({'error': 'Invalid index - index is None'}), 400

    try:
        message_index = int(index_value)
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid index - cannot convert: {index_value}'}), 400

    new_content = data.get('content')
    if not new_content:
        return jsonify({'error': 'No content provided'}), 400

    conversation = get_conversation()

    # Debug logging
    print(f"Conversation length: {len(conversation)}, Requested index: {message_index}")
    for i, msg in enumerate(conversation):
        print(f"  [{i}] {msg['role']}: {msg['content'][:50]}...")

    # Validate index (must be >= 1 because index 0 is system message)
    if message_index < 1 or message_index >= len(conversation):
        return jsonify({'error': f'Invalid index - out of range. Index: {message_index}, Conversation length: {len(conversation)}'}), 400

    # Verify we're editing a user message
    if conversation[message_index]['role'] != 'user':
        return jsonify({'error': 'Can only edit user messages'}), 400

    # Update the message
    conversation[message_index]['content'] = new_content

    # Remove everything after this message (truncate history)
    del conversation[message_index+1:]

    # Generate new response based on updated history
    ai_response_text = generate_ai_response(conversation)

    # Parse follow-up suggestions from the response
    clean_response, suggestions = parse_suggestions(ai_response_text)

    # Append new AI response (clean, without suggestion markers)
    conversation.append({"role": "assistant", "content": clean_response})
    ai_index = len(conversation) - 1

    save_conversation(conversation)

    return jsonify({
        'response': clean_response,
        'user_index': message_index,
        'ai_index': ai_index,
        'suggestions': suggestions,
        'timestamp': datetime.now().isoformat()
    })


@chat_bp.route('/chat/reset', methods=['POST'])
def reset_chat():
    """Reset conversation"""
    clear_conversation()
    return jsonify({'status': 'success', 'message': 'Conversation reset'})


@chat_bp.route('/chat/debug', methods=['GET'])
def debug_chat():
    """Debug endpoint to check conversation state"""
    return jsonify(get_debug_info())
