import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.auth.router import auth_router
from app.shared.container import Container
from app.shared.exceptions import BaseAppException
from app.shared.handlers import base_app_exception_handler
from app.projects.router import project_router, projects_router, document_router
from app.lifespan import lifespan


def create_app():
    container = Container()
    app = FastAPI(title="Project Manager API", lifespan=lifespan)
    app.state.container = container
    app.add_exception_handler(BaseAppException, base_app_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(projects_router)
    app.include_router(project_router)
    app.include_router(document_router)
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)