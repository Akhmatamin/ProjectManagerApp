import logging

import uvicorn
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.auth.router import auth_router
from app.documents.router import document_router
from app.lifespan import lifespan
from app.projects.router import project_router, projects_router
from app.shared.container_dishka import AppProvider
from app.shared.exceptions import BaseAppException
from app.shared.handlers import base_app_exception_handler
from app.shared.health import health_router
from app.shared.middleware import RequestLoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_app():
    app = FastAPI(title="Project Manager API", lifespan=lifespan)
    container = make_async_container(AppProvider(), FastapiProvider())
    setup_dishka(container=container, app=app)
    app.add_exception_handler(BaseAppException, base_app_exception_handler)

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(project_router)
    app.include_router(document_router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
