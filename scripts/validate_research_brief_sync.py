from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DASHBOARD = ROOT / "dashboard" / "index.html"
DEFAULT_OBSIDIAN_NOTE = Path(
    "/Users/tonyfu/Library/Mobile Documents/iCloud~md~obsidian/Documents/"
    "AI-Knowledge-Wiki/02-The-Wiki/05-商业金融与量化交易/01-量化交易/"
    "03-策略实践/台股量化基金.md"
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_research_brief(dashboard_path: Path) -> str:
    html_text = dashboard_path.read_text(encoding="utf-8")
    match = re.search(
        r'<textarea class="research-report"[^>]*>(.*?)</textarea>',
        html_text,
        flags=re.S,
    )
    if not match:
        raise AssertionError("Dashboard 未找到 research-report 摘要 textarea")
    return normalize_text(html.unescape(match.group(1)))


def validate_sync(dashboard_path: Path, obsidian_note: Path) -> tuple[int, int]:
    brief = extract_research_brief(dashboard_path)
    note_text = normalize_text(obsidian_note.read_text(encoding="utf-8"))
    brief_lines = [line.strip() for line in brief.splitlines() if line.strip()]

    missing_lines = [line for line in brief_lines if line not in note_text]
    if missing_lines:
        raise AssertionError("Obsidian 卡片缺少 Dashboard 摘要行: " + " | ".join(missing_lines))

    required_fragments = [
        "## 七、最新研究摘要",
        "AI 供应链权重 34.38%",
        "风险贡献 49.90%",
        "风险-权重差 +15.52%",
        "舊格式 2 筆",
        "不代表未来报酬预测",
        "实盘订单或券商账户状态",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in note_text]
    if missing_fragments:
        raise AssertionError("Obsidian 卡片缺少关键片段: " + " | ".join(missing_fragments))

    return len(brief_lines), len(required_fragments)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 Dashboard 研究摘要已同步到 Obsidian 项目卡片。")
    parser.add_argument("--dashboard", type=Path, default=DEFAULT_DASHBOARD)
    parser.add_argument("--obsidian-note", type=Path, default=DEFAULT_OBSIDIAN_NOTE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    line_count, fragment_count = validate_sync(args.dashboard, args.obsidian_note)
    print(
        "research_brief_sync_ok "
        f"dashboard={args.dashboard} "
        f"obsidian_note={args.obsidian_note} "
        f"brief_lines={line_count} "
        f"required_fragments={fragment_count}"
    )


if __name__ == "__main__":
    main()
