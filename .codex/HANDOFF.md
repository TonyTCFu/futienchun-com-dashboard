# 会话交接 - 台股 Dashboard

更新时间：2026-06-22 16:15 Asia/Shanghai

## 先读顺序

新对话框请先读：

1. `AGENTS.md`
2. `.codex/HANDOFF.md`
3. `progress.md`
4. `findings.md`
5. `.codex/PROJECT_CONTEXT.md`
6. `README.md`

## 当前边界

- 只读公开行情与本地模拟盘。
- 不读取 `.env`、`.shioaji.local.env`、API key、token、密码或券商凭证。
- 不调用 Shioaji / 券商下单、改单、撤单 API。
- `--execute-simulated-trades` 只写本地模拟盘 CSV，用于 paper portfolio。

## 当前 Dashboard 状态

- 公网地址：https://futienchun-com-dashboard.onrender.com/
- 当前公网已验证版本：commit `f7a2f3b`
- 今日 Dashboard 更新日期：`2026-06-22`
- 行情/回测最新日期：`2026-06-22`
- 模型盘市值日：`2026-06-22`
- 行情口径：`收盘定稿`
- 当前快照时间：`2026-06-22T15:31:54`
- 加权指数：`47,741.51`，`+1,276.31`，`+2.75%`
- 最后回测调仓日：`2026-06-17`
- 预计下次回测调仓：`2026-06-29`
- 待确认调仓：`0`
- 公网 `signal-pill sell`：`0`

## 模拟盘状态

- `data/simulated_trades_2026-06-22.csv` 仍为 3 笔已执行卖出，重跑保持幂等。
- 成交：
  - `2317` 卖出 `5` 股
  - `2881` 卖出 `38` 股
  - `2882` 卖出 `39` 股
- 当前关键持仓：
  - `2317` 剩 `15` 股
  - `2881` 剩 `151` 股
  - `2882` 剩 `156` 股
- 当前持仓市值：`NT$351,391`
- 未实现盈亏：`NT$13,768`
- 盈亏率：`+4.08%`

## 自动化与更新时段

- Codex 自动化 ID：`dashboard`
- 当前排程：每天 `13:45`
- RRULE：`FREQ=DAILY;BYHOUR=13;BYMINUTE=45;BYSECOND=0`
- Render 服务默认重建时间也已同步为 `13:45`：
  - `scripts/serve_dashboard.py`
  - `render.yaml`
  - `README.md`
- 若 13:45 TWSE public-close 尚未稳定，自动化应如实回报“数据未前进”或失败原因，不误报完成。

## 最近完成的 UI 调整

- 右侧栏：
  - 上框保留「模型盘建仓」，缩小「已取得执行价」。
  - `虚拟资金 / 建仓比例 / 策略现金池` 移入上框。
  - 下框改成「目前更新情况」，拆成：
    - `更新状态`：收盘时显示「已按每日 13:45 更新」
    - `行情口径`：收盘定稿 / 盘中暂估
    - `自动排程`：每日 13:45
    - `快照时间`
  - 盘中模式生成时应显示「台湾股市进行中 / 盘中暂估」。
- 今日市场摘要区：
  - 标题改为「已执行」与「短期行动计划」。
  - 两块区域仍左右并排。
  - 每块内部卡片改为上下垂直排列。
  - 生成逻辑在 `src/risk_dashboard.py`，当前静态页为 `dashboard/index.html`。

## 最新提交

- `f7a2f3b fix: stack summary cards within columns`
  - 修正摘要区：两块区域左右并排，每块内部内容卡片上下排列。
- `d08cf9d fix: stack dashboard update summary`
  - 上一版把整个摘要区改成上下排列，后来被用户纠正。
- `69aebba fix: clarify dashboard update status`
  - 将「行情状态」拆成「更新状态 / 行情口径 / 自动排程」。
- `6ad3330 chore: refresh dashboard close data`
  - 即时补跑 2026-06-22 收盘日更。
- `9f3f0cc feat: refine dashboard status sidebar`
  - 调整右侧模型盘状态栏。

## 验证记录

最近一次已通过：

```bash
./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py
./.venv/bin/python scripts/run_local_qa_checks.py
```

`run_local_qa_checks.py` 输出关键值：

- `ai_weight=34.38%`
- `risk_contribution=49.90%`
- `risk_weight_gap=+15.52%`
- `trade_count=3`

公网验证已通过：

- 可检索 `update-summary-list`
- 可检索「已执行」
- 可检索「短期行动计划」
- 可检索「已按每日 13:45 更新」
- `signal-pill sell` 为 `0`

## 工作区状态

当前 Git 追踪文件已提交并推送到 `dashboard` 与 `origin`。

仍有 4 个旧的未跟踪文件，之前已明确未纳入提交：

- `data/model_portfolio_market_2026-06-02.csv`
- `data/model_portfolio_market_2026-06-02_summary.txt`
- `data/simulated_positions_2026-06-02.csv`
- `data/simulated_trades_2026-06-02.csv`

除非用户明确要求处理旧 6/02 数据，否则下一轮忽略这些未跟踪文件。

## 下一轮建议

- 若用户继续调 Dashboard UI，优先改 `src/risk_dashboard.py`，再同步当前 `dashboard/index.html`，避免只改生成物。
- UI 小改后至少跑：
  - `py_compile`
  - `scripts/run_local_qa_checks.py`
  - 公网正文检索
- 若执行完整日更，使用自动化同口径：

```bash
./.venv/bin/python src/risk_dashboard.py \
  --start 2024-01 \
  --end 2026-06 \
  --offline-cache \
  --data-source twse \
  --model-portfolio \
  --model-build-date 2026-06-03 \
  --model-invest-ratio 0.75 \
  --model-method multi-factor-shrink \
  --ai-tilt moderate \
  --market-source public-close \
  --market-mode close \
  --execute-simulated-trades
```

完成后必须验证本地 Dashboard、QA、两远端推送和公网正文。
