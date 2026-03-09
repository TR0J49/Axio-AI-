"""
Laplacian AI - Application Factory
"""
from flask import Flask
from datetime import timedelta
import os


def create_app(config_name='development'):
    """Create and configure the Flask application"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    from app.config.settings import config
    app.config.from_object(config[config_name])

    # Initialize extensions and database
    from database import init_database, get_database
    use_mongodb = init_database()

    # Update MongoDB status in settings for services
    from app.config.settings import set_mongodb_status
    set_mongodb_status(use_mongodb)

    # Store database reference in app
    app.db = get_database()

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Print startup info
    _print_startup_info(app)

    return app


def _print_startup_info(app):
    """Print startup information"""
    from app.config.settings import AZURE_AVAILABLE, AZURE_OPENAI_DEPLOYMENT

    print("\n" + "="*50)
    print("LAPLACIAN AI - Backend Server")
    print("="*50)
    print(f"AI Backend: Azure OpenAI ({AZURE_OPENAI_DEPLOYMENT})")
    print(f"Azure OpenAI: {'Connected' if AZURE_AVAILABLE else 'Not Configured'}")
    print(f"MongoDB: {'Connected' if app.db and app.db.is_connected() else 'Using in-memory fallback'}")
    print("="*50 + "\n")
