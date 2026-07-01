from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
TMP_MARKDOWN_OUTPUT = Path("/tmp/tw_quant_local_qa_research_brief.md")
TMP_SUMMARY_OUTPUT = Path("/tmp/tw_quant_local_qa_summary.md")
TMP_SUMMARY_JSON_OUTPUT = Path("/tmp/tw_quant_local_qa_summary.json")


def latest_market_file() -> Path:
    market_files = list((ROOT / "data").glob("model_portfolio_market_*.csv"))
    if not market_files:
        raise FileNotFoundError("找不到任何 model_portfolio_market_*.csv")
    return max(market_files, key=lambda path: path.stat().st_mtime)


MONITORED_FILES = [
    ROOT / "dashboard" / "index.html",
    ROOT / "data" / "model_portfolio_latest.csv",
    ROOT / "data" / "model_portfolio_2026-06-03.csv",
    ROOT / "data" / "simulated_trades_2026-06-08.csv",
    ROOT / "data" / "simulated_positions_latest.csv",
    latest_market_file(),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_hashes() -> dict[Path, str]:
    return {path: sha256(path) for path in MONITORED_FILES}


def run_command(args: list[str]) -> str:
    completed = subprocess.run(
        [str(part) for part in args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def validate_markdown_output(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required_fragments = [
        "# 台股量化 Dashboard 研究摘要",
        "AI 供应链权重 33.00%",
        "风险贡献 52.76%",
        "风险-权重差 +19.76%",
        "不代表未来报酬预测",
        "实盘订单或券商账户状态",
        "默认写入 `/tmp` 作为预览",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in text]
    if missing:
        raise AssertionError("Markdown 导出缺少关键片段: " + " | ".join(missing))


def ensure_hashes_unchanged(before: dict[Path, str], after: dict[Path, str]) -> None:
    changed = []
    for path, before_hash in before.items():
        after_hash = after[path]
        if before_hash != after_hash:
            changed.append(f"{path}:{before_hash}->{after_hash}")
    if changed:
        raise AssertionError("正式产物 hash 发生变化: " + " | ".join(changed))


def write_summary(
    path: Path,
    *,
    markdown_output_path: Path,
    before_hashes: dict[Path, str],
    sync_output: str,
    metrics_output: str,
    markdown_output: str,
    legacy_output: str,
    skip_dashboard_fixture: bool,
) -> None:
    mode = "fast" if skip_dashboard_fixture else "full"
    dashboard_fixture = "off" if skip_dashboard_fixture else "on"
    lines = [
        "# 台股量化本地 QA 汇总",
        "",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 检查模式：{mode}",
        f"- dashboard_fixture：{dashboard_fixture}",
        f"- Markdown 预览：`{markdown_output_path}`",
        "",
        "## 结果",
        "",
        f"- 研究摘要同步检查：`{sync_output}`",
        f"- 研究摘要关键数字回归：`{metrics_output}`",
        f"- Markdown 导出：`{markdown_output}`",
        f"- 旧格式 fixture 验证：`{legacy_output}`",
        f"- 正式产物监控：`{len(before_hashes)}` 个文件，hash 前后一致",
        "",
        "## 正式产物 SHA-256",
        "",
    ]
    for monitored_path, digest in before_hashes.items():
        lines.append(f"- `{monitored_path.relative_to(ROOT)}`: `{digest}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary_json(
    path: Path,
    *,
    markdown_output_path: Path,
    summary_output_path: Path,
    before_hashes: dict[Path, str],
    sync_output: str,
    metrics_output: str,
    markdown_output: str,
    legacy_output: str,
    skip_dashboard_fixture: bool,
) -> None:
    mode = "fast" if skip_dashboard_fixture else "full"
    dashboard_fixture = "off" if skip_dashboard_fixture else "on"
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": mode,
        "dashboard_fixture": dashboard_fixture,
        "markdown_output": str(markdown_output_path),
        "summary_output": str(summary_output_path),
        "results": {
            "sync": sync_output,
            "metrics": metrics_output,
            "markdown": markdown_output,
            "legacy": legacy_output,
            "monitored_files": len(before_hashes),
            "hashes_unchanged": True,
        },
        "monitored_hashes": {
            str(monitored_path.relative_to(ROOT)): digest for monitored_path, digest in before_hashes.items()
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总执行本地 QA 检查脚本，并确认正式产物未被改动。")
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=TMP_MARKDOWN_OUTPUT,
        help="Markdown 预览输出路径，默认写 /tmp。",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=TMP_SUMMARY_OUTPUT,
        help="QA 摘要输出路径，默认写 /tmp。",
    )
    parser.add_argument(
        "--summary-json-output",
        type=Path,
        default=TMP_SUMMARY_JSON_OUTPUT,
        help="QA JSON 摘要输出路径，默认写 /tmp。",
    )
    parser.add_argument(
        "--skip-dashboard-fixture",
        action="store_true",
        help="跳过旧格式 fixture 的临时 Dashboard 页面验证，加快本地检查。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    before_hashes = snapshot_hashes()

    sync_output = run_command([PYTHON, ROOT / "scripts" / "validate_research_brief_sync.py"])
    metrics_output = run_command([PYTHON, ROOT / "scripts" / "validate_research_brief_metrics.py"])
    markdown_output = run_command(
        [
            PYTHON,
            ROOT / "scripts" / "export_research_brief_markdown.py",
            "--output",
            args.markdown_output,
        ]
    )
    validate_markdown_output(args.markdown_output)

    legacy_command = [PYTHON, ROOT / "scripts" / "validate_legacy_trade_batch_status.py"]
    if not args.skip_dashboard_fixture:
        legacy_command.append("--dashboard")
    legacy_output = run_command(legacy_command)

    after_hashes = snapshot_hashes()
    ensure_hashes_unchanged(before_hashes, after_hashes)
    write_summary(
        args.summary_output,
        markdown_output_path=args.markdown_output,
        before_hashes=before_hashes,
        sync_output=sync_output,
        metrics_output=metrics_output,
        markdown_output=markdown_output,
        legacy_output=legacy_output,
        skip_dashboard_fixture=args.skip_dashboard_fixture,
    )
    write_summary_json(
        args.summary_json_output,
        markdown_output_path=args.markdown_output,
        summary_output_path=args.summary_output,
        before_hashes=before_hashes,
        sync_output=sync_output,
        metrics_output=metrics_output,
        markdown_output=markdown_output,
        legacy_output=legacy_output,
        skip_dashboard_fixture=args.skip_dashboard_fixture,
    )

    print(
        "local_qa_checks_ok "
        f"sync='{sync_output}' "
        f"metrics='{metrics_output}' "
        f"markdown='{markdown_output}' "
        f"legacy='{legacy_output}' "
        f"monitored_files={len(MONITORED_FILES)} "
        f"dashboard_fixture={'off' if args.skip_dashboard_fixture else 'on'} "
        f"summary='{args.summary_output}' "
        f"summary_json='{args.summary_json_output}'"
    )


if __name__ == "__main__":
    main()
