import os
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

if TYPE_CHECKING:
    from typing import Any

    from sqlalchemy.engine import Dialect

UTC = ZoneInfo("UTC")


class TZDateTime(TypeDecorator[datetime]):
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

    def process_result_value(self, value: "Any | None", dialect: "Dialect") -> "datetime | None":
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    def __repr__(self):
        return "TZDateTime()"


_last_timestamp_v7 = None
_last_counter_v7 = 0  # 42-bit counter


def uuid7():
    """Generate a UUID from a Unix timestamp in milliseconds and random bits.
    UUIDv7 objects feature monotonicity within a millisecond.
    """
    # --- 48 ---   -- 4 --   --- 12 ---   -- 2 --   --- 30 ---   - 32 -
    # unix_ts_ms | version | counter_hi | variant | counter_lo | random
    #
    # 'counter = counter_hi | counter_lo' is a 42-bit counter constructed
    # with Method 1 of RFC 9562, §6.2, and its MSB is set to 0.
    #
    # 'random' is a 32-bit random value regenerated for every new UUID.
    #
    # If multiple UUIDs are generated within the same millisecond, the LSB
    # of 'counter' is incremented by 1. When overflowing, the timestamp is
    # advanced and the counter is reset to a random 42-bit integer with MSB
    # set to 0.

    def get_counter_and_tail():
        rand = int.from_bytes(os.urandom(10))
        # 42-bit counter with MSB set to 0
        rand_counter = (rand >> 32) & 0x1FFFFFFFFFF
        # 32-bit random data
        rand_tail = rand & 0xFFFFFFFF
        return rand_counter, rand_tail

    global _last_timestamp_v7
    global _last_counter_v7

    import time

    nanoseconds = time.time_ns()
    timestamp_ms, _ = divmod(nanoseconds, 1_000_000)

    if _last_timestamp_v7 is None or timestamp_ms > _last_timestamp_v7:
        counter, tail = get_counter_and_tail()
    else:
        if timestamp_ms < _last_timestamp_v7:
            timestamp_ms = _last_timestamp_v7 + 1
        # advance the counter
        counter = _last_counter_v7 + 1
        if counter > 0x3FFFFFFFFFF:
            timestamp_ms += 1  # advance the timestamp
            counter, tail = get_counter_and_tail()
        else:
            tail = int.from_bytes(os.urandom(4))

    _last_timestamp_v7 = timestamp_ms
    _last_counter_v7 = counter

    int_uuid_7 = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    int_uuid_7 |= ((counter >> 30) & 0xFFF) << 64
    int_uuid_7 |= (counter & 0x3FFFFFFF) << 32
    int_uuid_7 |= tail & 0xFFFFFFFF
    # Set the variant to RFC 4122.
    int_uuid_7 &= ~(0xC000 << 48)
    int_uuid_7 |= 0x8000 << 48

    # Set the version number to 7.
    int_uuid_7 |= 0x7000 << 64
    return UUID(int=int_uuid_7)
