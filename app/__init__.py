"""
Laplacian AI - Application Factory
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app(config_name='development'):
    """Create and configure the FastAPI application"""
    app = FastAPI(title="Laplacian AI", docs_url="/docs", redoc_url=None)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Add session middleware
    from app.middleware.session import SessionMiddleware
    app.add_middleware(SessionMiddleware)

    # Initialize extensions and database
    from database import init_database, get_database
    use_mongodb = init_database()

    # Update MongoDB status in settings for services
    from app.config.settings import set_mongodb_status
    set_mongodb_status(use_mongodb)

    # Store database reference on app state
    app.state.db = get_database()

    # Register routers
    from app.routes import register_routers
    register_routers(app)

    # Print startup info
    _print_startup_info(app)

    return app


def _print_startup_info(app):
    """Print startup information"""
    from app.config.settings import AZURE_AVAILABLE, AZURE_OPENAI_DEPLOYMENT

    db = app.state.db

    print("\n" + "="*50)
    print("LAPLACIAN AI - Backend Server (FastAPI)")
    print("="*50)
    print(f"AI Backend: Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT})")
    print(f"Azure OpenAI: {'Connected' if AZURE_AVAILABLE else 'Not Configured'}")
    print(f"MongoDB: {'Connected' if db and db.is_connected() else 'Using in-memory fallback'}")
    print("="*50 + "\n")
