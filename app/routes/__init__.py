"""Routes module - Blueprint registration"""
from flask import Flask


def register_blueprints(app: Flask):
    """Register all blueprints with the application"""
    from app.routes.main import main_bp
    from app.routes.models import models_bp
    from app.routes.chat import chat_bp
    from app.routes.search import search_bp
    from app.routes.code import code_bp
    from app.routes.productivity import productivity_bp
    from app.routes.dociq import dociq_bp
    from app.routes.viziq import viziq_bp
    from app.routes.apigee import apigee_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(models_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(code_bp, url_prefix='/api')
    app.register_blueprint(productivity_bp, url_prefix='/api')
    app.register_blueprint(dociq_bp, url_prefix='/api/dociq')
    app.register_blueprint(viziq_bp, url_prefix='/api/viziq')
    app.register_blueprint(apigee_bp, url_prefix='/api/apigee')
