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
    from app.config.settings import LITE_AVAILABLE, CODER_AVAILABLE

    print("\n" + "="*50)
    print("LAPLACIAN AI - Backend Server")
    print("="*50)
    print(f"GPT Model: {app.config.get('GPT_MODEL', 'N/A')}")
    print(f"Lite Model: {app.config.get('LITE_MODEL', 'N/A')} ({'Available' if LITE_AVAILABLE else 'Not Available'})")
    print(f"Coder Model: {app.config.get('CODER_MODEL', 'N/A')} ({'Available' if CODER_AVAILABLE else 'Not Available'})")
    print(f"MongoDB: {'Connected' if app.db and app.db.is_connected() else 'Using in-memory fallback'}")
    print("="*50 + "\n")
