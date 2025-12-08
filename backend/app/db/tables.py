# app/db/tables.py
from sqlalchemy import (
    Table,
    Column,
    String,
    Text,
    DateTime,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from app.db.session import metadata

integration_connections = Table(
    "integration_connections",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    Column("company_id", UUID(as_uuid=True), nullable=False),
    Column("provider", String, nullable=False),          # 'stripe' | 'ga4'
    Column("external_account_id", Text, nullable=False), # acct_xxx or GA property id

    Column("access_token", Text, nullable=False),
    Column("refresh_token", Text),
    Column("scopes", ARRAY(Text)),                       # optional text[] column

    Column("status", String, nullable=False, server_default=text("'connected'")),
    Column("last_synced_at", DateTime(timezone=True)),

    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),

    schema="core",
)
