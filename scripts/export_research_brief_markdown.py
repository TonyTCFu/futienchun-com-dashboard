from __future__ import annotations

import argparse
from pathlib import Path

from validate_research_brief_sync import DEFAULT_DASHBOARD, extract_research_brief


DEFAULT_OUTPUT = Path("/tmp/tw_quant_research_brief.md")


def build_markdown(brief: str, dashboard_path: Path) -> str:
    lines = [
        "# 台股量化 Dashboard 研究摘要",
        "",
        f"- 来源 Dashboard：`{dashboard_path}`",
        "- 用途：本地模拟盘研究记录与人工复核。",
        "- 边界：不代表未来报酬预测、个股买卖建议、实盘订单或券商账户状态。",
        "",
        "> [!note] Dashboard 研究摘要",
    ]
    lines.extend(f"> {line}" if line else ">" for line in brief.splitlines())
    lines.extend(
        [
            "",
            "---",
            "",
            "本文件由正式 Dashboard 的只读研究摘要导出，默认写入 `/tmp` 作为预览；不重建 Dashboard，不写入模拟成交 CSV，也不连接券商。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把 Dashboard 研究摘要导出为临时 Markdown 预览。")
    parser.add_argument("--dashboard", type=Path, default=DEFAULT_DASHBOARD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    brief = extract_research_brief(args.dashboard)
    markdown = build_markdown(brief, args.dashboard)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    line_count = len([line for line in brief.splitlines() if line.strip()])
    print(f"research_brief_markdown_ok output={args.output} brief_lines={line_count}")


if __name__ == "__main__":
    main()
