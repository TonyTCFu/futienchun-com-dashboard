from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = Path("/tmp")
TRADE_DATE = "2026-06-08"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)


def write_legacy_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    rows = [
        {
            "trade_date": TRADE_DATE,
            "symbol": "2317",
            "name": "鴻海",
            "action": "sell",
            "shares": "13",
            "trade_price": "155.5000",
            "gross_amount": "2021.50",
            "fee": "3.00",
            "tax": "6.00",
            "net_amount": "2012.50",
            "realized_cost": "2550.00",
            "realized_pnl": "-537.50",
            "remaining_shares": "37",
            "reason": "legacy fixture",
            "status": " executed ",
        },
        {
            "trade_date": TRADE_DATE,
            "symbol": "1301",
            "name": "台塑",
            "action": "sell",
            "shares": "71",
            "trade_price": "37.6000",
            "gross_amount": "2669.60",
            "fee": "4.00",
            "tax": "8.00",
            "net_amount": "2657.60",
            "realized_cost": "3920.00",
            "realized_pnl": "-1262.40",
            "remaining_shares": "210",
            "reason": "legacy fixture",
            "status": "executed",
        },
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_helper(fixture_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from risk_dashboard import load_simulated_trade_batch_status

    statuses = load_simulated_trade_batch_status(TRADE_DATE, fixture_path)
    assert len(statuses) == 1, statuses
    status = statuses[0]
    assert status.is_legacy is True, status
    assert status.batch_seq == "legacy", status
    assert status.label == "舊格式", status
    assert status.trade_count == 2, status
    assert status.symbols == ("1301", "2317"), status
    assert status.actions == ("sell",), status


def validate_dashboard(fixture_path: Path, output_path: Path, model_output_path: Path) -> None:
    command = [
        str(PYTHON),
        str(ROOT / "src" / "risk_dashboard.py"),
        "--start",
        "2024-01",
        "--end",
        "2026-06",
        "--offline-cache",
        "--data-source",
        "twse",
        "--model-portfolio",
        "--model-build-date",
        "2026-06-03",
        "--model-invest-ratio",
        "0.75",
        "--model-market-values",
        str(ROOT / "data" / "model_portfolio_market_2026-06-08.csv"),
        "--model-method",
        "multi-factor-shrink",
        "--ai-tilt",
        "moderate",
        "--simulated-trades-output",
        str(fixture_path),
        "--model-output",
        str(model_output_path),
        "--output",
        str(output_path),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    html = output_path.read_text(encoding="utf-8")
    required = [
        "模擬盤批次狀態小結",
        "暫無新格式批次",
        "舊格式紀錄：舊格式 2 筆",
        "<td>舊格式</td><td>2</td><td>1301、2317</td><td>sell</td>",
        "舊成交 CSV 無 trade_id，按交易日、標的、方向相容防重",
    ]
    for text in required:
        assert text in html, text
    assert "<td>批次 01</td><td>2</td>" not in html


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证旧格式模拟成交 CSV 的批次状态展示。")
    parser.add_argument("--dashboard", action="store_true", help="同时重建临时 Dashboard 并检查旧格式展示。")
    parser.add_argument("--fixture", type=Path, default=TMP_DIR / "tw_quant_legacy_trade_fixture.csv")
    parser.add_argument("--output", type=Path, default=TMP_DIR / "tw_quant_legacy_trade_fixture_dashboard.html")
    parser.add_argument("--model-output", type=Path, default=TMP_DIR / "tw_quant_legacy_trade_fixture_model.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_legacy_fixture(args.fixture)
    validate_helper(args.fixture)
    if args.dashboard:
        validate_dashboard(args.fixture, args.output, args.model_output)
    print(f"legacy_fixture_ok fixture={args.fixture}")
    if args.dashboard:
        print(f"legacy_dashboard_ok output={args.output}")


if __name__ == "__main__":
    main()
