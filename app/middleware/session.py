"""
Session middleware - replaces Flask's server-side session with
a cookie-keyed in-memory store for FastAPI.
"""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import Request as FastAPIRequest

# Server-side session store (mirrors Flask's default behaviour)
_sessions: dict[str, dict] = {}
_session_expiry: dict[str, float] = {}  # session_id -> expiry unix timestamp

COOKIE_NAME = "session_id"
MAX_AGE = 86400  # 24 hours

# Clean up expired sessions every N requests
_request_counter = 0
_CLEANUP_INTERVAL = 500


def _cleanup_expired_sessions():
    """Remove sessions that have passed their expiry time."""
    now = time.time()
    expired = [sid for sid, exp in _session_expiry.items() if exp < now]
    for sid in expired:
        _sessions.pop(sid, None)
        _session_expiry.pop(sid, None)


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _request_counter
        _request_counter += 1

        # Periodically purge expired sessions to prevent memory leak
        if _request_counter % _CLEANUP_INTERVAL == 0:
            _cleanup_expired_sessions()

        session_cookie = request.cookies.get(COOKIE_NAME)
        now = time.time()

        # Create new session if cookie is missing, unknown, or expired
        if (not session_cookie
                or session_cookie not in _sessions
                or _session_expiry.get(session_cookie, 0) < now):
            session_cookie = str(uuid.uuid4())
            _sessions[session_cookie] = {}

        # Refresh expiry on every request (sliding window)
        _session_expiry[session_cookie] = now + MAX_AGE

        request.state.session = _sessions[session_cookie]
        request.state.session_cookie = session_cookie
        # Authlib requires request.session for OAuth state storage
        request.scope['session'] = _sessions[session_cookie]

        response = await call_next(request)
        response.set_cookie(
            COOKIE_NAME,
            session_cookie,
            httponly=True,
            max_age=MAX_AGE,
            samesite="lax",
        )
        return response


def get_session(request: FastAPIRequest) -> dict:
    """FastAPI dependency – inject the current session dict."""
    return request.state.session
