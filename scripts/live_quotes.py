"""Read-only live quote gateway for the public dashboard."""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from pathlib import Path


BASE_DATA_URL = "https://raw.githubusercontent.com/TonyTCFu/taiwan-stock-analysis/main/data/stock_data.json"
BASE_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "stock_data.json"
STOCK_CODES = ("2330", "2059", "2383", "3017", "2317")


def _float(value, default=0.0):
    if value in (None, "", "-"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value, default=0):
    if value in (None, "", "-"):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _fetch_twse_mis():
    query = "|".join(f"tse_{code}.tw" for code in STOCK_CODES)
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = {item.get("c"): item for item in payload.get("msgArray", []) if item.get("c")}
    if not rows:
        raise RuntimeError("TWSE MIS returned no quote rows")
    times = [item.get("t") for item in rows.values() if item.get("t")]
    return rows, {
        "status": "ok",
        "quote_count": len(rows),
        "retrieved_at": dt.datetime.now().isoformat(timespec="seconds"),
        "market_time": max(times) if times else None,
    }


def _fetch_shioaji():
    try:
        import shioaji as sj
    except ImportError:
        return {}, {"status": "unavailable", "detail": "shioaji package is not installed"}

    api_key = os.environ.get("SHIOAJI_API_KEY", "").strip()
    secret_key = os.environ.get("SHIOAJI_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        return {}, {"status": "unavailable", "detail": "Shioaji credentials are not configured"}

    api = sj.Shioaji(simulation=False)
    try:
        api.login(api_key=api_key, secret_key=secret_key)
        contracts = [api.Contracts.Stocks[code] for code in STOCK_CODES]
        snapshots = api.snapshots(contracts)
        by_code = {str(snapshot.code): snapshot for snapshot in snapshots}
        return by_code, {
            "status": "ok" if by_code else "unavailable",
            "quote_count": len(by_code),
            "retrieved_at": dt.datetime.now().isoformat(timespec="seconds"),
            "quote_mode": "snapshot",
        }
    except Exception as exc:
        return {}, {"status": "unavailable", "detail": f"{type(exc).__name__}: {exc}"}
    finally:
        try:
            api.logout()
        except Exception:
            pass


def _base_payload():
    if BASE_DATA_PATH.exists():
        return json.loads(BASE_DATA_PATH.read_text(encoding="utf-8"))
    request = urllib.request.Request(BASE_DATA_URL, headers={"User-Agent": "TaiwanStockDashboard/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_live_quotes():
    """Return the published dashboard payload with fresh read-only quote fields."""
    shioaji_data, shioaji_status = _fetch_shioaji()
    try:
        twse_data, twse_status = _fetch_twse_mis()
    except Exception as exc:
        twse_data = {}
        twse_status = {"status": "unavailable", "detail": f"{type(exc).__name__}: {exc}"}

    if not shioaji_data and not twse_data:
        raise RuntimeError("Neither Shioaji nor TWSE MIS returned quotes")

    payload = _base_payload()
    for stock in payload.get("stocks", []):
        code = str(stock.get("code", ""))
        snapshot = shioaji_data.get(code)
        mis = twse_data.get(code, {})
        shioaji_last = _float(getattr(snapshot, "close", None)) if snapshot else 0.0
        quote_source = "Shioaji Snapshot" if shioaji_last else "TWSE MIS"
        last_price = shioaji_last or _float(mis.get("z"))
        prev_close = (_float(getattr(snapshot, "yesterday_close", None)) if snapshot else 0.0) or _float(mis.get("y")) or last_price
        open_price = (_float(getattr(snapshot, "open", None)) if snapshot else 0.0) or _float(mis.get("o")) or last_price
        high_price = (_float(getattr(snapshot, "high", None)) if snapshot else 0.0) or _float(mis.get("h")) or last_price
        low_price = (_float(getattr(snapshot, "low", None)) if snapshot else 0.0) or _float(mis.get("l")) or last_price
        volume = (_int(getattr(snapshot, "total_volume", None)) if snapshot else 0) or _int(mis.get("v"))
        change = round(last_price - prev_close, 1) if prev_close else 0.0
        stock.update({
            "open_price": round(open_price, 1),
            "high_price": round(high_price, 1),
            "low_price": round(low_price, 1),
            "last_price": round(last_price, 1),
            "prev_close": round(prev_close, 1),
            "change": change,
            "change_pct": round(change / prev_close * 100, 2) if prev_close else 0.0,
            "volume": volume,
            "quote_source": quote_source,
            "quote_time": mis.get("t") if quote_source == "TWSE MIS" else shioaji_status.get("retrieved_at"),
        })

    if shioaji_data and twse_data:
        data_source = "Shioaji Snapshot (primary) + TWSE MIS cross-check"
    elif shioaji_data:
        data_source = "Shioaji Snapshot"
    else:
        data_source = "TWSE MIS fallback (Shioaji unavailable)"
    payload.update({
        "updated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": data_source,
        "sources": {
            "shioaji": shioaji_status,
            "twse_mis": twse_status,
            "selected_quote_source": data_source,
        },
    })
    return payload
