"""SQLAlchemy engine and session configuration for CONOPS One Source."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://conops:conops@localhost:5432/conops_one_source",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Yield a database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in the ORM models."""
    Base.metadata.create_all(bind=engine)
