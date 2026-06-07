"""Conexión a base de datos async con SQLAlchemy 2.0.

- Engine async creado en lifespan (no en import time).
- async_sessionmaker como factory de sesiones.
- Base declarativa para modelos ORM.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base declarativa para todos los modelos ORM del proyecto."""
    pass


engine = None
AsyncSessionLocal = None


def init_db(database_url: str) -> None:
    """Inicializa el engine y la factory de sesiones."""
    global engine, AsyncSessionLocal
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
