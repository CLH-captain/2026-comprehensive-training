from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class BigIntIdMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
