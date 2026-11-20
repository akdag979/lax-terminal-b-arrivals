from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import requests

from .models import Arrival

AIRLABS_SCHEDULES_URL = "https://airlabs.co/api/v9/schedules"
LOS_ANGELES = ZoneInfo("America/Los_Angeles")
REQUEST_FIELDS = ",".join(
    (
        "airline_iata",
        "flight_iata",
        "flight_number",
        "cs_airline_iata",
        "cs_flight_iata",
        "cs_flight_number",
        "dep_iata",
        "arr_iata",
        "arr_terminal",
        "arr_gate",
        "arr_time",
        "arr_time_ts",
        "arr_estimated",
        "arr_estimated_ts",
        "arr_actual",
        "arr_actual_ts",
        "status",
    )
)

AIRLINE_NAMES = {
    "3U": "Sichuan Airlines",
    "AA": "American Airlines",
    "AF": "Air France",
    "AM": "Aeromexico",
    "AS": "Alaska Airlines",
    "AT": "Royal Air Maroc",
    "AV": "Avianca",
    "AY": "Finnair",
    "AZ": "ITA Airways",
    "BA": "British Airways",
    "BF": "French Bee",
    "BR": "EVA Air",
    "CA": "Air China",
    "CI": "China Airlines",
    "CM": "Copa Airlines",
    "CX": "Cathay Pacific",
    "EK": "Emirates",
    "ET": "Ethiopian Airlines",
    "EY": "Etihad Airways",
    "FJ": "Fiji Airways",
    "HU": "Hainan Airlines",
    "IB": "Iberia",
    "JL": "Japan Airlines",
    "KE": "Korean Air",
    "KL": "KLM",
    "LH": "Lufthansa",
    "LO": "LOT Polish Airlines",
    "LY": "EL AL",
    "NH": "ANA",
    "NZ": "Air New Zealand",
    "OZ": "Asiana Airlines",
    "PR": "Philippine Airlines",
    "QF": "Qantas",
    "QR": "Qatar Airways",
    "SK": "SAS",
    "SQ": "Singapore Airlines",
    "TK": "Turkish Airlines",
    "TN": "Air Tahiti Nui",
    "UA": "United Airlines",
    "VS": "Virgin Atlantic",
    "Y4": "Volaris",
    "YP": "Air Premia",
    "ZG": "ZIPAIR",
}

ORIGIN_OVERRIDES = {
    "AMS": "Amsterdam",
    "AKL": "Auckland",
    "BNE": "Brisbane",
    "CDG": "Paris Charles de Gaulle",
    "DFW": "Dallas-Ft. Worth",
    "DOH": "Doha",
    "DXB": "Dubai",
    "EZE": "Buenos Aires",
    "FCO": "Rome Fiumicino",
    "GDL": "Guadalajara",
    "GRU": "Sao Paulo",
    "HKG": "Hong Kong",
    "HND": "Tokyo Haneda",
    "ICN": "Seoul Incheon",
    "IST": "Istanbul",
    "KIX": "Osaka Kansai",
    "LHR": "London Heathrow",
    "MEL": "Melbourne",
    "MEX": "Mexico City",
    "MNL": "Manila",
    "NAN": "Nadi",
    "NRT": "Tokyo Narita",
    "ORD": "Chicago O'Hare",
    "PTY": "Panama City, PA",
    "PVG": "Shanghai Pudong",
    "SAL": "San Salvador",
    "SCL": "Santiago",
    "SYD": "Sydney",
    "TPE": "Taipei",
    "YVR": "Vancouver",
}


class AirLabsError(RuntimeError):
    """Raised for transport errors and AirLabs error responses."""


def fetch_schedules(api_key: str, timeout: float = 15.0) -> list[dict[str, Any]]:
    params = {
        "api_key": api_key,
        "arr_iata": "LAX",
        # Free AirLabs keys return at most 50 schedule rows.  Filtering out
        # completed/cancelled flights keeps that page centered on flights that
        # are still relevant to an arrivals display instead of earlier rows.
        "status": "scheduled,active",
        "limit": 50,
        "_fields": REQUEST_FIELDS,
    }
    try:
        response = requests.get(AIRLABS_SCHEDULES_URL, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise AirLabsError(f"Unable to retrieve AirLabs schedules: {exc}") from exc

    if isinstance(payload, Mapping) and payload.get("error"):
        error = payload["error"]
        if isinstance(error, Mapping):
            code = error.get("code", "api_error")
            message = error.get("message", "AirLabs rejected the request")
            raise AirLabsError(f"{code}: {message}")
        raise AirLabsError(str(error))

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, Mapping):
        records = payload.get("response", payload.get("data", []))
    else:
        records = []

    if not isinstance(records, list):
        raise AirLabsError("AirLabs returned an unexpected schedule format")
    return [record for record in records if isinstance(record, dict)]


def _parse_local_time(record: Mapping[str, Any], stem: str) -> datetime | None:
    timestamp = record.get(f"{stem}_ts")
    if timestamp not in (None, ""):
        try:
            return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).astimezone(LOS_ANGELES)
        except (TypeError, ValueError, OSError):
            pass

    value = record.get(stem)
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=LOS_ANGELES)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=LOS_ANGELES)
        return parsed.astimezone(LOS_ANGELES)
    except ValueError:
        return None


def is_terminal_b(terminal: Any, gate: Any) -> bool:
    normalized = re.sub(r"[^A-Z0-9]", "", str(terminal or "").upper())
    terminal_aliases = {
        "B",
        "TB",
        "TBIT",
        "TERMINALB",
        "TOMBRADLEY",
        "TOMBRADLEYINTERNATIONAL",
        "TOMBRADLEYINTERNATIONALTERMINAL",
    }
    if normalized in terminal_aliases:
        return True

    match = re.search(r"\d{3}", str(gate or ""))
    if not match:
        return False
    gate_number = int(match.group())
    return 130 <= gate_number <= 235


def _load_airports() -> Mapping[str, Mapping[str, Any]]:
    try:
        import airportsdata

        return airportsdata.load("IATA")
    except (ImportError, OSError, ValueError):
        return {}


def origin_name(code: str, airports: Mapping[str, Mapping[str, Any]]) -> str:
    if code in ORIGIN_OVERRIDES:
        return ORIGIN_OVERRIDES[code]
    airport = airports.get(code, {})
    city = str(airport.get("city") or "").strip()
    if city:
        return city
    name = str(airport.get("name") or "").strip()
    if name:
        return re.sub(r"\s+(International\s+)?Airport$", "", name, flags=re.IGNORECASE)
    return code or "Unknown"


def normalize_schedules(
    records: Iterable[Mapping[str, Any]],
    *,
    now: datetime | None = None,
    airports: Mapping[str, Mapping[str, Any]] | None = None,
    past_window: timedelta = timedelta(minutes=30),
    future_window: timedelta = timedelta(hours=4),
) -> list[Arrival]:
    now = (now or datetime.now(LOS_ANGELES)).astimezone(LOS_ANGELES)
    airports = airports if airports is not None else _load_airports()
    earliest = now - past_window
    latest = now + future_window
    arrivals: list[Arrival] = []

    for record in records:
        if str(record.get("arr_iata") or "LAX").upper() != "LAX":
            continue
        terminal = str(record.get("arr_terminal") or "").strip()
        gate = str(record.get("arr_gate") or "").strip()
        if not is_terminal_b(terminal, gate):
            continue

        scheduled = _parse_local_time(record, "arr_time")
        if scheduled is None or not (earliest <= scheduled <= latest):
            continue
        estimated = _parse_local_time(record, "arr_estimated")
        actual = _parse_local_time(record, "arr_actual")

        # AirLabs cs_* fields identify the operating flight for codeshare rows.
        airline_code = str(
            record.get("cs_airline_iata") or record.get("airline_iata") or ""
        ).strip().upper()
        flight_number = str(
            record.get("cs_flight_iata")
            or record.get("flight_iata")
            or (
                f"{airline_code}{record.get('cs_flight_number') or record.get('flight_number')}"
                if airline_code
                else record.get("flight_number") or ""
            )
        ).strip().upper()
        origin_code = str(record.get("dep_iata") or "").strip().upper()

        arrivals.append(
            Arrival(
                scheduled=scheduled,
                estimated=estimated,
                actual=actual,
                origin_code=origin_code,
                origin_name=origin_name(origin_code, airports),
                airline_code=airline_code,
                airline_name=AIRLINE_NAMES.get(airline_code, airline_code or "Airline"),
                flight_number=flight_number or "—",
                terminal=terminal,
                gate=gate,
                raw_status=str(record.get("status") or "scheduled").lower(),
            )
        )

    deduplicated: dict[tuple[str, str, str], Arrival] = {}
    for arrival in sorted(arrivals, key=lambda item: item.scheduled):
        existing = deduplicated.get(arrival.identity)
        if existing is None or (arrival.actual and not existing.actual):
            deduplicated[arrival.identity] = arrival
    return sorted(deduplicated.values(), key=lambda item: (item.scheduled, item.flight_number))


def fetch_arrivals(api_key: str, *, now: datetime | None = None) -> list[Arrival]:
    return normalize_schedules(fetch_schedules(api_key), now=now)

