from __future__ import annotations

import argparse
import html
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "dashboard" / "index.html"
START_MARKER = "<!-- AUTOMATION_STATUS_START -->"
END_MARKER = "<!-- AUTOMATION_STATUS_END -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a visible daily automation status in the public Dashboard.")
    parser.add_argument("--status", choices=("waiting", "failure"), required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--step", default="")
    parser.add_argument("--run-url", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    document = INDEX_PATH.read_text(encoding="utf-8")
    start = document.find(START_MARKER)
    if start >= 0:
        end = document.find(END_MARKER, start)
        if end < 0:
            raise SystemExit("Dashboard automation status marker is incomplete.")
        document = document[:start] + document[end + len(END_MARKER) :]

    title = "自动化状态：等待公开收盘资料" if args.status == "waiting" else "自动化状态：日更失败，已自动补偿"
    tone = "waiting" if args.status == "waiting" else "failure"
    details_html = [html.escape(f"日期 {args.date}"), html.escape(args.message)]
    if args.step:
        details_html.append(html.escape(f"步骤 {args.step}"))
    if args.run_url:
        details_html.append(f'<a href="{html.escape(args.run_url, quote=True)}">查看自动化运行记录</a>')
    status_html = (
        f'        {START_MARKER}\n'
        f'        <div class="automation-status {tone}" role="status">'
        f'<b>{html.escape(title)}</b><span>{"；".join(details_html)}</span></div>\n'
        f'        {END_MARKER}\n'
    )
    anchor = '        <p class="footer-note">只读行情与本地 paper portfolio；不代表实盘委托或投资建议。</p>'
    if anchor not in document:
        raise SystemExit("Dashboard Daily Update Summary footer anchor not found.")
    INDEX_PATH.write_text(document.replace(anchor, status_html + anchor, 1), encoding="utf-8")
    print(f"published_dashboard_automation_status={args.status} at {datetime.now().astimezone().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
