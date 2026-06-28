from __future__ import annotations

import argparse
import re
from pathlib import Path

from validate_research_brief_sync import DEFAULT_DASHBOARD, extract_research_brief


EXPECTED_METRICS = {
    "ai_weight_percent": "33.00%",
    "risk_contribution_percent": "52.82%",
    "risk_weight_gap_percent": "+19.82%",
    "trade_count": "1",
}


def validate_metrics(dashboard_path: Path) -> dict[str, str]:
    brief = extract_research_brief(dashboard_path)
    ai_line = next((line for line in brief.splitlines() if "AI 供应链权重" in line), "")
    trade_line = next((line for line in brief.splitlines() if "调仓状态" in line), "")

    patterns = {
        "ai_weight_percent": r"AI 供应链权重 ([0-9.]+%)",
        "risk_contribution_percent": r"AI 供应链权重 [0-9.]+%，风险贡献 ([0-9.]+%)",
        "risk_weight_gap_percent": r"风险-权重差 ([+-][0-9.]+%)",
        "trade_count": r"(?:已有|本轮有) (\d+) 笔(?:本日模拟调仓转为观察|待确认调仓)",
    }

    actual: dict[str, str] = {}
    missing = []
    mismatched = []
    for key, pattern in patterns.items():
        target_text = brief
        if key in {"ai_weight_percent", "risk_contribution_percent", "risk_weight_gap_percent"}:
            target_text = ai_line
        elif key == "trade_count":
            target_text = trade_line
        match = re.search(pattern, target_text)
        if not match:
            missing.append(key)
            continue
        actual[key] = match.group(1)
        expected = EXPECTED_METRICS[key]
        if actual[key] != expected:
            mismatched.append(f"{key}:{actual[key]}!={expected}")

    if missing:
        raise AssertionError("Dashboard 研究摘要缺少关键数字: " + " | ".join(missing))
    if mismatched:
        raise AssertionError("Dashboard 研究摘要关键数字回归: " + " | ".join(mismatched))

    return actual


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 Dashboard 研究摘要中的关键数字保持预期。")
    parser.add_argument("--dashboard", type=Path, default=DEFAULT_DASHBOARD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    actual = validate_metrics(args.dashboard)
    print(
        "research_brief_metrics_ok "
        f"dashboard={args.dashboard} "
        f"ai_weight={actual['ai_weight_percent']} "
        f"risk_contribution={actual['risk_contribution_percent']} "
        f"risk_weight_gap={actual['risk_weight_gap_percent']} "
        f"trade_count={actual['trade_count']}"
    )


if __name__ == "__main__":
    main()
