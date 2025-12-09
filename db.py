"""Quick manual connectivity check against the configured database."""

import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load local env vars when running outside containers.
if os.path.exists(".env.development"):
	load_dotenv(".env.development")

DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql+asyncpg://stories_user:StoriesDB1414@localhost:5432/stories_db",
)



async def check_connection() -> None:
	print(f"Attempting to connect using DATABASE_URL={DATABASE_URL}")
	engine = create_async_engine(DATABASE_URL, echo=False, future=True)
	try:
		async with engine.connect() as conn:
			result = await conn.execute(text("SELECT 1"))
			print("Database connection succeeded; SELECT 1 returned:", result.scalar())
	except Exception as exc:
		print("Database connection failed:", repr(exc))
	finally:
		await engine.dispose()


if __name__ == "__main__":
	asyncio.run(check_connection())


