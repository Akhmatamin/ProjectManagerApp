from libcloud.storage.drivers.s3 import S3StorageDriver
from sqlalchemy_file.storage import StorageManager
from libcloud.storage.types import ContainerDoesNotExistError
from app.shared.security import settings



def setup_storage():
    driver = S3StorageDriver(
        key=settings.AWS_ACCESS_KEY_ID,
        secret=settings.AWS_SECRET_ACCESS_KEY,
        region=settings.AWS_REGION,
    )

    container_name = settings.S3_BUCKET_NAME
    try:
        container = driver.get_container(container_name=container_name)
    except ContainerDoesNotExistError:
        container = driver.create_container(container_name=container_name)

    StorageManager.add_storage('default', container)