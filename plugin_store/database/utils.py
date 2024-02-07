from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect

UTC = ZoneInfo("UTC")


class TZDateTime(TypeDecorator):
    """
    A DateTime type which can only store tz-aware DateTimes.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: "datetime | None", dialect: "Dialect"):
        if isinstance(value, datetime):
            if value.tzinfo is None:
                raise ValueError(f"{value!r} must be TZ-aware")
            return value.astimezone(UTC)
        return value

    def process_result_value(self, value: "datetime", dialect: "Dialect") -> "datetime | None":
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def __repr__(self):
        return "TZDateTime()"
