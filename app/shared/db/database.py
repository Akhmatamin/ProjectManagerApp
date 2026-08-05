from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
from app.shared.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
