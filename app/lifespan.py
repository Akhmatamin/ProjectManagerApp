from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.shared.storage import setup_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_storage()

    yield
