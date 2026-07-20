from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src" / "risk_dashboard.py"
TMP_MARKDOWN_OUTPUT = Path("/tmp/tw_quant_factor_profile_compare.md")
TMP_JSON_OUTPUT = Path("/tmp/tw_quant_factor_profile_compare.json")
DEFAULT_FOCUS_SYMBOLS = ("0050", "2412", "00881", "2330", "2317", "2454", "2303")


def load_module():
    spec = importlib.util.spec_from_file_location("risk_dashboard_mod", SRC_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载主脚本：{SRC_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_months(start: str, end: str) -> list[str]:
    start_year, start_month = map(int, start.split("-"))
    end_year, end_month = map(int, end.split("-"))
    months: list[str] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        months.append(f"{year}{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def legacy_multi_factor_weights(mod, assets, price_data, build_date: str, shrink_covariance: np.ndarray, ai_tilt: str):
    price_index = mod.previous_available_date_index(price_data.dates, build_date)
    start_index = max(0, price_index - mod.ANNUALIZATION_DAYS)
    observations = price_index - start_index + 1
    if observations < mod.MIN_OBSERVATIONS:
        raise RuntimeError(f"旧 4 因子比较至少需要 {mod.MIN_OBSERVATIONS} 个共同交易日，当前仅有 {observations} 个。")

    window_prices = price_data.prices[start_index : price_index + 1]
    window_returns = mod.simple_returns(window_prices)
    valid_indices: list[int] = []
    momentum_values: list[float] = []
    low_vol_values: list[float] = []
    drawdown_values: list[float] = []
    liquidity_values: list[float] = []

    for index, _symbol in enumerate(price_data.symbols):
        series = window_prices[:, index]
        asset_returns = window_returns[:, index]
        if len(series) < mod.MIN_OBSERVATIONS or np.any(series <= 0) or not np.all(np.isfinite(series)):
            continue
        curve = series / series[0]
        max_dd = abs(float(mod.drawdown(curve).min()))
        volatility = mod.annualized_volatility(asset_returns)
        if max_dd <= 0 or volatility <= 0:
            continue
        if len(series) >= 253:
            momentum = float(series[-22] / series[-253] - 1.0)
        else:
            momentum = mod.capped_compound_return(series, min(120, len(series) - 1))
        liquidity = 0.0
        if price_data.amounts is not None:
            amount_series = price_data.amounts[start_index : price_index + 1, index]
            average_amount = mod.mean_tail(amount_series, min(20, len(amount_series)))
            liquidity = float(np.log1p(average_amount or 0.0))
        valid_indices.append(index)
        momentum_values.append(momentum)
        low_vol_values.append(-volatility)
        drawdown_values.append(-max_dd)
        liquidity_values.append(liquidity)

    momentum_z = mod.zscore(np.array(momentum_values, dtype=float))
    low_vol_z = mod.zscore(np.array(low_vol_values, dtype=float))
    drawdown_z = mod.zscore(np.array(drawdown_values, dtype=float))
    liquidity_z = mod.zscore(np.array(liquidity_values, dtype=float))
    legacy_scores = 0.35 * momentum_z + 0.25 * low_vol_z + 0.25 * drawdown_z + 0.15 * liquidity_z
    expected_returns = 0.06 + 0.025 * legacy_scores
    valid_covariance = shrink_covariance[np.ix_(valid_indices, valid_indices)]
    valid_weights = mod.drop_tiny_weights(mod.max_sharpe_weights(expected_returns, valid_covariance, mod.MAX_WEIGHT), max_weight=mod.MAX_WEIGHT)

    asset_by_symbol = {asset.symbol: asset for asset in assets}
    ai_mask = np.array(
        [asset_by_symbol.get(price_data.symbols[index], mod.Asset(price_data.symbols[index], "", "", "")).ai_supply_chain for index in valid_indices],
        dtype=bool,
    )
    if ai_tilt == "moderate":
        valid_weights = mod.drop_tiny_weights(mod.apply_group_tilt(valid_weights, ai_mask, 0.33, 0.35, mod.MAX_WEIGHT), max_weight=mod.MAX_WEIGHT)
    elif ai_tilt == "strong":
        valid_weights = mod.drop_tiny_weights(mod.apply_group_tilt(valid_weights, ai_mask, 0.38, 0.40, mod.MAX_WEIGHT), max_weight=mod.MAX_WEIGHT)

    weights = np.zeros(len(price_data.symbols), dtype=float)
    for offset, index in enumerate(valid_indices):
        weights[index] = valid_weights[offset]
    return weights


def summarize_weights(symbols: list[str], weights: np.ndarray) -> list[tuple[str, float]]:
    pairs = [(symbol, float(weights[index])) for index, symbol in enumerate(symbols)]
    return sorted(pairs, key=lambda item: item[1], reverse=True)


def group_exposure(symbols: list[str], weights: np.ndarray, assets, field: str) -> list[dict[str, float | str]]:
    asset_by_symbol = {asset.symbol: asset for asset in assets}
    grouped: dict[str, float] = {}
    for index, symbol in enumerate(symbols):
        asset = asset_by_symbol.get(symbol)
        raw_value = getattr(asset, field, "") if asset else ""
        group = str(raw_value or "").strip() or "未分类"
        grouped[group] = grouped.get(group, 0.0) + float(weights[index])
    items = [{"group": group, "weight": weight} for group, weight in grouped.items()]
    return sorted(items, key=lambda item: float(item["weight"]), reverse=True)


def ai_binary_exposure(symbols: list[str], weights: np.ndarray, assets) -> list[dict[str, float | str]]:
    asset_by_symbol = {asset.symbol: asset for asset in assets}
    grouped = {"AI 供应链": 0.0, "非 AI 供应链": 0.0}
    for index, symbol in enumerate(symbols):
        asset = asset_by_symbol.get(symbol)
        key = "AI 供应链" if asset and getattr(asset, "ai_supply_chain", False) else "非 AI 供应链"
        grouped[key] += float(weights[index])
    return [{"group": key, "weight": value} for key, value in grouped.items()]


def concentration_metrics(weights: np.ndarray) -> dict[str, float]:
    clean = np.asarray(weights, dtype=float)
    positive = clean[clean > 0]
    hhi = float(np.sum(clean**2))
    effective_n = float(1.0 / hhi) if hhi > 0 else 0.0
    top3_weight = float(np.sum(np.sort(clean)[-3:])) if len(clean) >= 3 else float(np.sum(clean))
    active_count = float(np.sum(clean > 1e-6))
    return {
        "hhi": hhi,
        "effective_n": effective_n,
        "top3_weight": top3_weight,
        "active_count": active_count,
        "max_weight": float(np.max(clean)) if len(clean) else 0.0,
    }


def exposure_diffs(
    legacy_groups: list[dict[str, float | str]],
    expanded_groups: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    legacy_map = {str(item["group"]): float(item["weight"]) for item in legacy_groups}
    expanded_map = {str(item["group"]): float(item["weight"]) for item in expanded_groups}
    all_groups = sorted(set(legacy_map) | set(expanded_map))
    diffs = []
    for group in all_groups:
        legacy_weight = legacy_map.get(group, 0.0)
        expanded_weight = expanded_map.get(group, 0.0)
        diffs.append(
            {
                "group": group,
                "legacy_weight": legacy_weight,
                "expanded_weight": expanded_weight,
                "diff": expanded_weight - legacy_weight,
            }
        )
    return sorted(diffs, key=lambda item: abs(float(item["diff"])), reverse=True)


def top_weight_diffs(symbols: list[str], legacy_weights: np.ndarray, expanded_weights: np.ndarray) -> list[dict[str, float | str]]:
    diffs = []
    for index, symbol in enumerate(symbols):
        legacy_weight = float(legacy_weights[index])
        expanded_weight = float(expanded_weights[index])
        diffs.append(
            {
                "symbol": symbol,
                "legacy_weight": legacy_weight,
                "expanded_weight": expanded_weight,
                "diff": expanded_weight - legacy_weight,
            }
        )
    return sorted(diffs, key=lambda item: abs(float(item["diff"])), reverse=True)


def risk_group_diffs(mod, assets, symbols: list[str], weights: np.ndarray, covariance: np.ndarray, field: str) -> list[dict[str, float | str]]:
    risk_values = mod.risk_contribution(weights, covariance)
    if field == "ai_binary":
        groups = mod.aggregate_group_exposure(
            assets,
            symbols,
            weights,
            risk_values,
            lambda asset: "AI 供应链" if asset and getattr(asset, "ai_supply_chain", False) else "非 AI 供应链",
        )
    else:
        groups = mod.aggregate_group_exposure(
            assets,
            symbols,
            weights,
            risk_values,
            lambda asset: getattr(asset, field, "") if asset else "",
        )
    return groups


def ai_weight(symbols: list[str], weights: np.ndarray, assets) -> float:
    ai_symbols = {asset.symbol for asset in assets if getattr(asset, "ai_supply_chain", False)}
    return float(sum(float(weights[index]) for index, symbol in enumerate(symbols) if symbol in ai_symbols))


def stress_summary(mod, weights: np.ndarray, covariance: np.ndarray) -> dict[str, float]:
    stressed = float(mod.stress_loss(weights, covariance))
    return {
        "stress_loss": stressed,
        "stress_drop": stressed - (-0.18),
    }


def overlap_summary(symbols: list[str], weights: np.ndarray, correlation: np.ndarray, threshold: float = 0.75) -> dict[str, float | str]:
    active = [index for index, weight in enumerate(weights) if float(weight) > 1e-6]
    if len(active) < 2:
        return {
            "pair_count": 0.0,
            "top_pair": "无",
            "top_pair_corr": 0.0,
            "average_pair_corr": 0.0,
        }
    best_pair = ("", "")
    best_corr = -1.0
    pair_count = 0
    corr_sum = 0.0
    corr_count = 0
    for offset, left in enumerate(active):
        for right in active[offset + 1 :]:
            value = float(correlation[left, right])
            corr_sum += value
            corr_count += 1
            if value >= threshold:
                pair_count += 1
            if value > best_corr:
                best_corr = value
                best_pair = (symbols[left], symbols[right])
    return {
        "pair_count": float(pair_count),
        "top_pair": f"{best_pair[0]} / {best_pair[1]}",
        "top_pair_corr": float(best_corr),
        "average_pair_corr": float(corr_sum / corr_count) if corr_count else 0.0,
    }


def write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# 台股多因子框架比较",
        "",
        f"- 建仓日：`{payload['build_date']}`",
        f"- 样本区间：`{payload['start']}` 到 `{payload['end']}`",
        f"- AI 倾斜：`{payload['ai_tilt']}`",
        f"- 数据源：`offline-cache + TWSE`",
        "",
        "## 约束检查",
        "",
        f"- 旧 4 因子权重合计：`{payload['legacy']['weight_sum']:.8f}`",
        f"- 新扩展框架权重合计：`{payload['expanded']['weight_sum']:.8f}`",
        f"- 旧 4 因子最大单一权重：`{payload['legacy']['max_weight']:.8f}`",
        f"- 新扩展框架最大单一权重：`{payload['expanded']['max_weight']:.8f}`",
        f"- 旧 4 因子 AI 群组权重：`{payload['legacy']['ai_weight']:.8f}`",
        f"- 新扩展框架 AI 群组权重：`{payload['expanded']['ai_weight']:.8f}`",
        "",
        "## 集中度变化",
        "",
        f"- 旧 4 因子 HHI：`{payload['legacy']['concentration']['hhi']:.8f}`",
        f"- 新扩展框架 HHI：`{payload['expanded']['concentration']['hhi']:.8f}`",
        f"- 旧 4 因子有效持仓数：`{payload['legacy']['concentration']['effective_n']:.4f}`",
        f"- 新扩展框架有效持仓数：`{payload['expanded']['concentration']['effective_n']:.4f}`",
        f"- 旧 4 因子前三大权重合计：`{payload['legacy']['concentration']['top3_weight']:.8f}`",
        f"- 新扩展框架前三大权重合计：`{payload['expanded']['concentration']['top3_weight']:.8f}`",
        f"- 旧 4 因子活跃持仓数：`{payload['legacy']['concentration']['active_count']:.0f}`",
        f"- 新扩展框架活跃持仓数：`{payload['expanded']['concentration']['active_count']:.0f}`",
        "",
        "## 压力情境变化",
        "",
        f"- 旧 4 因子压力估计损失：`{payload['legacy']['stress']['stress_loss']:.6f}`",
        f"- 新扩展框架压力估计损失：`{payload['expanded']['stress']['stress_loss']:.6f}`",
        f"- 压力损失变化：`{payload['stress_delta']:+.6f}`",
        "",
        "## 高相关重叠变化",
        "",
        f"- 旧 4 因子高相关配对数：`{payload['legacy']['overlap']['pair_count']:.0f}`",
        f"- 新扩展框架高相关配对数：`{payload['expanded']['overlap']['pair_count']:.0f}`",
        f"- 旧 4 因子最高相关配对：`{payload['legacy']['overlap']['top_pair']}`，相关性 `{payload['legacy']['overlap']['top_pair_corr']:.4f}`",
        f"- 新扩展框架最高相关配对：`{payload['expanded']['overlap']['top_pair']}`，相关性 `{payload['expanded']['overlap']['top_pair_corr']:.4f}`",
        f"- 旧 4 因子平均配对相关性：`{payload['legacy']['overlap']['average_pair_corr']:.4f}`",
        f"- 新扩展框架平均配对相关性：`{payload['expanded']['overlap']['average_pair_corr']:.4f}`",
        "",
        "## 关注标的差异",
        "",
        "| 代码 | 旧权重 | 新权重 | 变化 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in payload["focus_diffs"]:
        lines.append(
            f"| {item['symbol']} | {item['legacy_weight']:.6f} | {item['expanded_weight']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 权重变化最大标的",
            "",
            "| 代码 | 旧权重 | 新权重 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["top_weight_diffs"][:5]:
        lines.append(
            f"| {item['symbol']} | {item['legacy_weight']:.6f} | {item['expanded_weight']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 行业暴露变化",
            "",
            "| 行业 | 旧权重 | 新权重 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["sector_diffs"][:5]:
        lines.append(
            f"| {item['group']} | {item['legacy_weight']:.6f} | {item['expanded_weight']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 主题暴露变化",
            "",
            "| 主题 | 旧权重 | 新权重 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["theme_diffs"][:5]:
        lines.append(
            f"| {item['group']} | {item['legacy_weight']:.6f} | {item['expanded_weight']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## AI / 非 AI 暴露变化",
            "",
            "| 分组 | 旧权重 | 新权重 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["ai_diffs"]:
        lines.append(
            f"| {item['group']} | {item['legacy_weight']:.6f} | {item['expanded_weight']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 行业风险贡献变化",
            "",
            "| 行业 | 旧风险贡献 | 新风险贡献 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["sector_risk_diffs"][:5]:
        lines.append(
            f"| {item['group']} | {item['legacy_risk']:.6f} | {item['expanded_risk']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 主题风险贡献变化",
            "",
            "| 主题 | 旧风险贡献 | 新风险贡献 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["theme_risk_diffs"][:5]:
        lines.append(
            f"| {item['group']} | {item['legacy_risk']:.6f} | {item['expanded_risk']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## AI / 非 AI 风险贡献变化",
            "",
            "| 分组 | 旧风险贡献 | 新风险贡献 | 变化 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in payload["ai_risk_diffs"]:
        lines.append(
            f"| {item['group']} | {item['legacy_risk']:.6f} | {item['expanded_risk']:.6f} | {item['diff']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "## 新框架前五大权重",
            "",
            "| 排名 | 代码 | 权重 |",
            "| --- | --- | ---: |",
        ]
    )
    for rank, item in enumerate(payload["expanded_top"][:5], start=1):
        lines.append(f"| {rank} | {item['symbol']} | {item['weight']:.6f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较旧 4 因子与新扩展多因子框架的模型盘权重差异。")
    parser.add_argument("--start", default="2024-01")
    parser.add_argument("--end", default="2026-06")
    parser.add_argument("--build-date", default="2026-06-03")
    parser.add_argument("--ai-tilt", choices=("none", "moderate", "strong"), default="moderate")
    parser.add_argument("--markdown-output", type=Path, default=TMP_MARKDOWN_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=TMP_JSON_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mod = load_module()
    assets = mod.load_universe(ROOT / "config" / "universe_tw.csv")
    months = build_months(args.start, args.end)
    price_data, _issues = mod.load_prices(assets, months, ROOT / "data" / "cache", False, True, "twse")
    returns = mod.simple_returns(price_data.prices)
    shrink_covariance, _ = mod.estimate_shrink_covariance(returns)

    legacy_weights = legacy_multi_factor_weights(mod, assets, price_data, args.build_date, shrink_covariance, args.ai_tilt)
    expanded_weights, _metrics, _analysis_end, _analysis_start, _lookback_years = mod.multi_factor_shrink_weights(
        assets,
        price_data,
        args.build_date,
        shrink_covariance,
        [],
        ai_tilt=args.ai_tilt,
    )

    focus_diffs = []
    for symbol in DEFAULT_FOCUS_SYMBOLS:
        if symbol not in price_data.symbols:
            continue
        index = price_data.symbols.index(symbol)
        legacy_weight = float(legacy_weights[index])
        expanded_weight = float(expanded_weights[index])
        focus_diffs.append(
            {
                "symbol": symbol,
                "legacy_weight": legacy_weight,
                "expanded_weight": expanded_weight,
                "diff": expanded_weight - legacy_weight,
            }
        )

    legacy_top = summarize_weights(price_data.symbols, legacy_weights)
    expanded_top = summarize_weights(price_data.symbols, expanded_weights)
    correlation = mod.correlation_matrix(returns)
    legacy_sector = group_exposure(price_data.symbols, legacy_weights, assets, "sector")
    expanded_sector = group_exposure(price_data.symbols, expanded_weights, assets, "sector")
    legacy_theme = group_exposure(price_data.symbols, legacy_weights, assets, "theme")
    expanded_theme = group_exposure(price_data.symbols, expanded_weights, assets, "theme")
    legacy_ai = ai_binary_exposure(price_data.symbols, legacy_weights, assets)
    expanded_ai = ai_binary_exposure(price_data.symbols, expanded_weights, assets)
    legacy_sector_risk = risk_group_diffs(mod, assets, price_data.symbols, legacy_weights, shrink_covariance, "sector")
    expanded_sector_risk = risk_group_diffs(mod, assets, price_data.symbols, expanded_weights, shrink_covariance, "sector")
    legacy_theme_risk = risk_group_diffs(mod, assets, price_data.symbols, legacy_weights, shrink_covariance, "theme")
    expanded_theme_risk = risk_group_diffs(mod, assets, price_data.symbols, expanded_weights, shrink_covariance, "theme")
    legacy_ai_risk = risk_group_diffs(mod, assets, price_data.symbols, legacy_weights, shrink_covariance, "ai_binary")
    expanded_ai_risk = risk_group_diffs(mod, assets, price_data.symbols, expanded_weights, shrink_covariance, "ai_binary")
    payload = {
        "start": args.start,
        "end": args.end,
        "build_date": args.build_date,
        "ai_tilt": args.ai_tilt,
        "legacy": {
            "weight_sum": float(np.sum(legacy_weights)),
            "max_weight": float(np.max(legacy_weights)),
            "ai_weight": ai_weight(price_data.symbols, legacy_weights, assets),
            "concentration": concentration_metrics(legacy_weights),
            "stress": stress_summary(mod, legacy_weights, shrink_covariance),
            "overlap": overlap_summary(price_data.symbols, legacy_weights, correlation),
        },
        "expanded": {
            "weight_sum": float(np.sum(expanded_weights)),
            "max_weight": float(np.max(expanded_weights)),
            "ai_weight": ai_weight(price_data.symbols, expanded_weights, assets),
            "concentration": concentration_metrics(expanded_weights),
            "stress": stress_summary(mod, expanded_weights, shrink_covariance),
            "overlap": overlap_summary(price_data.symbols, expanded_weights, correlation),
        },
        "stress_delta": float(mod.stress_loss(expanded_weights, shrink_covariance) - mod.stress_loss(legacy_weights, shrink_covariance)),
        "focus_diffs": focus_diffs,
        "top_weight_diffs": top_weight_diffs(price_data.symbols, legacy_weights, expanded_weights),
        "sector_diffs": exposure_diffs(legacy_sector, expanded_sector),
        "theme_diffs": exposure_diffs(legacy_theme, expanded_theme),
        "ai_diffs": exposure_diffs(legacy_ai, expanded_ai),
        "sector_risk_diffs": [
            {
                "group": item["group"],
                "legacy_risk": next((float(left["risk"]) for left in legacy_sector_risk if str(left["group"]) == str(item["group"])), 0.0),
                "expanded_risk": next((float(right["risk"]) for right in expanded_sector_risk if str(right["group"]) == str(item["group"])), 0.0),
                "diff": next((float(right["risk"]) for right in expanded_sector_risk if str(right["group"]) == str(item["group"])), 0.0)
                - next((float(left["risk"]) for left in legacy_sector_risk if str(left["group"]) == str(item["group"])), 0.0),
            }
            for item in exposure_diffs(legacy_sector, expanded_sector)
        ],
        "theme_risk_diffs": [
            {
                "group": item["group"],
                "legacy_risk": next((float(left["risk"]) for left in legacy_theme_risk if str(left["group"]) == str(item["group"])), 0.0),
                "expanded_risk": next((float(right["risk"]) for right in expanded_theme_risk if str(right["group"]) == str(item["group"])), 0.0),
                "diff": next((float(right["risk"]) for right in expanded_theme_risk if str(right["group"]) == str(item["group"])), 0.0)
                - next((float(left["risk"]) for left in legacy_theme_risk if str(left["group"]) == str(item["group"])), 0.0),
            }
            for item in exposure_diffs(legacy_theme, expanded_theme)
        ],
        "ai_risk_diffs": [
            {
                "group": item["group"],
                "legacy_risk": next((float(left["risk"]) for left in legacy_ai_risk if str(left["group"]) == str(item["group"])), 0.0),
                "expanded_risk": next((float(right["risk"]) for right in expanded_ai_risk if str(right["group"]) == str(item["group"])), 0.0),
                "diff": next((float(right["risk"]) for right in expanded_ai_risk if str(right["group"]) == str(item["group"])), 0.0)
                - next((float(left["risk"]) for left in legacy_ai_risk if str(left["group"]) == str(item["group"])), 0.0),
            }
            for item in exposure_diffs(legacy_ai, expanded_ai)
        ],
        "legacy_top": [{"symbol": symbol, "weight": weight} for symbol, weight in legacy_top[:10]],
        "expanded_top": [{"symbol": symbol, "weight": weight} for symbol, weight in expanded_top[:10]],
    }

    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(args.markdown_output, payload)
    args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "factor_profile_compare_ok "
        f"markdown='{args.markdown_output}' "
        f"json='{args.json_output}' "
        f"legacy_ai_weight={payload['legacy']['ai_weight']:.8f} "
        f"expanded_ai_weight={payload['expanded']['ai_weight']:.8f}"
    )


if __name__ == "__main__":
    main()
