"""
Session middleware - replaces Flask's server-side session with
a cookie-keyed in-memory store for FastAPI.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import Request as FastAPIRequest

# Server-side session store (mirrors Flask's default behaviour)
_sessions: dict[str, dict] = {}

COOKIE_NAME = "session_id"
MAX_AGE = 86400  # 24 hours


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_cookie = request.cookies.get(COOKIE_NAME)

        if not session_cookie or session_cookie not in _sessions:
            session_cookie = str(uuid.uuid4())
            _sessions[session_cookie] = {}

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
