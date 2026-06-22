from __future__ import annotations

import argparse
import csv
import hashlib
import html
import os
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UNIVERSE = ROOT / "config" / "universe_tw.csv"
DEFAULT_OUTPUT = ROOT / "dashboard" / "index.html"
DEFAULT_CACHE_DIR = ROOT / "data" / "cache"
DEFAULT_MATRIX_CACHE_DIR = ROOT / "data" / "matrix_cache"
DEFAULT_SHIOAJI_HOME = ROOT / ".shioaji.runtime"
DEFAULT_MODEL_OUTPUT = ROOT / "data" / "model_portfolio_latest.csv"
DEFAULT_SIMULATED_POSITIONS_OUTPUT = ROOT / "data" / "simulated_positions_latest.csv"
DEFAULT_MODEL_BUILD_DATE = "2026-06-03"
ANNUALIZATION_DAYS = 252
MIN_OBSERVATIONS = 60
MAX_WEIGHT = 0.25
REQUEST_TIMEOUT = 15
SHIOAJI_KBARS_RETRIES = 3
DEFAULT_REBALANCE_WINDOW = 60
DEFAULT_REBALANCE_STEP = 7
DEFAULT_MODEL_CASH = 500_000.0
DEFAULT_MODEL_INVEST_RATIO = 0.75
DEFAULT_DASHBOARD_UPDATE_TIME_LABEL = "每日 13:45"
MODEL_LOOKBACK_YEARS = 5
MODEL_FALLBACK_LOOKBACK_YEARS = 2


@dataclass(frozen=True)
class Asset:
    symbol: str
    name: str
    asset_type: str
    market: str
    sector: str = ""
    theme: str = ""
    ai_supply_chain: bool = False


@dataclass(frozen=True)
class DataIssue:
    symbol: str
    message: str


@dataclass(frozen=True)
class PriceData:
    dates: list[str]
    symbols: list[str]
    prices: np.ndarray
    volumes: np.ndarray | None = None
    amounts: np.ndarray | None = None


@dataclass(frozen=True)
class MarketBar:
    close: float
    volume: float | None = None
    amount: float | None = None


@dataclass(frozen=True)
class BacktestMetrics:
    annual_return: float
    annual_volatility: float
    max_drawdown: float
    average_turnover: float
    cumulative_turnover: float


@dataclass(frozen=True)
class BacktestResult:
    dates: list[str]
    rebalance_dates: list[str]
    sample_curve: np.ndarray
    shrink_curve: np.ndarray
    sample_returns: np.ndarray
    shrink_returns: np.ndarray
    sample_turnovers: np.ndarray
    shrink_turnovers: np.ndarray
    sample_metrics: BacktestMetrics
    shrink_metrics: BacktestMetrics
    window: int
    step: int
    rebalance_count: int


@dataclass(frozen=True)
class ModelPosition:
    symbol: str
    name: str
    price: float | None
    max_drawdown: float | None
    annual_volatility: float | None
    drawdown_days: int | None
    risk_score: float | None
    price_factor_score: float | None
    industry_ai_score: float | None
    macro_external_score: float | None
    composite_score: float | None
    trend_strength_score: float | None
    target_weight: float
    target_value: float
    shares: int | None
    market_value: float | None
    buy_commission: float | None = None
    buy_tax: float | None = None
    total_buy_cost: float | None = None
    future_sell_tax: float | None = None
    current_price: float | None = None
    current_market_value: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_pct: float | None = None
    current_volume: float | None = None
    current_total_volume: float | None = None
    current_total_amount: float | None = None


@dataclass(frozen=True)
class ModelPortfolio:
    build_date: str
    analysis_start_date: str
    analysis_end_date: str
    execution_date: str
    execution_price_status: str
    method: str
    ai_tilt: str | None
    lookback_years: int
    initial_cash: float
    invest_ratio: float
    cash_reserve: float
    invested_value: float
    remaining_cash: float
    total_value: float
    positions: list[ModelPosition]
    output_path: Path
    dated_output_path: Path | None
    market_date: str | None = None
    market_mode: str | None = None
    market_quote_time: str | None = None


@dataclass(frozen=True)
class TradeSignal:
    symbol: str
    name: str
    trade_id: str
    trigger_code: str
    action: str
    status: str
    reason: str
    latest_price: float
    cost_price: float | None
    ma20: float | None
    ma60: float | None
    rsi14: float | None
    volume_ratio: float | None
    average_amount20: float | None
    factor_score: float
    persistence_days: int
    return_since_entry: float | None
    proposed_shares: int | None


@dataclass(frozen=True)
class SimulatedTradeBatchStatus:
    batch_seq: str
    label: str
    trade_count: int
    symbols: tuple[str, ...]
    actions: tuple[str, ...]
    is_legacy: bool


@dataclass(frozen=True)
class SimulatedTradeExecutionSummary:
    trade_date: str
    trade_count: int
    buy_count: int
    sell_count: int
    symbols: tuple[str, ...]
    details: tuple[str, ...]
    source_path: Path | None


@dataclass(frozen=True)
class MarketSnapshotUpdate:
    path: Path
    market_date: str
    market_mode: str
    quote_time: str
    quote_count: int
    missing_count: int


@dataclass(frozen=True)
class TaiexSnapshot:
    trade_date: str
    open_index: float
    high_index: float
    low_index: float
    close_index: float
    change_points: float
    change_pct: float


@dataclass(frozen=True)
class FactorScoreBreakdown:
    price_factor_score: float
    industry_ai_score: float
    macro_external_score: float
    composite_score: float
    trend_strength_score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成台股稳健投资组合风险仪表盘。")
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE, help="资产池 CSV 路径。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="仪表盘 HTML 输出路径。")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="行情缓存目录。")
    parser.add_argument("--start", default="2021-01", help="起始月份，格式 YYYY-MM。")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m"), help="结束月份，格式 YYYY-MM。")
    parser.add_argument("--allow-stale-cache", action="store_true", help="接口失败时允许使用任意可用缓存。")
    parser.add_argument("--offline-cache", action="store_true", help="只读取本地缓存，不请求 TWSE。")
    parser.add_argument("--rebalance-window", type=int, default=DEFAULT_REBALANCE_WINDOW, help="再平衡回测的滚动估计窗口，单位为交易日。")
    parser.add_argument("--rebalance-step", type=int, default=DEFAULT_REBALANCE_STEP, help="再平衡间隔，单位为交易日。")
    parser.add_argument("--model-portfolio", action="store_true", help="生成手动模拟建仓模型盘，不会下单。")
    parser.add_argument("--model-build-date", default=DEFAULT_MODEL_BUILD_DATE, help="模型盘建仓日，格式 YYYY-MM-DD。")
    parser.add_argument(
        "--model-method",
        choices=("drawdown-risk", "shrink-minvar", "multi-factor-shrink"),
        default="drawdown-risk",
        help="模型盘权重方法。multi-factor-shrink 使用台股价格/量能多因子预期收益搭配收缩协方差。",
    )
    parser.add_argument("--model-cash", type=float, default=DEFAULT_MODEL_CASH, help="模型盘初始虚拟资金，单位为台币。")
    parser.add_argument("--model-invest-ratio", type=float, default=DEFAULT_MODEL_INVEST_RATIO, help="模型盘目标建仓比例，例如 0.75 表示使用 75% 资金建仓。")
    parser.add_argument(
        "--ai-tilt",
        choices=("none", "moderate", "strong"),
        default="none",
        help="仅用于 multi-factor-shrink：提高 AI 供应链目标权重。moderate 约 33%，strong 约 38%。",
    )
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL_OUTPUT, help="模型盘 CSV 输出路径。")
    parser.add_argument("--model-execution-orders", type=Path, help="手动建仓执行单 CSV；未指定时会自动读取 data/manual_build_orders_建仓日.csv。")
    parser.add_argument("--model-market-values", type=Path, help="模型盘当日市值/盈亏 CSV；未指定时会自动读取 data/model_portfolio_market_建仓日.csv。")
    parser.add_argument("--execute-simulated-trades", action="store_true", help="将本轮模拟盘建议单落账为模拟成交，并更新模拟持仓 CSV；不会连接券商。")
    parser.add_argument("--simulated-trades-output", type=Path, help="模拟成交 CSV 路径；落账时写入，Dashboard 验证时可读取指定路径。")
    parser.add_argument("--simulated-positions-output", type=Path, help="最新模拟持仓 CSV 输出路径；仅用于 --execute-simulated-trades。")
    parser.add_argument(
        "--simulated-trade-batch-seq",
        type=normalize_simulated_trade_batch_seq,
        default="01",
        help="模拟成交批次号，默认 01；显式传 02、03 等才允许同日同标的同方向分批。",
    )
    parser.add_argument("--update-daily-market", action="store_true", help="使用 Shioaji snapshot 更新每日模型盘市值檔，不会下单。")
    parser.add_argument("--market-date", default=date.today().isoformat(), help="每日行情日期，格式 YYYY-MM-DD。")
    parser.add_argument("--market-mode", choices=("intraday", "close"), default="intraday", help="每日行情模式：intraday 为盘中暂估，close 为收盘定稿。")
    parser.add_argument(
        "--market-source",
        choices=("file", "shioaji", "public-close"),
        default="file",
        help="模型盘市值来源。file 读取既有 CSV；shioaji 读取盘中快照；public-close 用最新公开收盘价重建。",
    )
    parser.add_argument(
        "--data-source",
        choices=("twse", "shioaji", "auto"),
        default="twse",
        help="行情来源。auto 会优先使用 Shioaji，失败后回退 TWSE。",
    )
    return parser.parse_args()


def normalize_simulated_trade_batch_seq(value: str) -> str:
    normalized = str(value).strip()
    if normalized.isdigit() and 1 <= len(normalized) <= 2:
        normalized = normalized.zfill(2)
    if len(normalized) != 2 or not normalized.isdigit() or normalized == "00":
        raise ValueError("--simulated-trade-batch-seq 必须是 01 到 99 的两位数字。")
    return normalized


def month_range(start: str, end: str) -> list[str]:
    start_dt = datetime.strptime(start, "%Y-%m")
    end_dt = datetime.strptime(end, "%Y-%m")
    months: list[str] = []
    year = start_dt.year
    month = start_dt.month
    while (year, month) <= (end_dt.year, end_dt.month):
        months.append(f"{year}{month:02d}")
        month += 1
        if month > 12:
            year += 1
            month = 1
    return months


def load_universe(path: Path) -> list[Asset]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"symbol", "name", "type", "market"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path} 必须包含字段：symbol,name,type,market")
        return [
            Asset(
                symbol=row["symbol"].strip(),
                name=row["name"].strip(),
                asset_type=row["type"].strip(),
                market=row["market"].strip(),
                sector=(row.get("sector") or "").strip(),
                theme=(row.get("theme") or "").strip(),
                ai_supply_chain=(row.get("ai_supply_chain") or "").strip().lower() in {"1", "true", "yes", "y"},
            )
            for row in reader
            if row.get("symbol")
        ]


def twse_url(symbol: str, month: str) -> str:
    return (
        "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
        f"?date={month}01&stockNo={symbol}&response=json"
    )


def twse_taiex_history_url(target_date: str) -> str:
    compact_date = target_date.replace("-", "")
    return f"https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={compact_date}&response=json"


def parse_twse_number(value: str) -> float:
    return float((value or "0").replace(",", "").strip())


def twse_roc_date_to_iso(value: str) -> str:
    year_text, month_text, day_text = value.split("/")
    return f"{int(year_text) + 1911:04d}-{int(month_text):02d}-{int(day_text):02d}"


def fetch_taiex_snapshot(target_date: str) -> TaiexSnapshot | None:
    try:
        import requests

        response = requests.get(twse_taiex_history_url(target_date), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data") or []
        if len(rows) < 2:
            return None
        latest_row = rows[-1]
        previous_row = rows[-2]
        close_index = parse_twse_number(latest_row[4])
        previous_close = parse_twse_number(previous_row[4])
        change_points = close_index - previous_close
        change_pct = change_points / previous_close if previous_close else 0.0
        return TaiexSnapshot(
            trade_date=twse_roc_date_to_iso(latest_row[0]),
            open_index=parse_twse_number(latest_row[1]),
            high_index=parse_twse_number(latest_row[2]),
            low_index=parse_twse_number(latest_row[3]),
            close_index=close_index,
            change_points=change_points,
            change_pct=change_pct,
        )
    except Exception:
        return None


def parse_float(value: str) -> float | None:
    cleaned = value.replace(",", "").strip()
    if cleaned in {"", "--", "X"}:
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def parse_twse_rows(payload: dict, symbol: str) -> dict[str, MarketBar]:
    rows = payload.get("data") or []
    if not rows:
        raise ValueError(f"{symbol} 无行情资料")
    parsed: dict[str, MarketBar] = {}
    for row in rows:
        raw_date = row[0]
        parts = raw_date.split("/")
        if len(parts) != 3:
            continue
        year = int(parts[0]) + 1911
        trade_date = f"{year}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        close = parse_float(row[6])
        volume = parse_float(row[1])
        amount = parse_float(row[2])
        if close is not None:
            parsed[trade_date] = MarketBar(close=close, volume=volume, amount=amount)
    if not parsed:
        raise ValueError(f"{symbol} 无可解析收盘价")
    return parsed


def matrix_cache_path(assets: Iterable[Asset], months: list[str], cache_dir: Path) -> Path:
    asset_list = list(assets)
    source_files: list[dict[str, object]] = []
    for asset in asset_list:
        for month in months:
            path = cache_dir / f"{asset.symbol}_{month}.json"
            if path.exists():
                stat = path.stat()
                source_files.append({"name": path.name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
            else:
                source_files.append({"name": path.name, "missing": True})
    key_payload = {
        "symbols": [asset.symbol for asset in asset_list],
        "months": months,
        "cache_dir": str(cache_dir.resolve()),
        "sources": source_files,
    }
    cache_key = hashlib.sha256(json.dumps(key_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return DEFAULT_MATRIX_CACHE_DIR / f"twse_prices_{cache_key}.npz"


def load_price_matrix_cache(path: Path) -> tuple[PriceData, list[DataIssue]] | None:
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as payload:
            dates = payload["dates"].astype(str).tolist()
            symbols = payload["symbols"].astype(str).tolist()
            prices = payload["prices"].astype(float)
            volumes = payload["volumes"].astype(float)
            amounts = payload["amounts"].astype(float)
            issue_rows = payload["issues"].astype(str).tolist()
    except Exception:
        return None
    issues: list[DataIssue] = []
    for row in issue_rows:
        symbol, _, message = row.partition("\t")
        if symbol and message:
            issues.append(DataIssue(symbol, message))
    issues.append(DataIssue("CACHE", f"已使用聚合行情矩阵缓存：{path}"))
    return PriceData(dates=dates, symbols=symbols, prices=prices, volumes=volumes, amounts=amounts), issues


def write_price_matrix_cache(path: Path, price_data: PriceData, issues: list[DataIssue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    issue_rows = np.array([f"{issue.symbol}\t{issue.message}" for issue in issues], dtype=str)
    np.savez_compressed(
        path,
        dates=np.array(price_data.dates, dtype=str),
        symbols=np.array(price_data.symbols, dtype=str),
        prices=price_data.prices,
        volumes=price_data.volumes if price_data.volumes is not None else np.empty((0, 0), dtype=float),
        amounts=price_data.amounts if price_data.amounts is not None else np.empty((0, 0), dtype=float),
        issues=issue_rows,
    )


def fetch_month(symbol: str, month: str, cache_dir: Path, allow_stale_cache: bool, offline_cache: bool) -> tuple[dict[str, MarketBar] | None, str | None]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{symbol}_{month}.json"

    if offline_cache:
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return parse_twse_rows(payload, symbol), f"{symbol} {month} 使用离线缓存"
        return None, f"{symbol} {month} 无离线缓存"

    try:
        import requests

        response = requests.get(twse_url(symbol, month), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if payload.get("stat") not in {"OK", "很抱歉，沒有符合條件的資料!"}:
            raise ValueError(str(payload.get("stat")))
        if payload.get("stat") != "OK":
            if allow_stale_cache and cache_path.exists():
                cached_payload = json.loads(cache_path.read_text(encoding="utf-8"))
                return parse_twse_rows(cached_payload, symbol), f"{symbol} {month} 使用缓存：无新公开资料"
            cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return None, f"{symbol} {month} 无资料"
        cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return parse_twse_rows(payload, symbol), None
    except Exception as exc:
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return parse_twse_rows(payload, symbol), f"{symbol} {month} 使用缓存：{exc}"
        if allow_stale_cache:
            merged: dict[str, MarketBar] = {}
            stale_files = sorted(cache_dir.glob(f"{symbol}_*.json"))
            for path in stale_files:
                payload = json.loads(path.read_text(encoding="utf-8"))
                merged.update(parse_twse_rows(payload, symbol))
            if merged:
                return merged, f"{symbol} 使用旧缓存：{exc}"
        return None, f"{symbol} {month} 下载失败：{exc}"


def load_prices_from_twse(assets: Iterable[Asset], months: list[str], cache_dir: Path, allow_stale_cache: bool, offline_cache: bool) -> tuple[PriceData, list[DataIssue]]:
    assets = list(assets)
    if offline_cache and not allow_stale_cache:
        cached = load_price_matrix_cache(matrix_cache_path(assets, months, cache_dir))
        if cached:
            return cached

    price_by_symbol: dict[str, dict[str, MarketBar]] = {}
    issues: list[DataIssue] = []

    total_assets = len(assets)
    for asset_index, asset in enumerate(assets, start=1):
        if offline_cache:
            print(f"读取离线行情缓存：{asset.symbol} ({asset_index}/{total_assets})", file=sys.stderr, flush=True)
        merged: dict[str, MarketBar] = {}
        for month in months:
            month_prices, issue = fetch_month(asset.symbol, month, cache_dir, allow_stale_cache, offline_cache)
            if issue:
                issues.append(DataIssue(asset.symbol, issue))
            if month_prices:
                merged.update(month_prices)
        if not merged:
            issues.append(DataIssue(asset.symbol, "未取得任何可用行情，已剔除"))
            continue
        if len(merged) < MIN_OBSERVATIONS:
            issues.append(DataIssue(asset.symbol, f"有效交易日少于 {MIN_OBSERVATIONS}，已剔除"))
            continue
        price_by_symbol[asset.symbol] = merged

    if not price_by_symbol:
        raise RuntimeError("没有可用于分析的资产行情。请检查网络、资产代码或缓存。")

    common_dates = set.intersection(*(set(values) for values in price_by_symbol.values()))
    dates = sorted(common_dates)
    if len(dates) < MIN_OBSERVATIONS:
        raise RuntimeError(f"交易日交集少于 {MIN_OBSERVATIONS}，无法稳定估计协方差。")

    symbols = list(price_by_symbol)
    matrix = np.array([[price_by_symbol[symbol][day].close for symbol in symbols] for day in dates], dtype=float)
    volume_matrix = np.array([[price_by_symbol[symbol][day].volume or 0.0 for symbol in symbols] for day in dates], dtype=float)
    amount_matrix = np.array([[price_by_symbol[symbol][day].amount or 0.0 for symbol in symbols] for day in dates], dtype=float)
    price_data = PriceData(dates=dates, symbols=symbols, prices=matrix, volumes=volume_matrix, amounts=amount_matrix)
    if offline_cache and not allow_stale_cache:
        cache_path = matrix_cache_path(assets, months, cache_dir)
        write_price_matrix_cache(cache_path, price_data, issues)
        issues.append(DataIssue("CACHE", f"已生成聚合行情矩阵缓存：{cache_path}"))
    return price_data, issues


def month_to_date(month: str, is_end: bool) -> str:
    year = int(month[:4])
    month_number = int(month[4:])
    if not is_end:
        return f"{year}-{month_number:02d}-01"
    next_year = year + (1 if month_number == 12 else 0)
    next_month = 1 if month_number == 12 else month_number + 1
    last_day = date(next_year, next_month, 1).toordinal() - 1
    return date.fromordinal(last_day).strftime("%Y-%m-%d")


def shioaji_credentials() -> tuple[str, str]:
    api_key = os.environ.get("SHIOAJI_API_KEY", "").strip()
    secret_key = os.environ.get("SHIOAJI_SECRET_KEY", "").strip()
    if not api_key or not secret_key:
        raise RuntimeError("缺少 SHIOAJI_API_KEY 或 SHIOAJI_SECRET_KEY 环境变量。")
    return api_key, secret_key


def parse_shioaji_kbars(kbars: object) -> dict[str, MarketBar]:
    timestamps = list(getattr(kbars, "ts", []))
    closes = list(getattr(kbars, "Close", []))
    volumes = list(getattr(kbars, "Volume", []))
    amounts = list(getattr(kbars, "Amount", []))
    daily_close: dict[str, MarketBar] = {}
    for offset, (ts_value, close) in enumerate(zip(timestamps, closes)):
        timestamp = np.datetime64(ts_value, "ns")
        day = str(timestamp.astype("datetime64[D]"))
        close_value = float(close)
        if math.isfinite(close_value):
            volume_value = float(volumes[offset]) if offset < len(volumes) else 0.0
            amount_value = float(amounts[offset]) if offset < len(amounts) else close_value * volume_value
            daily_close[day] = MarketBar(close=close_value, volume=volume_value, amount=amount_value)
    return daily_close


def fetch_shioaji_daily_close(api: object, contract: object, start_date: str, end_date: str) -> dict[str, MarketBar]:
    last_error: Exception | None = None
    for _ in range(SHIOAJI_KBARS_RETRIES):
        try:
            return parse_shioaji_kbars(api.kbars(contract=contract, start=start_date, end=end_date))
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else "Shioaji kbars 取数失败")


def load_prices_from_shioaji(assets: Iterable[Asset], months: list[str]) -> tuple[PriceData, list[DataIssue]]:
    os.environ.setdefault("SJ_HOME_PATH", str(DEFAULT_SHIOAJI_HOME))
    DEFAULT_SHIOAJI_HOME.mkdir(parents=True, exist_ok=True)
    DEFAULT_SHIOAJI_HOME.chmod(0o700)

    try:
        import shioaji as sj
    except Exception as exc:
        raise RuntimeError(f"Shioaji 套件不可用：{exc}") from exc

    api_key, secret_key = shioaji_credentials()
    api = sj.Shioaji()
    issues: list[DataIssue] = []
    price_by_symbol: dict[str, dict[str, MarketBar]] = {}
    logged_in = False

    try:
        api.login(api_key=api_key, secret_key=secret_key)
        logged_in = True
        for asset in assets:
            failed_months: list[str] = []
            merged_daily_close: dict[str, MarketBar] = {}
            try:
                contract = api.Contracts.Stocks[asset.symbol]
                for month in months:
                    start_date = month_to_date(month, is_end=False)
                    end_date = month_to_date(month, is_end=True)
                    try:
                        merged_daily_close.update(fetch_shioaji_daily_close(api, contract, start_date, end_date))
                    except Exception:
                        failed_months.append(month)
                if len(merged_daily_close) < MIN_OBSERVATIONS:
                    issues.append(DataIssue(asset.symbol, f"Shioaji 有效交易日少于 {MIN_OBSERVATIONS}，已剔除"))
                    continue
                if failed_months:
                    issues.append(DataIssue(asset.symbol, f"Shioaji 有 {len(failed_months)} 个月份取数失败，已使用其余月份"))
                price_by_symbol[asset.symbol] = merged_daily_close
            except Exception as exc:
                issues.append(DataIssue(asset.symbol, f"Shioaji 取数失败，已剔除：{exc}"))
    finally:
        logout = getattr(api, "logout", None)
        if logged_in and callable(logout):
            logout()

    if not price_by_symbol:
        raise RuntimeError("Shioaji 没有取得任何可用于分析的资产行情。")

    common_dates = set.intersection(*(set(values) for values in price_by_symbol.values()))
    dates = sorted(common_dates)
    if len(dates) < MIN_OBSERVATIONS:
        raise RuntimeError(f"Shioaji 交易日交集少于 {MIN_OBSERVATIONS}，无法稳定估计协方差。")

    symbols = list(price_by_symbol)
    matrix = np.array([[price_by_symbol[symbol][day].close for symbol in symbols] for day in dates], dtype=float)
    volume_matrix = np.array([[price_by_symbol[symbol][day].volume or 0.0 for symbol in symbols] for day in dates], dtype=float)
    amount_matrix = np.array([[price_by_symbol[symbol][day].amount or 0.0 for symbol in symbols] for day in dates], dtype=float)
    return PriceData(dates=dates, symbols=symbols, prices=matrix, volumes=volume_matrix, amounts=amount_matrix), issues


def load_prices(
    assets: list[Asset],
    months: list[str],
    cache_dir: Path,
    allow_stale_cache: bool,
    offline_cache: bool,
    data_source: str,
) -> tuple[PriceData, list[DataIssue]]:
    if data_source == "shioaji":
        price_data, issues = load_prices_from_shioaji(assets, months)
        issues.append(DataIssue("DATA", "数据源：Shioaji"))
        return price_data, issues
    if data_source == "auto" and not offline_cache:
        try:
            price_data, issues = load_prices_from_shioaji(assets, months)
            issues.append(DataIssue("DATA", "数据源：Shioaji"))
            return price_data, issues
        except Exception as exc:
            price_data, issues = load_prices_from_twse(assets, months, cache_dir, allow_stale_cache, offline_cache)
            issues.append(DataIssue("DATA", f"Shioaji 不可用，已回退 TWSE：{exc}"))
            return price_data, issues
    price_data, issues = load_prices_from_twse(assets, months, cache_dir, allow_stale_cache, offline_cache)
    issues.append(DataIssue("DATA", "数据源：TWSE"))
    return price_data, issues


def latest_available_public_close_date(
    assets: list[Asset],
    months: list[str],
    cache_dir: Path,
    allow_stale_cache: bool,
) -> tuple[str | None, list[DataIssue]]:
    """Refresh TWSE public-close data for the requested months and return the newest common date."""
    issues: list[DataIssue] = []
    dates_by_symbol: list[set[str]] = []
    for asset in assets:
        asset_dates: set[str] = set()
        for month in months:
            month_prices, issue = fetch_month(
                asset.symbol,
                month,
                cache_dir=cache_dir,
                allow_stale_cache=allow_stale_cache,
                offline_cache=False,
            )
            if issue:
                issues.append(DataIssue(asset.symbol, issue))
            if month_prices:
                asset_dates.update(month_prices)
        if asset_dates:
            dates_by_symbol.append(asset_dates)
        else:
            issues.append(DataIssue(asset.symbol, "public-close 刷新未取得可用月资料"))
    issues.append(DataIssue("DATA", "public-close 已主动刷新 TWSE 月资料"))
    if not dates_by_symbol:
        return None, issues
    common_dates = set.intersection(*dates_by_symbol)
    return (max(common_dates) if common_dates else None), issues


def simple_returns(prices: np.ndarray) -> np.ndarray:
    return prices[1:] / prices[:-1] - 1.0


def as_return_matrix(returns: np.ndarray) -> np.ndarray:
    matrix = np.asarray(returns, dtype=float)
    if matrix.ndim == 1:
        matrix = matrix.reshape(-1, 1)
    if matrix.ndim != 2:
        raise RuntimeError(f"收益率矩阵必须为二维，当前维度为 {matrix.ndim}。")
    return matrix


def covariance_matrix(returns: np.ndarray) -> np.ndarray:
    matrix = as_return_matrix(returns)
    covariance = np.cov(matrix, rowvar=False, ddof=1) * ANNUALIZATION_DAYS
    if np.ndim(covariance) == 0:
        return np.array([[float(covariance)]], dtype=float)
    return np.asarray(covariance, dtype=float)


def correlation_matrix(returns: np.ndarray) -> np.ndarray:
    matrix = as_return_matrix(returns)
    correlation = np.corrcoef(matrix, rowvar=False)
    if np.ndim(correlation) == 0:
        return np.array([[1.0]], dtype=float)
    return np.asarray(correlation, dtype=float)


def estimate_shrink_covariance(returns: np.ndarray) -> tuple[np.ndarray, DataIssue | None]:
    try:
        from sklearn.covariance import LedoitWolf

        covariance = LedoitWolf().fit(returns).covariance_ * ANNUALIZATION_DAYS
        return covariance, None
    except Exception as exc:
        sample_cov = covariance_matrix(returns)
        target = np.diag(np.diag(sample_cov))
        shrinkage = 0.25
        covariance = (1 - shrinkage) * sample_cov + shrinkage * target
        return covariance, DataIssue("MODEL", f"Ledoit-Wolf 不可用，已使用 25% 对角收缩替代：{exc}")


def project_capped_simplex(values: np.ndarray, max_weight: float) -> np.ndarray:
    low = float(np.min(values) - max_weight)
    high = float(np.max(values))
    for _ in range(80):
        middle = (low + high) / 2
        projected = np.clip(values - middle, 0.0, max_weight)
        projected_sum = float(projected.sum())
        if abs(projected_sum - 1.0) <= 1e-12:
            high = middle
            break
        if projected_sum > 1:
            low = middle
        else:
            high = middle
    projected = np.clip(values - high, 0.0, max_weight)
    total = projected.sum()
    if total <= 0:
        return np.repeat(1 / len(values), len(values))
    if abs(total - 1) > 1e-8:
        projected = projected / total
    return projected


def projected_gradient_min_variance(covariance: np.ndarray, initial: np.ndarray, max_weight: float) -> np.ndarray:
    weights = project_capped_simplex(initial, max_weight)
    eigen_max = float(np.max(np.linalg.eigvalsh(covariance)))
    step = 1.0 / max(2 * eigen_max, 1e-8)
    for _ in range(2000):
        previous = weights
        gradient = 2 * covariance @ weights
        weights = project_capped_simplex(weights - step * gradient, max_weight)
        if np.linalg.norm(weights - previous, ord=1) < 1e-10:
            break
    return weights


def min_variance_weights(covariance: np.ndarray, max_weight: float = MAX_WEIGHT, initial: np.ndarray | None = None) -> np.ndarray:
    n_assets = covariance.shape[0]
    if n_assets * max_weight < 1:
        raise RuntimeError(f"资产数量不足，无法在单一资产上限 {max_weight:.0%} 下满仓。")
    if initial is None:
        initial_weights = np.repeat(1 / n_assets, n_assets)
    else:
        initial_weights = project_capped_simplex(np.asarray(initial, dtype=float), max_weight)

    try:
        from scipy.optimize import minimize

        bounds = [(0.0, max_weight) for _ in range(n_assets)]
        constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}
        result = minimize(
            lambda weights: float(weights.T @ covariance @ weights),
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if result.success:
            return project_capped_simplex(result.x, max_weight)
    except Exception:
        pass

    return projected_gradient_min_variance(covariance, initial_weights, max_weight)


def risk_contribution(weights: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    portfolio_var = float(weights.T @ covariance @ weights)
    if portfolio_var <= 0:
        return np.zeros_like(weights)
    marginal = covariance @ weights
    return weights * marginal / portfolio_var


def portfolio_curve(returns: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return np.cumprod(1 + np.dot(returns, weights))


def drawdown(curve: np.ndarray) -> np.ndarray:
    peak = np.maximum.accumulate(curve)
    return curve / peak - 1


def annualized_return(curve: np.ndarray) -> float:
    if len(curve) == 0:
        return 0.0
    years = len(curve) / ANNUALIZATION_DAYS
    if years <= 0 or curve[-1] <= 0:
        return 0.0
    return float(curve[-1] ** (1 / years) - 1)


def annualized_volatility(returns: np.ndarray) -> float:
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * math.sqrt(ANNUALIZATION_DAYS))


def backtest_metrics(curve: np.ndarray, returns: np.ndarray, turnovers: list[float]) -> BacktestMetrics:
    turnover_values = np.array(turnovers[1:] if len(turnovers) > 1 else turnovers, dtype=float)
    return BacktestMetrics(
        annual_return=annualized_return(curve),
        annual_volatility=annualized_volatility(returns),
        max_drawdown=float(drawdown(curve).min()) if len(curve) else 0.0,
        average_turnover=float(turnover_values.mean()) if len(turnover_values) else 0.0,
        cumulative_turnover=float(turnover_values.sum()) if len(turnover_values) else 0.0,
    )


def rolling_rebalance_backtest(returns: np.ndarray, dates: list[str], window: int, step: int) -> BacktestResult:
    if window < MIN_OBSERVATIONS:
        raise RuntimeError(f"再平衡估计窗口必须至少为 {MIN_OBSERVATIONS} 个交易日。")
    if step <= 0:
        raise RuntimeError("再平衡间隔必须大于 0。")
    if len(returns) <= window:
        raise RuntimeError(f"交易日不足，无法使用 {window} 日窗口执行再平衡回测。")

    sample_daily: list[float] = []
    shrink_daily: list[float] = []
    backtest_dates: list[str] = []
    sample_turnovers: list[float] = []
    shrink_turnovers: list[float] = []
    rebalance_dates: list[str] = []
    previous_sample_weights: np.ndarray | None = None
    previous_shrink_weights: np.ndarray | None = None

    for start_index in range(window, len(returns), step):
        rebalance_dates.append(dates[start_index])
        estimation_returns = returns[start_index - window : start_index]
        sample_cov = covariance_matrix(estimation_returns)
        shrink_cov, _ = estimate_shrink_covariance(estimation_returns)
        sample_weights = min_variance_weights(sample_cov)
        shrink_weights = min_variance_weights(shrink_cov)

        if previous_sample_weights is None:
            sample_turnovers.append(0.0)
            shrink_turnovers.append(0.0)
        else:
            sample_turnovers.append(float(np.sum(np.abs(sample_weights - previous_sample_weights))))
            shrink_turnovers.append(float(np.sum(np.abs(shrink_weights - previous_shrink_weights))))

        end_index = min(start_index + step, len(returns))
        holding_returns = returns[start_index:end_index]
        sample_daily.extend(np.dot(holding_returns, sample_weights).tolist())
        shrink_daily.extend(np.dot(holding_returns, shrink_weights).tolist())
        backtest_dates.extend(dates[start_index:end_index])
        previous_sample_weights = sample_weights
        previous_shrink_weights = shrink_weights

    sample_returns = np.array(sample_daily, dtype=float)
    shrink_returns = np.array(shrink_daily, dtype=float)
    sample_curve = np.cumprod(1 + sample_returns)
    shrink_curve = np.cumprod(1 + shrink_returns)
    return BacktestResult(
        dates=backtest_dates,
        rebalance_dates=rebalance_dates,
        sample_curve=sample_curve,
        shrink_curve=shrink_curve,
        sample_returns=sample_returns,
        shrink_returns=shrink_returns,
        sample_turnovers=np.array(sample_turnovers, dtype=float),
        shrink_turnovers=np.array(shrink_turnovers, dtype=float),
        sample_metrics=backtest_metrics(sample_curve, sample_returns, sample_turnovers),
        shrink_metrics=backtest_metrics(shrink_curve, shrink_returns, shrink_turnovers),
        window=window,
        step=step,
        rebalance_count=len(sample_turnovers),
    )


def stress_loss(weights: np.ndarray, covariance: np.ndarray, market_drop: float = -0.18, vol_multiplier: float = 1.8, corr_to_one: float = 0.35) -> float:
    vol = np.sqrt(np.diag(covariance))
    safe_outer = np.outer(vol, vol)
    corr = np.divide(covariance, safe_outer, out=np.eye(len(vol)), where=safe_outer != 0)
    stressed_corr = corr * (1 - corr_to_one) + np.ones_like(corr) * corr_to_one
    stressed_cov = np.outer(vol * vol_multiplier, vol * vol_multiplier) * stressed_corr
    portfolio_vol = math.sqrt(float(weights.T @ stressed_cov @ weights))
    return market_drop - portfolio_vol / math.sqrt(ANNUALIZATION_DAYS)


def to_percent(values: np.ndarray) -> list[float]:
    return [round(float(value) * 100, 2) for value in values]


def aggregate_group_exposure(
    assets: list[Asset],
    symbols: list[str],
    weights: np.ndarray,
    risk_values: np.ndarray,
    group_getter,
) -> list[dict[str, float | str]]:
    asset_by_symbol = {asset.symbol: asset for asset in assets}
    groups: dict[str, dict[str, float | str]] = {}
    for index, symbol in enumerate(symbols):
        asset = asset_by_symbol.get(symbol)
        group = str(group_getter(asset)).strip() if asset else ""
        if not group:
            group = "未分类"
        item = groups.setdefault(group, {"group": group, "weight": 0.0, "risk": 0.0, "count": 0})
        item["weight"] = float(item["weight"]) + float(weights[index])
        item["risk"] = float(item["risk"]) + float(risk_values[index])
        item["count"] = int(item["count"]) + 1
    return sorted(groups.values(), key=lambda item: (float(item["risk"]), float(item["weight"])), reverse=True)


def apply_dark_layout(fig: go.Figure, title: str, yaxis_title: str | None = None) -> None:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#1e2f2d"), x=0.02),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#32433f", family="PingFang TC, Microsoft JhengHei, sans-serif", size=12),
        margin=dict(l=42, r=18, t=52, b=52),
        legend=dict(
            bgcolor="#ffffff",
            bordercolor="#dce6e1",
            borderwidth=1,
            font=dict(color="#52635f"),
        ),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#0f8f76", font=dict(color="#1e2f2d")),
    )
    fig.update_xaxes(
        gridcolor="#edf2ef",
        linecolor="#d6e0dc",
        tickfont=dict(color="#6c7d78"),
        zerolinecolor="#d6e0dc",
    )
    fig.update_yaxes(
        gridcolor="#edf2ef",
        linecolor="#d6e0dc",
        tickfont=dict(color="#6c7d78"),
        zerolinecolor="#d6e0dc",
        title=dict(text=yaxis_title or "", font=dict(color="#6c7d78")),
    )


def bar_figure(title: str, x: list[str], y: list[float], colors: list[str]) -> str:
    fig = go.Figure(
        go.Bar(
            x=x,
            y=y,
            marker=dict(
                color=y,
                colorscale=colors,
                line=dict(color="rgba(255,255,255,0.18)", width=1),
            ),
            hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
        )
    )
    apply_dark_layout(fig, title, "百分比")
    return pio.to_html(fig, include_plotlyjs=False, full_html=False)


def heatmap_figure(symbols: list[str], corr: np.ndarray) -> str:
    fig = go.Figure(
        go.Heatmap(
            z=corr,
            x=symbols,
            y=symbols,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0.0, "#11284d"],
                [0.22, "#255f79"],
                [0.48, "#f2e8c4"],
                [0.72, "#f49b64"],
                [1.0, "#fb3f5f"],
            ],
            colorbar=dict(title=dict(text="相关性", font=dict(color="#d7e7df")), tickfont=dict(color="#a8bcb4")),
            hovertemplate="%{y} × %{x}<br>相关性 %{z:.2f}<extra></extra>",
        )
    )
    apply_dark_layout(fig, "【Codex】台灣股市投資量化模型：相關性熱力圖")
    return pio.to_html(fig, include_plotlyjs=True, full_html=False)


def line_figure(title: str, dates: list[str], sample_curve: np.ndarray, shrink_curve: np.ndarray) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=sample_curve,
            mode="lines",
            name="普通协方差",
            line=dict(color="#52d6ff", width=3),
            hovertemplate="%{x}<br>净值 %{y:.4f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=shrink_curve,
            mode="lines",
            name="收缩协方差",
            fill="tonexty",
            fillcolor="rgba(97,244,201,0.12)",
            line=dict(color="#65f4c9", width=3),
            hovertemplate="%{x}<br>净值 %{y:.4f}<extra></extra>",
        )
    )
    apply_dark_layout(fig, title, "净值")
    return pio.to_html(fig, include_plotlyjs=False, full_html=False)


def drawdown_figure(dates: list[str], sample_dd: np.ndarray, shrink_dd: np.ndarray) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=sample_dd * 100,
            mode="lines",
            name="普通协方差",
            fill="tozeroy",
            fillcolor="rgba(251,63,95,0.18)",
            line=dict(color="#fb3f5f", width=3),
            hovertemplate="%{x}<br>回撤 %{y:.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=shrink_dd * 100,
            mode="lines",
            name="收缩协方差",
            line=dict(color="#f6c85f", width=3),
            hovertemplate="%{x}<br>回撤 %{y:.2f}%<extra></extra>",
        )
    )
    apply_dark_layout(fig, "回撤对比", "回撤百分比")
    return pio.to_html(fig, include_plotlyjs=False, full_html=False)


def backtest_curve_figure(backtest: BacktestResult) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=backtest.dates,
            y=backtest.sample_curve,
            mode="lines",
            name="普通协方差滚动组合",
            line=dict(color="#52d6ff", width=3),
            hovertemplate="%{x}<br>回测净值 %{y:.4f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=backtest.dates,
            y=backtest.shrink_curve,
            mode="lines",
            name="收缩协方差滚动组合",
            fill="tonexty",
            fillcolor="rgba(97,244,201,0.12)",
            line=dict(color="#65f4c9", width=3),
            hovertemplate="%{x}<br>回测净值 %{y:.4f}<extra></extra>",
        )
    )
    apply_dark_layout(fig, "滚动再平衡回测净值", "净值")
    return pio.to_html(fig, include_plotlyjs=False, full_html=False)


def format_percent(value: float, signed: bool = False) -> str:
    sign = "+" if signed else ""
    return f"{value * 100:{sign}.2f}%"


def format_twd(value: float) -> str:
    return f"NT$ {value:,.0f}"


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def previous_available_date_index(dates: list[str], target_date: str) -> int:
    target = parse_iso_date(target_date)
    available = [index for index, value in enumerate(dates) if parse_iso_date(value) < target]
    if not available:
        raise RuntimeError(f"建仓日前没有可用收盘价：{target_date}")
    return available[-1]


def normalize_metric(values: np.ndarray) -> np.ndarray:
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if abs(maximum - minimum) < 1e-12:
        return np.ones_like(values)
    return (values - minimum) / (maximum - minimum) + 1e-6


def zscore(values: np.ndarray) -> np.ndarray:
    clean = np.asarray(values, dtype=float)
    mean = float(np.mean(clean))
    std = float(np.std(clean, ddof=0))
    if std <= 1e-12:
        return np.zeros_like(clean)
    return (clean - mean) / std


def capped_compound_return(series: np.ndarray, days: int) -> float:
    if len(series) <= days:
        return float(series[-1] / series[0] - 1.0)
    return float(series[-1] / series[-(days + 1)] - 1.0)


def safe_group_value(name: str) -> str:
    value = str(name or "").strip()
    return value or "unclassified"


def average_group_scores(
    values: np.ndarray,
    group_names: list[str],
    valid_indices: list[int],
) -> np.ndarray:
    result = np.zeros(len(valid_indices), dtype=float)
    if not valid_indices:
        return result
    grouped: dict[str, list[float]] = {}
    for offset, index in enumerate(valid_indices):
        group = safe_group_value(group_names[index] if index < len(group_names) else "")
        grouped.setdefault(group, []).append(float(values[offset]))
    group_avg = {group: float(np.mean(scores)) for group, scores in grouped.items()}
    for offset, index in enumerate(valid_indices):
        group = safe_group_value(group_names[index] if index < len(group_names) else "")
        result[offset] = group_avg[group]
    return result


def build_proxy_external_overlay(
    assets: list[Asset],
    price_data: PriceData,
    valid_indices: list[int],
    momentum_values: np.ndarray,
    low_vol_values: np.ndarray,
    drawdown_values: np.ndarray,
    liquidity_values: np.ndarray,
    trend_strength_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if not valid_indices:
        return np.zeros(0, dtype=float), np.zeros(0, dtype=float)
    asset_by_symbol = {asset.symbol: asset for asset in assets}
    symbols = price_data.symbols

    sector_names = [asset_by_symbol.get(symbol, Asset(symbol, "", "", "")).sector for symbol in symbols]
    theme_names = [asset_by_symbol.get(symbol, Asset(symbol, "", "", "")).theme for symbol in symbols]
    ai_mask = np.array(
        [asset_by_symbol.get(symbols[index], Asset(symbols[index], "", "", "")).ai_supply_chain for index in valid_indices],
        dtype=bool,
    )

    sector_relative = average_group_scores(momentum_values + trend_strength_values, sector_names, valid_indices)
    theme_relative = average_group_scores(momentum_values + 0.5 * liquidity_values, theme_names, valid_indices)
    sector_relative_z = zscore(sector_relative)
    theme_relative_z = zscore(theme_relative)
    ai_score = np.where(ai_mask, 1.0, -0.25)
    industry_ai_score = (
        0.40 * sector_relative_z
        + 0.25 * theme_relative_z
        + 0.20 * zscore(ai_score)
        + 0.15 * zscore(liquidity_values)
    )

    correlation_window = min(60, price_data.prices.shape[0] - 1)
    if correlation_window >= MIN_OBSERVATIONS:
        recent_returns = simple_returns(price_data.prices[-(correlation_window + 1) :])
        valid_returns = recent_returns[:, valid_indices]
        corr = np.corrcoef(valid_returns, rowvar=False)
        if corr.ndim == 0:
            avg_corr = np.zeros(len(valid_indices), dtype=float)
        else:
            corr = np.nan_to_num(corr, nan=0.0)
            avg_corr = np.mean(corr - np.eye(corr.shape[0]), axis=1)
    else:
        avg_corr = np.zeros(len(valid_indices), dtype=float)
    volatility_pressure = zscore(-low_vol_values)
    crowding_pressure = zscore(avg_corr)
    ai_crowding_pressure = np.where(ai_mask, 1.0, 0.0)
    funds_flow_proxy = zscore(liquidity_values + 0.5 * momentum_values)
    macro_external_score = (
        0.35 * funds_flow_proxy
        + 0.30 * zscore(-crowding_pressure)
        + 0.20 * zscore(-volatility_pressure)
        + 0.15 * zscore(-ai_crowding_pressure)
    )
    return industry_ai_score, macro_external_score


def max_sharpe_weights(expected_returns: np.ndarray, covariance: np.ndarray, max_weight: float = MAX_WEIGHT) -> np.ndarray:
    n_assets = covariance.shape[0]
    if n_assets * max_weight < 1:
        raise RuntimeError(f"资产数量不足，无法在单一资产上限 {max_weight:.0%} 下满仓。")
    initial = np.repeat(1 / n_assets, n_assets)

    def negative_sharpe(weights: np.ndarray) -> float:
        portfolio_return = float(weights @ expected_returns)
        portfolio_volatility = math.sqrt(max(float(weights.T @ covariance @ weights), 1e-12))
        return -portfolio_return / portfolio_volatility

    try:
        from scipy.optimize import minimize

        bounds = [(0.0, max_weight) for _ in range(n_assets)]
        constraints = {"type": "eq", "fun": lambda weights: np.sum(weights) - 1.0}
        result = minimize(
            negative_sharpe,
            initial,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if result.success:
            return project_capped_simplex(result.x, max_weight)
    except Exception:
        pass

    volatility = np.sqrt(np.maximum(np.diag(covariance), 1e-12))
    shifted_returns = expected_returns - float(np.min(expected_returns)) + 1e-6
    score = shifted_returns / volatility
    if float(np.sum(score)) <= 0:
        return initial
    return project_capped_simplex(score / float(np.sum(score)), max_weight)


def drop_tiny_weights(weights: np.ndarray, threshold: float = 0.001, max_weight: float = MAX_WEIGHT) -> np.ndarray:
    cleaned = np.array(weights, dtype=float)
    cleaned[cleaned < threshold] = 0.0
    total = float(np.sum(cleaned))
    if total <= 0:
        return weights
    cleaned = cleaned / total
    if float(np.max(cleaned)) > max_weight:
        return project_capped_simplex(cleaned, max_weight)
    return cleaned


def apply_group_tilt(
    weights: np.ndarray,
    group_mask: np.ndarray,
    target_weight: float,
    cap_weight: float,
    max_weight: float = MAX_WEIGHT,
) -> np.ndarray:
    adjusted = np.array(weights, dtype=float)
    if not np.any(group_mask):
        return adjusted
    current_group = float(np.sum(adjusted[group_mask]))
    target = min(target_weight, cap_weight)
    if current_group >= target:
        if current_group <= cap_weight:
            return adjusted
        excess = current_group - cap_weight
        group_total = float(np.sum(adjusted[group_mask]))
        non_group_total = float(np.sum(adjusted[~group_mask]))
        if group_total <= 0 or non_group_total <= 0:
            return adjusted
        adjusted[group_mask] *= cap_weight / group_total
        adjusted[~group_mask] += excess * adjusted[~group_mask] / non_group_total
        return project_capped_simplex(adjusted, max_weight)

    needed = target - current_group
    donor_total = float(np.sum(adjusted[~group_mask]))
    if donor_total <= needed or donor_total <= 0:
        return adjusted
    receiver_capacity = np.maximum(max_weight - adjusted[group_mask], 0.0)
    available = float(np.sum(receiver_capacity))
    shift = min(needed, available)
    if shift <= 0:
        return adjusted
    adjusted[~group_mask] *= (donor_total - shift) / donor_total
    receiver_base = adjusted[group_mask]
    if float(np.sum(receiver_base)) > 0:
        allocation = receiver_base / float(np.sum(receiver_base))
    else:
        allocation = np.repeat(1 / int(np.sum(group_mask)), int(np.sum(group_mask)))
    adjusted[group_mask] += shift * allocation
    adjusted[group_mask] = np.minimum(adjusted[group_mask], max_weight)
    return adjusted / float(np.sum(adjusted))


def max_drawdown_duration(drawdowns: np.ndarray) -> int:
    longest = 0
    current = 0
    for value in drawdowns:
        if value < -1e-12:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def drawdown_risk_weights(
    price_data: PriceData,
    build_date: str,
    issues: list[DataIssue],
    max_weight: float = MAX_WEIGHT,
) -> tuple[np.ndarray, dict[str, dict[str, float]], str, str, int]:
    price_index = previous_available_date_index(price_data.dates, build_date)
    price_date = price_data.dates[price_index]
    build_dt = parse_iso_date(build_date)
    start_index: int | None = None
    lookback_start = ""
    lookback_years = MODEL_LOOKBACK_YEARS
    for candidate_years in (MODEL_LOOKBACK_YEARS, MODEL_FALLBACK_LOOKBACK_YEARS):
        candidate_start = add_years(build_dt, -candidate_years).isoformat()
        start_candidates = [index for index, value in enumerate(price_data.dates[: price_index + 1]) if value >= candidate_start]
        if not start_candidates:
            continue
        candidate_index = start_candidates[0]
        observations = price_index - candidate_index + 1
        if observations >= ANNUALIZATION_DAYS * candidate_years * 0.75:
            start_index = candidate_index
            lookback_start = candidate_start
            lookback_years = candidate_years
            break
        if candidate_years == MODEL_LOOKBACK_YEARS:
            issues.append(
                DataIssue(
                    "MODEL_PORTFOLIO",
                    f"5 年回撤估计资料不足，仅有 {observations} 个共同交易日，已改用 {MODEL_FALLBACK_LOOKBACK_YEARS} 年回撤。",
                )
            )
    if start_index is None:
        observations = price_index + 1
        if observations < MIN_OBSERVATIONS:
            raise RuntimeError(
                f"5 年、{MODEL_FALLBACK_LOOKBACK_YEARS} 年与可用资料回撤估计均不足，仅有 {observations} 个共同交易日。"
            )
        start_index = 0
        lookback_start = price_data.dates[0]
        lookback_years = 0
        issues.append(
            DataIssue(
                "MODEL_PORTFOLIO",
                f"2 年回撤估计资料不足，已改用可用资料：{lookback_start} 至 {price_date}。",
            )
        )

    window_prices = price_data.prices[start_index : price_index + 1]
    window_returns = simple_returns(window_prices)
    valid_indices: list[int] = []
    metrics: dict[str, dict[str, float]] = {}

    for index, symbol in enumerate(price_data.symbols):
        series = window_prices[:, index]
        asset_returns = window_returns[:, index]
        if len(series) < MIN_OBSERVATIONS or np.any(series <= 0) or not np.all(np.isfinite(series)):
            issues.append(DataIssue(symbol, f"{lookback_years} 年回撤资料不足或价格异常，模型盘已剔除"))
            continue
        curve = series / series[0]
        dd = drawdown(curve)
        max_dd = abs(float(dd.min()))
        volatility = annualized_volatility(asset_returns)
        duration = max_drawdown_duration(dd)
        if max_dd <= 0 or volatility <= 0:
            issues.append(DataIssue(symbol, f"{lookback_years} 年回撤风险过低或波动不可估，模型盘已剔除"))
            continue
        valid_indices.append(index)
        metrics[symbol] = {
            "max_drawdown": max_dd,
            "annual_volatility": volatility,
            "drawdown_days": float(duration),
        }

    if not valid_indices:
        raise RuntimeError(f"没有资产满足 {lookback_years} 年回撤风险模型盘建仓条件。")
    if len(valid_indices) * max_weight < 1:
        raise RuntimeError(f"满足条件的资产数量不足，无法在单一资产上限 {max_weight:.0%} 下满仓。")

    max_dd_values = np.array([metrics[price_data.symbols[index]]["max_drawdown"] for index in valid_indices], dtype=float)
    volatility_values = np.array([metrics[price_data.symbols[index]]["annual_volatility"] for index in valid_indices], dtype=float)
    duration_values = np.array([metrics[price_data.symbols[index]]["drawdown_days"] for index in valid_indices], dtype=float)
    risk_scores = (
        0.60 * normalize_metric(max_dd_values)
        + 0.25 * normalize_metric(volatility_values)
        + 0.15 * normalize_metric(duration_values)
    )
    inverse_risk = 1.0 / np.maximum(risk_scores, 1e-6)
    valid_weights = project_capped_simplex(inverse_risk / inverse_risk.sum(), max_weight)

    weights = np.zeros(len(price_data.symbols), dtype=float)
    for offset, index in enumerate(valid_indices):
        symbol = price_data.symbols[index]
        weights[index] = valid_weights[offset]
        metrics[symbol]["risk_score"] = float(risk_scores[offset])
    return weights, metrics, price_date, lookback_start, lookback_years


def multi_factor_shrink_weights(
    assets: list[Asset],
    price_data: PriceData,
    build_date: str,
    shrink_covariance: np.ndarray,
    issues: list[DataIssue],
    ai_tilt: str = "none",
    max_weight: float = MAX_WEIGHT,
) -> tuple[np.ndarray, dict[str, dict[str, float]], str, str, int]:
    price_index = previous_available_date_index(price_data.dates, build_date)
    price_date = price_data.dates[price_index]
    start_index = max(0, price_index - ANNUALIZATION_DAYS)
    observations = price_index - start_index + 1
    if observations < MIN_OBSERVATIONS:
        raise RuntimeError(f"多因子模型至少需要 {MIN_OBSERVATIONS} 个共同交易日，当前仅有 {observations} 个。")

    window_prices = price_data.prices[start_index : price_index + 1]
    window_returns = simple_returns(window_prices)
    valid_indices: list[int] = []
    metrics: dict[str, dict[str, float]] = {}
    momentum_values: list[float] = []
    low_vol_values: list[float] = []
    drawdown_values: list[float] = []
    liquidity_values: list[float] = []
    trend_strength_values: list[float] = []

    for index, symbol in enumerate(price_data.symbols):
        series = window_prices[:, index]
        asset_returns = window_returns[:, index]
        if len(series) < MIN_OBSERVATIONS or np.any(series <= 0) or not np.all(np.isfinite(series)):
            issues.append(DataIssue(symbol, "多因子模型资料不足或价格异常，模型盘已剔除"))
            continue
        curve = series / series[0]
        max_dd = abs(float(drawdown(curve).min()))
        volatility = annualized_volatility(asset_returns)
        if max_dd <= 0 or volatility <= 0:
            issues.append(DataIssue(symbol, "多因子模型回撤或波动不可估，模型盘已剔除"))
            continue
        if len(series) >= 253:
            momentum = float(series[-22] / series[-253] - 1.0)
        else:
            momentum = capped_compound_return(series, min(120, len(series) - 1))
        ma20 = mean_tail(series, 20)
        ma60 = mean_tail(series, 60)
        price_vs_ma60 = float(series[-1] / ma60 - 1.0) if ma60 and ma60 > 0 else 0.0
        ma_spread = float(ma20 / ma60 - 1.0) if ma20 and ma60 and ma60 > 0 else 0.0
        trend_strength = 0.6 * price_vs_ma60 + 0.4 * ma_spread
        liquidity = 0.0
        if price_data.amounts is not None:
            amount_series = price_data.amounts[start_index : price_index + 1, index]
            average_amount = mean_tail(amount_series, min(20, len(amount_series)))
            liquidity = math.log1p(average_amount or 0.0)
        valid_indices.append(index)
        momentum_values.append(momentum)
        low_vol_values.append(-volatility)
        drawdown_values.append(-max_dd)
        liquidity_values.append(liquidity)
        trend_strength_values.append(trend_strength)
        metrics[symbol] = {
            "max_drawdown": max_dd,
            "annual_volatility": volatility,
            "drawdown_days": float(max_drawdown_duration(drawdown(curve))),
        }

    if not valid_indices:
        raise RuntimeError("没有资产满足多因子模型盘建仓条件。")
    if len(valid_indices) * max_weight < 1:
        raise RuntimeError(f"满足条件的资产数量不足，无法在单一资产上限 {max_weight:.0%} 下满仓。")

    momentum_z = zscore(np.array(momentum_values, dtype=float))
    low_vol_z = zscore(np.array(low_vol_values, dtype=float))
    drawdown_z = zscore(np.array(drawdown_values, dtype=float))
    liquidity_z = zscore(np.array(liquidity_values, dtype=float))
    trend_strength_z = zscore(np.array(trend_strength_values, dtype=float))
    price_factor_scores = (
        0.28 * momentum_z
        + 0.22 * low_vol_z
        + 0.20 * drawdown_z
        + 0.12 * liquidity_z
        + 0.18 * trend_strength_z
    )
    industry_ai_scores, macro_external_scores = build_proxy_external_overlay(
        assets=assets,
        price_data=price_data,
        valid_indices=valid_indices,
        momentum_values=np.array(momentum_values, dtype=float),
        low_vol_values=np.array(low_vol_values, dtype=float),
        drawdown_values=np.array(drawdown_values, dtype=float),
        liquidity_values=np.array(liquidity_values, dtype=float),
        trend_strength_values=np.array(trend_strength_values, dtype=float),
    )
    composite_scores = 0.60 * price_factor_scores + 0.25 * industry_ai_scores + 0.15 * macro_external_scores
    expected_returns = 0.06 + 0.025 * composite_scores
    valid_covariance = shrink_covariance[np.ix_(valid_indices, valid_indices)]
    valid_weights = drop_tiny_weights(max_sharpe_weights(expected_returns, valid_covariance, max_weight), max_weight=max_weight)
    asset_by_symbol = {asset.symbol: asset for asset in assets}
    ai_mask = np.array(
        [asset_by_symbol.get(price_data.symbols[index], Asset(price_data.symbols[index], "", "", "")).ai_supply_chain for index in valid_indices],
        dtype=bool,
    )
    if ai_tilt == "moderate":
        valid_weights = drop_tiny_weights(apply_group_tilt(valid_weights, ai_mask, 0.33, 0.35, max_weight), max_weight=max_weight)
        issues.append(DataIssue("MODEL_PORTFOLIO", "AI 供应链倾斜：moderate，软目标约 33%，群组上限 35%。"))
    elif ai_tilt == "strong":
        valid_weights = drop_tiny_weights(apply_group_tilt(valid_weights, ai_mask, 0.38, 0.40, max_weight), max_weight=max_weight)
        issues.append(DataIssue("MODEL_PORTFOLIO", "AI 供应链倾斜：strong，软目标约 38%，群组上限 40%。"))

    weights = np.zeros(len(price_data.symbols), dtype=float)
    for offset, index in enumerate(valid_indices):
        symbol = price_data.symbols[index]
        weights[index] = valid_weights[offset]
        metrics[symbol]["risk_score"] = float(composite_scores[offset])
        metrics[symbol]["price_factor_score"] = float(price_factor_scores[offset])
        metrics[symbol]["industry_ai_score"] = float(industry_ai_scores[offset])
        metrics[symbol]["macro_external_score"] = float(macro_external_scores[offset])
        metrics[symbol]["composite_score"] = float(composite_scores[offset])
        metrics[symbol]["trend_strength_score"] = float(trend_strength_z[offset])
    return weights, metrics, price_date, price_data.dates[start_index], 1


def mean_tail(values: np.ndarray, window: int) -> float | None:
    if len(values) < window:
        return None
    tail = values[-window:]
    if not np.all(np.isfinite(tail)):
        return None
    return float(np.mean(tail))


def rsi(values: np.ndarray, window: int = 14) -> float | None:
    if len(values) <= window:
        return None
    deltas = np.diff(values[-(window + 1) :])
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    average_gain = float(np.mean(gains))
    average_loss = float(np.mean(losses))
    if average_loss <= 1e-12:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return float(100 - 100 / (1 + relative_strength))


def pct_change(values: np.ndarray, days: int) -> float | None:
    if len(values) <= days or values[-days - 1] <= 0:
        return None
    return float(values[-1] / values[-days - 1] - 1.0)


def consecutive_true(flags: list[bool]) -> int:
    count = 0
    for flag in reversed(flags):
        if not flag:
            break
        count += 1
    return count


def concentration_metrics(weights: np.ndarray) -> dict[str, float]:
    clean = np.asarray(weights, dtype=float)
    hhi = float(np.sum(clean**2))
    top3_weight = float(np.sum(np.sort(clean)[-3:])) if len(clean) >= 3 else float(np.sum(clean))
    active_count = float(np.sum(clean > 1e-6))
    return {
        "hhi": hhi,
        "effective_n": float(1.0 / hhi) if hhi > 0 else 0.0,
        "top3_weight": top3_weight,
        "active_count": active_count,
        "max_weight": float(np.max(clean)) if len(clean) else 0.0,
    }


def legacy_multi_factor_weights(
    assets: list[Asset],
    price_data: PriceData,
    build_date: str,
    shrink_covariance: np.ndarray,
    ai_tilt: str = "none",
    max_weight: float = MAX_WEIGHT,
) -> np.ndarray:
    price_index = previous_available_date_index(price_data.dates, build_date)
    start_index = max(0, price_index - ANNUALIZATION_DAYS)
    observations = price_index - start_index + 1
    if observations < MIN_OBSERVATIONS:
        raise RuntimeError(f"旧 4 因子比较至少需要 {MIN_OBSERVATIONS} 个共同交易日，当前仅有 {observations} 个。")

    window_prices = price_data.prices[start_index : price_index + 1]
    window_returns = simple_returns(window_prices)
    valid_indices: list[int] = []
    momentum_values: list[float] = []
    low_vol_values: list[float] = []
    drawdown_values: list[float] = []
    liquidity_values: list[float] = []

    for index, _symbol in enumerate(price_data.symbols):
        series = window_prices[:, index]
        asset_returns = window_returns[:, index]
        if len(series) < MIN_OBSERVATIONS or np.any(series <= 0) or not np.all(np.isfinite(series)):
            continue
        curve = series / series[0]
        max_dd = abs(float(drawdown(curve).min()))
        volatility = annualized_volatility(asset_returns)
        if max_dd <= 0 or volatility <= 0:
            continue
        if len(series) >= 253:
            momentum = float(series[-22] / series[-253] - 1.0)
        else:
            momentum = capped_compound_return(series, min(120, len(series) - 1))
        liquidity = 0.0
        if price_data.amounts is not None:
            amount_series = price_data.amounts[start_index : price_index + 1, index]
            average_amount = mean_tail(amount_series, min(20, len(amount_series)))
            liquidity = float(np.log1p(average_amount or 0.0))
        valid_indices.append(index)
        momentum_values.append(momentum)
        low_vol_values.append(-volatility)
        drawdown_values.append(-max_dd)
        liquidity_values.append(liquidity)

    momentum_z = zscore(np.array(momentum_values, dtype=float))
    low_vol_z = zscore(np.array(low_vol_values, dtype=float))
    drawdown_z = zscore(np.array(drawdown_values, dtype=float))
    liquidity_z = zscore(np.array(liquidity_values, dtype=float))
    legacy_scores = 0.35 * momentum_z + 0.25 * low_vol_z + 0.25 * drawdown_z + 0.15 * liquidity_z
    expected_returns = 0.06 + 0.025 * legacy_scores
    valid_covariance = shrink_covariance[np.ix_(valid_indices, valid_indices)]
    valid_weights = drop_tiny_weights(max_sharpe_weights(expected_returns, valid_covariance, max_weight), max_weight=max_weight)

    asset_by_symbol = {asset.symbol: asset for asset in assets}
    ai_mask = np.array(
        [asset_by_symbol.get(price_data.symbols[index], Asset(price_data.symbols[index], "", "", "")).ai_supply_chain for index in valid_indices],
        dtype=bool,
    )
    if ai_tilt == "moderate":
        valid_weights = drop_tiny_weights(apply_group_tilt(valid_weights, ai_mask, 0.33, 0.35, max_weight), max_weight=max_weight)
    elif ai_tilt == "strong":
        valid_weights = drop_tiny_weights(apply_group_tilt(valid_weights, ai_mask, 0.38, 0.40, max_weight), max_weight=max_weight)

    weights = np.zeros(len(price_data.symbols), dtype=float)
    for offset, index in enumerate(valid_indices):
        weights[index] = valid_weights[offset]
    return weights


def strategy_structure_summary(
    assets: list[Asset],
    price_data: PriceData,
    build_date: str,
    shrink_covariance: np.ndarray,
    ai_tilt: str = "moderate",
) -> str:
    legacy_weights = legacy_multi_factor_weights(assets, price_data, build_date, shrink_covariance, ai_tilt=ai_tilt)
    expanded_weights, _, _, _, _ = multi_factor_shrink_weights(
        assets=assets,
        price_data=price_data,
        build_date=build_date,
        shrink_covariance=shrink_covariance,
        issues=[],
        ai_tilt=ai_tilt,
    )
    legacy_conc = concentration_metrics(legacy_weights)
    expanded_conc = concentration_metrics(expanded_weights)
    legacy_rc = risk_contribution(legacy_weights, shrink_covariance)
    expanded_rc = risk_contribution(expanded_weights, shrink_covariance)
    legacy_ai_group = next(
        (
            group
            for group in aggregate_group_exposure(
                assets,
                price_data.symbols,
                legacy_weights,
                legacy_rc,
                lambda asset: "AI 供应链" if asset and asset.ai_supply_chain else "非 AI 供应链",
            )
            if group["group"] == "AI 供应链"
        ),
        {"weight": 0.0, "risk": 0.0},
    )
    expanded_ai_group = next(
        (
            group
            for group in aggregate_group_exposure(
                assets,
                price_data.symbols,
                expanded_weights,
                expanded_rc,
                lambda asset: "AI 供应链" if asset and asset.ai_supply_chain else "非 AI 供应链",
            )
            if group["group"] == "AI 供应链"
        ),
        {"weight": 0.0, "risk": 0.0},
    )
    legacy_stress = stress_loss(legacy_weights, shrink_covariance)
    expanded_stress = stress_loss(expanded_weights, shrink_covariance)
    return (
        "相较旧 4 因子，新扩展框架更分散："
        f"HHI 从 {legacy_conc['hhi']:.4f} 降到 {expanded_conc['hhi']:.4f}，"
        f"前三大权重从 {format_percent(legacy_conc['top3_weight'])} 降到 {format_percent(expanded_conc['top3_weight'])}，"
        f"有效持仓数从 {legacy_conc['effective_n']:.2f} 升到 {expanded_conc['effective_n']:.2f}；"
        f"AI 供应链权重从 {format_percent(float(legacy_ai_group['weight']))} 升到 {format_percent(float(expanded_ai_group['weight']))}，"
        f"风险贡献从 {format_percent(float(legacy_ai_group['risk']))} 升到 {format_percent(float(expanded_ai_group['risk']))}；"
        f"压力估计损失从 {format_percent(abs(legacy_stress))} 变为 {format_percent(abs(expanded_stress))}。"
        "结论是组合更分散，但风险仍更偏向 AI 供应链。"
    )


def build_trade_signals(
    price_data: PriceData,
    model_portfolio: ModelPortfolio | None,
    trade_output_path: Path | None = None,
    trade_batch_seq: str = "01",
) -> list[TradeSignal]:
    if not model_portfolio:
        return []
    trade_batch_seq = normalize_simulated_trade_batch_seq(trade_batch_seq)
    position_by_symbol = {position.symbol: position for position in model_portfolio.positions}
    market_pnl_history = load_recent_market_pnl_history(model_portfolio.market_date)
    executed_trade_ids, legacy_trade_keys = load_simulated_trade_keys(model_portfolio.market_date, trade_output_path)
    signals: list[TradeSignal] = []
    for index, symbol in enumerate(price_data.symbols):
        position = position_by_symbol.get(symbol)
        if not position:
            continue
        series = price_data.prices[:, index]
        if len(series) < MIN_OBSERVATIONS or not np.all(np.isfinite(series[-MIN_OBSERVATIONS:])):
            continue
        latest_price = position.current_price or float(series[-1])
        ma20 = mean_tail(series, 20)
        ma60 = mean_tail(series, 60)
        rsi14 = rsi(series, 14)
        ret20 = pct_change(series, 20)
        ret60 = pct_change(series, 60)
        volume_ratio: float | None = None
        average_amount20: float | None = None
        if price_data.volumes is not None:
            volume_series = price_data.volumes[:, index]
            average_volume20 = mean_tail(volume_series, 20)
            if average_volume20 and average_volume20 > 0:
                latest_volume = position.current_total_volume or volume_series[-1]
                volume_ratio = float(latest_volume / average_volume20)
        if price_data.amounts is not None:
            amount_series = price_data.amounts[:, index]
            average_amount20 = mean_tail(amount_series, 20)
        cost_price = position.price
        entry_return = (latest_price / cost_price - 1.0) if cost_price else None
        action = "观察"
        status = "observe"
        reason = "未触发价格目标或风险控制阈值，继续持有并观察。"
        trigger_code = ""
        proposed_shares: int | None = None
        shares = int(position.shares or 0)

        trend_positive = ma20 is not None and ma60 is not None and latest_price >= ma60 and ma20 >= ma60
        trend_negative = ma20 is not None and ma60 is not None and latest_price < ma60 and ma20 < ma60
        is_overheated = rsi14 is not None and rsi14 >= 70
        is_cool = rsi14 is not None and 35 <= rsi14 <= 55
        trend_factor = 1.0 if trend_positive else (-1.0 if trend_negative else 0.0)
        momentum_factor = 0.0
        if ret20 is not None and ret60 is not None:
            momentum_factor = (1.0 if ret20 > 0 else -1.0) + (1.0 if ret60 > 0 else -1.0)
            momentum_factor /= 2.0
        risk_factor = 0.0
        if entry_return is not None:
            if entry_return <= -0.06:
                risk_factor = -1.0
            elif entry_return >= 0.08:
                risk_factor = 0.5
        volume_factor = 0.0
        if volume_ratio is not None:
            if volume_ratio >= 1.5:
                volume_factor = 1.0
            elif volume_ratio <= 0.7:
                volume_factor = -0.5
        factor_score = 0.35 * trend_factor + 0.25 * momentum_factor + 0.25 * risk_factor + 0.15 * volume_factor

        buy_flags: list[bool] = []
        sell_flags: list[bool] = []
        for offset in range(max(0, len(series) - 5), len(series)):
            partial = series[: offset + 1]
            partial_ma20 = mean_tail(partial, 20)
            partial_ma60 = mean_tail(partial, 60)
            partial_rsi = rsi(partial, 14)
            partial_price = float(partial[-1])
            partial_entry_return = (partial_price / cost_price - 1.0) if cost_price else None
            partial_trend_positive = partial_ma20 is not None and partial_ma60 is not None and partial_price >= partial_ma60 and partial_ma20 >= partial_ma60
            partial_trend_negative = partial_ma20 is not None and partial_ma60 is not None and partial_price < partial_ma60 and partial_ma20 < partial_ma60
            partial_cool = partial_rsi is not None and 35 <= partial_rsi <= 55
            partial_hot = partial_rsi is not None and partial_rsi >= 70
            buy_flags.append(bool(partial_entry_return is not None and partial_entry_return <= -0.03 and partial_trend_positive and partial_cool))
            sell_flags.append(bool(partial_entry_return is not None and (partial_entry_return <= -0.06 or (partial_trend_negative and partial_entry_return < -0.03) or (partial_entry_return >= 0.08 and partial_hot))))
        buy_persistence = consecutive_true(buy_flags)
        sell_persistence = consecutive_true(sell_flags)
        market_loss_persistence = consecutive_true([value <= -0.06 for _, value in market_pnl_history.get(symbol, [])[-5:]])
        sell_persistence = max(sell_persistence, market_loss_persistence)
        persistence_days = max(buy_persistence, sell_persistence)

        if shares > 0 and entry_return is not None:
            if market_loss_persistence >= 2:
                action = "建议卖出"
                status = "sell"
                trigger_code = "market_loss_stop_25"
                proposed_shares = max(1, math.ceil(shares * 0.25))
                reason = "模拟盘连续收盘亏损超过约 6%，已连续观察至少 2 天，建议先减码 25%。"
            elif (entry_return <= -0.06 or (trend_negative and entry_return < -0.03)) and sell_persistence >= 2:
                action = "建议卖出"
                status = "sell"
                trigger_code = "cost_or_trend_stop_25"
                proposed_shares = max(1, math.ceil(shares * 0.25))
                reason = "价格跌破建仓成本约 6%，或跌破 60 日趋势且持仓转弱，并已连续观察至少 2 天，建议先减码 25%。"
            elif entry_return >= 0.08 and is_overheated and sell_persistence >= 2:
                action = "建议卖出"
                status = "sell"
                trigger_code = "profit_take_hot_20"
                proposed_shares = max(1, math.ceil(shares * 0.20))
                reason = "持仓获利超过约 8% 且 RSI 偏热，并已连续观察至少 2 天，建议分批获利了结 20%。"
            elif entry_return <= -0.03 and trend_positive and is_cool and buy_persistence >= 2 and volume_factor >= 0:
                action = "建议买入"
                status = "buy"
                trigger_code = "pullback_add_15"
                proposed_shares = max(1, math.floor(shares * 0.15))
                reason = "价格较建仓成本回落约 3%，但仍在 60 日趋势上方、RSI 未过热，且量能未明显萎缩，可考虑小幅加码。"
        trade_action = "sell" if status == "sell" else "buy" if status == "buy" else ""
        trade_id = (
            stable_simulated_trade_id(
                model_portfolio.market_date or model_portfolio.execution_date,
                model_portfolio.build_date,
                model_portfolio.method,
                symbol,
                trade_action,
                trigger_code,
                trade_batch_seq,
            )
            if trade_action
            else ""
        )
        if trade_action and (
            trade_id in executed_trade_ids
            or (
                trade_batch_seq == "01"
                and legacy_simulated_trade_key(model_portfolio.market_date or model_portfolio.execution_date, symbol, trade_action) in legacy_trade_keys
            )
        ):
            action = "观察"
            status = "observe"
            proposed_shares = None
            reason = "本日模拟调仓已落账，当前不再列为待确认清单。"

        signals.append(
            TradeSignal(
                symbol=symbol,
                name=position.name,
                trade_id=trade_id,
                trigger_code=trigger_code,
                action=action,
                status=status,
                reason=reason,
                latest_price=latest_price,
                cost_price=cost_price,
                ma20=ma20,
                ma60=ma60,
                rsi14=rsi14,
                volume_ratio=volume_ratio,
                average_amount20=average_amount20,
                factor_score=factor_score,
                persistence_days=persistence_days,
                return_since_entry=entry_return,
                proposed_shares=proposed_shares,
            )
        )
    return signals


def short_trade_reason(signal: TradeSignal) -> str:
    if "已落账" in signal.reason:
        return "已落账"
    if signal.trigger_code == "market_loss_stop_25":
        return "亏损止损"
    if signal.trigger_code == "cost_or_trend_stop_25":
        return "趋势转弱"
    if signal.trigger_code == "profit_take_hot_20":
        return "获利了结"
    if signal.trigger_code == "pullback_add_15":
        return "回落加码"
    if signal.status == "observe":
        return "继续观察"
    return signal.reason[:10]


def build_model_portfolio(
    assets: list[Asset],
    price_data: PriceData,
    weights: np.ndarray,
    initial_cash: float,
    output_path: Path,
    build_date: str,
    analysis_start_date: str,
    analysis_end_date: str,
    method: str,
    ai_tilt: str | None = None,
    invest_ratio: float = DEFAULT_MODEL_INVEST_RATIO,
    risk_metrics: dict[str, dict[str, float]] | None = None,
    lookback_years: int = MODEL_LOOKBACK_YEARS,
    execution_price_ready: bool = False,
    execution_orders: dict[str, dict[str, float]] | None = None,
    market_values: dict[str, dict[str, float]] | None = None,
) -> ModelPortfolio:
    if initial_cash <= 0:
        raise RuntimeError("模型盘初始资金必须大于 0。")
    if not 0 < invest_ratio <= 1:
        raise RuntimeError("模型盘目标建仓比例必须大于 0 且不超过 1。")
    invest_cash = initial_cash * invest_ratio
    cash_reserve = initial_cash - invest_cash
    asset_name = {asset.symbol: asset.name for asset in assets}
    price_index = price_data.dates.index(analysis_end_date)
    latest_prices = price_data.prices[price_index]
    positions: list[ModelPosition] = []

    for index, symbol in enumerate(price_data.symbols):
        analysis_price = float(latest_prices[index])
        target_weight = float(weights[index])
        target_value = invest_cash * target_weight
        order = (execution_orders or {}).get(symbol)
        buy_commission = None
        buy_tax = None
        total_buy_cost = None
        future_sell_tax = None
        current_price = None
        current_market_value = None
        unrealized_pnl = None
        unrealized_pnl_pct = None
        current_volume = None
        current_total_volume = None
        current_total_amount = None
        if order:
            price = order.get("buy_reference_price")
            shares = int(order.get("shares", 0))
            market_value = order.get("gross_amount")
            buy_commission = order.get("buy_commission_estimate")
            buy_tax = order.get("buy_tax_estimate")
            total_buy_cost = order.get("total_buy_cost")
            future_sell_tax = order.get("future_sell_tax_estimate")
        elif execution_price_ready:
            price = analysis_price
            shares = int(math.floor(target_value / price)) if price > 0 else 0
            market_value = shares * price
        else:
            price = None
            shares = None
            market_value = None
        if target_weight <= 0 and not order:
            continue
        mark = (market_values or {}).get(symbol)
        if mark:
            current_price = mark.get("current_price")
            if shares is not None and current_price is not None:
                current_market_value = shares * current_price
                cost_basis = total_buy_cost if total_buy_cost is not None else market_value or 0.0
                unrealized_pnl = current_market_value - cost_basis
                unrealized_pnl_pct = unrealized_pnl / cost_basis if cost_basis else 0.0
            else:
                current_market_value = mark.get("current_market_value")
                unrealized_pnl = mark.get("unrealized_pnl")
                unrealized_pnl_pct = mark.get("unrealized_pnl_pct")
            current_volume = mark.get("volume")
            current_total_volume = mark.get("total_volume")
            current_total_amount = mark.get("total_amount")
        metrics = (risk_metrics or {}).get(symbol, {})
        positions.append(
            ModelPosition(
                symbol=symbol,
                name=asset_name.get(symbol, ""),
                price=price,
                max_drawdown=metrics.get("max_drawdown"),
                annual_volatility=metrics.get("annual_volatility"),
                drawdown_days=int(metrics["drawdown_days"]) if "drawdown_days" in metrics else None,
                risk_score=metrics.get("risk_score"),
                price_factor_score=metrics.get("price_factor_score"),
                industry_ai_score=metrics.get("industry_ai_score"),
                macro_external_score=metrics.get("macro_external_score"),
                composite_score=metrics.get("composite_score"),
                trend_strength_score=metrics.get("trend_strength_score"),
                target_weight=target_weight,
                target_value=target_value,
                shares=shares,
                market_value=market_value,
                buy_commission=buy_commission,
                buy_tax=buy_tax,
                total_buy_cost=total_buy_cost,
                future_sell_tax=future_sell_tax,
                current_price=current_price,
                current_market_value=current_market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
                current_volume=current_volume,
                current_total_volume=current_total_volume,
                current_total_amount=current_total_amount,
            )
        )

    invested_value = float(sum(position.market_value or 0.0 for position in positions))
    total_buy_cost = float(sum(position.total_buy_cost if position.total_buy_cost is not None else position.market_value or 0.0 for position in positions))
    remaining_cash = initial_cash - total_buy_cost
    market_meta = next(iter((market_values or {}).values()), {})
    dated_output_path = output_path.with_name(f"model_portfolio_{build_date}.csv")
    portfolio = ModelPortfolio(
        build_date=build_date,
        analysis_start_date=analysis_start_date,
        analysis_end_date=analysis_end_date,
        execution_date=build_date,
        execution_price_status="ready" if execution_price_ready or execution_orders else "pending_open_price",
        method=method,
        ai_tilt=ai_tilt,
        lookback_years=lookback_years,
        initial_cash=initial_cash,
        invest_ratio=invest_ratio,
        cash_reserve=cash_reserve,
        invested_value=invested_value,
        remaining_cash=remaining_cash,
        total_value=invested_value + remaining_cash,
        positions=positions,
        output_path=output_path,
        dated_output_path=dated_output_path,
        market_date=str(market_meta.get("market_date") or "") or None,
        market_mode=str(market_meta.get("market_mode") or "") or None,
        market_quote_time=str(market_meta.get("quote_time") or "") or None,
    )
    write_model_portfolio_csv(portfolio, output_path)
    write_model_portfolio_csv(portfolio, dated_output_path)
    return portfolio


def write_model_portfolio_csv(portfolio: ModelPortfolio, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "build_date",
                "analysis_start_date",
                "analysis_end_date",
                "execution_date",
                "execution_price_status",
                "method",
                "lookback_years",
                "invest_ratio",
                "cash_reserve",
                "symbol",
                "name",
                "execution_price",
                "max_drawdown",
                "annual_volatility",
                "drawdown_days",
                "risk_score",
                "price_factor_score",
                "industry_ai_score",
                "macro_external_score",
                "composite_score",
                "trend_strength_score",
                "target_weight",
                "target_value",
                "shares",
                "market_value",
                "buy_commission",
                "buy_tax",
                "total_buy_cost",
                "future_sell_tax_estimate",
                "current_price",
                "current_market_value",
                "unrealized_pnl",
                "unrealized_pnl_pct",
                "remaining_cash",
            ]
        )
        for position in portfolio.positions:
            writer.writerow(
                [
                    portfolio.build_date,
                    portfolio.analysis_start_date,
                    portfolio.analysis_end_date,
                    portfolio.execution_date,
                    portfolio.execution_price_status,
                    portfolio.method,
                    portfolio.lookback_years,
                    f"{portfolio.invest_ratio:.4f}",
                    f"{portfolio.cash_reserve:.2f}",
                    position.symbol,
                    position.name,
                    "" if position.price is None else f"{position.price:.4f}",
                    "" if position.max_drawdown is None else f"{position.max_drawdown:.8f}",
                    "" if position.annual_volatility is None else f"{position.annual_volatility:.8f}",
                    "" if position.drawdown_days is None else position.drawdown_days,
                    "" if position.risk_score is None else f"{position.risk_score:.8f}",
                    "" if position.price_factor_score is None else f"{position.price_factor_score:.8f}",
                    "" if position.industry_ai_score is None else f"{position.industry_ai_score:.8f}",
                    "" if position.macro_external_score is None else f"{position.macro_external_score:.8f}",
                    "" if position.composite_score is None else f"{position.composite_score:.8f}",
                    "" if position.trend_strength_score is None else f"{position.trend_strength_score:.8f}",
                    f"{position.target_weight:.8f}",
                    f"{position.target_value:.2f}",
                    "" if position.shares is None else position.shares,
                    "" if position.market_value is None else f"{position.market_value:.2f}",
                    "" if position.buy_commission is None else f"{position.buy_commission:.2f}",
                    "" if position.buy_tax is None else f"{position.buy_tax:.2f}",
                    "" if position.total_buy_cost is None else f"{position.total_buy_cost:.2f}",
                    "" if position.future_sell_tax is None else f"{position.future_sell_tax:.2f}",
                    "" if position.current_price is None else f"{position.current_price:.4f}",
                    "" if position.current_market_value is None else f"{position.current_market_value:.2f}",
                    "" if position.unrealized_pnl is None else f"{position.unrealized_pnl:.2f}",
                    "" if position.unrealized_pnl_pct is None else f"{position.unrealized_pnl_pct:.6f}",
                    f"{portfolio.remaining_cash:.2f}",
                ]
            )


def load_model_execution_orders(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    orders: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue
            try:
                shares = int(float(row.get("shares") or 0))
                price = float(row.get("buy_reference_price") or 0)
            except ValueError:
                continue
            if shares <= 0 or price <= 0:
                continue
            orders[symbol] = {
                "buy_reference_price": price,
                "shares": float(shares),
                "gross_amount": float(row.get("gross_amount") or price * shares),
                "buy_commission_estimate": float(row.get("buy_commission_estimate") or 0),
                "buy_tax_estimate": float(row.get("buy_tax_estimate") or 0),
                "total_buy_cost": float(row.get("total_buy_cost") or price * shares),
                "future_sell_tax_estimate": float(row.get("future_sell_tax_estimate") or 0),
            }
    return orders


def default_execution_orders_path(build_date: str) -> Path:
    if DEFAULT_SIMULATED_POSITIONS_OUTPUT.exists():
        return DEFAULT_SIMULATED_POSITIONS_OUTPUT
    return ROOT / "data" / f"manual_build_orders_{build_date}.csv"


def write_execution_orders_csv(orders: dict[str, dict[str, float]], assets: list[Asset], output_path: Path, execution_date: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    name_by_symbol = {asset.symbol: asset.name for asset in assets}
    fieldnames = [
        "execution_date",
        "symbol",
        "name",
        "buy_reference_price",
        "shares",
        "gross_amount",
        "buy_commission_estimate",
        "buy_tax_estimate",
        "total_buy_cost",
        "future_sell_tax_estimate",
        "status",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for symbol, order in orders.items():
            shares = int(order.get("shares") or 0)
            if shares <= 0:
                continue
            writer.writerow(
                {
                    "execution_date": execution_date,
                    "symbol": symbol,
                    "name": name_by_symbol.get(symbol, ""),
                    "buy_reference_price": f"{float(order.get('buy_reference_price') or 0):.4f}",
                    "shares": shares,
                    "gross_amount": f"{float(order.get('gross_amount') or 0):.2f}",
                    "buy_commission_estimate": f"{float(order.get('buy_commission_estimate') or 0):.2f}",
                    "buy_tax_estimate": f"{float(order.get('buy_tax_estimate') or 0):.2f}",
                    "total_buy_cost": f"{float(order.get('total_buy_cost') or 0):.2f}",
                    "future_sell_tax_estimate": f"{float(order.get('future_sell_tax_estimate') or 0):.2f}",
                    "status": "simulated_position",
                }
            )


def simulated_trade_file(trade_date: str, output_path: Path | None = None) -> Path:
    if output_path is not None:
        return output_path
    return ROOT / "data" / f"simulated_trades_{trade_date}.csv"


def latest_simulated_trade_file(trade_date: str | None = None, output_path: Path | None = None) -> Path:
    if output_path is not None:
        return output_path
    candidates = sorted(ROOT.glob("data/simulated_trades_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    if trade_date:
        return simulated_trade_file(trade_date)
    return ROOT / "data" / "simulated_trades_latest.csv"


def stable_simulated_trade_id(
    trade_date: str,
    build_date: str,
    method: str,
    symbol: str,
    action: str,
    trigger_code: str,
    batch_seq: str = "01",
) -> str:
    normalized_parts = [
        "paper-v1",
        trade_date.strip(),
        build_date.strip(),
        method.strip(),
        symbol.strip(),
        action.strip().lower(),
        trigger_code.strip(),
        batch_seq.strip(),
    ]
    digest = hashlib.sha256("|".join(normalized_parts).encode("utf-8")).hexdigest()[:10]
    date_label = trade_date.replace("-", "")
    return f"paper-{date_label}-{symbol.strip()}-{action.strip().lower()}-{batch_seq}-{digest}"


def legacy_simulated_trade_key(trade_date: str, symbol: str, action: str) -> str:
    return f"legacy:{trade_date.strip()}:{symbol.strip()}:{action.strip().lower()}"


def load_simulated_trade_keys(trade_date: str | None, trade_path: Path | None = None) -> tuple[set[str], set[str]]:
    if not trade_date:
        return set(), set()
    path = trade_path or latest_simulated_trade_file(trade_date)
    if not path.exists():
        return set(), set()
    trade_ids: set[str] = set()
    legacy_keys: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("status") or "").strip().lower() == "executed":
                trade_id = (row.get("trade_id") or "").strip()
                symbol = (row.get("symbol") or "").strip()
                action = (row.get("action") or "").strip()
                if trade_id:
                    trade_ids.add(trade_id)
                elif symbol and action:
                    legacy_keys.add(legacy_simulated_trade_key(trade_date, symbol, action))
    return trade_ids, legacy_keys


def simulated_trade_batch_from_id(trade_id: str) -> str | None:
    parts = trade_id.strip().split("-")
    if len(parts) < 6 or parts[0] != "paper":
        return None
    batch_seq = parts[-2]
    if len(batch_seq) == 2 and batch_seq.isdigit() and batch_seq != "00":
        return batch_seq
    return None


def load_simulated_trade_batch_status(
    trade_date: str | None,
    trade_path: Path | None = None,
) -> list[SimulatedTradeBatchStatus]:
    if not trade_date:
        return []
    path = trade_path or latest_simulated_trade_file(trade_date)
    if not path.exists():
        return []
    grouped: dict[str, dict[str, object]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("status") or "").strip().lower() != "executed":
                continue
            trade_id = (row.get("trade_id") or "").strip()
            batch_seq = simulated_trade_batch_from_id(trade_id) if trade_id else None
            key = batch_seq or "legacy"
            group = grouped.setdefault(
                key,
                {
                    "trade_count": 0,
                    "symbols": set(),
                    "actions": set(),
                    "is_legacy": key == "legacy",
                },
            )
            group["trade_count"] = int(group["trade_count"]) + 1
            symbol = (row.get("symbol") or "").strip()
            action = (row.get("action") or "").strip().lower()
            if symbol:
                group["symbols"].add(symbol)  # type: ignore[union-attr]
            if action:
                group["actions"].add(action)  # type: ignore[union-attr]

    statuses: list[SimulatedTradeBatchStatus] = []
    for key, group in grouped.items():
        is_legacy = bool(group["is_legacy"])
        label = "舊格式" if is_legacy else f"批次 {key}"
        statuses.append(
            SimulatedTradeBatchStatus(
                batch_seq=key,
                label=label,
                trade_count=int(group["trade_count"]),
                symbols=tuple(sorted(group["symbols"])),  # type: ignore[arg-type]
                actions=tuple(sorted(group["actions"])),  # type: ignore[arg-type]
                is_legacy=is_legacy,
            )
        )
    return sorted(statuses, key=lambda item: (item.is_legacy, item.batch_seq))


def load_simulated_trade_execution_summary(
    trade_date: str | None,
    trade_path: Path | None = None,
) -> SimulatedTradeExecutionSummary | None:
    path = trade_path or latest_simulated_trade_file(trade_date)
    if not path.exists():
        return None
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("status") or "").strip().lower() == "executed":
                rows.append(row)
    if not rows:
        return None
    row_trade_dates = sorted({(row.get("trade_date") or "").strip() for row in rows if (row.get("trade_date") or "").strip()})
    summary_trade_date = row_trade_dates[-1] if row_trade_dates else (trade_date or "")
    buy_count = sum(1 for row in rows if (row.get("action") or "").strip().lower() == "buy")
    sell_count = sum(1 for row in rows if (row.get("action") or "").strip().lower() == "sell")
    symbols = tuple(sorted({(row.get("symbol") or "").strip() for row in rows if (row.get("symbol") or "").strip()}))
    details = tuple(
        f"{(row.get('symbol') or '').strip()} {('买入' if (row.get('action') or '').strip().lower() == 'buy' else '卖出')} {(row.get('shares') or '').strip()} 股"
        for row in rows
        if (row.get("symbol") or "").strip()
    )
    return SimulatedTradeExecutionSummary(
        trade_date=summary_trade_date,
        trade_count=len(rows),
        buy_count=buy_count,
        sell_count=sell_count,
        symbols=symbols,
        details=details,
        source_path=path,
    )


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


def add_weekdays(start: date, count: int) -> date:
    current = start
    remaining = max(0, count)
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def write_simulated_trades(
    portfolio: ModelPortfolio,
    signals: list[TradeSignal],
    execution_orders: dict[str, dict[str, float]],
    assets: list[Asset],
    trade_output_path: Path | None = None,
    positions_output_path: Path | None = None,
    trade_batch_seq: str = "01",
) -> tuple[Path, Path, int]:
    trade_date = portfolio.market_date or date.today().isoformat()
    trade_batch_seq = normalize_simulated_trade_batch_seq(trade_batch_seq)
    trade_path = simulated_trade_file(trade_date, trade_output_path)
    positions_path = positions_output_path or DEFAULT_SIMULATED_POSITIONS_OUTPUT
    existing_rows: list[dict[str, object]] = []
    existing_trade_ids, legacy_trade_keys = load_simulated_trade_keys(trade_date, trade_path)
    if trade_path.exists():
        with trade_path.open("r", encoding="utf-8-sig", newline="") as handle:
            existing_rows = list(csv.DictReader(handle))

    position_by_symbol = {position.symbol: position for position in portfolio.positions}
    name_by_symbol = {asset.symbol: asset.name for asset in assets}
    new_rows: list[dict[str, object]] = []
    for signal in signals:
        if signal.status not in {"buy", "sell"} or signal.proposed_shares is None:
            continue
        action = "sell" if signal.status == "sell" else "buy"
        trade_id = signal.trade_id or stable_simulated_trade_id(
            trade_date,
            portfolio.build_date,
            portfolio.method,
            signal.symbol,
            action,
            signal.trigger_code,
            trade_batch_seq,
        )
        if trade_id in existing_trade_ids or (
            trade_batch_seq == "01" and legacy_simulated_trade_key(trade_date, signal.symbol, action) in legacy_trade_keys
        ):
            continue
        if action != "sell":
            continue
        order = execution_orders.get(signal.symbol)
        position = position_by_symbol.get(signal.symbol)
        if not order or not position or not position.shares:
            continue
        current_shares = int(order.get("shares") or 0)
        trade_shares = min(int(signal.proposed_shares), current_shares)
        if trade_shares <= 0:
            continue
        trade_price = float(signal.latest_price)
        gross_amount = trade_shares * trade_price
        fee = round(gross_amount * 0.001425)
        previous_gross = float(order.get("gross_amount") or 0)
        tax_rate = (float(order.get("future_sell_tax_estimate") or 0) / previous_gross) if previous_gross > 0 else 0.003
        tax = round(gross_amount * tax_rate)
        net_amount = gross_amount - fee - tax
        current_cost = float(order.get("total_buy_cost") or 0)
        unit_cost = current_cost / current_shares if current_shares else 0.0
        realized_cost = unit_cost * trade_shares
        realized_pnl = net_amount - realized_cost

        remaining_shares = current_shares - trade_shares
        ratio = remaining_shares / current_shares if current_shares else 0.0
        order["shares"] = float(remaining_shares)
        order["gross_amount"] = float(order.get("gross_amount") or 0) * ratio
        order["buy_commission_estimate"] = float(order.get("buy_commission_estimate") or 0) * ratio
        order["buy_tax_estimate"] = float(order.get("buy_tax_estimate") or 0) * ratio
        order["total_buy_cost"] = current_cost * ratio
        order["future_sell_tax_estimate"] = float(order.get("future_sell_tax_estimate") or 0) * ratio

        new_rows.append(
            {
                "trade_id": trade_id,
                "trade_date": trade_date,
                "symbol": signal.symbol,
                "name": name_by_symbol.get(signal.symbol, signal.name),
                "action": action,
                "shares": trade_shares,
                "trade_price": f"{trade_price:.4f}",
                "gross_amount": f"{gross_amount:.2f}",
                "fee": f"{fee:.2f}",
                "tax": f"{tax:.2f}",
                "net_amount": f"{net_amount:.2f}",
                "realized_cost": f"{realized_cost:.2f}",
                "realized_pnl": f"{realized_pnl:.2f}",
                "remaining_shares": remaining_shares,
                "reason": signal.reason,
                "status": "executed",
            }
        )
        existing_trade_ids.add(trade_id)

    trade_fieldnames = [
        "trade_id",
        "trade_date",
        "symbol",
        "name",
        "action",
        "shares",
        "trade_price",
        "gross_amount",
        "fee",
        "tax",
        "net_amount",
        "realized_cost",
        "realized_pnl",
        "remaining_shares",
        "reason",
        "status",
    ]
    with trade_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=trade_fieldnames)
        writer.writeheader()
        for row in existing_rows + new_rows:
            writer.writerow({field: row.get(field, "") for field in trade_fieldnames})

    if positions_output_path is None:
        dated_positions = ROOT / "data" / f"simulated_positions_{trade_date}.csv"
    else:
        dated_positions = positions_path.with_name(f"{positions_path.stem}_{trade_date}{positions_path.suffix}")
    write_execution_orders_csv(execution_orders, assets, positions_path, trade_date)
    write_execution_orders_csv(execution_orders, assets, dated_positions, trade_date)
    return trade_path, dated_positions, len(new_rows)


def load_model_market_values(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    market_values: dict[str, dict[str, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue
            try:
                market_values[symbol] = {
                    "current_price": float(row.get("current_price") or 0),
                    "current_market_value": float(row.get("current_market_value") or 0),
                    "unrealized_pnl": float(row.get("unrealized_pnl") or 0),
                    "unrealized_pnl_pct": float(row.get("unrealized_pnl_pct") or 0),
                    "market_date": row.get("mark_date") or "",
                    "market_mode": row.get("market_mode") or "",
                    "quote_time": row.get("quote_time") or "",
                    "quote_status": row.get("quote_status") or "",
                    "volume": float(row.get("volume") or 0),
                    "total_volume": float(row.get("total_volume") or 0),
                    "total_amount": float(row.get("total_amount") or 0),
                }
            except ValueError:
                continue
    return market_values


def append_market_snapshot_to_price_data(price_data: PriceData, market_values_path: Path | None, issues: list[DataIssue]) -> PriceData:
    if not market_values_path or not market_values_path.exists():
        return price_data
    market_values = load_model_market_values(market_values_path)
    if not market_values:
        return price_data
    market_date = str(next(iter(market_values.values())).get("market_date") or "")
    if not market_date or (price_data.dates and market_date <= price_data.dates[-1]):
        return price_data

    prices: list[float] = []
    volumes: list[float] = []
    amounts: list[float] = []
    missing: list[str] = []
    for symbol in price_data.symbols:
        mark = market_values.get(symbol)
        price = float(mark.get("current_price") or 0.0) if mark else 0.0
        if price <= 0:
            missing.append(symbol)
            break
        prices.append(price)
        volumes.append(float(mark.get("total_volume") or mark.get("volume") or 0.0))
        amounts.append(float(mark.get("total_amount") or 0.0))
    if missing:
        issues.append(DataIssue("DAILY_MARKET", f"最新市值档 {market_values_path} 缺少 {missing[0]} 有效价格，未并入回测序列。"))
        return price_data

    appended_prices = np.vstack([price_data.prices, np.array(prices, dtype=float)])
    appended_volumes = (
        np.vstack([price_data.volumes, np.array(volumes, dtype=float)])
        if price_data.volumes is not None
        else np.array([volumes], dtype=float)
    )
    appended_amounts = (
        np.vstack([price_data.amounts, np.array(amounts, dtype=float)])
        if price_data.amounts is not None
        else np.array([amounts], dtype=float)
    )
    issues.append(DataIssue("DAILY_MARKET", f"已将最新市值档 {market_values_path} 并入回测价格序列，最新日期 {market_date}。"))
    return PriceData(
        dates=[*price_data.dates, market_date],
        symbols=price_data.symbols,
        prices=appended_prices,
        volumes=appended_volumes,
        amounts=appended_amounts,
    )


def build_public_close_market_values(
    assets: list[Asset],
    execution_orders: dict[str, dict[str, float]],
    price_data: PriceData,
    market_date: str,
    market_mode: str,
    output_path: Path,
) -> MarketSnapshotUpdate:
    if not price_data.dates:
        raise RuntimeError("缺少公开行情资料，无法生成每日持仓市值。")

    name_by_symbol = {asset.symbol: asset.name for asset in assets}
    symbol_index = {symbol: index for index, symbol in enumerate(price_data.symbols)}
    latest_prices = price_data.prices[-1]
    latest_volumes = price_data.volumes[-1]
    latest_amounts = price_data.amounts[-1]
    quote_time = datetime.now().isoformat(timespec="seconds")
    rows: list[dict[str, object]] = []
    market_values: dict[str, dict[str, float]] = {}
    missing_count = 0

    for symbol in [symbol for symbol in execution_orders if symbol in name_by_symbol]:
        order = execution_orders[symbol]
        shares = int(order.get("shares") or 0)
        entry_price = float(order.get("buy_reference_price") or 0)
        entry_cost = float(order.get("total_buy_cost") or entry_price * shares)
        index = symbol_index.get(symbol)
        if index is None:
            missing_count += 1
            current_price = 0.0
            current_market_value = 0.0
            unrealized_pnl = 0.0
            unrealized_pnl_pct = 0.0
            volume = 0.0
            total_volume = 0.0
            total_amount = 0.0
            price_source = "missing"
            quote_status = "missing"
        else:
            current_price = float(latest_prices[index])
            volume = float(latest_volumes[index]) if latest_volumes.size else 0.0
            total_volume = float(latest_volumes[index]) if latest_volumes.size else 0.0
            total_amount = float(latest_amounts[index]) if latest_amounts.size else 0.0
            current_market_value = shares * current_price if shares and current_price > 0 else 0.0
            unrealized_pnl = current_market_value - entry_cost
            unrealized_pnl_pct = unrealized_pnl / entry_cost if entry_cost else 0.0
            price_source = "public_close"
            quote_status = "ready" if current_price > 0 else "missing"
            if quote_status == "missing":
                missing_count += 1
        row = {
            "mark_date": market_date,
            "market_mode": market_mode,
            "quote_time": quote_time,
            "symbol": symbol,
            "name": name_by_symbol.get(symbol, ""),
            "shares": shares,
            "entry_price": entry_price,
            "entry_cost": entry_cost,
            "current_price": current_price,
            "current_price_source": price_source,
            "current_market_value": current_market_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "volume": volume,
            "total_volume": total_volume,
            "total_amount": total_amount,
            "quote_status": quote_status,
        }
        rows.append(row)
        market_values[symbol] = {
            "current_price": current_price,
            "current_market_value": current_market_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "market_date": market_date,
            "market_mode": market_mode,
            "quote_time": quote_time,
            "quote_status": quote_status,
            "volume": volume,
            "total_volume": total_volume,
            "total_amount": total_amount,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mark_date",
        "market_mode",
        "quote_time",
        "symbol",
        "name",
        "shares",
        "entry_price",
        "entry_cost",
        "current_price",
        "current_price_source",
        "current_market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "volume",
        "total_volume",
        "total_amount",
        "quote_status",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    summary_path = output_path.with_name(output_path.stem + "_summary.txt")
    total_cost = sum(float(row["entry_cost"]) for row in rows)
    total_market_value = sum(float(row["current_market_value"]) for row in rows)
    total_pnl = total_market_value - total_cost
    summary_path.write_text(
        "\n".join(
            [
                f"market_date={market_date}",
                f"market_mode={market_mode}",
                f"quote_time={quote_time}",
                f"total_cost={total_cost:.2f}",
                f"current_market_value={total_market_value:.2f}",
                f"unrealized_pnl={total_pnl:.2f}",
                f"unrealized_pnl_pct={(total_pnl / total_cost if total_cost else 0):.6f}",
                f"quote_count={len(rows) - missing_count}",
                f"missing_count={missing_count}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return MarketSnapshotUpdate(
        path=output_path,
        market_date=market_date,
        market_mode=market_mode,
        quote_time=quote_time,
        quote_count=len(rows) - missing_count,
        missing_count=missing_count,
    )


def load_recent_market_pnl_history(current_market_date: str | None) -> dict[str, list[tuple[str, float]]]:
    if not current_market_date:
        return {}
    history: dict[str, list[tuple[str, float]]] = {}
    for path in sorted((ROOT / "data").glob("model_portfolio_market_*.csv")):
        if "_intraday" in path.stem:
            continue
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    mark_date = (row.get("mark_date") or "").strip()
                    symbol = (row.get("symbol") or "").strip()
                    if not mark_date or mark_date > current_market_date or not symbol:
                        continue
                    if (row.get("market_mode") or "close") not in {"", "close"}:
                        continue
                    if (row.get("quote_status") or "ready") != "ready":
                        continue
                    pnl_pct = float(row.get("unrealized_pnl_pct") or 0.0)
                    history.setdefault(symbol, []).append((mark_date, pnl_pct))
        except (OSError, ValueError):
            continue
    for symbol, rows in history.items():
        deduped = {mark_date: value for mark_date, value in rows}
        history[symbol] = sorted(deduped.items())
    return history


def daily_market_output_path(market_date: str, market_mode: str) -> Path:
    suffix = "_intraday" if market_mode == "intraday" else ""
    return ROOT / "data" / f"model_portfolio_market_{market_date}{suffix}.csv"


def latest_market_values_path() -> Path | None:
    market_files = [
        path
        for path in (ROOT / "data").glob("model_portfolio_market_*.csv")
        if path.is_file()
    ]
    if not market_files:
        return None

    def rank(path: Path) -> tuple[str, int, float]:
        market_date = ""
        market_mode = ""
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.DictReader(handle), {})
                market_date = str(row.get("mark_date") or "")
                market_mode = str(row.get("market_mode") or "")
        except (OSError, StopIteration):
            pass
        mode_rank = 1 if market_mode == "close" else 0
        return market_date, mode_rank, path.stat().st_mtime

    return max(market_files, key=rank)


def snapshot_field(snapshot: object, name: str, default: object = None) -> object:
    if isinstance(snapshot, dict):
        return snapshot.get(name, default)
    return getattr(snapshot, name, default)


def snapshot_price(snapshot: object) -> tuple[float | None, str]:
    for field in ("close", "last_price", "price"):
        value = snapshot_field(snapshot, field)
        try:
            price = float(value)
        except (TypeError, ValueError):
            continue
        if price > 0 and math.isfinite(price):
            return price, field
    return None, "missing"


def update_daily_market_values(
    assets: list[Asset],
    execution_orders: dict[str, dict[str, float]],
    market_date: str,
    market_mode: str,
    output_path: Path,
) -> MarketSnapshotUpdate:
    if not execution_orders:
        raise RuntimeError("缺少已执行建仓单，无法计算每日持仓市值。")
    os.environ.setdefault("SJ_HOME_PATH", str(DEFAULT_SHIOAJI_HOME))
    DEFAULT_SHIOAJI_HOME.mkdir(parents=True, exist_ok=True)
    DEFAULT_SHIOAJI_HOME.chmod(0o700)
    try:
        import shioaji as sj
    except Exception as exc:
        raise RuntimeError(f"Shioaji 套件不可用：{exc}") from exc

    api_key, secret_key = shioaji_credentials()
    api = sj.Shioaji()
    name_by_symbol = {asset.symbol: asset.name for asset in assets}
    logged_in = False
    rows: list[dict[str, object]] = []
    quote_times: list[str] = []
    missing_count = 0
    run_quote_time = datetime.now().isoformat(timespec="seconds")
    try:
        api.login(api_key=api_key, secret_key=secret_key)
        logged_in = True
        symbols = [symbol for symbol in execution_orders if symbol in name_by_symbol]
        contracts = [api.Contracts.Stocks[symbol] for symbol in symbols]
        snapshots = api.snapshots(contracts) if contracts else []
        snapshot_by_symbol = {str(snapshot_field(snapshot, "code", "")): snapshot for snapshot in snapshots}
        for symbol in symbols:
            order = execution_orders[symbol]
            shares = int(order.get("shares") or 0)
            entry_price = float(order.get("buy_reference_price") or 0)
            entry_cost = float(order.get("total_buy_cost") or entry_price * shares)
            snapshot = snapshot_by_symbol.get(symbol)
            price, price_source = snapshot_price(snapshot or {})
            quote_time = str(snapshot_field(snapshot or {}, "datetime", "") or run_quote_time)
            total_volume = snapshot_field(snapshot or {}, "total_volume", "")
            total_amount = snapshot_field(snapshot or {}, "total_amount", "")
            volume = snapshot_field(snapshot or {}, "volume", "")
            quote_status = "ready" if price is not None else "missing"
            if quote_time:
                quote_times.append(quote_time)
            if price is None:
                missing_count += 1
                current_market_value = 0.0
                unrealized_pnl = 0.0
                unrealized_pnl_pct = 0.0
                current_price = 0.0
            else:
                current_price = price
                current_market_value = shares * current_price
                unrealized_pnl = current_market_value - entry_cost
                unrealized_pnl_pct = unrealized_pnl / entry_cost if entry_cost else 0.0
            rows.append(
                {
                    "mark_date": market_date,
                    "market_mode": market_mode,
                    "quote_time": quote_time,
                    "symbol": symbol,
                    "name": name_by_symbol.get(symbol, ""),
                    "shares": shares,
                    "entry_price": entry_price,
                    "entry_cost": entry_cost,
                    "current_price": current_price,
                    "current_price_source": price_source,
                    "current_market_value": current_market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "volume": volume,
                    "total_volume": total_volume,
                    "total_amount": total_amount,
                    "quote_status": quote_status,
                }
            )
    finally:
        logout = getattr(api, "logout", None)
        if logged_in and callable(logout):
            logout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mark_date",
        "market_mode",
        "quote_time",
        "symbol",
        "name",
        "shares",
        "entry_price",
        "entry_cost",
        "current_price",
        "current_price_source",
        "current_market_value",
        "unrealized_pnl",
        "unrealized_pnl_pct",
        "volume",
        "total_volume",
        "total_amount",
        "quote_status",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    summary_path = output_path.with_name(output_path.stem + "_summary.txt")
    total_cost = sum(float(row["entry_cost"]) for row in rows)
    total_market_value = sum(float(row["current_market_value"]) for row in rows)
    total_pnl = total_market_value - total_cost
    summary_path.write_text(
        "\n".join(
            [
                f"market_date={market_date}",
                f"market_mode={market_mode}",
                f"quote_time={max(quote_times) if quote_times else ''}",
                f"total_cost={total_cost:.2f}",
                f"current_market_value={total_market_value:.2f}",
                f"unrealized_pnl={total_pnl:.2f}",
                f"unrealized_pnl_pct={(total_pnl / total_cost if total_cost else 0):.6f}",
                f"quote_count={len(rows) - missing_count}",
                f"missing_count={missing_count}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return MarketSnapshotUpdate(
        path=output_path,
        market_date=market_date,
        market_mode=market_mode,
        quote_time=max(quote_times) if quote_times else "",
        quote_count=len(rows) - missing_count,
        missing_count=missing_count,
    )


def write_model_portfolio_status_csv(output_path: Path, build_date: str, method: str, message: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["build_date", "method", "status", "message"])
        writer.writerow([build_date, method, "not_generated", message])


def render_dashboard(
    output: Path,
    assets: list[Asset],
    price_data: PriceData,
    returns: np.ndarray,
    sample_weights: np.ndarray,
    shrink_weights: np.ndarray,
    sample_cov: np.ndarray,
    shrink_cov: np.ndarray,
    backtest: BacktestResult | None,
    model_portfolio: ModelPortfolio | None,
    issues: list[DataIssue],
    trade_output_path: Path | None = None,
    trade_batch_seq: str = "01",
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    symbols = price_data.symbols
    asset_name = {asset.symbol: asset.name for asset in assets}
    labels = [f"{symbol} {asset_name.get(symbol, '')}" for symbol in symbols]
    corr = correlation_matrix(returns)

    chart_dates = price_data.dates[1:]
    dashboard_data_start = price_data.dates[0] if price_data.dates else "无可用资料"
    dashboard_data_end = price_data.dates[-1] if price_data.dates else "无可用资料"
    dashboard_generated_date = date.today().isoformat()
    sample_curve = portfolio_curve(returns, sample_weights)
    shrink_curve = portfolio_curve(returns, shrink_weights)
    sample_dd = drawdown(sample_curve)
    shrink_dd = drawdown(shrink_curve)
    trade_batch_seq = normalize_simulated_trade_batch_seq(trade_batch_seq)
    trade_signals = build_trade_signals(price_data, model_portfolio, trade_output_path, trade_batch_seq)
    actionable_signals = [signal for signal in trade_signals if signal.status in {"buy", "sell"}]

    def format_optional_price(value: float | None) -> str:
        return "" if value is None else f"{value:.2f}"
    sample_rc = risk_contribution(sample_weights, sample_cov)
    shrink_rc = risk_contribution(shrink_weights, shrink_cov)
    sample_stress = stress_loss(sample_weights, sample_cov)
    shrink_stress = stress_loss(shrink_weights, shrink_cov)
    if model_portfolio:
        model_target_by_symbol = {position.symbol: position.target_weight for position in model_portfolio.positions}
        attribution_weights = np.array([model_target_by_symbol.get(symbol, 0.0) for symbol in symbols], dtype=float)
        weight_sum = float(attribution_weights.sum())
        if weight_sum > 0:
            attribution_weights = attribution_weights / weight_sum
        attribution_label = "模型盘目标权重"
    else:
        attribution_weights = shrink_weights
        attribution_label = "收缩协方差最小方差权重"
    attribution_rc = risk_contribution(attribution_weights, shrink_cov)
    sector_groups = aggregate_group_exposure(assets, symbols, attribution_weights, attribution_rc, lambda asset: asset.sector if asset else "")
    theme_groups = aggregate_group_exposure(assets, symbols, attribution_weights, attribution_rc, lambda asset: asset.theme if asset else "")
    ai_groups = aggregate_group_exposure(
        assets,
        symbols,
        attribution_weights,
        attribution_rc,
        lambda asset: "AI 供应链" if asset and asset.ai_supply_chain else "非 AI 供应链",
    )
    max_pair_text = "未发现高相关资产对"
    concentration_delta = float(np.max(sample_weights) - np.max(shrink_weights))
    drawdown_delta = float(shrink_dd.min() - sample_dd.min())

    overlap_pairs = []
    for left_index, left_symbol in enumerate(symbols):
        for right_index in range(left_index + 1, len(symbols)):
            value = float(corr[left_index, right_index])
            if value >= 0.75:
                overlap_pairs.append((left_symbol, symbols[right_index], value))
    overlap_pairs = sorted(overlap_pairs, key=lambda item: item[2], reverse=True)[:8]
    if overlap_pairs:
        max_pair_text = f"{overlap_pairs[0][0]} / {overlap_pairs[0][1]} ({overlap_pairs[0][2]:.2f})"

    top_sample_weight_index = int(np.argmax(sample_weights))
    top_shrink_weight_index = int(np.argmax(shrink_weights))
    top_sample_risk_index = int(np.argmax(sample_rc))
    top_shrink_risk_index = int(np.argmax(shrink_rc))
    sample_final = float(sample_curve[-1]) if len(sample_curve) else 1.0
    shrink_final = float(shrink_curve[-1]) if len(shrink_curve) else 1.0
    curve_leader = "收缩协方差" if shrink_final >= sample_final else "普通协方差"
    dd_leader = "收缩协方差" if shrink_dd.min() >= sample_dd.min() else "普通协方差"
    high_corr_count = len(overlap_pairs)
    heatmap_advice = (
        f"当前高相关资产对共 {high_corr_count} 组，最高为 {max_pair_text}。建议把这些标的视为同一风险来源，后续加码时避免同时扩大同源部位。"
        if high_corr_count
        else "当前没有相关性高于 0.75 的资产对，组合分散度暂时较好；后续仍需观察科技与 ETF 是否同步升高。"
    )
    weight_advice = (
        f"普通权重最高为 {symbols[top_sample_weight_index]}，收缩后最高为 {symbols[top_shrink_weight_index]}。"
        f"集中度变化 {format_percent(concentration_delta, signed=True)}；若集中度上升，调仓时应优先检查是否过度依赖单一资产。"
    )
    risk_advice = (
        f"收缩协方差下最大风险贡献来自 {symbols[top_shrink_risk_index]}，贡献 {format_percent(shrink_rc[top_shrink_risk_index])}。"
        f"普通协方差下最大风险贡献来自 {symbols[top_sample_risk_index]}。若风险贡献长期高于权重，应考虑减码或用现金池缓冲。"
    )
    top_sector = sector_groups[0] if sector_groups else {"group": "未分类", "weight": 0.0, "risk": 0.0, "count": 0}
    top_theme = theme_groups[0] if theme_groups else {"group": "未分类", "weight": 0.0, "risk": 0.0, "count": 0}
    ai_group = next((group for group in ai_groups if group["group"] == "AI 供应链"), {"group": "AI 供应链", "weight": 0.0, "risk": 0.0, "count": 0})
    non_ai_group = next((group for group in ai_groups if group["group"] == "非 AI 供应链"), {"group": "非 AI 供应链", "weight": 0.0, "risk": 0.0, "count": 0})
    ai_risk_gap = float(ai_group["risk"]) - float(ai_group["weight"])
    sector_theme_rows = "\n".join(
        f"<tr><td>{html.escape(str(item['group']))}</td><td>{int(item['count'])}</td><td>{format_percent(float(item['weight']))}</td><td>{format_percent(float(item['risk']))}</td><td>{format_percent(float(item['risk']) - float(item['weight']), signed=True)}</td></tr>"
        for item in sector_groups[:5]
    )
    theme_rows = "\n".join(
        f"<tr><td>{html.escape(str(item['group']))}</td><td>{int(item['count'])}</td><td>{format_percent(float(item['weight']))}</td><td>{format_percent(float(item['risk']))}</td><td>{format_percent(float(item['risk']) - float(item['weight']), signed=True)}</td></tr>"
        for item in theme_groups[:5]
    )
    ai_rows = "\n".join(
        f"<tr><td>{html.escape(str(item['group']))}</td><td>{int(item['count'])}</td><td>{format_percent(float(item['weight']))}</td><td>{format_percent(float(item['risk']))}</td><td>{format_percent(float(item['risk']) - float(item['weight']), signed=True)}</td></tr>"
        for item in ai_groups
    )
    group_risk_html = f"""
      <section class="section panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Group Risk Attribution</span>
            <h2>行业、主题与 AI 供应链风险归因</h2>
          </div>
          <span class="status-pill">{len(sector_groups)} 组行业 / {len(theme_groups)} 组主题</span>
        </div>
        <div class="analysis-note"><b>行业风险归因：</b>{html.escape(attribution_label)}口径下，风险贡献最高行业为 {html.escape(str(top_sector['group']))}，权重 {format_percent(float(top_sector['weight']))}、风险贡献 {format_percent(float(top_sector['risk']))}。这是群组风险解释，不代表该行业应立即买入或卖出。</div>
        <div class="analysis-note"><b>主题风险归因：</b>风险贡献最高主题为 {html.escape(str(top_theme['group']))}，权重 {format_percent(float(top_theme['weight']))}、风险贡献 {format_percent(float(top_theme['risk']))}；若风险贡献长期高于权重，代表同源风险可能比表面权重更集中。</div>
        <div class="analysis-note"><b>AI 供应链风险归因：</b>直接标记为 AI 供应链的标的共 {int(ai_group['count'])} 檔，权重 {format_percent(float(ai_group['weight']))}、风险贡献 {format_percent(float(ai_group['risk']))}，风险贡献相对权重差 {format_percent(ai_risk_gap, signed=True)}。该口径只按标的分类，不穿透 ETF 成分，不是未来报酬预测。</div>
        <div class="table-grid">
          <div>
            <h3>行业风险贡献 Top 5</h3>
            <table class="metric-table compact-table">
              <thead><tr><th>行业</th><th>檔数</th><th>权重</th><th>风险贡献</th><th>风险-权重</th></tr></thead>
              <tbody>{sector_theme_rows}</tbody>
            </table>
          </div>
          <div>
            <h3>主题风险贡献 Top 5</h3>
            <table class="metric-table compact-table">
              <thead><tr><th>主题</th><th>檔数</th><th>权重</th><th>风险贡献</th><th>风险-权重</th></tr></thead>
              <tbody>{theme_rows}</tbody>
            </table>
          </div>
        </div>
        <table class="metric-table compact-table">
          <thead><tr><th>AI 供应链分组</th><th>檔数</th><th>权重</th><th>风险贡献</th><th>风险-权重</th></tr></thead>
          <tbody>{ai_rows}</tbody>
        </table>
        <p class="footer-note">群组归因使用{html.escape(attribution_label)}、收缩协方差风险贡献与资产池分类字段，只用于解释同源风险与组合暴露；不代表个股买卖建议，也不是未来报酬预测。ETF 成分未穿透，AI 供应链分类仅代表标的本身标签。</p>
      </section>
"""
    curve_advice = (
        f"净值曲线当前由{curve_leader}领先，普通净值 {sample_final:.4f}、收缩净值 {shrink_final:.4f}。"
        "若领先优势来自更低回撤而非更高波动，优先保留该模型作为调仓参考。"
    )
    drawdown_advice = (
        f"回撤曲线当前由{dd_leader}表现较稳，普通最大回撤 {format_percent(sample_dd.min())}、收缩最大回撤 {format_percent(shrink_dd.min())}。"
        "若收缩模型回撤较浅，说明稳健协方差对风险控制有帮助；若较深，需要降低单一风险贡献。"
    )
    backtest_start_date = "无可用资料"
    backtest_end_date = "无可用资料"
    last_rebalance_date = "无调仓记录"
    estimated_next_rebalance_date = "无可用资料"
    trading_days_to_next_rebalance = 0
    rebalance_schedule_stale = False
    rebalance_schedule_note = ""
    if backtest:
        backtest_start_date = backtest.dates[0] if backtest.dates else backtest_start_date
        backtest_end_date = backtest.dates[-1] if backtest.dates else backtest_end_date
        last_rebalance_date = backtest.rebalance_dates[-1] if backtest.rebalance_dates else last_rebalance_date
        trading_days_after_rebalance = sum(1 for item in backtest.dates if item > last_rebalance_date)
        trading_days_to_next_rebalance = max(0, backtest.step - trading_days_after_rebalance)
        parsed_backtest_end = parse_iso_date(backtest_end_date)
        today_date = date.today()
        estimated_next_rebalance_date = (
            add_weekdays(parsed_backtest_end, trading_days_to_next_rebalance).isoformat()
            if parsed_backtest_end and trading_days_to_next_rebalance
            else "下一个共同交易日"
        )
        parsed_next_rebalance = parse_iso_date(estimated_next_rebalance_date)
        if parsed_next_rebalance and parsed_next_rebalance < today_date:
            rebalance_schedule_stale = True
            rebalance_schedule_note = (
                f"该日期是基于目前只到 {backtest_end_date} 的共同交易日序列推算出的旧计划；"
                f"在新的正式收盘资料并入前，不能据此判定 2026-06-19 已完成或错过回测调仓。"
            )
            estimated_next_rebalance_date = "待新正式行情后重算"
            trading_days_to_next_rebalance = 0
    actionable_buy_count = sum(1 for signal in actionable_signals if signal.status == "buy")
    actionable_sell_count = sum(1 for signal in actionable_signals if signal.status == "sell")
    settled_signal_count = sum(1 for signal in trade_signals if "已落账" in signal.reason)
    trade_batch_statuses = load_simulated_trade_batch_status(
        (model_portfolio.market_date or model_portfolio.execution_date) if model_portfolio else None,
        trade_output_path,
    )
    execution_summary = load_simulated_trade_execution_summary(
        (model_portfolio.market_date or model_portfolio.execution_date) if model_portfolio else None,
        trade_output_path,
    )
    execution_detail_text = "、".join(execution_summary.details) if execution_summary else "本轮尚无已落账模拟成交"
    execution_trade_date = execution_summary.trade_date if execution_summary else "无执行记录"
    execution_trade_count = execution_summary.trade_count if execution_summary else 0
    execution_buy_count = execution_summary.buy_count if execution_summary else 0
    execution_sell_count = execution_summary.sell_count if execution_summary else 0
    settled_batch_labels = "、".join(status.label for status in trade_batch_statuses if not status.is_legacy) or "暫無新格式批次"
    legacy_batch_status = next((status for status in trade_batch_statuses if status.is_legacy), None)
    legacy_batch_text = f"舊格式 {legacy_batch_status.trade_count} 筆" if legacy_batch_status else "無舊格式紀錄"
    pending_batch_text = (
        f"批次 {trade_batch_seq} 待確認 {len(actionable_signals)} 筆"
        if actionable_signals
        else f"目前批次 {trade_batch_seq} 暫無待確認單"
    )
    if trade_batch_statuses:
        batch_rows = "\n".join(
            (
                f"<tr><td>{html.escape(status.label)}</td><td>{status.trade_count}</td>"
                f"<td>{html.escape('、'.join(status.symbols) or '未记录')}</td>"
                f"<td>{html.escape('、'.join(status.actions) or '未记录')}</td>"
                f"<td>{'舊成交 CSV 無 trade_id，按交易日、標的、方向相容防重' if status.is_legacy else '新格式 trade_id 已帶批次，可支援明確分批'}</td></tr>"
            )
            for status in trade_batch_statuses
        )
    else:
        batch_rows = '<tr><td colspan="5" class="empty-order-cell">本交易日尚無本地模擬成交 CSV 紀錄。</td></tr>'
    trade_batch_status_html = f"""
      <div class="analysis-note"><b>模擬盤批次狀態小結：</b>目前批次為 {html.escape(trade_batch_seq)}；已寫入本地模擬成交 CSV 的批次：{html.escape(settled_batch_labels)}；舊格式紀錄：{html.escape(legacy_batch_text)}；目前待確認：{html.escape(pending_batch_text)}。頁面確認只保存在目前瀏覽器，真正寫入本地模擬成交 CSV 仍需執行 Python 主腳本。</div>
      <table class="metric-table compact-table">
        <thead><tr><th>已落帳批次</th><th>筆數</th><th>標的</th><th>方向</th><th>口徑</th></tr></thead>
        <tbody>{batch_rows}</tbody>
      </table>
"""
    if actionable_signals:
        top_signal_items = "".join(
            (
                f"<li>{html.escape(signal.symbol)} {html.escape(signal.name)}："
                f"{'买入' if signal.status == 'buy' else '卖出'} {signal.proposed_shares or 0:,} 股；"
                f"{html.escape(signal.reason)}</li>"
            )
            for signal in actionable_signals[:3]
        )
        if len(actionable_signals) > 3:
            top_signal_items += f"<li>另有 {len(actionable_signals) - 3} 笔待确认调仓，详见下方建议单。</li>"
        trade_reason_summary = (
            f"本轮有 {len(actionable_signals)} 笔待确认调仓：买入 {actionable_buy_count} 笔、卖出 {actionable_sell_count} 笔。"
            "这些只是本地模拟盘复核事项，不会自动送出订单。"
        )
        trade_reason_boundary = "待确认单代表规则已触发模拟盘复核，但仍需用脚本落账才会写入本地 CSV。"
    elif settled_signal_count:
        top_signal_items = "<li>本日触发过的模拟调仓已在本地 CSV 落账，当前页面不再重复列为待确认清单。</li>"
        trade_reason_summary = f"本轮没有新的待确认调仓；已有 {settled_signal_count} 笔本日模拟调仓转为观察。"
        trade_reason_boundary = "没有待确认单不代表风险解除；本轮是因为本日建议已通过脚本落账并转为观察。"
    else:
        top_signal_items = "<li>本轮没有新的待确认调仓；持仓维持观察，等待价格、趋势、RSI 或连续天数重新触发。</li>"
        trade_reason_summary = "本轮没有新的待确认调仓；当前更适合观察风险集中、回撤和压力情境。"
        trade_reason_boundary = "没有待确认单不代表风险解除，只代表本轮没有标的同时满足买入/卖出阈值。"
    taiex_snapshot = fetch_taiex_snapshot(dashboard_generated_date)
    if taiex_snapshot:
        taiex_change_class = "positive" if taiex_snapshot.change_points >= 0 else "negative"
        taiex_market_text = (
            f"加权指数 {taiex_snapshot.trade_date} 收 {taiex_snapshot.close_index:,.2f}，"
            f"{taiex_snapshot.change_points:+,.2f} 点、{format_percent(taiex_snapshot.change_pct, signed=True)}；"
            f"盘中区间 {taiex_snapshot.low_index:,.2f} - {taiex_snapshot.high_index:,.2f}。"
        )
        taiex_cards = f"""
          <div class="card"><div class="metric">{taiex_snapshot.close_index:,.2f}</div><p class="metric-label">加权指数收盘</p></div>
          <div class="card"><div class="metric {taiex_change_class}">{taiex_snapshot.change_points:+,.2f}</div><p class="metric-label">加权指数涨跌点</p></div>
          <div class="card"><div class="metric {taiex_change_class}">{format_percent(taiex_snapshot.change_pct, signed=True)}</div><p class="metric-label">加权指数涨跌幅</p></div>
        """
    else:
        taiex_market_text = "TWSE 加权指数公开资料暂时无法读取；本区仍保留模型盘与行情序列状态。"
        taiex_cards = """
          <div class="card"><div class="metric">暂不可用</div><p class="metric-label">加权指数收盘</p></div>
          <div class="card"><div class="metric">暂不可用</div><p class="metric-label">加权指数涨跌点</p></div>
          <div class="card"><div class="metric">暂不可用</div><p class="metric-label">加权指数涨跌幅</p></div>
        """
    portfolio_market_date = model_portfolio.market_date if model_portfolio else dashboard_data_end
    market_mode_text = (
        "收盘定稿"
        if model_portfolio and model_portfolio.market_mode == "close"
        else "盘中暂估"
        if model_portfolio and model_portfolio.market_mode == "intraday"
        else "未套用今日行情"
    )
    current_market_value = sum((position.current_market_value or 0.0) for position in model_portfolio.positions) if model_portfolio else 0.0
    current_unrealized_pnl = sum((position.unrealized_pnl or 0.0) for position in model_portfolio.positions) if model_portfolio else 0.0
    update_actions = [
        f"已刷新公开收盘价路径，Dashboard 行情/回测序列最新日期为 {dashboard_data_end}。",
        f"已套用本地模型盘市值档 {portfolio_market_date}（{market_mode_text}），当前持仓市值 {format_twd(current_market_value)}，未实现盈亏 {format_twd(current_unrealized_pnl)}。",
        f"已复核策略监控：待确认调仓 {len(actionable_signals)} 笔，已落账模拟成交 {execution_trade_count} 笔，红色卖出建议不会重复显示已落账标的。",
    ]
    next_steps = [
        "下一交易日继续用公开收盘价刷新 Dashboard，并把公网首页正文作为发布完成标准。",
        f"继续观察是否走满 {backtest.step if backtest else DEFAULT_REBALANCE_STEP} 个共同交易日；当前预计下次回测调仓为 {estimated_next_rebalance_date}。",
        "短期重点看 AI 供应链风险贡献是否继续高于权重，并复核新的待确认调仓是否需要本地模拟盘落账。",
    ]
    update_summary_html = f"""
      <section id="update-summary" class="section panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Today Brief</span>
            <h2>今日市场与更新摘要</h2>
          </div>
          <span class="status-pill">当前状态 / 已做事项 / 短期下一步</span>
        </div>
        <div class="analysis-note"><b>今天台股：</b>{html.escape(taiex_market_text)}</div>
        <div class="metric-grid backtest-grid">
          {taiex_cards}
          <div class="card"><div class="metric">{html.escape(dashboard_data_end)}</div><p class="metric-label">行情/回测最新日</p></div>
          <div class="card"><div class="metric">{html.escape(portfolio_market_date)}</div><p class="metric-label">模型盘市值日</p></div>
          <div class="card"><div class="metric">{len(actionable_signals)}</div><p class="metric-label">待确认调仓</p></div>
        </div>
        <div class="table-grid">
          <div>
            <h3>已执行</h3>
            <ul class="risk-list update-summary-list">{''.join(f'<li>{html.escape(item)}</li>' for item in update_actions)}</ul>
          </div>
          <div>
            <h3>短期行动计划</h3>
            <ul class="risk-list update-summary-list">{''.join(f'<li>{html.escape(item)}</li>' for item in next_steps)}</ul>
          </div>
        </div>
        <p class="footer-note">本区使用 TWSE 公开指数资料、本地公开收盘价缓存和模拟盘 CSV 生成；只用于研究与本地 paper portfolio 复核，不代表实盘委托或投资建议。</p>
      </section>
"""
    rebalance_execution_calendar_html = f"""
      <section id="rebalance-calendar" class="section panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Rebalance Calendar</span>
            <h2>调仓与执行日历</h2>
          </div>
          <span class="status-pill">回测调仓 / 模拟盘执行分开记录</span>
        </div>
        <div class="analysis-note"><b>口径说明：</b>“回测调仓”是模型每 {backtest.step if backtest else DEFAULT_REBALANCE_STEP} 个共同交易日重新计算一次权重；“模拟盘执行调仓”是本地 paper portfolio 已经写入模拟成交 CSV 的买卖动作。你今天执行的卖出计入模拟盘执行调仓，但不会强行改写回测模型的 7 日重新估计节奏。{' ' + html.escape(rebalance_schedule_note) if rebalance_schedule_note else ''}</div>
        <div class="metric-grid backtest-grid">
          <div class="card"><div class="metric">{html.escape(last_rebalance_date)}</div><p class="metric-label">最后回测调仓日</p></div>
          <div class="card"><div class="metric">{html.escape(estimated_next_rebalance_date)}</div><p class="metric-label">预计下次回测调仓</p></div>
          <div class="card"><div class="metric">{trading_days_to_next_rebalance}</div><p class="metric-label">距下次还差交易日</p></div>
          <div class="card"><div class="metric">{html.escape(execution_trade_date)}</div><p class="metric-label">最后模拟盘执行日</p></div>
          <div class="card"><div class="metric">{execution_trade_count}</div><p class="metric-label">已落账模拟成交</p></div>
          <div class="card"><div class="metric">{execution_sell_count}</div><p class="metric-label">其中卖出笔数</p></div>
        </div>
        <div class="analysis-note"><b>本次执行记录：</b>{html.escape(execution_detail_text)}。买入 {execution_buy_count} 笔、卖出 {execution_sell_count} 笔；这些都只属于本地模拟盘，不是券商委托。</div>
      </section>
"""
    strategy_structure_text = ""
    if model_portfolio and model_portfolio.method == "multi-factor-shrink":
        strategy_structure_text = strategy_structure_summary(
            assets=assets,
            price_data=price_data,
            build_date=model_portfolio.build_date,
            shrink_covariance=shrink_cov,
            ai_tilt=model_portfolio.ai_tilt or "moderate",
        )
    research_report_text = "\n".join(
        [
            "本轮研究摘要：",
            f"1. 收缩协方差下，最大风险贡献来自 {symbols[top_shrink_risk_index]}，风险贡献 {format_percent(shrink_rc[top_shrink_risk_index])}；最高相关资产对为 {max_pair_text}，用于识别同源风险。",
            f"2. 群组归因显示，{str(top_sector['group'])} 与 {str(top_theme['group'])} 是当前主要群组风险来源；AI 供应链权重 {format_percent(float(ai_group['weight']))}，风险贡献 {format_percent(float(ai_group['risk']))}，风险-权重差 {format_percent(ai_risk_gap, signed=True)}。",
            f"3. 压力情境下，普通协方差估计损失约 {format_percent(abs(sample_stress))}，收缩协方差估计损失约 {format_percent(abs(shrink_stress))}；该口径仅用于研究解释。",
            f"4. 调仓状态：{trade_reason_summary}",
            f"5. 策略结构变化结论：{strategy_structure_text}" if strategy_structure_text else "5. 策略结构变化结论：当前模型盘尚未采用 multi-factor-shrink，暂不生成结构变化比较。",
            "6. 本摘要仅用于本地模拟盘研究记录，不代表未来报酬预测、个股买卖建议、实盘订单或券商账户状态。",
        ]
    )
    strategy_structure_html = ""
    if strategy_structure_text:
        strategy_structure_html = f"""
        <div class="analysis-note"><b>策略结构变化结论：</b>{html.escape(strategy_structure_text)}</div>
"""
    research_report_html = f"""
        <div class="analysis-note"><b>群组风险研究报告摘要：</b>以下文字用于研究记录和人工复核，可复制到报告或 Obsidian；内容只解释本地模型盘与风险归因，不构成投资建议、预测或券商委托；不会新增交易信号，不会写入模拟成交 CSV，也不连接券商。</div>
        {strategy_structure_html}
        <textarea class="research-report" readonly rows="7">{html.escape(research_report_text)}</textarea>
"""
    decision_summary_html = f"""
      <section class="section panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Decision Brief</span>
            <h2>本轮风险归因与调仓摘要</h2>
          </div>
          <span class="status-pill">{len(actionable_signals)} 笔待确认</span>
        </div>
        <div class="analysis-note"><b>主要风险：</b>收缩协方差下最大风险贡献来自 {html.escape(symbols[top_shrink_risk_index])}，贡献 {format_percent(shrink_rc[top_shrink_risk_index])}；最高相关资产对为 {html.escape(max_pair_text)}。这些项目用于识别同源风险，不代表个股买卖建议。</div>
        <div class="analysis-note"><b>压力情境：</b>规则压力测试下，普通协方差估计损失约 {format_percent(abs(sample_stress))}，收缩协方差估计损失约 {format_percent(abs(shrink_stress))}。这是解释型压力口径，不是未来预测。</div>
        <div class="analysis-note"><b>调仓原因：</b>{html.escape(trade_reason_summary)}</div>
        <ul class="risk-list">{top_signal_items}</ul>
{research_report_html}
      </section>
"""

    charts = {
        "heatmap": heatmap_figure(symbols, corr),
        "weights_sample": bar_figure("普通样本协方差：最小方差权重", labels, to_percent(sample_weights), ["#12304a", "#52d6ff"]),
        "weights_shrink": bar_figure("收缩协方差：最小方差权重", labels, to_percent(shrink_weights), ["#163629", "#65f4c9"]),
        "risk_sample": bar_figure("普通样本协方差：风险贡献", labels, to_percent(sample_rc), ["#37152a", "#fb3f5f"]),
        "risk_shrink": bar_figure("收缩协方差：风险贡献", labels, to_percent(shrink_rc), ["#3a2b12", "#f6c85f"]),
        "curve": line_figure("组合净值曲线", chart_dates, sample_curve, shrink_curve),
        "drawdown": drawdown_figure(chart_dates, sample_dd, shrink_dd),
    }
    if backtest:
        charts["backtest"] = backtest_curve_figure(backtest)

    rows = "\n".join(
        f"<tr><td>{html.escape(symbol)}</td><td>{html.escape(asset_name.get(symbol, ''))}</td><td>{sample_weights[i] * 100:.2f}%</td><td>{shrink_weights[i] * 100:.2f}%</td><td>{sample_rc[i] * 100:.2f}%</td><td>{shrink_rc[i] * 100:.2f}%</td></tr>"
        for i, symbol in enumerate(symbols)
    )
    overlap_html = "\n".join(
        f"<li>{html.escape(left)} 与 {html.escape(right)}：相关性 {value:.2f}</li>" for left, right, value in overlap_pairs
    ) or "<li>本期未发现相关性高于 0.75 的资产对。</li>"
    issues_html = "\n".join(f"<li>{html.escape(issue.symbol)}: {html.escape(issue.message)}</li>" for issue in issues) or "<li>本轮未记录数据问题。</li>"
    if backtest:
        sample_bt = backtest.sample_metrics
        shrink_bt = backtest.shrink_metrics
        if rebalance_schedule_stale:
            next_rebalance_note = (
                f"回测曲线目前只纳入到 {backtest_end_date}，最后一次重新计算权重仍是 {last_rebalance_date}。"
                f" 原先推算的下一次回测调仓日期已经早于今天，说明正式共同交易日资料还没追上；"
                " 需要等新的公开收盘资料并入后，才能重新判断下一次回测调仓是否已经触发。"
            )
        else:
            next_rebalance_text = (
                f"还差 {trading_days_to_next_rebalance} 个共同交易日；若无休市，最早约 {estimated_next_rebalance_date}"
                if trading_days_to_next_rebalance
                else "下一笔共同交易日即可触发新一轮调仓"
            )
            next_rebalance_note = (
                f"回测曲线已纳入 {backtest_end_date}，但 7 个交易日调仓节奏下，最后一次重新计算权重发生在 {last_rebalance_date}；距离下一次重新计算权重{next_rebalance_text}。"
                if backtest_end_date != last_rebalance_date
                else f"回测曲线与最后一次重新计算权重都更新到 {backtest_end_date}。"
            )
        turnover_delta = shrink_bt.average_turnover - sample_bt.average_turnover
        drawdown_improvement = shrink_bt.max_drawdown - sample_bt.max_drawdown
        backtest_leader = "收缩协方差" if backtest.shrink_curve[-1] >= backtest.sample_curve[-1] else "普通协方差"
        turnover_text = "降低" if turnover_delta < 0 else "提高"
        drawdown_text = "改善" if drawdown_improvement > 0 else "恶化"
        backtest_advice = (
            f"本期回测期末净值由{backtest_leader}领先。收缩协方差相对普通协方差使平均换手率{turnover_text} {format_percent(abs(turnover_delta))}，"
            f"最大回撤{drawdown_text} {format_percent(abs(drawdown_improvement))}。若回撤改善且换手率没有明显升高，后续调仓优先参考收缩模型。"
        )
        backtest_html = f"""
    <section class="section panel">
      <h2>滚动再平衡回测</h2>
      <p>使用 {backtest.window} 个交易日估计窗口，每 {backtest.step} 个交易日重新计算一次最小方差权重，共执行 {backtest.rebalance_count} 次调仓。回测覆盖区间为 {backtest_start_date} 至 {backtest_end_date}；最后一次重新计算权重日期为 {last_rebalance_date}。</p>
      <div class="analysis-note"><b>滚动更新记录：</b>{html.escape(next_rebalance_note)}如果最新行情只补进 1 个交易日、还没走满 7 个交易日，就会更新净值曲线与行情日期，但调仓次数不会增加。</div>
      <div class="analysis-note"><b>回测对比建议：</b>{html.escape(backtest_advice)}</div>
      <div class="metric-grid backtest-grid">
        <div class="card"><div class="metric">{html.escape(backtest_end_date)}</div><p class="metric-label">回测最新日期</p></div>
        <div class="card"><div class="metric">{html.escape(last_rebalance_date)}</div><p class="metric-label">最后调仓日期</p></div>
        <div class="card"><div class="metric">{html.escape(estimated_next_rebalance_date)}</div><p class="metric-label">预计下次回测调仓</p></div>
        <div class="card"><div class="metric">{trading_days_to_next_rebalance}</div><p class="metric-label">距下次还差交易日</p></div>
        <div class="card"><div class="metric">{format_percent(sample_bt.annual_return)}</div><p class="metric-label">普通协方差年化收益</p></div>
        <div class="card"><div class="metric hero-stat">{format_percent(shrink_bt.annual_return)}</div><p class="metric-label">收缩协方差年化收益</p></div>
        <div class="card"><div class="metric stress-number">{format_percent(sample_bt.max_drawdown)}</div><p class="metric-label">普通协方差最大回撤</p></div>
        <div class="card"><div class="metric">{format_percent(shrink_bt.max_drawdown)}</div><p class="metric-label">收缩协方差最大回撤</p></div>
      </div>
      <div class="chart">{charts["backtest"]}</div>
      <table class="metric-table">
        <thead><tr><th>模型</th><th>年化波动</th><th>平均换手率</th><th>累计换手率</th><th>回测期末净值</th></tr></thead>
        <tbody>
          <tr><td>普通协方差</td><td>{format_percent(sample_bt.annual_volatility)}</td><td>{format_percent(sample_bt.average_turnover)}</td><td>{format_percent(sample_bt.cumulative_turnover)}</td><td>{backtest.sample_curve[-1]:.4f}</td></tr>
          <tr><td>收缩协方差</td><td>{format_percent(shrink_bt.annual_volatility)}</td><td>{format_percent(shrink_bt.average_turnover)}</td><td>{format_percent(shrink_bt.cumulative_turnover)}</td><td>{backtest.shrink_curve[-1]:.4f}</td></tr>
        </tbody>
      </table>
      <p class="footer-note">收缩协方差相对普通协方差：平均换手率变化 {format_percent(turnover_delta, signed=True)}，最大回撤变化 {format_percent(drawdown_improvement, signed=True)}。正的回撤变化代表回撤较浅，负值代表回撤较深。</p>
    </section>
"""
    else:
        backtest_html = """
    <section class="section panel">
      <h2>滚动再平衡回测</h2>
      <p>本轮资料不足以执行滚动再平衡回测。请拉长起止月份，或降低估计窗口与调仓间隔后重新生成仪表盘。</p>
    </section>
"""
    if trade_signals:
        settled_signal_count = sum(1 for signal in trade_signals if "已落账" in signal.reason)
        signal_status_text = f"{len(actionable_signals)} 笔待确认"
        if settled_signal_count:
            signal_status_text += f" / {settled_signal_count} 笔已落账"
        signal_rows = "\n".join(
            (
                f"<tr class=\"signal-{html.escape(signal.status)}\" data-trade-id=\"{html.escape(signal.trade_id)}\"><td><span class=\"signal-pill {html.escape(signal.status)}\">{html.escape(signal.action)}</span></td>"
                f"<td>{html.escape(signal.symbol)}</td><td class=\"name-cell\"><span class=\"asset-name\">{html.escape(signal.name)}</span></td><td>{signal.latest_price:.2f}</td>"
                f"<td>{format_optional_price(signal.cost_price)}</td><td>{signal.persistence_days}</td>"
                f"<td>{'' if signal.return_since_entry is None else format_percent(signal.return_since_entry, signed=True)}</td>"
                f"<td>{'' if signal.proposed_shares is None else f'{signal.proposed_shares:,}'}</td>"
                f"<td title=\"{html.escape(signal.reason)}\">{html.escape(short_trade_reason(signal))}</td></tr>"
            )
            for signal in trade_signals
        )
        signal_summary = (
            f"本轮触发 {len(actionable_signals)} 笔手工建议单；未触发的标的只列为观察。"
            if actionable_signals
            else "本轮没有触发新的买入或卖出建议，维持现有持仓观察。"
        )
        trade_signal_html = f"""
    <section id="trade-signals" class="section panel">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Rule Based Signals</span>
          <h2>策略监控与建议单</h2>
        </div>
        <span class="status-pill">{html.escape(signal_status_text)}</span>
      </div>
      <p>{signal_summary} 表格只保留决策复核需要的核心栏位；趋势、RSI、量能和多因子分数仍在规则内部计算，只生成手工建议，不会自动下单。</p>
      <div class="analysis-note"><b>訊號口徑：</b>「觀察」代表未進入本輪待處理清單；「建議買入 / 建議賣出」只代表本地模擬盤待確認，不會送到券商。若標的顯示「本日模擬調倉已落帳」，表示同一交易日已有本地 CSV 紀錄，系統會避免重複列為待確認清單。</div>
      <div class="analysis-note"><b>本轮调仓解释：</b>{html.escape(trade_reason_summary)} {html.escape(trade_reason_boundary)}</div>
      <table class="metric-table signal-table">
        <colgroup>
          <col class="signal-col-action">
          <col class="signal-col-code">
          <col class="signal-col-name">
          <col class="signal-col-price">
          <col class="signal-col-cost">
          <col class="signal-col-days">
          <col class="signal-col-return">
          <col class="signal-col-shares">
          <col class="signal-col-reason">
        </colgroup>
        <thead><tr><th>动作</th><th>代码</th><th>名称</th><th>监控价</th><th>成本价</th><th>连续天数</th><th>建仓后报酬</th><th>建议股数</th><th>触发原因</th></tr></thead>
        <tbody>{signal_rows}</tbody>
      </table>
      <p class="footer-note">买入触发：回落约 3%、长期趋势仍正向、RSI 未过热、量能未明显萎缩，并连续观察至少 2 天。卖出触发：亏损约 6% 或趋势转弱，或获利约 8% 且 RSI 过热，并连续观察至少 2 天。阈值是 MVP 起点，后续可用回测再校准。</p>
    </section>
"""
    else:
        trade_signal_html = """
    <section id="trade-signals" class="section panel">
      <h2>策略监控与建议单</h2>
      <p>本轮未生成模型盘持仓，因此没有技术监控与建议单。</p>
    </section>
"""
    default_trade_state_json = "{}"
    if model_portfolio:
        method_labels = {
            "drawdown-risk": "回撤风险加权",
            "shrink-minvar": "收缩协方差最小方差",
            "multi-factor-shrink": "台股多因子收缩优化",
        }
        method_label = method_labels.get(model_portfolio.method, model_portfolio.method)
        lookback_label = f"{model_portfolio.lookback_years} 年" if model_portfolio.lookback_years else "可用"
        execution_status = "待执行价" if model_portfolio.execution_price_status == "pending_open_price" else "已取得执行价"
        target_total = sum(position.target_value for position in model_portfolio.positions)
        total_commission = sum(position.buy_commission or 0.0 for position in model_portfolio.positions)
        total_future_sell_tax = sum(position.future_sell_tax or 0.0 for position in model_portfolio.positions)
        current_market_total = sum(position.current_market_value or 0.0 for position in model_portfolio.positions)
        current_pnl_total = sum(position.unrealized_pnl or 0.0 for position in model_portfolio.positions)
        current_cost_total = sum(position.total_buy_cost if position.total_buy_cost is not None else position.market_value or 0.0 for position in model_portfolio.positions)
        current_pnl_pct = current_pnl_total / current_cost_total if current_cost_total else 0.0
        has_market_values = any(position.current_market_value is not None for position in model_portfolio.positions)
        mode_label = "盘中暂估" if model_portfolio.market_mode == "intraday" else "收盘定稿" if model_portfolio.market_mode == "close" else ""
        market_status = f"今日行情：{mode_label}" if mode_label else "今日行情尚未更新"
        market_time_label = model_portfolio.market_quote_time or "等待快照"
        history_note = (
            f"今日快照 {html.escape(model_portfolio.market_date or '')} 已更新持仓损益与策略监控，但尚未纳入滚动回测和长期回撤序列。"
            if model_portfolio.market_date and model_portfolio.market_date not in price_data.dates
            else "今日行情已随历史资料进入本轮价格序列。"
            if model_portfolio.market_date
            else "尚未套用今日行情快照；回撤、回测与策略监控仍使用当前历史资料。"
        )
        model_rows = "\n".join(
            f"<tr><td>{html.escape(position.symbol)}</td><td class=\"name-cell\"><span class=\"asset-name\">{html.escape(position.name)}</span></td><td>{'待执行价' if position.price is None else f'{position.price:.2f}'}</td><td>{'等待行情' if position.current_price is None else f'{position.current_price:.2f}'}</td><td>{'待执行价' if position.shares is None else f'{position.shares:,}'}</td><td>{'待执行价' if position.market_value is None else format_twd(position.market_value)}</td><td>{'等待行情' if position.current_market_value is None else format_twd(position.current_market_value)}</td><td>{'等待行情' if position.unrealized_pnl is None else format_twd(position.unrealized_pnl)}</td><td>{'' if position.unrealized_pnl_pct is None else format_percent(position.unrealized_pnl_pct)}</td><td>{format_percent(position.target_weight)}</td><td>{format_twd(position.target_value)}</td><td>{'' if position.buy_commission is None else format_twd(position.buy_commission)}</td></tr>"
            for position in model_portfolio.positions
        )
        default_trade_state = {}
        for signal in actionable_signals:
            default_trade_state[signal.trade_id or signal.symbol] = False
        default_trade_state_json = json.dumps(default_trade_state, ensure_ascii=False)
        if actionable_signals:
            manual_trade_rows = "\n".join(
                f"<tr data-symbol=\"{html.escape(signal.symbol)}\" data-trade-id=\"{html.escape(signal.trade_id)}\"><td><span class=\"trade-status\" data-trade-status=\"{html.escape(signal.trade_id)}\">待确认</span></td><td>{'买入' if signal.status == 'buy' else '卖出'}</td><td>{html.escape(signal.symbol)}<div class=\"trade-id\">单号：{html.escape(signal.trade_id)}</div></td><td class=\"name-cell\"><span class=\"asset-name\">{html.escape(signal.name)}</span></td><td>{signal.latest_price:.2f}</td><td>{'' if signal.proposed_shares is None else f'{signal.proposed_shares:,}'}</td><td>{'' if signal.proposed_shares is None else format_twd(signal.latest_price * signal.proposed_shares)}</td><td>页面复核</td><td>脚本落账</td><td><button class=\"trade-button\" type=\"button\" data-trade-toggle=\"{html.escape(signal.trade_id)}\">页面标记已确认</button></td></tr>"
                for signal in actionable_signals
            )
        else:
            manual_trade_rows = '<tr><td colspan="10" class="empty-order-cell">目前没有待确认的模拟调仓单。初始建仓单已归入持仓与盈亏统计；若本日建议已通过脚本落账，会从待确认清单移除，并反映到模拟持仓。若策略监控表仍有观察标的，请看触发原因栏；它们通常是连续天数、趋势、RSI、量能或建仓后报酬尚未同时达标。</td></tr>'
        manual_trade_html = f"""
    <section id="manual-trading" class="section panel">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Paper Portfolio Review</span>
          <h2>模拟盘调仓确认</h2>
        </div>
        <div class="trade-actions">
          <button id="mark-all-trades" class="trade-button primary" type="button">全部标记完成</button>
          <button id="reset-trade-status" class="trade-button" type="button">重置状态</button>
        </div>
      </div>
      <p>这里是本地模拟盘调仓清单。页面按钮只会在当前浏览器记录检查状态，不会连接券商、不送出真实订单；真正落成 CSV 只由 Python 主脚本的 <code>--execute-simulated-trades</code> 完成。</p>
{trade_batch_status_html}
      <table class="metric-table">
        <thead><tr><th>状态</th><th>方向</th><th>代码</th><th>名称</th><th>参考价</th><th>股数</th><th>估算金额</th><th>确认</th><th>记录</th><th>操作</th></tr></thead>
        <tbody>{manual_trade_rows}</tbody>
      </table>
      <p class="footer-note">执行建议：先在本页面逐笔复核，再由脚本写入本地模拟成交 CSV。默认批次为 01，同一交易日、同一标的、同一方向重复落账会保持幂等；只有明确使用新的模拟成交批次号时，才视为同日分批。点击“重置状态”只恢复浏览器里的检查状态，不会送出、撤回或修改任何真实订单。</p>
    </section>
"""
        market_mode_label = (
            "收盘定稿"
            if model_portfolio.market_mode == "close"
            else "盘中暂估"
            if model_portfolio.market_mode == "intraday"
            else "未套用今日行情"
        )
        update_status_label = (
            f"已按{DEFAULT_DASHBOARD_UPDATE_TIME_LABEL} 更新"
            if model_portfolio.market_mode == "close"
            else "台湾股市进行中"
            if model_portfolio.market_mode == "intraday"
            else "等待行情更新"
        )
        model_html = f"""
    <section class="section panel">
      <h2>今日持仓与收盘盈亏</h2>
      <p>本区块只生成虚拟持仓与行情更新，不会连接券商交易端、不做实盘下单。模型盘建仓日为 {html.escape(model_portfolio.build_date)}；方法为{method_label}，实际使用{lookback_label}回撤资料。{html.escape(history_note)}</p>
      <div class="metric-grid backtest-grid">
        <div class="card"><div class="metric">{format_twd(model_portfolio.initial_cash)}</div><p class="metric-label">初始虚拟资金</p></div>
        <div class="card"><div class="metric">{format_percent(model_portfolio.invest_ratio)}</div><p class="metric-label">目标建仓比例</p></div>
        <div class="card"><div class="metric">{format_twd(model_portfolio.cash_reserve)}</div><p class="metric-label">策略现金池</p></div>
        <div class="card"><div class="metric">{html.escape(update_status_label)}</div><p class="metric-label">更新状态</p></div>
        <div class="card"><div class="metric">{html.escape(market_mode_label)}</div><p class="metric-label">行情口径</p></div>
        <div class="card"><div class="metric">{html.escape(market_time_label)}</div><p class="metric-label">快照时间</p></div>
        <div class="card"><div class="metric hero-stat">{format_twd(target_total)}</div><p class="metric-label">目标配置金额</p></div>
        <div class="card"><div class="metric">{format_twd(current_market_total)}</div><p class="metric-label">当前持仓市值</p></div>
        <div class="card"><div class="metric {'positive' if current_pnl_total >= 0 else 'negative'}">{format_twd(current_pnl_total)}</div><p class="metric-label">未实现盈亏</p></div>
        <div class="card"><div class="metric {'positive' if current_pnl_total >= 0 else 'negative'}">{format_percent(current_pnl_pct, signed=True)}</div><p class="metric-label">未实现盈亏率</p></div>
        <div class="card"><div class="metric">{execution_status}</div><p class="metric-label">手动执行价状态</p></div>
        <div class="card"><div class="metric">{model_portfolio.execution_date}</div><p class="metric-label">计划建仓日</p></div>
        <div class="card"><div class="metric">{format_twd(model_portfolio.remaining_cash)}</div><p class="metric-label">买进后剩余现金</p></div>
        <div class="card"><div class="metric">{format_twd(total_commission)}</div><p class="metric-label">买进手续费估算</p></div>
        <div class="card"><div class="metric">{format_twd(total_future_sell_tax)}</div><p class="metric-label">未来卖出税估算</p></div>
      </div>
      <div class="analysis-note"><b>持仓状态解释：</b>当前持仓市值与未实现盈亏来自本地模拟持仓和市值档，不是券商账户资料。持仓表说明“现在模拟盘长什么样”，下方建议单说明“规则是否触发下一步动作”；两者不是同一件事。</div>
      <table class="metric-table">
        <thead><tr><th>代码</th><th>名称</th><th>建仓价</th><th>当前价</th><th>持仓股数</th><th>买入市值</th><th>当前市值</th><th>未实现盈亏</th><th>盈亏率</th><th>目标权重</th><th>目标金额</th><th>买进手续费</th></tr></thead>
        <tbody>{model_rows}</tbody>
      </table>
      <p class="footer-note">模型建仓分析区间：{model_portfolio.analysis_start_date} 至 {model_portfolio.analysis_end_date}；当前回测/行情序列最新日期：{dashboard_data_end}。模型盘 CSV 已输出到 {html.escape(str(model_portfolio.output_path))} 与 {html.escape(str(model_portfolio.dated_output_path))}。这是研究用途的 paper portfolio；持仓、盈亏和建议单都只属于本地模拟盘，不构成投资建议，也不是券商委托状态。</p>
    </section>
{manual_trade_html}
"""
    else:
        model_html = """
    <section class="section panel">
      <h2>手动模型盘建仓</h2>
      <p>本轮未生成模型盘。若要生成虚拟建仓建议，请使用 <code>--model-portfolio</code> 手动触发。</p>
    </section>
"""
    if model_portfolio:
        sidebar_positions = sorted(model_portfolio.positions, key=lambda item: item.target_weight, reverse=True)
        sidebar_rows = "\n".join(
            f"<li><span>{html.escape(position.symbol)}</span><b>{format_percent(position.target_weight)}</b><small>{format_twd(position.target_value)}</small></li>"
            for position in sidebar_positions
        )
        execution_status = "待执行价" if model_portfolio.execution_price_status == "pending_open_price" else "已取得执行价"
        execution_hint = (
            "录入今日开盘价或实际成交价后，再换算整数股。"
            if model_portfolio.execution_price_status == "pending_open_price"
            else "已按手动建仓单建立虚拟持仓；证券交易税不预留，只在卖出时估算。"
        )
        total_buy_cost = sum(position.total_buy_cost if position.total_buy_cost is not None else position.market_value or 0.0 for position in model_portfolio.positions)
        total_commission = sum(position.buy_commission or 0.0 for position in model_portfolio.positions)
        current_market_total = sum(position.current_market_value or 0.0 for position in model_portfolio.positions)
        current_pnl_total = sum(position.unrealized_pnl or 0.0 for position in model_portfolio.positions)
        current_pnl_pct = current_pnl_total / total_buy_cost if total_buy_cost else 0.0
        sidebar_market_date = model_portfolio.market_date or dashboard_data_end
        sidebar_market_time = model_portfolio.market_quote_time or "等待快照"
        order_sidebar_html = f"""
      <aside id="orders" class="execution-panel">
        <div class="side-card warning">
          <p class="eyebrow-label">模型盘建仓</p>
          <h3>{html.escape(model_portfolio.build_date)}</h3>
          <div class="compact-status">{execution_status}</div>
          <p>{execution_hint}</p>
          <div class="split-row"><span>虚拟资金</span><b>{format_twd(model_portfolio.initial_cash)}</b></div>
          <div class="split-row"><span>建仓比例</span><b>{format_percent(model_portfolio.invest_ratio)}</b></div>
          <div class="split-row"><span>策略现金池</span><b>{format_twd(model_portfolio.cash_reserve)}</b></div>
        </div>
        <div class="side-card">
          <p class="eyebrow-label">目前更新情况</p>
          <div class="split-row"><span>更新日期</span><b>{html.escape(sidebar_market_date)}</b></div>
          <div class="split-row"><span>更新状态</span><b>{html.escape(update_status_label)}</b></div>
          <div class="split-row"><span>行情口径</span><b>{html.escape(market_mode_label)}</b></div>
          <div class="split-row"><span>自动排程</span><b>{html.escape(DEFAULT_DASHBOARD_UPDATE_TIME_LABEL)}</b></div>
          <div class="split-row"><span>快照时间</span><b>{html.escape(sidebar_market_time)}</b></div>
          <div class="split-row"><span>回测最新日</span><b>{html.escape(dashboard_data_end)}</b></div>
          <div class="split-row"><span>买进总成本</span><b>{format_twd(total_buy_cost)}</b></div>
          <div class="split-row"><span>买进手续费</span><b>{format_twd(total_commission)}</b></div>
          <div class="split-row"><span>剩余现金</span><b>{format_twd(model_portfolio.remaining_cash)}</b></div>
          <div class="split-row"><span>收盘持仓市值</span><b>{format_twd(current_market_total)}</b></div>
          <div class="split-row"><span>未实现盈亏</span><b>{format_twd(current_pnl_total)}</b></div>
          <div class="split-row"><span>盈亏率</span><b>{format_percent(current_pnl_pct, signed=True)}</b></div>
          <div class="split-row"><span>待确认调仓</span><b>{len(actionable_signals)} 笔</b></div>
          <div class="split-row"><span>本日模拟成交</span><b>{execution_trade_count} 笔</b></div>
        </div>
        <div class="side-card">
          <p class="eyebrow-label">调仓周期</p>
          <div class="split-row"><span>估计窗口</span><b>{backtest.window if backtest else DEFAULT_REBALANCE_WINDOW} 日</b></div>
          <div class="split-row"><span>检查间隔</span><b>{backtest.step if backtest else DEFAULT_REBALANCE_STEP} 日</b></div>
          <div class="split-row"><span>调仓次数</span><b>{backtest.rebalance_count if backtest else 0}</b></div>
          <p>建议每月两次人工复核，只有偏离目标权重或风险状态明显变化时才交易。</p>
        </div>
        <div class="side-card">
          <p class="eyebrow-label">建仓执行清单</p>
          <ul class="order-list">{sidebar_rows}</ul>
        </div>
      </aside>
"""
    else:
        order_sidebar_html = """
      <aside id="orders" class="execution-panel">
        <div class="side-card warning">
          <p class="eyebrow-label">模型盘建仓</p>
          <h3>未生成</h3>
          <div class="big-risk">待触发</div>
          <p>使用 --model-portfolio 生成目标权重与待执行清单。</p>
        </div>
      </aside>
"""
    etf_count = sum(1 for asset in assets if asset.asset_type.upper() == "ETF")
    stock_count = len(assets) - etf_count
    execution_check_html = ""
    if model_portfolio:
        positions_with_shares = [position for position in model_portfolio.positions if position.shares is not None and position.shares > 0]
        total_buy_cost_check = sum(position.total_buy_cost if position.total_buy_cost is not None else position.market_value or 0.0 for position in model_portfolio.positions)
        total_buy_tax = sum(position.buy_tax or 0.0 for position in model_portfolio.positions)
        current_market_total_check = sum(position.current_market_value or 0.0 for position in model_portfolio.positions)
        current_pnl_total_check = sum(position.unrealized_pnl or 0.0 for position in model_portfolio.positions)
        current_pnl_pct_check = current_pnl_total_check / total_buy_cost_check if total_buy_cost_check else 0.0
        integer_status = "全部持仓为整数股" if all(float(position.shares or 0).is_integer() for position in model_portfolio.positions) else "存在非整数股，请复核"
        market_check_status = "已套用 13:30 最后成交价" if current_market_total_check else "尚未套用今日收盘价"
        execution_check_html = f"""
      <section id="execution-check" class="check-panel" aria-live="polite">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Manual Execution Check</span>
            <h2>手动执行检查</h2>
          </div>
          <span class="status-pill">{html.escape(model_portfolio.execution_price_status)}</span>
        </div>
        <div class="check-grid">
          <div class="check-item pass"><b>建仓状态</b><span>{len(positions_with_shares)} / {len(model_portfolio.positions)} 檔已有建仓股数，执行价状态为 {execution_status}。</span></div>
          <div class="check-item pass"><b>股数规则</b><span>{integer_status}，符合零股可买卖但必须为整数股的规则。</span></div>
          <div class="check-item pass"><b>资金使用</b><span>目标建仓 {format_percent(model_portfolio.invest_ratio)}，买进总成本 {format_twd(total_buy_cost_check)}，剩余现金 {format_twd(model_portfolio.remaining_cash)}。</span></div>
          <div class="check-item pass"><b>交易税口径</b><span>买进证券交易税 {format_twd(total_buy_tax)}；不预留证交税，未来卖出时再估算。</span></div>
          <div class="check-item {'pass' if current_market_total_check else 'warn'}"><b>今日盈亏</b><span>{market_check_status}，持仓市值 {format_twd(current_market_total_check)}，未实现盈亏 {format_twd(current_pnl_total_check)}（{format_percent(current_pnl_pct_check, signed=True)}）。</span></div>
          <div class="check-item pass"><b>后续节奏</b><span>60 日估计窗口、7 日检查间隔；先人工复核，暂不自动下单。</span></div>
        </div>
      </section>
"""
    universe_strategy_html = f"""
      <section id="universe-strategy" class="section panel">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Universe Design</span>
            <h2>股票池策略与机制</h2>
          </div>
          <span class="status-pill">{len(assets)} 檔核心池</span>
        </div>
        <p>目前 15 檔不是每日自动从全市场扫描出来的名单，而是第一版 MVP 的人工核心资产池。设计目标是先覆盖台湾市场的宽基、股息、防御、科技、金融与产业龙头，再用回撤风险加权决定建仓权重。</p>
        <div class="strategy-list">
          <div class="card"><b>ETF 核心层</b><p>{etf_count} 檔 ETF 覆盖台股宽基、高股息、低波、科技主题，用来降低单一公司风险。</p></div>
          <div class="card"><b>产业龙头层</b><p>{stock_count} 檔个股代表半导体、电子制造、金融、电信与传统产业，用来保留台股主要风险因子。</p></div>
          <div class="card"><b>风险过滤层</b><p>模型盘使用 2 年回撤风险加权：最大回撤 60%、年化波动 25%、回撤持续时间 15%。风险分数越低，权重越高。</p></div>
          <div class="card"><b>执行约束层</b><p>Long-only，单一标的上限 25%，当前目标建仓比例 75%，保留约 25% 现金池供滑价、零股差异和后续调仓使用。</p></div>
        </div>
        <p class="footer-note">下一阶段若要更接近真正量化选股，可把人工核心池升级为规则筛选：流动性、上市年限、波动/回撤、财报质量、股息稳定性和产业分散约束。</p>
      </section>
"""
    asset_tabs_html = "\n".join(
        f"<div class=\"asset-chip\"><b>{html.escape(symbol)}</b><span>{html.escape(asset_name.get(symbol, ''))}</span></div>"
        for symbol in symbols
    )

    page = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>【Codex】台灣股市投資量化模型</title>
  <style>
    :root {{
      --bg: #f4f8f6;
      --panel: #ffffff;
      --panel-soft: #f8fbf9;
      --line: #dce6e1;
      --line-strong: #c9d8d2;
      --ink: #1e2f2d;
      --muted: #6b7d78;
      --green: #0f8f76;
      --green-soft: #e8f5f1;
      --red: #c94444;
      --red-soft: #fff0f0;
      --amber: #b86b00;
      --orange: #c66b00;
      --shadow: 0 18px 42px rgba(31, 58, 50, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
      font-size: 14px;
      overflow-x: hidden;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .app-shell {{
      display: grid;
      grid-template-columns: 72px minmax(0, 1fr) 280px;
      gap: 12px;
      min-height: 100vh;
      padding: 14px;
    }}
    .left-nav {{
      position: sticky;
      top: 18px;
      height: calc(100vh - 36px);
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 14px 10px;
      box-shadow: var(--shadow);
    }}
    .brand-mark {{
      width: 38px;
      height: 38px;
      margin: 0 auto 18px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #fff;
      font-weight: 800;
      background: var(--green);
    }}
    .nav-item {{
      display: grid;
      place-items: center;
      gap: 4px;
      min-height: 58px;
      color: var(--muted);
      border-radius: 8px;
      font-size: 11px;
    }}
    .nav-item.active {{ color: var(--green); background: var(--green-soft); font-weight: 700; }}
    .nav-icon {{ font-size: 17px; line-height: 1; }}
    .app-main {{ min-width: 0; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      margin-bottom: 14px;
    }}
    .title-block h1 {{
      margin: 0 0 6px;
      font-size: 25px;
      line-height: 1.18;
      font-weight: 850;
    }}
    .title-block p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .top-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .action-button {{
      border: 0;
      border-radius: 8px;
      padding: 9px 12px;
      color: #fff;
      background: var(--green);
      font-weight: 700;
      cursor: pointer;
    }}
    .action-button:focus-visible {{
      outline: 3px solid rgba(36, 128, 105, 0.25);
      outline-offset: 2px;
    }}
    .check-panel {{
      display: none;
      margin: -2px 0 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      box-shadow: var(--shadow);
      padding: 14px;
    }}
    .check-panel.is-open {{ display: block; }}
    .check-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 10px;
    }}
    .check-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfdfc;
    }}
    .check-item b {{ display: block; margin-bottom: 4px; color: var(--text); }}
    .check-item span {{ color: var(--muted); font-size: 12px; line-height: 1.45; }}
    .check-item.pass {{ border-color: rgba(36, 128, 105, 0.28); background: var(--green-soft); }}
    .check-item.warn {{ border-color: rgba(190, 112, 37, 0.28); background: #fff8ee; }}
    .trade-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .trade-button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 10px;
      background: #fff;
      color: var(--text);
      font-weight: 700;
      cursor: pointer;
    }}
    .trade-button.primary {{
      border-color: var(--green);
      background: var(--green);
      color: #fff;
    }}
    .trade-button.done {{
      border-color: rgba(36, 128, 105, 0.24);
      background: var(--green-soft);
      color: var(--green);
    }}
    .trade-status {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 72px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      background: #fff8ee;
      color: #9b5c17;
    }}
    .trade-status.done {{
      background: var(--green-soft);
      color: var(--green);
    }}
    .trade-id {{
      margin-top: 2px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      line-height: 1.35;
      white-space: nowrap;
    }}
    .signal-pill {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 72px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      background: #eef3f1;
      color: var(--muted);
    }}
    .signal-pill.buy {{
      background: var(--green-soft);
      color: var(--green);
    }}
    .signal-pill.sell {{
      background: var(--red-soft);
      color: var(--red);
    }}
    .empty-order-cell {{
      padding: 18px 16px;
      color: var(--muted);
      font-weight: 700;
      text-align: center;
      background: #f8fbf9;
    }}
    .strategy-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .strategy-list .card {{ padding: 12px; }}
    .asset-tabs {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
      gap: 8px;
      margin-bottom: 14px;
    }}
    .asset-chip {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 9px 10px;
      min-height: 54px;
      box-shadow: 0 6px 18px rgba(31,58,50,0.04);
    }}
    .asset-chip b {{ display: block; font-size: 13px; margin-bottom: 3px; }}
    .asset-chip span {{ display: block; color: var(--muted); font-size: 11px; line-height: 1.25; }}
    .hero, .panel, .chart, .side-card {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .hero {{ padding: 18px; margin-bottom: 14px; }}
    .hero-content {{ display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; align-items: stretch; }}
    .eyebrow {{ color: var(--green); font-size: 12px; font-weight: 800; margin-bottom: 8px; }}
    .lead {{ color: var(--muted); line-height: 1.6; max-width: 760px; }}
    .insight-strip, .metric-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}
    .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 0; }}
    .insight, .card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
      padding: 13px;
      min-width: 0;
    }}
    .insight b, .metric-label, .eyebrow-label {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      margin: 0 0 6px;
    }}
    .insight span, .metric {{
      display: block;
      color: var(--ink);
      font-size: 22px;
      line-height: 1.15;
      font-weight: 850;
    }}
    .hero-stat {{ color: var(--green); }}
    .stress-number, .big-risk {{ color: var(--red); }}
    .section {{ margin-top: 14px; }}
    .panel {{ padding: 16px; }}
    .chart {{ padding: 12px; overflow: hidden; }}
    .chart .plotly-graph-div {{ min-height: 360px; }}
    .chart-wide .plotly-graph-div {{ min-height: 430px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .stress-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 14px; align-items: stretch; }}
    h2 {{ margin: 0 0 10px; font-size: 18px; line-height: 1.25; }}
    h3 {{ margin: 0 0 8px; font-size: 16px; }}
    p {{ color: var(--muted); line-height: 1.65; margin: 0 0 10px; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    .metric-table {{ margin-top: 12px; }}
    th, td {{ padding: 10px 9px; border-bottom: 1px solid #edf2ef; text-align: left; font-size: 12px; vertical-align: middle; }}
    th {{ color: var(--muted); background: var(--panel-soft); font-size: 11px; font-weight: 800; }}
    tr:hover td {{ background: #fbfdfc; }}
    .risk-list {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0 0; padding: 0; list-style: none; }}
    .risk-list li {{ padding: 11px 12px; border: 1px solid #f0d3d3; border-radius: 8px; color: #7e2b2b; background: var(--red-soft); font-size: 12px; line-height: 1.45; }}
    .analysis-note {{
      margin: 0 0 10px;
      padding: 11px 12px;
      border: 1px solid rgba(36, 128, 105, 0.18);
      border-radius: 8px;
      background: var(--green-soft);
      color: var(--ink);
      font-size: 13px;
      line-height: 1.6;
    }}
    .analysis-note b {{ color: var(--green); }}
    .section-toolbar {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      align-items: flex-start;
      margin: 0 0 12px;
    }}
    .section-toolbar p {{
      margin: 0;
      flex: 1 1 420px;
    }}
    .section-toolbar .trade-actions {{
      margin-left: auto;
    }}
    textarea.research-report {{
      display: block;
      width: 100%;
      min-height: 150px;
      white-space: pre-wrap;
      margin: 0;
      padding: 14px;
      border: 1px solid #dce6e1;
      border-radius: 8px;
      background: #f8fbf9;
      color: var(--ink);
      font: 13px/1.7 "PingFang TC", "Microsoft JhengHei", sans-serif;
      resize: vertical;
      box-sizing: border-box;
    }}
    .table-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      align-items: start;
    }}
    .update-summary-list {{
      grid-template-columns: 1fr;
    }}
    .compact-table th, .compact-table td {{ padding: 8px 7px; }}
    .signal-table th, .signal-table td {{ padding: 8px 7px; }}
    .signal-table {{ table-layout: fixed; }}
    .signal-col-action {{ width: 9%; }}
    .signal-col-code {{ width: 7%; }}
    .signal-col-name {{ width: 18%; }}
    .signal-col-price {{ width: 9%; }}
    .signal-col-cost {{ width: 9%; }}
    .signal-col-days {{ width: 7%; }}
    .signal-col-return {{ width: 10%; }}
    .signal-col-shares {{ width: 8%; }}
    .signal-col-reason {{ width: 23%; }}
    .signal-table .name-cell {{ min-width: 92px; }}
    .signal-table th:nth-child(1), .signal-table td:nth-child(1),
    .signal-table th:nth-child(2), .signal-table td:nth-child(2),
    .signal-table th:nth-child(4), .signal-table td:nth-child(4),
    .signal-table th:nth-child(5), .signal-table td:nth-child(5),
    .signal-table th:nth-child(6), .signal-table td:nth-child(6),
    .signal-table th:nth-child(7), .signal-table td:nth-child(7),
    .signal-table th:nth-child(8), .signal-table td:nth-child(8) {{ text-align: center; }}
    .signal-table td:last-child, .signal-table th:last-child {{ white-space: nowrap; }}
    .name-cell {{ min-width: 112px; }}
    .asset-name {{ display: inline-block; white-space: nowrap; }}
    .footer-note {{ margin-top: 12px; font-size: 12px; color: var(--muted); }}
    .issues ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
    code {{ color: var(--green); background: var(--green-soft); padding: 2px 5px; border-radius: 5px; }}
    .execution-panel {{
      position: sticky;
      top: 18px;
      height: calc(100vh - 36px);
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow: auto;
      padding-right: 2px;
    }}
    .side-card {{ padding: 14px; }}
    .side-card.warning {{ background: #fff7f7; border-color: #f0cdcd; }}
    .big-risk {{ font-size: 28px; font-weight: 900; margin-bottom: 8px; }}
    .compact-status {{ color: var(--red); font-size: 20px; font-weight: 900; margin-bottom: 8px; }}
    .split-row {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 8px 0;
      border-bottom: 1px solid #edf2ef;
      color: var(--muted);
      font-size: 12px;
    }}
    .split-row b {{ color: var(--ink); }}
    .order-list {{ list-style: none; margin: 0; padding: 0; }}
    .order-list li {{
      display: grid;
      grid-template-columns: 52px 1fr;
      gap: 4px 8px;
      padding: 8px 0;
      border-bottom: 1px solid #edf2ef;
      font-size: 12px;
    }}
    .order-list span {{ font-weight: 800; color: var(--ink); }}
    .order-list b {{ text-align: right; color: var(--green); }}
    .order-list small {{ grid-column: 2; text-align: right; color: var(--muted); }}
    @media (max-width: 1180px) {{
      .app-shell {{ grid-template-columns: 72px minmax(0, 1fr); }}
      .execution-panel {{ position: static; height: auto; grid-column: 2; }}
      .hero-content, .stress-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 760px) {{
      .app-shell {{ display: block; padding: 10px; }}
      .left-nav {{ position: static; height: auto; display: flex; gap: 6px; margin-bottom: 10px; overflow-x: auto; }}
      .brand-mark {{ margin: 0 8px 0 0; flex: 0 0 38px; }}
      .nav-item {{ min-width: 64px; min-height: 48px; }}
      .topbar {{ display: block; }}
      .top-actions {{ margin-top: 10px; flex-wrap: wrap; }}
      .asset-tabs, .grid, .metric-grid, .insight-strip, .risk-list, .table-grid {{ grid-template-columns: 1fr; }}
      .chart {{ padding: 6px; }}
      table {{ display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
      .metric-table {{ min-width: 720px; }}
      .compact-table {{ min-width: 620px; }}
      .metric-table th, .metric-table td {{ white-space: nowrap; }}
      .metric-table td:last-child, .metric-table th:last-child {{ white-space: normal; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="left-nav">
      <div class="brand-mark">量</div>
      <a class="nav-item" href="#update-summary"><span class="nav-icon">◎</span><span>摘要</span></a>
      <a class="nav-item active" href="#risk-map"><span class="nav-icon">▦</span><span>風險</span></a>
      <a class="nav-item" href="#backtest"><span class="nav-icon">↻</span><span>回測</span></a>
      <a class="nav-item" href="#model"><span class="nav-icon">◎</span><span>建倉</span></a>
      <a class="nav-item" href="#rebalance-calendar"><span class="nav-icon">◇</span><span>日曆</span></a>
      <a class="nav-item" href="#trade-signals"><span class="nav-icon">⌁</span><span>訊號</span></a>
      <a class="nav-item" href="#manual-trading"><span class="nav-icon">▣</span><span>交易</span></a>
      <a class="nav-item" href="#orders"><span class="nav-icon">☑</span><span>執行</span></a>
      <a class="nav-item" href="#issues"><span class="nav-icon">!</span><span>記錄</span></a>
    </aside>
    <main class="app-main">
      <div class="topbar">
        <div class="title-block">
          <h1>【Codex】台灣股市投資量化模型</h1>
          <p>今日 Dashboard 更新日期：{html.escape(dashboard_generated_date)}；行情/回测序列最新日期：{html.escape(dashboard_data_end)}。用 {html.escape(dashboard_data_start)} 至 {html.escape(dashboard_data_end)} 的台股资料，连接风险分析、模型盘建仓与调仓节奏。</p>
        </div>
        <div class="top-actions">
          <span>今日更新 {html.escape(dashboard_generated_date)}</span>
          <span>行情最新 {html.escape(dashboard_data_end)}</span>
          <span>估计窗口 {backtest.window if backtest else DEFAULT_REBALANCE_WINDOW} 日</span>
          <span>调仓间隔 {backtest.step if backtest else DEFAULT_REBALANCE_STEP} 日</span>
          <button id="execution-check-button" class="action-button" type="button" aria-expanded="false" aria-controls="execution-check">手动执行检查</button>
        </div>
      </div>
{execution_check_html}
      <div class="asset-tabs">{asset_tabs_html}</div>

      <section class="hero">
        <div class="hero-content">
          <div>
            <div class="eyebrow">台灣股市穩健量化引擎</div>
            <p class="lead">本仪表盘比较普通样本协方差与收缩协方差下的最小方差组合，并把手动模型盘执行状态固定在右侧，方便从研究结果走到建仓与复核。</p>
            <div class="insight-strip">
              <div class="insight"><b>最高相关资产对</b><span>{html.escape(max_pair_text)}</span></div>
              <div class="insight"><b>集中度变化</b><span>{concentration_delta * 100:+.2f}%</span></div>
              <div class="insight"><b>回撤差异</b><span>{drawdown_delta * 100:+.2f}%</span></div>
            </div>
          </div>
          <div class="metric-grid">
            <div class="card"><div class="metric hero-stat">{len(symbols)}</div><p class="metric-label">纳入分析资产数</p></div>
            <div class="card"><div class="metric">{len(price_data.dates)}</div><p class="metric-label">共同交易日数量</p></div>
            <div class="card"><div class="metric stress-number">{sample_dd.min() * 100:.2f}%</div><p class="metric-label">普通协方差最大回撤</p></div>
            <div class="card"><div class="metric">{shrink_dd.min() * 100:.2f}%</div><p class="metric-label">收缩协方差最大回撤</p></div>
          </div>
        </div>
      </section>

{update_summary_html}

{model_html}

{rebalance_execution_calendar_html}

{trade_signal_html}

{decision_summary_html}

{group_risk_html}

{universe_strategy_html}

      <section id="risk-map" class="section chart chart-wide">
        <div class="analysis-note"><b>热力图分析：</b>{html.escape(heatmap_advice)}</div>
        {charts["heatmap"]}
      </section>
      <section class="section grid">
        <div class="panel">
          <h2>隐藏同源风险</h2>
          <div class="analysis-note"><b>风险建议：</b>{html.escape(heatmap_advice)}</div>
          <ul class="risk-list">{overlap_html}</ul>
        </div>
        <div class="chart">
          <div class="analysis-note"><b>风险贡献分析：</b>{html.escape(risk_advice)}</div>
          {charts["risk_shrink"]}
        </div>
      </section>
      <section class="section grid">
        <div class="chart">
          <div class="analysis-note"><b>普通方差权重：</b>普通样本协方差更容易受近期价格波动影响，若单一权重明显偏高，应视为短期样本风险而非确定机会。</div>
          {charts["weights_sample"]}
        </div>
        <div class="chart">
          <div class="analysis-note"><b>收缩方差权重：</b>{html.escape(weight_advice)}</div>
          {charts["weights_shrink"]}
        </div>
      </section>
      <section class="section chart">
        <div class="analysis-note"><b>净值曲线分析：</b>{html.escape(curve_advice)}</div>
        {charts["curve"]}
      </section>
      <section class="section chart">
        <div class="analysis-note"><b>回撤曲线分析：</b>{html.escape(drawdown_advice)}</div>
        {charts["drawdown"]}
      </section>

      <div id="backtest">{backtest_html}</div>

      <section class="section panel stress-grid">
        <div>
          <h2>压力情境摘要</h2>
          <p>规则情境：市场整体下跌 18%，波动率放大 1.8 倍，相关性向 1 收敛 35%。这是解释型压力测试，不代表真实未来损失。</p>
        </div>
        <div class="grid">
          <div class="card"><div class="metric stress-number">{sample_stress * 100:.2f}%</div><p class="metric-label">普通协方差压力估计损失</p></div>
          <div class="card"><div class="metric">{shrink_stress * 100:.2f}%</div><p class="metric-label">收缩协方差压力估计损失</p></div>
        </div>
      </section>

      <section class="section panel">
        <h2>组合明细</h2>
        <div class="analysis-note"><b>权重与风险贡献总览：</b>{html.escape(weight_advice)} {html.escape(risk_advice)}</div>
        <table>
          <thead><tr><th>代码</th><th>名称</th><th>普通权重</th><th>收缩权重</th><th>普通风险贡献</th><th>收缩风险贡献</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </section>

      <section id="issues" class="section panel issues">
        <h2>数据问题记录</h2>
        <ul>{issues_html}</ul>
        <p class="footer-note">页面由本地脚本生成，不包含 API Key、Token 或交易权限。压力情境仅用于研究解释，不构成投资建议。</p>
      </section>
    </main>
{order_sidebar_html}
  </div>
  <script>
    (() => {{
      const button = document.getElementById("execution-check-button");
      const panel = document.getElementById("execution-check");
      if (button && panel) {{
        button.addEventListener("click", () => {{
          const isOpen = panel.classList.toggle("is-open");
          button.setAttribute("aria-expanded", String(isOpen));
          button.textContent = isOpen ? "收起执行检查" : "手动执行检查";
          if (isOpen) {{
            panel.scrollIntoView({{ behavior: "smooth", block: "start" }});
          }}
        }});
      }}

      const storageKey = "risk-dashboard-manual-trades-v2-{html.escape(model_portfolio.build_date if model_portfolio else DEFAULT_MODEL_BUILD_DATE)}-{html.escape(model_portfolio.market_date if model_portfolio and model_portfolio.market_date else 'no-market')}";
      const defaultTradeState = {default_trade_state_json};
      const readState = () => {{
        try {{
          const savedState = localStorage.getItem(storageKey);
          return savedState ? JSON.parse(savedState) : {{ ...defaultTradeState }};
        }} catch {{
          return {{ ...defaultTradeState }};
        }}
      }};
      const writeState = (state) => localStorage.setItem(storageKey, JSON.stringify(state));
      const setTradeStatus = (tradeId, done) => {{
        const status = document.querySelector(`[data-trade-status="${{tradeId}}"]`);
        const toggle = document.querySelector(`[data-trade-toggle="${{tradeId}}"]`);
        if (!status || !toggle) return;
        status.textContent = done ? "页面已确认" : "待确认";
        status.classList.toggle("done", done);
        toggle.textContent = done ? "改回待确认" : "页面标记已确认";
        toggle.classList.toggle("done", done);
        document.querySelectorAll(`tr[data-trade-id="${{tradeId}}"]`).forEach((row) => {{
          row.classList.toggle("trade-done", done);
          row.hidden = done;
        }});
      }};
      const applyTradeState = () => {{
        const state = readState();
        document.querySelectorAll("[data-trade-toggle]").forEach((toggle) => {{
          const tradeId = toggle.getAttribute("data-trade-toggle");
          setTradeStatus(tradeId, Boolean(state[tradeId]));
        }});
      }};
      document.querySelectorAll("[data-trade-toggle]").forEach((toggle) => {{
        toggle.addEventListener("click", () => {{
          const tradeId = toggle.getAttribute("data-trade-toggle");
          const state = readState();
          state[tradeId] = !state[tradeId];
          writeState(state);
          setTradeStatus(tradeId, Boolean(state[tradeId]));
        }});
      }});
      const markAll = document.getElementById("mark-all-trades");
      if (markAll) {{
        markAll.addEventListener("click", () => {{
          const state = {{}};
          document.querySelectorAll("[data-trade-toggle]").forEach((toggle) => {{
            const tradeId = toggle.getAttribute("data-trade-toggle");
            state[tradeId] = true;
          }});
          writeState(state);
          applyTradeState();
        }});
      }}
      const reset = document.getElementById("reset-trade-status");
      if (reset) {{
        reset.addEventListener("click", () => {{
          localStorage.removeItem(storageKey);
          applyTradeState();
          const originalText = reset.textContent;
          reset.textContent = "已重置";
          reset.classList.add("done");
          window.setTimeout(() => {{
            reset.textContent = originalText;
            reset.classList.remove("done");
          }}, 1200);
        }});
      }}
      applyTradeState();
    }})();
  </script>
</body>
</html>"""
    output.write_text(page, encoding="utf-8")


def main() -> None:
    args = parse_args()
    assets = load_universe(args.universe)
    months = month_range(args.start, args.end)
    price_data, issues = load_prices(
        assets=assets,
        months=months,
        cache_dir=args.cache_dir,
        allow_stale_cache=args.allow_stale_cache,
        offline_cache=args.offline_cache,
        data_source=args.data_source,
    )
    snapshot_path = args.model_market_values or latest_market_values_path()
    price_data = append_market_snapshot_to_price_data(price_data, snapshot_path, issues)
    returns = simple_returns(price_data.prices)

    sample_cov = covariance_matrix(returns)
    shrink_cov, model_issue = estimate_shrink_covariance(returns)
    if model_issue:
        issues.append(model_issue)

    sample_weights = min_variance_weights(sample_cov)
    shrink_weights = min_variance_weights(shrink_cov)
    backtest: BacktestResult | None = None
    try:
        backtest = rolling_rebalance_backtest(
            returns=returns,
            dates=price_data.dates[1:],
            window=args.rebalance_window,
            step=args.rebalance_step,
        )
    except Exception as exc:
        issues.append(DataIssue("BACKTEST", f"滚动再平衡回测未执行：{exc}"))
    model_portfolio: ModelPortfolio | None = None
    if args.model_portfolio or args.update_daily_market:
        try:
            model_weights = shrink_weights
            model_metrics: dict[str, dict[str, float]] | None = None
            model_analysis_start = price_data.dates[0]
            model_analysis_end = price_data.dates[-1]
            model_lookback_years = MODEL_LOOKBACK_YEARS
            if args.model_method == "drawdown-risk":
                model_weights, model_metrics, model_analysis_end, model_analysis_start, model_lookback_years = drawdown_risk_weights(
                    price_data=price_data,
                    build_date=args.model_build_date,
                    issues=issues,
                )
                issues.append(
                    DataIssue(
                        "MODEL_PORTFOLIO",
                        (
                            f"模型盘使用 {model_lookback_years} 年回撤风险加权：{model_analysis_start} 至 {model_analysis_end}"
                            if model_lookback_years
                            else f"模型盘使用可用资料回撤风险加权：{model_analysis_start} 至 {model_analysis_end}"
                        ),
                    )
                )
            elif args.model_method == "multi-factor-shrink":
                model_weights, model_metrics, model_analysis_end, model_analysis_start, model_lookback_years = multi_factor_shrink_weights(
                    assets=assets,
                    price_data=price_data,
                    build_date=args.model_build_date,
                    shrink_covariance=shrink_cov,
                    issues=issues,
                    ai_tilt=args.ai_tilt,
                )
                issues.append(
                    DataIssue(
                        "MODEL_PORTFOLIO",
                        (
                            f"模型盘使用台股多层多因子收缩优化：{model_analysis_start} 至 {model_analysis_end}；"
                            "价格层因子为动量、低波、回撤防御、流动性与趋势强度；"
                            "代理层因子为行业/主题相对强弱、AI 产业暴露、资金流代理与风险偏好代理；"
                            f"AI 倾斜为 {args.ai_tilt}。"
                        ),
                    )
                )
            else:
                issues.append(
                    DataIssue(
                        "MODEL_PORTFOLIO",
                        f"模型盘使用收缩协方差最小方差权重：{model_analysis_start} 至 {model_analysis_end}",
                    )
                )
            execution_orders_path = args.model_execution_orders or default_execution_orders_path(args.model_build_date)
            execution_orders = load_model_execution_orders(execution_orders_path)
            if execution_orders:
                issues.append(DataIssue("MODEL_PORTFOLIO", f"已套用模拟持仓/建仓执行单：{execution_orders_path}"))
            updated_market: MarketSnapshotUpdate | None = None
            if args.market_source == "shioaji" or args.update_daily_market:
                market_output_path = args.model_market_values or daily_market_output_path(args.market_date, args.market_mode)
                updated_market = update_daily_market_values(
                    assets=assets,
                    execution_orders=execution_orders,
                    market_date=args.market_date,
                    market_mode=args.market_mode,
                    output_path=market_output_path,
                )
                issues.append(
                    DataIssue(
                        "DAILY_MARKET",
                        f"已更新每日行情：{updated_market.path}，模式 {updated_market.market_mode}，成功 {updated_market.quote_count} 檔，缺失 {updated_market.missing_count} 檔。",
                    )
                )
            elif args.market_source == "public-close":
                refreshed_issues: list[DataIssue] = []
                effective_market_date = price_data.dates[-1] if price_data.dates else args.market_date
                refresh_months = months[-1:] or months
                try:
                    refreshed_market_date, refreshed_issues = latest_available_public_close_date(
                        assets=assets,
                        months=refresh_months,
                        cache_dir=args.cache_dir,
                        allow_stale_cache=True,
                    )
                    issues.extend(refreshed_issues)
                    if refreshed_market_date:
                        effective_market_date = refreshed_market_date
                        price_data, refresh_load_issues = load_prices(
                            assets=assets,
                            months=months,
                            cache_dir=args.cache_dir,
                            allow_stale_cache=args.allow_stale_cache,
                            offline_cache=args.offline_cache,
                            data_source=args.data_source,
                        )
                        issues.extend(refresh_load_issues)
                except Exception as exc:
                    issues.append(DataIssue("DAILY_MARKET", f"public-close 刷新公开月资料失败，继续使用现有序列：{exc}"))
                market_output_path = args.model_market_values or daily_market_output_path(effective_market_date, "close")
                try:
                    updated_market = build_public_close_market_values(
                        assets=assets,
                        execution_orders=execution_orders,
                        price_data=price_data,
                        market_date=effective_market_date,
                        market_mode="close",
                        output_path=market_output_path,
                    )
                    issues.append(
                        DataIssue(
                            "DAILY_MARKET",
                            f"已用公开收盘价重建每日行情：{updated_market.path}，日期 {updated_market.market_date}，成功 {updated_market.quote_count} 檔，缺失 {updated_market.missing_count} 檔。",
                        )
                    )
                except Exception as exc:
                    issues.append(DataIssue("DAILY_MARKET", f"公开收盘重建失败，改用既有市值檔：{exc}"))
            market_values_path = updated_market.path if updated_market else args.model_market_values or latest_market_values_path() or (ROOT / "data" / f"model_portfolio_market_{args.model_build_date}.csv")
            market_values = load_model_market_values(market_values_path)
            if market_values:
                issues.append(DataIssue("MODEL_PORTFOLIO", f"已套用今日持仓市值：{market_values_path}"))
            model_portfolio = build_model_portfolio(
                assets=assets,
                price_data=price_data,
                weights=model_weights,
                initial_cash=args.model_cash,
                output_path=args.model_output,
                build_date=args.model_build_date,
                analysis_start_date=model_analysis_start,
                analysis_end_date=model_analysis_end,
                method=args.model_method,
                ai_tilt=args.ai_tilt,
                invest_ratio=args.model_invest_ratio,
                risk_metrics=model_metrics,
                lookback_years=model_lookback_years,
                execution_price_ready=False,
                execution_orders=execution_orders,
                market_values=market_values,
            )
            if args.execute_simulated_trades:
                trade_batch_seq = normalize_simulated_trade_batch_seq(args.simulated_trade_batch_seq)
                signals = build_trade_signals(price_data, model_portfolio, args.simulated_trades_output, trade_batch_seq)
                trade_path, positions_path, trade_count = write_simulated_trades(
                    portfolio=model_portfolio,
                    signals=signals,
                    execution_orders=execution_orders,
                    assets=assets,
                    trade_output_path=args.simulated_trades_output,
                    positions_output_path=args.simulated_positions_output,
                    trade_batch_seq=trade_batch_seq,
                )
                issues.append(
                    DataIssue(
                        "SIMULATED_TRADES",
                        f"已落账模拟成交 {trade_count} 笔，批次 {trade_batch_seq}：{trade_path}；已更新模拟持仓：{positions_path}",
                    )
                )
                execution_orders = load_model_execution_orders(args.simulated_positions_output or DEFAULT_SIMULATED_POSITIONS_OUTPUT)
                model_portfolio = build_model_portfolio(
                    assets=assets,
                    price_data=price_data,
                    weights=model_weights,
                    initial_cash=args.model_cash,
                    output_path=args.model_output,
                    build_date=args.model_build_date,
                    analysis_start_date=model_analysis_start,
                    analysis_end_date=model_analysis_end,
                    method=args.model_method,
                    ai_tilt=args.ai_tilt,
                    invest_ratio=args.model_invest_ratio,
                    risk_metrics=model_metrics,
                    lookback_years=model_lookback_years,
                    execution_price_ready=False,
                    execution_orders=execution_orders,
                    market_values=market_values,
                )
            issues.append(DataIssue("MODEL_PORTFOLIO", f"已生成手动模型盘：{args.model_output}"))
        except Exception as exc:
            write_model_portfolio_status_csv(
                output_path=args.model_output,
                build_date=args.model_build_date,
                method=args.model_method,
                message=str(exc),
            )
            issues.append(DataIssue("MODEL_PORTFOLIO", f"手动模型盘未生成：{exc}"))

    render_dashboard(
        output=args.output,
        assets=assets,
        price_data=price_data,
        returns=returns,
        sample_weights=sample_weights,
        shrink_weights=shrink_weights,
        sample_cov=sample_cov,
        shrink_cov=shrink_cov,
        backtest=backtest,
        model_portfolio=model_portfolio,
        issues=issues,
        trade_output_path=args.simulated_trades_output,
        trade_batch_seq=args.simulated_trade_batch_seq,
    )
    print(f"已生成仪表盘：{args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"运行失败：{exc}", file=sys.stderr)
        sys.exit(1)
