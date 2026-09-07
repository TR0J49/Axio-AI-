"""
SEO configuration and structured-data builder for Laplacian AI.

Single source of truth for meta tags, Open Graph, Twitter cards, geo tags and
schema.org JSON-LD. Import `build_seo(page, path)` from routes and pass the
result to the template as `seo`; `templates/partials/seo_head.html` renders it.
"""
from datetime import date

from app.config.settings import SITE_URL

# ── Brand / entity facts ────────────────────────────────────────────────
PRODUCT_NAME = "Laplacian AI"
ORG_NAME = "Perfionix AI"
ORG_LEGAL_NAME = "Perfionix AI"
FOUNDER_NAME = "Shubham Rahangdale"
FOUNDER_TITLE = "Founder & CEO"

# Set to a real ISO year/date once confirmed (e.g. "2025"); left blank it is
# simply omitted from structured data rather than guessed.
FOUNDING_DATE = ""

CITY = "Nagpur"
REGION = "Maharashtra"
REGION_CODE = "IN-MH"
COUNTRY = "IN"
GEO_LAT = "21.1458"
GEO_LON = "79.0882"

TAGLINE = "India's First AI Workspace"

DESCRIPTION = (
    "Laplacian AI is an enterprise AI workspace by Perfionix AI - an AI startup "
    "founded by Shubham Rahangdale in Nagpur, India. AI chat, DocIQ document "
    "intelligence, VizIQ data visualisation, code execution and an Apigee proxy "
    "generator in one private, data-sovereign platform."
)

# Longer copy used for the crawlable on-page section.
ABOUT_PARAGRAPHS = [
    (
        "Laplacian AI is a product of Perfionix AI, an artificial-intelligence "
        "startup based in Nagpur, Maharashtra, India and founded by "
        "Shubham Rahangdale. It brings generative AI, document intelligence and "
        "data visualisation together in a single secure workspace built for "
        "Indian businesses and teams."
    ),
    (
        "Unlike generic AI chatbots, Laplacian AI is designed around data "
        "sovereignty: your documents and conversations stay under your control. "
        "The platform is powered by enterprise-grade large language models and "
        "combines chat, retrieval-augmented answers over your own files, "
        "one-click data dashboards, code execution and an Apigee API-proxy "
        "generator."
    ),
    (
        "Perfionix AI is led by founder and CEO Shubham Rahangdale, and is part "
        "of the growing AI startup ecosystem in Nagpur and across India. "
        "Laplacian AI is the company's flagship AI SaaS product."
    ),
]

FEATURES = [
    ("AI Chat", "Multi-session AI chat with web search and image understanding."),
    ("DocIQ", "Ask questions across your PDFs, Word and text documents with cited answers."),
    ("VizIQ", "Turn CSV, Excel and JSON data into KPIs, charts and insight dashboards."),
    ("Apigee Proxy Generator", "Describe an API proxy in plain English and download a ready Apigee bundle."),
    ("Code Execution", "Run code in many languages directly inside the workspace."),
    ("Productivity", "Built-in notes, tasks and reminders for every user."),
]

FAQ = [
    (
        "What is Laplacian AI?",
        "Laplacian AI is an enterprise AI workspace built by Perfionix AI. It "
        "combines AI chat, DocIQ document Q&A, VizIQ data visualisation, code "
        "execution and an Apigee API-proxy generator in a single private "
        "platform that keeps your data under your control.",
    ),
    (
        "Who is the founder of Laplacian AI and Perfionix AI?",
        "Perfionix AI and its Laplacian AI product were founded by "
        "Shubham Rahangdale, an AI entrepreneur based in Nagpur, Maharashtra, "
        "India.",
    ),
    (
        "What is Perfionix AI?",
        "Perfionix AI is an artificial-intelligence startup headquartered in "
        "Nagpur, India, founded by Shubham Rahangdale. It builds Laplacian AI, "
        "an AI workspace for Indian businesses and teams.",
    ),
    (
        "Where is Perfionix AI located?",
        "Perfionix AI is based in Nagpur, Maharashtra, India.",
    ),
    (
        "What can I do with Laplacian AI?",
        "You can chat with AI models, ask questions across your documents with "
        "DocIQ, turn spreadsheets into dashboards with VizIQ, run code, generate "
        "Apigee proxy bundles from plain English, and manage notes, tasks and "
        "reminders.",
    ),
    (
        "Is Laplacian AI free to use?",
        "Laplacian AI offers a free tier so you can try the workspace, with paid "
        "upgrades for higher usage.",
    ),
]

KEYWORDS = [
    "Laplacian AI", "Laplacian AI Perfionix", "Laplacian AI workspace", "Laplacian",
    "Perfionix AI", "Perfionix AI Nagpur", "Perfionix", "Perfionix AI startup",
    "Shubham Rahangdale", "Shubham Rahangdale Perfionix AI",
    "Shubham Rahangdale founder", "Shubham Rahangdale Nagpur",
    "AI startup Nagpur", "AI company Nagpur", "AI startup India", "Indian AI startup",
    "AI startup Maharashtra", "best AI startup Nagpur", "AI company India",
    "enterprise AI workspace", "AI workspace India", "generative AI platform",
    "AI productivity platform", "AI SaaS India", "private AI platform",
    "data sovereignty AI", "DocIQ", "VizIQ", "document intelligence AI",
    "data visualization AI", "RAG AI platform", "Apigee proxy generator",
    "AI code assistant", "AI chat assistant India", "Azure OpenAI application",
]

# Fill with real profile URLs when available - used for schema.org `sameAs`.
SOCIAL_LINKS: list[str] = [
    # "https://www.linkedin.com/company/perfionix-ai/",
    # "https://twitter.com/perfionixai",
    # "https://www.linkedin.com/in/shubham-rahangdale/",
    # "https://www.instagram.com/perfionixai/",
]

# e.g. "@perfionixai" - used for twitter:site / twitter:creator.
TWITTER_HANDLE = ""

OG_IMAGE = f"{SITE_URL}/static/Laplacian%20AI%20Logo.png"
LOGO_URL = f"{SITE_URL}/static/New%20lap%20logo.png"

# Pages exposed to search engines (also drives sitemap.xml).
PUBLIC_PATHS = ["/", "/login"]


def _organization() -> dict:
    org = {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": ORG_NAME,
        "legalName": ORG_LEGAL_NAME,
        "url": SITE_URL,
        "logo": {
            "@type": "ImageObject",
            "url": LOGO_URL,
        },
        "description": (
            f"{ORG_NAME} is an AI startup based in {CITY}, {REGION}, {COUNTRY}, "
            f"founded by {FOUNDER_NAME}. It builds {PRODUCT_NAME}, an enterprise "
            "AI workspace."
        ),
        "founder": {"@id": f"{SITE_URL}/#founder"},
        "address": {
            "@type": "PostalAddress",
            "addressLocality": CITY,
            "addressRegion": REGION,
            "addressCountry": COUNTRY,
        },
        "areaServed": "IN",
        "knowsAbout": [
            "Artificial Intelligence", "Generative AI", "Large Language Models",
            "Document Intelligence", "Data Visualisation", "Enterprise Software",
        ],
    }
    if FOUNDING_DATE:
        org["foundingDate"] = FOUNDING_DATE
    if SOCIAL_LINKS:
        org["sameAs"] = SOCIAL_LINKS
    return org


def _founder() -> dict:
    person = {
        "@type": "Person",
        "@id": f"{SITE_URL}/#founder",
        "name": FOUNDER_NAME,
        "jobTitle": FOUNDER_TITLE,
        "worksFor": {"@id": f"{SITE_URL}/#organization"},
        "description": (
            f"{FOUNDER_NAME} is the {FOUNDER_TITLE} of {ORG_NAME}, an AI startup "
            f"in {CITY}, {REGION}, India, and the creator of {PRODUCT_NAME}."
        ),
        "homeLocation": {
            "@type": "Place",
            "name": f"{CITY}, {REGION}, India",
        },
        "nationality": {"@type": "Country", "name": "India"},
    }
    founder_links = [s for s in SOCIAL_LINKS if "/in/" in s or "linkedin.com/in" in s]
    if founder_links:
        person["sameAs"] = founder_links
    return person


def _website() -> dict:
    return {
        "@type": "WebSite",
        "@id": f"{SITE_URL}/#website",
        "url": SITE_URL,
        "name": PRODUCT_NAME,
        "alternateName": [f"{PRODUCT_NAME} by {ORG_NAME}", "Laplacian", ORG_NAME],
        "description": DESCRIPTION,
        "inLanguage": "en-IN",
        "publisher": {"@id": f"{SITE_URL}/#organization"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{SITE_URL}/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def _software_application() -> dict:
    return {
        "@type": ["SoftwareApplication", "WebApplication"],
        "@id": f"{SITE_URL}/#software",
        "name": PRODUCT_NAME,
        "url": SITE_URL,
        "applicationCategory": "BusinessApplication",
        "applicationSuite": "Laplacian AI",
        "operatingSystem": "Web, Windows, macOS, Linux, Android, iOS",
        "browserRequirements": "Requires a modern web browser with JavaScript.",
        "description": DESCRIPTION,
        "featureList": [name for name, _ in FEATURES],
        "publisher": {"@id": f"{SITE_URL}/#organization"},
        "author": {"@id": f"{SITE_URL}/#founder"},
        "inLanguage": "en-IN",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "INR",
            "description": "Free tier with paid upgrades for higher usage.",
        },
    }


def _faq_page() -> dict:
    return {
        "@type": "FAQPage",
        "@id": f"{SITE_URL}/#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in FAQ
        ],
    }


def _breadcrumb(path: str) -> dict:
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL}]
    if path not in ("", "/"):
        items.append({
            "@type": "ListItem",
            "position": 2,
            "name": path.strip("/").replace("-", " ").title(),
            "item": f"{SITE_URL}{path}",
        })
    return {"@type": "BreadcrumbList", "itemListElement": items}


def build_json_ld(path: str = "/") -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            _website(),
            _organization(),
            _founder(),
            _software_application(),
            _faq_page(),
            _breadcrumb(path),
        ],
    }


def build_seo(page: str = "home", path: str = "/", *, index: bool = True,
              title: str | None = None, description: str | None = None) -> dict:
    """Return the context dict consumed by partials/seo_head.html."""
    if title is None:
        title = (
            f"{PRODUCT_NAME} - {TAGLINE} by {ORG_NAME}"
            if page == "home"
            else f"{PRODUCT_NAME} - {page.title()}"
        )
    description = description or DESCRIPTION
    canonical = f"{SITE_URL}{path if path.startswith('/') else '/' + path}"

    robots = (
        "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
        if index
        else "noindex, follow"
    )

    return {
        "site_url": SITE_URL,
        "site_name": PRODUCT_NAME,
        "org_name": ORG_NAME,
        "founder_name": FOUNDER_NAME,
        "title": title,
        "description": description,
        "keywords": ", ".join(KEYWORDS),
        "canonical": canonical,
        "robots": robots,
        "og_type": "website",
        "og_image": OG_IMAGE,
        "logo": LOGO_URL,
        "locale": "en_IN",
        "twitter_handle": TWITTER_HANDLE,
        "social_links": SOCIAL_LINKS,
        "geo": {
            "region": REGION_CODE,
            "placename": CITY,
            "position": f"{GEO_LAT};{GEO_LON}",
            "icbm": f"{GEO_LAT}, {GEO_LON}",
        },
        "tagline": TAGLINE,
        "about_paragraphs": ABOUT_PARAGRAPHS,
        "features": FEATURES,
        "faq": FAQ,
        "json_ld": build_json_ld(path),
        "updated": date.today().isoformat(),
    }
