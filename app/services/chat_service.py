"""
Chat Service - Conversation management and AI chat (multi-session)
"""
import re
import uuid
from datetime import datetime

from app.config.settings import USE_MONGODB
from app.services.ai_service import get_system_prompt, generate_ai_response
from app.services.search_service import should_search_web, web_search, image_search
from app.utils.session import get_session_id


def clean_citation_markers(text):
    """Remove raw citation markers like [^1^], [^2^][^3^], etc. from AI response"""
    # Remove [^N^] patterns (single or grouped)
    text = re.sub(r'\[\^(\d+)\^\]', '', text)
    # Remove leftover empty parenthetical refs like ()
    text = re.sub(r'\(\s*\)', '', text)
    # Clean up extra spaces left behind
    text = re.sub(r'  +', ' ', text)
    # Clean trailing spaces before punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    return text.strip()


def parse_suggestions(ai_response_text):
    """Extract follow-up suggestions from AI response and return clean text + suggestions list"""
    # Clean citation markers first
    ai_response_text = clean_citation_markers(ai_response_text)

    match = re.search(r'<<<SUGGESTIONS>>>(.*?)<<<END_SUGGESTIONS>>>', ai_response_text, re.DOTALL)
    if not match:
        return ai_response_text, []

    raw = match.group(1).strip()
    suggestions = [s.strip() for s in raw.split('|||') if s.strip()]
    suggestions = [s[:80] for s in suggestions[:3]]

    clean_text = ai_response_text[:match.start()].rstrip()
    return clean_text, suggestions


# ---------------------------------------------------------------------------
# Multi-chat in-memory storage
# Structure: { session_id: { chat_id: { "messages": [...], "title": str,
#              "created_at": str, "updated_at": str } } }
# ---------------------------------------------------------------------------
_chat_sessions: dict[str, dict[str, dict]] = {}


def _get_user_chats(session: dict) -> dict:
    """Get or create the chat dict for this browser session."""
    sid = get_session_id(session)
    if sid not in _chat_sessions:
        _chat_sessions[sid] = {}
    return _chat_sessions[sid]


def _ensure_active_chat(session: dict) -> str:
    """Make sure a current_chat_id exists; create one if not."""
    if not session.get('current_chat_id'):
        return create_new_chat(session)
    # Also verify the chat_id still exists in the store
    chats = _get_user_chats(session)
    if session['current_chat_id'] not in chats:
        return create_new_chat(session)
    return session['current_chat_id']


def _derive_title(message: str) -> str:
    """Derive a short title from the first user message."""
    title = message.strip().replace('\n', ' ')
    return title[:60] + '…' if len(title) > 60 else title


# ---------------------------------------------------------------------------
# Public API — CRUD for chat sessions
# ---------------------------------------------------------------------------

def create_new_chat(session: dict) -> str:
    """Create a brand-new chat session and make it active."""
    chat_id = str(uuid.uuid4())
    chats = _get_user_chats(session)
    now = datetime.now().isoformat()
    chats[chat_id] = {
        "messages": [{"role": "system", "content": get_system_prompt()}],
        "title": "New Chat",
        "created_at": now,
        "updated_at": now,
    }
    session['current_chat_id'] = chat_id
    return chat_id


def list_chats(session: dict) -> list[dict]:
    """Return summaries of all chats, newest first."""
    chats = _get_user_chats(session)
    active = session.get('current_chat_id')
    result = []
    for cid, data in chats.items():
        # Count only user+assistant messages (skip system)
        msg_count = sum(1 for m in data["messages"] if m["role"] in ("user", "assistant"))
        result.append({
            "chat_id": cid,
            "title": data["title"],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "message_count": msg_count,
            "is_active": cid == active,
        })
    result.sort(key=lambda c: c["updated_at"], reverse=True)
    return result


def load_chat(session: dict, chat_id: str):
    """Switch to an existing chat and return its messages (excluding system)."""
    chats = _get_user_chats(session)
    if chat_id not in chats:
        return None, "Chat not found"

    session['current_chat_id'] = chat_id
    data = chats[chat_id]

    # Return messages without the system prompt
    messages = []
    for i, m in enumerate(data["messages"]):
        if m["role"] == "system":
            continue
        messages.append({
            "role": m["role"],
            "content": m["content"],
            "index": i,
        })

    return {
        "chat_id": chat_id,
        "title": data["title"],
        "messages": messages,
    }, None


def delete_chat(session: dict, chat_id: str) -> bool:
    """Delete a chat session. If it was active, start a new one."""
    chats = _get_user_chats(session)
    if chat_id not in chats:
        return False
    del chats[chat_id]
    if session.get('current_chat_id') == chat_id:
        if chats:
            # Switch to the most recent remaining chat
            newest = max(chats, key=lambda c: chats[c]["updated_at"])
            session['current_chat_id'] = newest
        else:
            create_new_chat(session)
    return True


# ---------------------------------------------------------------------------
# Existing conversation helpers (now chat_id-aware)
# ---------------------------------------------------------------------------

def get_conversation(session: dict):
    """Get the active conversation's message list."""
    _ensure_active_chat(session)
    chats = _get_user_chats(session)
    chat_id = session['current_chat_id']
    return chats[chat_id]["messages"]


def save_conversation(session: dict, conversation):
    """Persist the conversation list back into the store and update metadata."""
    _ensure_active_chat(session)
    chats = _get_user_chats(session)
    chat_id = session['current_chat_id']
    chats[chat_id]["messages"] = conversation
    chats[chat_id]["updated_at"] = datetime.now().isoformat()

    # Derive title from the first user message if still "New Chat"
    if chats[chat_id]["title"] == "New Chat":
        for m in conversation:
            if m["role"] == "user":
                chats[chat_id]["title"] = _derive_title(m["content"])
                break

    # Also save to MongoDB if connected
    from database import get_database
    db = get_database()
    sid = get_session_id(session)
    if USE_MONGODB and db.is_connected():
        if len(conversation) >= 2:
            for msg in conversation[-2:]:
                if msg.get("role") in ["user", "assistant"] and "_id" not in msg:
                    msg_id = db.save_chat_message(
                        session_id=sid,
                        role=msg["role"],
                        content=msg["content"],
                        metadata={"searched": msg.get("searched", False), "chat_id": chat_id}
                    )
                    msg["_id"] = msg_id


def clear_conversation(session: dict):
    """Reset = create a new chat (old one stays in history)."""
    create_new_chat(session)


def chat_with_ai(session: dict, user_message: str, force_search: bool = False, image_data: dict = None):
    """Send message to AI and get response, with optional web search and image."""
    conversation = get_conversation(session)

    # Check if we should perform a web search
    search_results = None
    search_images = []
    if force_search or should_search_web(user_message):
        print(f"Performing web search for: {user_message}")
        search_results = web_search(user_message)
        print(f"Search results: {len(search_results) if search_results else 0} results found")

        # Extract images from the search result pages
        if search_results:
            search_images = image_search(user_message, search_results=search_results)
            print(f"Search images: {len(search_images)} images found")

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

    # Build the last user message content — with image if provided
    if image_data and image_data.get('base64'):
        # Use multimodal content format for vision
        user_content = [
            {"type": "text", "text": enhanced_message},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_data.get('mime_type', 'image/png')};base64,{image_data['base64']}"
                }
            }
        ]
        temp_conversation[-1] = {"role": "user", "content": user_content}
        print(f"[Chat] Sending message with image ({image_data.get('mime_type')})")
    else:
        temp_conversation[-1] = {"role": "user", "content": enhanced_message}

    # Get AI response
    ai_response_text = generate_ai_response(temp_conversation, session=session)

    # Parse follow-up suggestions from the response
    clean_response, suggestions = parse_suggestions(ai_response_text)

    # Add AI response (clean, without suggestion markers)
    ai_msg_obj = {"role": "assistant", "content": clean_response}
    conversation.append(ai_msg_obj)
    ai_index = len(conversation) - 1

    save_conversation(session, conversation)
    return clean_response, user_index, ai_index, bool(search_results), suggestions, search_images


def edit_message(session: dict, message_index: int, new_content: str):
    """Edit a message and regenerate AI response."""
    conversation = get_conversation(session)

    if message_index < 1 or message_index >= len(conversation):
        return None, f"Invalid index - out of range. Index: {message_index}, Conversation length: {len(conversation)}"

    if conversation[message_index]['role'] != 'user':
        return None, "Can only edit user messages"

    conversation[message_index]['content'] = new_content
    del conversation[message_index+1:]

    ai_response_text = generate_ai_response(conversation, session=session)
    clean_response, suggestions = parse_suggestions(ai_response_text)

    conversation.append({"role": "assistant", "content": clean_response})
    ai_index = len(conversation) - 1

    save_conversation(session, conversation)

    return {
        'response': clean_response,
        'user_index': message_index,
        'ai_index': ai_index,
        'suggestions': suggestions,
        'timestamp': datetime.now().isoformat()
    }, None


def get_debug_info(session: dict):
    """Get debug info about current conversation."""
    conversation = get_conversation(session)
    return {
        'chat_id': session.get('current_chat_id'),
        'length': len(conversation),
        'messages': [{'index': i, 'role': m['role'], 'content': m['content'][:100]} for i, m in enumerate(conversation)]
    }
