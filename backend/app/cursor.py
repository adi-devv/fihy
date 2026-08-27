import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timezone


class InvalidCursor(ValueError):
    pass


@dataclass(frozen=True)
class NearbyCursor:
    """Keyset position: last row's squared distance and id."""

    squared_distance: float
    issue_id: str

    def encode(self) -> str:
        raw = json.dumps(
            {"d": self.squared_distance, "i": self.issue_id},
            separators=(",", ":"),
        ).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @classmethod
    def decode(cls, value: str) -> "NearbyCursor":
        padded = value + "=" * (-len(value) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded))
            return cls(
                squared_distance=float(payload["d"]), issue_id=str(payload["i"])
            )
        except (
            binascii.Error,
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise InvalidCursor("That page link is no longer valid.") from exc


@dataclass(frozen=True)
class TimeCursor:
    """Keyset position for newest-first lists: last row's timestamp and id.

    The timestamp is an ISO string rather than an epoch float because a float
    cannot round-trip microseconds at current timestamps, and a page boundary
    that shifts by a microsecond drops or repeats a row.
    """

    @staticmethod
    def moment(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def parse(value: str) -> datetime:
        return datetime.fromisoformat(value)

    created_at: str
    row_id: str

    def encode(self) -> str:
        raw = json.dumps(
            {"t": self.created_at, "i": self.row_id}, separators=(",", ":")
        ).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    @classmethod
    def decode(cls, value: str) -> "TimeCursor":
        padded = value + "=" * (-len(value) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded))
            return cls(created_at=str(payload["t"]), row_id=str(payload["i"]))
        except (
            binascii.Error,
            UnicodeDecodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise InvalidCursor("That page link is no longer valid.") from exc
