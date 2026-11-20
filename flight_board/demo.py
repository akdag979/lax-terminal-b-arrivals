from __future__ import annotations

from datetime import datetime, timedelta

from .airlabs import LOS_ANGELES
from .models import Arrival


def demo_arrivals(now: datetime | None = None) -> list[Arrival]:
    now = (now or datetime.now(LOS_ANGELES)).replace(second=0, microsecond=0)
    samples = [
        (-18, -7, "Istanbul", "IST", "TK", "Turkish Airlines", "TK 179", "active"),
        (-3, -3, "Tokyo Haneda", "HND", "AA", "American Airlines", "AA 26", "active"),
        (8, 1, "Seoul Incheon", "ICN", "YP", "Air Premia", "YP 102", "active"),
        (12, 12, "Hong Kong", "HKG", "CX", "Cathay Pacific", "CX 898", "scheduled"),
        (19, 29, "Shanghai Pudong", "PVG", "MU", "China Eastern", "MU 583", "active"),
        (25, 25, "Auckland", "AKL", "NZ", "Air New Zealand", "NZ 6", "cancelled"),
        (31, 27, "San Salvador", "SAL", "AV", "Avianca", "AV 522", "active"),
        (38, 38, "Guatemala City", "GUA", "AV", "Avianca", "AV 640", "scheduled"),
        (45, 57, "Amsterdam", "AMS", "KL", "KLM", "KL 601", "active"),
        (51, 43, "Panama City, PA", "PTY", "CM", "Copa Airlines", "CM 302", "active"),
        (60, 60, "Manila", "MNL", "PR", "Philippine Airlines", "PR 102", "scheduled"),
        (69, 64, "Nadi", "NAN", "FJ", "Fiji Airways", "FJ 810", "active"),
        (78, 78, "Doha", "DOH", "QR", "Qatar Airways", "QR 739", "scheduled"),
        (87, 95, "Dubai", "DXB", "EK", "Emirates", "EK 215", "active"),
        (98, 98, "Taipei", "TPE", "BR", "EVA Air", "BR 6", "scheduled"),
        (110, 118, "London Heathrow", "LHR", "BA", "British Airways", "BA 281", "active"),
    ]
    rows: list[Arrival] = []
    for index, (scheduled_delta, estimate_delta, origin, code, airline, name, flight, status) in enumerate(samples):
        scheduled = now + timedelta(minutes=scheduled_delta)
        estimated = now + timedelta(minutes=estimate_delta)
        rows.append(
            Arrival(
                scheduled=scheduled,
                estimated=estimated,
                actual=None,
                origin_code=code,
                origin_name=origin,
                airline_code=airline,
                airline_name=name,
                flight_number=flight,
                terminal="B",
                gate=str(130 + index),
                raw_status=status,
            )
        )
    return rows

