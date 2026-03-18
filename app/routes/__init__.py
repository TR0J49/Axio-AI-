"""Routes module - Router registration"""
from fastapi import FastAPI


def register_routers(app: FastAPI):
    """Register all routers with the application"""
    from app.routes.main import main_router
    from app.routes.models import models_router
    from app.routes.chat import chat_router
    from app.routes.search import search_router
    from app.routes.code import code_router
    from app.routes.productivity import productivity_router
    from app.routes.dociq import dociq_router
    from app.routes.viziq import viziq_router
    from app.routes.apigee import apigee_router

    # Register routers
    app.include_router(main_router)
    app.include_router(models_router, prefix='/api')
    app.include_router(chat_router, prefix='/api')
    app.include_router(search_router, prefix='/api')
    app.include_router(code_router, prefix='/api')
    app.include_router(productivity_router, prefix='/api')
    app.include_router(dociq_router, prefix='/api/dociq')
    app.include_router(viziq_router, prefix='/api/viziq')
    app.include_router(apigee_router, prefix='/api/apigee')
