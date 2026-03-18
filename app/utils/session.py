"""
Session management utilities
"""
import uuid


def get_session_id(session: dict) -> str:
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def get_dociq_session_id(session: dict) -> str:
    """Get or create DocIQ session ID"""
    if 'dociq_session_id' not in session:
        session['dociq_session_id'] = str(uuid.uuid4())
        print(f"[DocIQ] Created new session ID: {session['dociq_session_id']}")
    return session['dociq_session_id']
