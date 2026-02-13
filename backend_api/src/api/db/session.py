from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.core.config import get_settings

settings = get_settings()

# Use SQLAlchemy engine + sessionmaker (sync) for simplicity in this demo.
engine = create_engine(settings.postgres_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db():
    """FastAPI dependency that yields a SQLAlchemy session and closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
