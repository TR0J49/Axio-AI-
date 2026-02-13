"""
Chat Service - Conversation management and AI chat
"""
import re
from flask import session
from datetime import datetime

from app.config.settings import USE_MONGODB
from app.services.ai_service import get_system_prompt, generate_ai_response
from app.services.search_service import should_search_web, web_search
from app.utils.session import get_session_id


def parse_suggestions(ai_response_text):
    """Extract follow-up suggestions from AI response and return clean text + suggestions list"""
    match = re.search(r'<<<SUGGESTIONS>>>(.*?)<<<END_SUGGESTIONS>>>', ai_response_text, re.DOTALL)
    if not match:
        return ai_response_text, []

    raw = match.group(1).strip()
    suggestions = [s.strip() for s in raw.split('|||') if s.strip()]
    # Validate: max 3 suggestions, each max 80 chars
    suggestions = [s[:80] for s in suggestions[:3]]

    clean_text = ai_response_text[:match.start()].rstrip()
    return clean_text, suggestions


# In-memory conversation storage (fallback when MongoDB unavailable)
_memory_store = {}


def get_conversation():
    """Get or initialize conversation for current session"""
    from database import get_database
    db = get_database()
    session_id = get_session_id()

    # Try to get from MongoDB first (primary storage)
    if USE_MONGODB and db.is_connected():
        messages = db.get_chat_history(session_id, limit=50)
        if messages:
            # Convert to conversation format
            conversation = [{"role": "system", "content": get_system_prompt()}]
            for msg in messages:
                conversation.append({
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "_id": msg.get("id")  # Store MongoDB ID for editing
                })
            return conversation
        else:
            # No messages yet, return fresh conversation
            return [{"role": "system", "content": get_system_prompt()}]

    # Fallback to in-memory storage (not session cookie) when MongoDB unavailable
    if session_id not in _memory_store:
        _memory_store[session_id] = [
            {"role": "system", "content": get_system_prompt()}
        ]
    return _memory_store[session_id]


def save_conversation(conversation):
    """Save conversation to MongoDB (no longer uses session cookie to avoid size limits)"""
    from database import get_database
    db = get_database()
    session_id = get_session_id()

    # Save to MongoDB if connected (primary storage)
    if USE_MONGODB and db.is_connected():
        # Get the last two messages (user + assistant) to save
        if len(conversation) >= 2:
            # Check if these are new messages (don't have _id)
            for msg in conversation[-2:]:
                if msg.get("role") in ["user", "assistant"] and "_id" not in msg:
                    msg_id = db.save_chat_message(
                        session_id=session_id,
                        role=msg["role"],
                        content=msg["content"],
                        metadata={"searched": msg.get("searched", False)}
                    )
                    msg["_id"] = msg_id
    else:
        # Fallback: save to in-memory storage
        _memory_store[session_id] = conversation


def clear_conversation():
    """Clear conversation history"""
    from database import get_database
    db = get_database()
    session_id = get_session_id()

    # Clear from MongoDB
    if USE_MONGODB and db.is_connected():
        db.clear_chat_history(session_id)

    # Clear from in-memory storage (fallback)
    if session_id in _memory_store:
        del _memory_store[session_id]


def chat_with_ai(user_message: str, force_search: bool = False):
    """Send message to AI and get response, with optional web search"""
    conversation = get_conversation()

    # Check if we should perform a web search
    search_results = None
    if force_search or should_search_web(user_message):
        print(f"Performing web search for: {user_message}")
        search_results = web_search(user_message)
        print(f"Search results: {len(search_results) if search_results else 0} results found")

    # Build the user message with search results if available
    if search_results:
        search_context = "\n\n📊 **Web Search Results:**\n\n"
        for i, result in enumerate(search_results, 1):
            search_context += f"**{i}. {result.get('title', 'No title')}**\n"
            if result.get('snippet'):
                search_context += f"{result['snippet']}\n"
            if result.get('link'):
                search_context += f"🔗 {result['link']}\n"
            search_context += "\n"

        enhanced_message = f"{user_message}\n{search_context}\nPlease use the above search results to provide an accurate and helpful response. Cite sources when relevant."
    else:
        enhanced_message = user_message

    # Add user message (original, not enhanced)
    user_msg_obj = {"role": "user", "content": user_message}
    conversation.append(user_msg_obj)
    user_index = len(conversation) - 1

    # Create a temporary conversation with enhanced message for AI
    temp_conversation = conversation.copy()
    temp_conversation[-1] = {"role": "user", "content": enhanced_message}

    # Get AI response
    ai_response_text = generate_ai_response(temp_conversation)

    # Parse follow-up suggestions from the response
    clean_response, suggestions = parse_suggestions(ai_response_text)

    # Add AI response (clean, without suggestion markers)
    ai_msg_obj = {"role": "assistant", "content": clean_response}
    conversation.append(ai_msg_obj)
    ai_index = len(conversation) - 1

    save_conversation(conversation)
    return clean_response, user_index, ai_index, bool(search_results), suggestions


def edit_message(message_index: int, new_content: str):
    """Edit a message and regenerate AI response"""
    conversation = get_conversation()

    # Validate index (must be >= 1 because index 0 is system message)
    if message_index < 1 or message_index >= len(conversation):
        return None, f"Invalid index - out of range. Index: {message_index}, Conversation length: {len(conversation)}"

    # Verify we're editing a user message
    if conversation[message_index]['role'] != 'user':
        return None, "Can only edit user messages"

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

    return {
        'response': clean_response,
        'user_index': message_index,
        'ai_index': ai_index,
        'suggestions': suggestions,
        'timestamp': datetime.now().isoformat()
    }, None


def get_debug_info():
    """Get debug info about current conversation"""
    conversation = get_conversation()
    return {
        'length': len(conversation),
        'messages': [{'index': i, 'role': m['role'], 'content': m['content'][:100]} for i, m in enumerate(conversation)]
    }
