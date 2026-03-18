"""
Main routes - Index page
"""
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

main_router = APIRouter(tags=["main"])
templates = Jinja2Templates(directory="templates")


@main_router.get('/')
async def index(request: Request):
    """Main page"""
    return templates.TemplateResponse("index.html", {"request": request})


@main_router.get('/favicon.ico')
async def favicon():
    """Serve favicon"""
    return FileResponse("static/lap favivon.png", media_type="image/png")


@main_router.get('/sw.js')
async def service_worker():
    """Serve service worker from root scope"""
    return FileResponse("static/sw.js", media_type="application/javascript")


@main_router.get('/manifest.json')
async def manifest():
    """Serve PWA manifest from root"""
    return FileResponse("static/manifest.json", media_type="application/json")
