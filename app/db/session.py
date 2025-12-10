# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
from app.db.data_models import *
from dotenv import load_dotenv
from app.db.base import Base

ENV = os.getenv("APP_ENV", "development")  # default to development

if ENV == "development":
    load_dotenv(".env.development")
db_url = os.getenv("DATABASE_URL")


def AsyncSessionLocal():
    """Create a fresh engine and session each time to avoid event loop issues."""
    engine = create_async_engine(db_url, echo=False, future=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return factory()
