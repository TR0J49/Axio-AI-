"""
Google OAuth 2.0 Authentication Routes
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.config.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

auth_router = APIRouter(tags=["auth"])

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


@auth_router.get('/auth/login')
async def login(request: Request):
    """Redirect to Google OAuth"""
    redirect_uri = request.url_for('auth_callback')
    # In production, force HTTPS
    redirect_uri = str(redirect_uri)
    if request.headers.get('x-forwarded-proto') == 'https':
        redirect_uri = redirect_uri.replace('http://', 'https://')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_router.get('/auth/callback')
async def auth_callback(request: Request):
    """Handle Google OAuth callback"""
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')

    if user_info:
        session = request.state.session
        session['user'] = {
            'name': user_info.get('name', ''),
            'email': user_info.get('email', ''),
            'picture': user_info.get('picture', ''),
        }
        session['logged_in'] = True

    return RedirectResponse(url='/')


@auth_router.get('/auth/logout')
async def logout(request: Request):
    """Logout user"""
    session = request.state.session
    session.pop('user', None)
    session.pop('logged_in', None)
    return RedirectResponse(url='/login')


@auth_router.get('/api/auth/user')
async def get_user(request: Request):
    """Get current user info"""
    session = request.state.session
    if session.get('logged_in'):
        return {'logged_in': True, 'user': session.get('user')}
    return {'logged_in': False, 'user': None}
