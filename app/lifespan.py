import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager
from libcloud.storage.types import ContainerDoesNotExistError

UPLOAD_DIR = './uploaded_files'

def setup_storage():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    driver = LocalStorageDriver(UPLOAD_DIR)

    container_name = 'default'
    try:
        container = driver.get_container(container_name=container_name)
    except ContainerDoesNotExistError:
        container = driver.create_container(container_name=container_name)

    StorageManager.add_storage('default', container)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_storage()

    yield
