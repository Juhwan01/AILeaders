from typing import Optional
from .config import DefaultConfig

from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()
DBSessionLocal: Optional[sessionmaker] = None
db_engine: Optional[Engine] = None
db_session: Optional[Session] = None


def init_db(config: DefaultConfig) -> None:
    global DBSessionLocal, db_engine, db_session

    postgres_endpoint = config.postgresql_endpoint
    postgres_port = config.postgresql_port
    postgres_table = config.postgresql_table
    postgres_user = config.postgresql_user
    postgres_password = config.postgresql_password

    db_url = (
        "postgresql+asyncpg://"
        + f"{postgres_user}:{postgres_password}"
        + f"@{postgres_endpoint}:{postgres_port}/{postgres_table}"
    )

    db_engine = create_async_engine(db_url)

    DBSessionLocal = sessionmaker(
        bind=db_engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def provide_session():
    if DBSessionLocal is None:
        raise ImportError("You need to call init_db before this function")

    async with sessionmaker(
        bind=db_engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )() as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        else:
            session.commit()
        finally:
            session.close()
