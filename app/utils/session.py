"""
Session management utilities
"""
from flask import session
import uuid


def get_session_id():
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.modified = True
    return session['session_id']


def get_dociq_session_id():
    """Get or create DocIQ session ID"""
    if 'dociq_session_id' not in session:
        session['dociq_session_id'] = str(uuid.uuid4())
        session.modified = True
        print(f"[DocIQ] Created new session ID: {session['dociq_session_id']}")
    return session['dociq_session_id']
