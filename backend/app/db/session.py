# app/db/session.py
from sqlalchemy import create_engine, MetaData

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,   # set True while debugging
)

metadata = MetaData()
