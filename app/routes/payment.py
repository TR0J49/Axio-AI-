"""
Payment / upgrade page and usage API
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.middleware.session import get_session
from app.utils.usage import get_user_email, get_usage, FREE_TIER_LIMIT

payment_router = APIRouter(tags=["payment"])
templates = Jinja2Templates(directory="templates")


@payment_router.get('/payment', response_class=HTMLResponse)
async def payment_page(request: Request):
    """Upgrade / payment page shown when free tier is exhausted."""
    session = request.state.session
    user = session.get('user', {})
    return templates.TemplateResponse("payment.html", {"request": request, "user": user})


@payment_router.get('/api/usage')
async def get_usage_status(session: dict = Depends(get_session)):
    """Return current usage count and limit for the logged-in user."""
    email = get_user_email(session)
    if not email:
        return {"used": 0, "limit": FREE_TIER_LIMIT, "remaining": FREE_TIER_LIMIT}
    used = get_usage(email)
    remaining = max(0, FREE_TIER_LIMIT - used)
    return {"used": used, "limit": FREE_TIER_LIMIT, "remaining": remaining}
