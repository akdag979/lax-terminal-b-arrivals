from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Arrival:
    """Normalized arrival record used by the display layer."""

    scheduled: datetime
    estimated: datetime | None
    actual: datetime | None
    origin_code: str
    origin_name: str
    airline_code: str
    airline_name: str
    flight_number: str
    terminal: str
    gate: str
    raw_status: str

    @property
    def best_time(self) -> datetime:
        return self.actual or self.estimated or self.scheduled

    @property
    def identity(self) -> tuple[str, str, str]:
        return (
            self.origin_code,
            self.scheduled.strftime("%Y-%m-%dT%H:%M"),
            self.flight_number,
        )

