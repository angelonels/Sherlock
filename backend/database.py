import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv


load_dotenv()


user = os.getenv("POSTGRES_USER", "sherlock_admin")
password = os.getenv("POSTGRES_PASSWORD", "change_me")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db_name = os.getenv("POSTGRES_DB", "sherlock_db")

DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


engine = create_async_engine(DATABASE_URL, echo=False)


AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autoflush=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
