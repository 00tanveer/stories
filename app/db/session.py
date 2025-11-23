# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
from app.db.data_models import *
from dotenv import load_dotenv

load_dotenv(".env.development")
db_url = os.getenv("DATABASE_URL")
print(db_url)
engine = create_async_engine(db_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# async def init_db():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)
