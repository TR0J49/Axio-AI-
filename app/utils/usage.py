"""
Free-tier usage tracking: 10 requests per user across Chat, DocIQ, and VizIQ.
Uses MongoDB when available, falls back to in-memory store.
"""
import threading

FREE_TIER_LIMIT = 10

# In-memory fallback keyed by email
_usage_store: dict = {}
_usage_lock = threading.Lock()


def get_user_email(session: dict):
    """Extract email from session, or None if not logged in."""
    user = session.get('user', {})
    return user.get('email') if user else None


def get_usage(email: str) -> int:
    """Return current request count for this user."""
    from database import get_database
    db = get_database()
    if db.is_connected():
        return db.get_user_usage(email)
    with _usage_lock:
        return _usage_store.get(email, 0)


def check_and_increment(session: dict):
    """
    Check whether the user has hit the free-tier limit.
    If not, increment the counter.

    Returns (limit_exceeded: bool, used: int, limit: int)
    """
    email = get_user_email(session)
    if not email:
        # Unauthenticated — block access; auth guard should have caught this
        return True, FREE_TIER_LIMIT, FREE_TIER_LIMIT

    from database import get_database
    db = get_database()

    if db.is_connected():
        count = db.get_user_usage(email)
        if count >= FREE_TIER_LIMIT:
            return True, count, FREE_TIER_LIMIT
        new_count = db.increment_user_usage(email)
        return False, new_count, FREE_TIER_LIMIT
    else:
        with _usage_lock:
            count = _usage_store.get(email, 0)
            if count >= FREE_TIER_LIMIT:
                return True, count, FREE_TIER_LIMIT
            _usage_store[email] = count + 1
            return False, _usage_store[email], FREE_TIER_LIMIT
