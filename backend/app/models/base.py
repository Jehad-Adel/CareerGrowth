import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Integer, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# Native JSONB on Postgres, plain JSON on SQLite so tests can run in memory.
JSONType = JSON().with_variant(JSONB(), "postgresql")

# BigInteger on Postgres for high-volume append-only tables; plain Integer
# on SQLite, because SQLite's implicit ROWID-alias autoincrement only
# applies to columns typed exactly Integer, not BigInteger.
BigIntegerType = Integer().with_variant(BigInteger(), "postgresql")


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
