#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from risk_dashboard import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_SHIOAJI_HOME,
    DEFAULT_UNIVERSE,
    load_universe,
    month_range,
    month_to_date,
    shioaji_credentials,
)


@dataclass
class DailyBar:
    close: float
    volume: float = 0.0
    amount: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="用 Shioaji 只读历史 K 线初始化 data/cache/，供 --offline-cache 在新路径复跑。"
    )
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE, help="资产池 CSV，默认 config/universe_tw.csv。")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="TWSE 兼容月缓存输出目录。")
    parser.add_argument("--start", default="2024-01", help="起始月份，格式 YYYY-MM。")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m"), help="结束月份，格式 YYYY-MM。")
    parser.add_argument("--symbols", help="只初始化指定代码，逗号分隔；默认使用 universe 全部资产。")
    parser.add_argument("--sleep", type=float, default=0.25, help="每次 Shioaji kbars 请求后的暂停秒数，避免请求过密。")
    parser.add_argument("--force", action="store_true", help="覆盖既有月份缓存。默认跳过已存在文件。")
    parser.add_argument("--dry-run", action="store_true", help="只列出将处理的标的和月份，不登录、不写文件。")
    return parser.parse_args()


def roc_date(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{int(year) - 1911}/{int(month):02d}/{int(day):02d}"


def to_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def kbars_to_daily(kbars: object) -> dict[str, DailyBar]:
    timestamps = list(getattr(kbars, "ts", []))
    closes = list(getattr(kbars, "Close", []))
    volumes = list(getattr(kbars, "Volume", []))
    amounts = list(getattr(kbars, "Amount", []))
    daily: dict[str, DailyBar] = {}
    for offset, ts_value in enumerate(timestamps):
        close = to_float(closes[offset] if offset < len(closes) else None)
        if close is None or close <= 0:
            continue
        day = str(np.datetime64(ts_value, "ns").astype("datetime64[D]"))
        volume = to_float(volumes[offset] if offset < len(volumes) else None) or 0.0
        amount = to_float(amounts[offset] if offset < len(amounts) else None) or close * volume
        if day not in daily:
            daily[day] = DailyBar(close=close)
        daily[day].close = close
        daily[day].volume += volume
        daily[day].amount += amount
    return daily


def twse_payload(symbol: str, month: str, daily: dict[str, DailyBar]) -> dict[str, object]:
    rows = []
    for trade_date in sorted(daily):
        if trade_date.replace("-", "")[:6] != month:
            continue
        bar = daily[trade_date]
        rows.append(
            [
                roc_date(trade_date),
                str(int(round(bar.volume))),
                str(int(round(bar.amount))),
                "",
                "",
                "",
                f"{bar.close:.4f}".rstrip("0").rstrip("."),
                "",
                "",
            ]
        )
    return {
        "stat": "OK" if rows else "很抱歉，沒有符合條件的資料!",
        "date": f"{month}01",
        "title": f"{symbol} Shioaji daily cache",
        "fields": ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數"],
        "data": rows,
        "notes": ["Generated from Shioaji kbars by scripts/init_shioaji_market_cache.py"],
    }


def date_chunks(start_date: str, end_date: str, max_days: int = 30) -> list[tuple[str, str]]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    chunks: list[tuple[str, str]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=max_days - 1), end)
        chunks.append((cursor.isoformat(), chunk_end.isoformat()))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def fetch_month_daily(api: object, contract: object, month: str) -> dict[str, DailyBar]:
    merged: dict[str, DailyBar] = {}
    for start_date, end_date in date_chunks(month_to_date(month, is_end=False), month_to_date(month, is_end=True)):
        merged.update(kbars_to_daily(api.kbars(contract=contract, start=start_date, end=end_date)))
    return merged


def selected_assets(universe: Path, symbols: str | None):
    assets = load_universe(universe)
    if not symbols:
        return assets
    wanted = {item.strip() for item in symbols.split(",") if item.strip()}
    return [asset for asset in assets if asset.symbol in wanted]


def main() -> None:
    args = parse_args()
    assets = selected_assets(args.universe, args.symbols)
    months = month_range(args.start, args.end)
    pending = [
        (asset, month)
        for asset in assets
        for month in months
        if args.force or not (args.cache_dir / f"{asset.symbol}_{month}.json").exists()
    ]
    print(f"assets={len(assets)} months={len(months)} pending_files={len(pending)}")
    if args.dry_run:
        for asset, month in pending[:40]:
            print(f"DRY_RUN {asset.symbol} {month}")
        if len(pending) > 40:
            print(f"... {len(pending) - 40} more")
        return

    os.environ.setdefault("SJ_HOME_PATH", str(DEFAULT_SHIOAJI_HOME))
    DEFAULT_SHIOAJI_HOME.mkdir(parents=True, exist_ok=True)
    DEFAULT_SHIOAJI_HOME.chmod(0o700)

    try:
        import shioaji as sj
    except Exception as exc:
        raise SystemExit(f"Shioaji 套件不可用，请先安装：{exc}") from exc

    api_key, secret_key = shioaji_credentials()
    api = sj.Shioaji()
    fetched: dict[tuple[str, str], int] = {}
    failed: dict[str, list[str]] = defaultdict(list)
    logged_in = False
    try:
        api.login(api_key=api_key, secret_key=secret_key)
        logged_in = True
        args.cache_dir.mkdir(parents=True, exist_ok=True)
        total = len(pending)
        for index, (asset, month) in enumerate(pending, start=1):
            output = args.cache_dir / f"{asset.symbol}_{month}.json"
            print(f"[{index}/{total}] {asset.symbol} {month}", flush=True)
            try:
                contract = api.Contracts.Stocks[asset.symbol]
                daily = fetch_month_daily(api, contract, month)
                payload = twse_payload(asset.symbol, month, daily)
                temp_output = output.with_suffix(".json.tmp")
                temp_output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                temp_output.replace(output)
                fetched[(asset.symbol, month)] = len(payload.get("data") or [])
            except Exception as exc:
                failed[asset.symbol].append(f"{month}: {exc}")
            time.sleep(max(args.sleep, 0.0))
    finally:
        logout = getattr(api, "logout", None)
        if logged_in and callable(logout):
            logout()

    ready = sum(1 for rows in fetched.values() if rows > 0)
    empty = sum(1 for rows in fetched.values() if rows == 0)
    print(f"cache_init_done written={len(fetched)} ready={ready} empty={empty} failed={sum(len(v) for v in failed.values())}")
    if failed:
        for symbol, errors in failed.items():
            print(f"FAILED {symbol}: {'; '.join(errors[:3])}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
