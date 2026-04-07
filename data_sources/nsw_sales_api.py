from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)

NSW_VALUATION_LAYER_URL = (
    "https://maps.six.nsw.gov.au/arcgis/rest/services/public/Valuation/MapServer/1/query"
)

DEFAULT_TARGET_SUBURBS = [
    "Beecroft",
    "Normanhurst",
    "Pennant Hills",
    "Thornleigh",
]


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "property-intelligence-au/1.0"})
    return session


def escape_sql(value: str) -> str:
    return value.replace("'", "''")


def build_where_clause(suburb: str, years_back: int = 8, mode: str = "all-property-types") -> str:
    suburb_value = escape_sql(suburb.upper())
    clauses = [
        f"suburb = '{suburb_value}' "
        f"AND price > 0 "
    ]

    if mode == "house-only":
        clauses.append("AND strata = 0 ")
        clauses.append("AND deal_props = 1")
    elif mode == "single-title":
        clauses.append("AND deal_props = 1")
    elif mode == "all-property-types":
        pass
    else:
        raise ValueError(f"Unsupported NSW sales mode: {mode}")

    return "".join(clauses)


def cutoff_date(years_back: int = 8) -> date:
    current_year = date.today().year
    start_year = current_year - years_back + 1
    return date(start_year, 1, 1)


def parse_sale_date(value) -> date | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value) / 1000).date()
        except Exception:  # noqa: BLE001
            return None

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text) / 1000).date()
        except Exception:  # noqa: BLE001
            return None

    return None


def request_json(
    session: requests.Session,
    params: Dict[str, object],
    timeout=(20, 120),
    max_attempts: int = 5,
) -> Dict[str, object]:
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(NSW_VALUATION_LAYER_URL, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
            return payload
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(min(2 ** attempt, 12))

    raise RuntimeError(f"NSW sales request failed: {last_error}") from last_error


def fetch_count(session: requests.Session, suburb: str, years_back: int = 8, mode: str = "all-property-types") -> int:
    params = {
        "where": build_where_clause(suburb, years_back=years_back, mode=mode),
        "returnCountOnly": "true",
        "f": "json",
    }
    payload = request_json(session, params)
    return int(payload.get("count", 0))


def fetch_batch(
    session: requests.Session,
    suburb: str,
    offset: int,
    page_size: int,
    years_back: int = 8,
    mode: str = "all-property-types",
) -> List[Dict[str, object]]:
    params = {
        "where": build_where_clause(suburb, years_back=years_back, mode=mode),
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": page_size,
        "orderByFields": "sale_date DESC",
    }
    payload = request_json(session, params)
    features = payload.get("features", [])
    rows = []
    for feature in features:
        attrs = feature.get("attributes") or {}
        if attrs:
            rows.append(attrs)
    return rows


def fetch_sales_rows(
    suburbs: Iterable[str] | None = None,
    years_back: int = 8,
    page_size: int = 200,
    mode: str = "all-property-types",
) -> List[Dict[str, object]]:
    suburbs = list(suburbs or DEFAULT_TARGET_SUBURBS)
    session = build_session()
    collected: List[Dict[str, object]] = []
    min_sale_date = cutoff_date(years_back)

    for suburb in suburbs:
        total = fetch_count(session, suburb, years_back=years_back, mode=mode)
        print(f"Downloading {suburb} [{mode}] - up to {total} candidate rows")

        for offset in range(0, total, page_size):
            start = offset + 1
            end = min(offset + page_size, total)
            print(f"  fetching rows {start}-{end}")
            rows = fetch_batch(
                session=session,
                suburb=suburb,
                offset=offset,
                page_size=page_size,
                years_back=years_back,
                mode=mode,
            )
            if not rows:
                break

            recent_rows = []
            for row in rows:
                sale_dt = parse_sale_date(row.get("sale_date"))
                if sale_dt is None or sale_dt >= min_sale_date:
                    recent_rows.append(row)

            collected.extend(recent_rows)

            last_row_date = parse_sale_date(rows[-1].get("sale_date"))
            if last_row_date is not None and last_row_date < min_sale_date:
                print(f"  stopping early for {suburb}: reached sales older than {min_sale_date.isoformat()}")
                break

    return collected
