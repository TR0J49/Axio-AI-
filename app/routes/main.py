"""
Main routes - Index page, SEO endpoints (robots.txt, sitemap.xml)
"""
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.config.seo import PUBLIC_PATHS, build_seo
from app.config.settings import SITE_URL

main_router = APIRouter(tags=["main"])
templates = Jinja2Templates(directory="templates")


@main_router.get('/')
async def index(request: Request):
    """Main page - requires login"""
    session = request.state.session
    if not session.get('logged_in'):
        return RedirectResponse(url='/login')
    user = session.get('user', {})
    seo = build_seo(page="workspace", path="/", index=False)
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "seo": seo})


@main_router.get('/login')
async def login_page(request: Request):
    """Login / public landing page - primary SEO surface"""
    session = request.state.session
    if session.get('logged_in'):
        return RedirectResponse(url='/')
    # Canonical is the site root: `/` 307-redirects here for anonymous visitors,
    # so search engines consolidate ranking signals on the homepage URL.
    seo = build_seo(page="home", path="/")
    return templates.TemplateResponse("login.html", {"request": request, "seo": seo})


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


@main_router.get('/robots.txt')
async def robots_txt():
    """robots.txt - allow public pages, block app/API surfaces, point to sitemap"""
    body = "\n".join([
        "User-agent: *",
        "Allow: /$",
        "Allow: /login",
        "Allow: /static/",
        "Allow: /manifest.json",
        "Disallow: /api/",
        "Disallow: /auth/",
        "Disallow: /payment",
        "Disallow: /uploads/",
        "",
        "User-agent: GPTBot",
        "Allow: /",
        "",
        "User-agent: Google-Extended",
        "Allow: /",
        "",
        f"Sitemap: {SITE_URL}/sitemap.xml",
        "",
    ])
    return Response(content=body, media_type="text/plain")


@main_router.get('/sitemap.xml')
async def sitemap_xml():
    """XML sitemap of the crawlable public pages"""
    today = date.today().isoformat()
    urls = []
    for path in PUBLIC_PATHS:
        priority = "1.0" if path == "/" else "0.8"
        urls.append(
            "  <url>\n"
            f"    <loc>{SITE_URL}{path if path != '/' else '/'}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")
