# Loop Engineering Progress

## 2026-06-23 二次补跑推进收盘行情

### Session Goal

回应用户要求“立刻补跑一次 Dashboard 更新，把公网行情日期推进到 2026-06-23”，只更新 `https://futienchun-com-dashboard.onrender.com/` 对应的 Dashboard 远端，不触碰其他智能体维护的远端。

### Actions

- 已确认 TWSE `STOCK_DAY` 公开接口现在 15 檔资产均可读到 `115/06/23`，因此补跑正式 `public-close + market-mode close + --execute-simulated-trades`。
- 已生成 `data/model_portfolio_market_2026-06-23.csv` 与 `data/model_portfolio_market_2026-06-23_summary.txt`；`quote_count=15`、`missing_count=0`。
- Dashboard 已推进为 `今日 Dashboard 更新日期：2026-06-23`、`行情/回测序列最新日期：2026-06-23`，并保留 `<title>台灣股市Codex</title>`。
- 本轮只准备推送 `dashboard` 远端；`origin` 远端保持外部智能体版本，不再触碰。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/validate_research_brief_metrics.py` 通过。
- 正式补跑完成：`/usr/bin/time -p` 实测 `real 64.93`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-23`、`行情/回测序列最新日期：2026-06-23`、`已用公开收盘价重建每日行情：data/model_portfolio_market_2026-06-23.csv`。
- iCloud Obsidian `台股量化基金.md` 已同步 Dashboard 当前研究摘要中的策略结构变化数字。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_2026-06-03.csv`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_market_2026-06-23.csv`
- `data/model_portfolio_market_2026-06-23_summary.txt`
- `data/simulated_positions_2026-06-23.csv`
- `data/simulated_positions_latest.csv`
- `data/simulated_trades_2026-06-23.csv`
- `progress.md`
- `findings.md`
- `.codex/HANDOFF.md`
- iCloud Obsidian `台股量化基金.md`

## 2026-06-23

### Session Goal

回应用户要求“更新一下公网今天 Dashboard 的内容”，按正式 public-close 日更口径重建本地 Dashboard、同步研究摘要 QA，并准备推送公网。

### Actions

- 已按项目边界读取 `AGENTS.md`、`.codex/HANDOFF.md`、`progress.md`、`findings.md`、`.codex/PROJECT_CONTEXT.md`、README 相关命令与台股/Shioaji skill；本轮未读取 `.env`、`.shioaji.local.env`、API key、token，未调用券商下单。
- 已执行正式重建：`--market-source public-close --market-mode close --execute-simulated-trades`、`multi-factor-shrink`、`ai_tilt moderate`；重建耗时 `real 72.19`。
- Dashboard 已刷新为 `今日 Dashboard 更新日期：2026-06-23`，但 TWSE 公开收盘资料本轮未前进，行情/回测序列最新日期与模型盘市值日仍为 `2026-06-22`；未生成 `data/model_portfolio_market_2026-06-23.csv`。
- 今日市场摘要区显示 TWSE 加权指数公开资料暂不可用；本轮仍保留模型盘与行情序列状态，避免把未取得的指数资料包装成已确认事实。
- 本地模拟盘保持幂等：最后模拟盘执行日仍为 `2026-06-22`，已落账模拟成交仍为 `3` 笔，未新增 `2026-06-23` 模拟成交。
- 已同步 iCloud Obsidian `台股量化基金.md` 的 Dashboard 研究摘要，使本地 QA 恢复通过。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/validate_research_brief_metrics.py` 通过。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 72.19`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-23`、`行情/回测序列最新日期：2026-06-22`、`模型盘市值日：2026-06-22`、`待确认调仓：0`、`signal-pill sell=0`、`建议卖出=0`、`<title>台灣股市Codex</title>`。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过；关键数字为 `AI 供应链权重 34.38%`、`风险贡献 49.90%`、`风险-权重差 +15.52%`、`trade_count=3`。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`
- `.codex/HANDOFF.md`
- iCloud Obsidian `台股量化基金.md`

### Next Loop Recommendation

- 若稍后 TWSE 2026-06-23 官方收盘资料稳定，应再跑一次同口径重建，确认行情/回测序列是否推进到 `2026-06-23`；若仍未前进，应继续明确回报“页面已刷新、正式行情未前进”。

## 2026-06-22 策略监控列宽比例

### Session Goal

回应用户截图反馈：“策略监控与建议单”的表格间隔比例还需要调整。

### Actions

- 已最小修改 `src/risk_dashboard.py`：为 `signal-table` 加入 `colgroup` 和固定列宽比例，避免浏览器自动分配导致 `触发原因` 被推得过远。
- 当前列宽比例为：动作 `9%`、代码 `7%`、名称 `18%`、监控价 `9%`、成本价 `9%`、连续天数 `7%`、建仓后报酬 `10%`、建议股数 `8%`、触发原因 `23%`。
- 已把短数字列置中，保留名称和触发原因靠左；未改变策略规则、建议单、模拟盘落账逻辑。
- 已用正式 public-close 日更同口径重建 `dashboard/index.html`；本轮带 `--execute-simulated-trades`，模拟盘保持幂等，新增模拟成交 `0` 笔。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py` 通过。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过；关键数字仍为 `AI 供应链权重 34.38%`、`风险贡献 49.90%`、`风险-权重差 +15.52%`、`trade_count=3`。
- 本地浏览器验证 `#trade-signals`：实际列宽比例为 `9 / 7 / 18 / 9 / 9 / 7 / 10 / 8 / 23`，`tableFits=true`、`sectionClearOfSide=true`、页面无水平溢出。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `progress.md`

## 2026-06-22 策略监控原因短标签

### Session Goal

回应用户要求：“策略监控与建议单”的 `触发原因` 内容要简短，约 10 个字以内。

### Actions

- 已最小修改 `src/risk_dashboard.py`：新增 `short_trade_reason()`，把长原因映射为短标签，例如 `继续观察`、`已落账`、`亏损止损`、`趋势转弱`、`获利了结`、`回落加码`。
- Dashboard 表格正文只显示短标签；完整长原因保留在 `title` 属性中，方便需要时 hover 查看，不影响策略规则、建议单、模拟盘落账或 QA 数字。
- 已用正式 public-close 日更同口径重建 `dashboard/index.html`；本轮带 `--execute-simulated-trades`，模拟盘保持幂等，新增模拟成交 `0` 笔。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py` 通过。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过；关键数字仍为 `AI 供应链权重 34.38%`、`风险贡献 49.90%`、`风险-权重差 +15.52%`、`trade_count=3`。
- 页面解析确认 `触发原因` 可见文本只剩 `继续观察` 与 `已落账`，最长 `4` 个字；完整长原因不再出现在表格可见正文，但仍存在于 `title`。
- 本地浏览器验证 `#trade-signals`：`maxReasonLength=4`、`tableFits=true`、`sectionClearOfSide=true`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `progress.md`

## 2026-06-22 策略监控表格修正

### Session Goal

回应用户截图反馈：“策略监控与建议单”的表格右半部分在当前桌面视口被挤到可视区域外；同步缩小左右栏比例，并拿掉表内不必要的技术因素列。

### Actions

- 已最小修改 `src/risk_dashboard.py`：策略监控表从 15 列瘦身为 9 列，保留 `动作 / 代码 / 名称 / 监控价 / 成本价 / 连续天数 / 建仓后报酬 / 建议股数 / 触发原因`。
- 已从策略监控表头移除 `MA20 / MA60 / RSI14 / 量比 / 20 日均额 / 因子分`；这些因素仍保留在规则内部计算，只是不再占用首屏表格宽度。
- 已把整体三栏布局从 `78px / main / 330px` 调整为 `72px / main / 280px`，并缩小外层 gap 与 padding，让主内容表格取得更多横向空间。
- 已用正式 public-close 日更同口径重建 `dashboard/index.html`；本轮带 `--execute-simulated-trades`，但模拟盘保持幂等，新增模拟成交 `0` 笔。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py` 通过。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过；关键数字仍为 `AI 供应链权重 34.38%`、`风险贡献 49.90%`、`风险-权重差 +15.52%`、`trade_count=3`。
- 正式重建命令耗时 `real 36.72`，并保留 `public-close` 日更日志；`SIMULATED_TRADES` 显示新增模拟成交 `0` 笔。
- 本地浏览器验证 `http://127.0.0.1:8765/dashboard/index.html#trade-signals`：策略监控表头只剩 9 列，旧技术列无命中；表格 `right=1395`、主区块 `right=1412`，右侧栏 `x=1424`，确认表格没有被右侧栏裁切。
- 页面检索确认仍显示 `今日 Dashboard 更新日期：2026-06-22`、`行情/回测序列最新日期：2026-06-22`、`已按每日 13:45 更新`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `progress.md`

### Next Loop Recommendation

- 若继续调整桌面表格，可优先做列宽与金额格式微调；若要系统性处理手机端宽表，建议另开一轮把所有宽表统一包进可横向滚动容器。

## 2026-06-22

### Session Goal

回应用户要求“现在就更新 Dashboard”，在 13:45 收盘自动化排程之外即时补跑一次完整 public-close 日更，并推送公网。

### Actions

- 已按项目边界读取自动化 memory、`AGENTS.md`、`progress.md`、`findings.md`、`.codex/PROJECT_CONTEXT.md`、`README.md` 和台股/Shioaji skill；未读取 `.env`、`.shioaji.local.env`、API key 或 token，未调用券商下单。
- 已执行完整收盘重建：`--market-source public-close --market-mode close --execute-simulated-trades`、`multi-factor-shrink`、`ai_tilt moderate`；重建耗时 `real 33.69`。
- Dashboard 已确认仍为 `2026-06-22` 收盘定稿：今日更新日期 `2026-06-22`，行情/回测序列最新日期 `2026-06-22`，模型盘市值日 `2026-06-22`。
- 本轮 `--execute-simulated-trades` 保持幂等：模拟成交 CSV 仍为 3 笔已执行卖出，未新增重复成交；`2317` 剩 `15` 股、`2881` 剩 `151` 股、`2882` 剩 `156` 股。
- 研究摘要随正式重建微调：AI 供应链权重 `34.38%`、风险贡献 `49.90%`、风险-权重差 `+15.52%`；已同步 QA 基线与 iCloud Obsidian `台股量化基金.md`。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/validate_research_brief_metrics.py` 通过。
- 页面检索通过：`今日市场与更新摘要`、`加权指数 2026-06-22 收 47,741.51`、`今日行情：收盘定稿`、`目前更新情况`、`本日模拟成交 3 笔`。
- 模拟盘 CSV 检查通过：`data/simulated_trades_2026-06-22.csv` 共 3 笔，分别为 `2317` 卖出 `5` 股、`2881` 卖出 `38` 股、`2882` 卖出 `39` 股；状态均为 `executed`。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `scripts/validate_research_brief_sync.py`
- `scripts/validate_research_brief_metrics.py`
- `scripts/run_local_qa_checks.py`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`
- iCloud Obsidian `台股量化基金.md`

### Next Loop Recommendation

- 每日固定排程已改为 `13:45`；若用户当天临时要求“现在更新”，可直接补跑完整 public-close 日更，但需同步 QA 基线与 Obsidian 摘要中随重建漂移的研究数字。

## 2026-06-22 早前摘要区更新

### Session Goal

回答“台湾股市今天情况如何”，并把 Dashboard 加上当前更新摘要：今天市场、已做事项、目前状态与短期下一步。

### Actions

- 已读取 `AGENTS.md`、`progress.md`、`findings.md`、`.codex/PROJECT_CONTEXT.md`、`README.md` 和台股/Shioaji skill；本轮仍保持只读公开行情与本地模拟盘边界，未读取 `.env`、`.shioaji.local.env`、API key 或 token，未调用券商下单。
- 已用 TWSE 官方公开资料确认 2026-06-22 台股状态：加权指数收 `47,741.51`，上涨 `1,276.31` 点、`+2.75%`，盘中区间 `46,679.57 - 47,871.19`；台积电收 `2,510`，上涨 `100`。
- 已在 `src/risk_dashboard.py` 新增 `TaiexSnapshot` 与 TWSE 加权指数公开资料读取 helper，并在 Dashboard 顶部新增“今日市场与更新摘要”区块。
- 新摘要区现在显示：今日台股、行情/回测最新日、模型盘市值日、待确认调仓、目前已经做了什么、未来短时间会做的事。
- 已执行正式重建：`--market-source public-close --market-mode close --execute-simulated-trades`；Dashboard 行情/回测序列最新日期已推进到 `2026-06-22`。
- 本地模拟盘本轮新增 `3` 笔卖出：`2317` 卖出 `5` 股、`2881` 卖出 `38` 股、`2882` 卖出 `39` 股；执行后 `2317` 剩 `15` 股、`2881` 剩 `151` 股、`2882` 剩 `156` 股。
- Dashboard 摘要显示执行后的当前持仓市值 `NT$351,391`、未实现盈亏 `NT$13,768`，待确认调仓 `0` 笔；最后模拟盘执行日 `2026-06-22`，已落账模拟成交 `3` 笔。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/validate_research_brief_metrics.py` 通过。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 44.98`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日市场与更新摘要`、`加权指数 2026-06-22 收 47,741.51`、`行情/回测序列最新日期：2026-06-22`、`模型盘市值日：2026-06-22`、`待确认调仓：0`、`预计下次回测调仓：2026-06-26`。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过，输出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`；关键数字仍为 `AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`。
- iCloud Obsidian `台股量化基金.md` 已同步 Dashboard 研究摘要中随 6/22 行情微调的策略结构结论，确保同步检查继续通过。
- 已将提交 `e40ce2f` 推送到 `dashboard` 与 `origin`；Render 公网首页正文已验证 `今日 Dashboard 更新日期：2026-06-22`、`行情/回测序列最新日期：2026-06-22`，并可检索到新区块 `今日市场与更新摘要` 与 `加权指数 2026-06-22 收 47,741.51`；公网 `signal_sell_count=0`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `data/model_portfolio_market_2026-06-22.csv`
- `data/model_portfolio_market_2026-06-22_summary.txt`
- `data/simulated_trades_2026-06-22.csv`
- `data/simulated_positions_2026-06-22.csv`
- `data/simulated_positions_latest.csv`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`
- iCloud Obsidian `台股量化基金.md`

### Next Loop Recommendation

- 下一个短期重点是继续观察是否在 `2026-06-26` 触发下一次回测调仓；若 AI 供应链风险贡献仍显著高于权重，应优先在摘要区保留风险提示，再决定是否调整模拟盘。

## 2026-06-21

### Session Goal

执行每日收盘自动化：使用公开收盘价与本地模拟盘边界重建 Dashboard，验证本地页面状态，修复本轮发现的 `public-close` 刷新问题，并准备推送公网。

### Actions

- 已读取自动化 memory、`AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`、`.codex/PROJECT_CONTEXT.md`、`README.md`，并确认本轮不读取 `.env`、`.shioaji.local.env`、API key、token，也不调用券商下单。
- 已执行正式命令：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close --execute-simulated-trades`。
- 今日为周日，公开收盘价共同交易日未前进；正式 Dashboard 更新日期已切到 `2026-06-21`，行情/回测序列最新日期仍为 `2026-06-18`。
- 本轮发现并最小修复 `src/risk_dashboard.py` 的 `public-close` 主动刷新路径：先把 `months` 绑定为局部变量；刷新范围收窄为最近月份；TWSE 返回无资料时不再覆盖已有月缓存；最近公开收盘日判定改用轻量日期交集，不再套 60 日回测门槛。
- 模拟盘落账保持幂等：本轮新增 `0` 笔，最后模拟盘执行日仍为 `2026-06-18`，累计已落账模拟成交 `3` 笔，其中卖出 `3` 笔；持仓变化延续上一轮结果：`2317` 剩 `20` 股、`2881` 剩 `189` 股、`2882` 剩 `195` 股。
- 本地页面已确认 `signal-pill sell=0`、`建议卖出=0`，没有已落账标的仍显示红色建议卖出。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/validate_research_brief_metrics.py` 通过。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 34.80`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-21`、`行情/回测序列最新日期：2026-06-18`、`最后回测调仓日：2026-06-17`、`预计下次回测调仓：2026-06-26`、`距下次还差交易日：6`、`最后模拟盘执行日：2026-06-18`、`已落账模拟成交：3`。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过，输出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`；关键数字仍为 `AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`。
- 已将提交 `7f6f47e` 推送到 `dashboard` 与 `origin`；Render 公网首页正文第 4 轮轮询切到 `今日 Dashboard 更新日期：2026-06-21`、`行情/回测序列最新日期：2026-06-18`，且 `signal_sell_count=0`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-18.csv`
- `data/model_portfolio_market_2026-06-18_summary.txt`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 后续每日自动化应继续刷新最近月份公开资料；若遇到假日或 TWSE 暂无新资料，保持既有月缓存并明确回报“行情序列未前进”，不要误判为 Dashboard 重建失败。

## 2026-06-20

### Session Goal

继续处理两件事：查清 `public-close` 为什么一直停在 `2026-06-16`，并把 Dashboard 里已经过期的“预计下次回测调仓”提示修成真实口径；若数据能补齐，则顺带完成正式重建、模拟盘落账与 QA 闭环。

### Actions

- 已读取 `dashboard/index.html`、`data/cache/`、自动化 memory 和项目交接文件，确认昨天页面虽然更新到 `2026-06-19`，但“行情/回测序列最新日期”仍卡在 `2026-06-16`，同时“预计下次回测调仓：2026-06-19”已经过期。
- 已定位数据根因：`public-close` 路径在 `--offline-cache` 下会复用本地 TWSE 月缓存与矩阵缓存；而当时 `202606` 月缓存不完整，15 檔资产的共同交易日被卡住，导致页面日期前进但回测序列不前进。
- 已最小修改 `src/risk_dashboard.py`：`public-close` 路径现在会主动刷新 TWSE 当月公开收盘资料，再回到现有缓存/矩阵流程；同时当推算出的“下一次回测调仓日”已经早于今天且正式行情仍未跟上时，页面会降级显示为“待新正式行情后重算”，并附上解释。
- 已用项目 `.venv` 把 15 檔资产的 `202606` 月公开收盘缓存全部补齐到 `2026-06-18`；其中 `00713` 曾因 TWSE 读取超时而回退旧缓存，后续单独重试后也已补到 `2026-06-18`。
- 补齐缓存后已重新执行正式收盘重建，当前正式页面已推进到 `行情/回测序列最新日期：2026-06-18`、`最后回测调仓日：2026-06-17`、`预计下次回测调仓：2026-06-26`、`距下次还差交易日：6`。
- 本轮新增本地模拟盘执行落账 `3` 笔卖出：`2317 卖出 7 股`、`2881 卖出 48 股`、`2882 卖出 49 股`；对应 `data/simulated_trades_2026-06-18.csv` 与 `data/simulated_positions_2026-06-18.csv` 已生成，`data/simulated_positions_latest.csv` 已切到新状态。
- 研究摘要、QA 基线与 iCloud Obsidian 项目卡片已同步到新口径：`AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py` 通过。
- 已直接验证 TWSE 月资料刷新：15 檔 `202606` 缓存全部可读到 `2026-06-18`，共同最新日期为 `2026-06-18`。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 15.53`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-20`、`行情/回测序列最新日期：2026-06-18`、`最后回测调仓日：2026-06-17`、`预计下次回测调仓：2026-06-26`、`最后模拟盘执行日：2026-06-18`、`已落账模拟成交：3`、`signal-pill sell=0`。
- `./.venv/bin/python scripts/validate_research_brief_sync.py` 通过。
- `./.venv/bin/python scripts/validate_research_brief_metrics.py` 通过，当前关键数字为 `AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过，输出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `data/model_portfolio_market_2026-06-18.csv`
- `data/model_portfolio_market_2026-06-18_summary.txt`
- `data/simulated_trades_2026-06-18.csv`
- `data/simulated_positions_2026-06-18.csv`
- `data/simulated_positions_latest.csv`
- `scripts/validate_research_brief_sync.py`
- `scripts/validate_research_brief_metrics.py`
- `scripts/run_local_qa_checks.py`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 后续每日自动化可继续保留 `--offline-cache`，但需要依赖本轮新增的 `public-close` 主动刷新逻辑；若再遇到 TWSE 个别标的超时，应优先重试该月缓存，而不是误判为整轮 Dashboard 未更新。

## 2026-06-19

### Session Goal

按每日收盘自动化流程完成 `public-close` 正式重建、双远端推送与 Render 公网复核，并确认模拟盘状态没有回退。

### Actions

- 已按自动化要求读取 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`、`.codex/PROJECT_CONTEXT.md`、`README.md`，并确认继续保持只读行情与本地模拟盘边界。
- 已执行正式收盘重建命令：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close --execute-simulated-trades`。
- 本轮正式重建成功，`dashboard/index.html` 已刷新为 `今日 Dashboard 更新日期：2026-06-19`；但公开收盘价路径本次仍只复用了 `data/model_portfolio_market_2026-06-16.csv`，所以“行情/回测序列最新日期”继续停在 `2026-06-16`。
- 本轮产物变更仅限 `dashboard/index.html`、`data/model_portfolio_market_2026-06-16.csv` 与 `data/model_portfolio_market_2026-06-16_summary.txt`；核心差异是页面更新日期与 `quote_time` 从 `2026-06-18T18:42:12` 刷新到 `2026-06-19T23:31:34`，当前持仓市值与未实现盈亏继续为 `NT$366,451.18` / `NT$7,198.15`。
- `--execute-simulated-trades` 本轮继续保持幂等：Dashboard 显示最后模拟盘执行日仍为 `2026-06-16`、已落账模拟成交 `2` 笔，其中卖出 `2` 笔；`signal-pill sell` 无命中，说明没有已落账标的残留红色卖出建议。
- 已将提交 `a02dba2` 推送到 `dashboard` 与 `origin` 两个远端；Render 公网首页在前 5 轮轮询中仍返回 `2026-06-18`，第 6 轮正文才切换为 `2026-06-19`，再次验证了 `/healthz=200` 不等于首页内容已经切到最新版本。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py` 通过。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 15.11`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-19`、`行情/回测序列最新日期：2026-06-16`、最后回测调仓日 `2026-05-28`、预计下次回测调仓 `2026-06-19`、最后模拟盘执行日 `2026-06-16`、已落账模拟成交 `2` 笔。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过，输出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`；研究摘要同步、关键数字回归、Markdown 导出与旧格式 fixture 验证均为 `ok`。
- `curl -I -L --max-time 30 https://futienchun-com-dashboard.onrender.com/healthz` 返回 `HTTP/2 200`。
- Render 首页正文轮询通过：前 5 轮仍返回 `今日 Dashboard 更新日期：2026-06-18`，第 6 轮切换为 `2026-06-19`；同时 `signal_sell_count=0`，公网继续没有红色卖出建议残留。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-16.csv`
- `data/model_portfolio_market_2026-06-16_summary.txt`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 后续每日自动化仍应先接受“页面已更新但行情序列未前进”的可能性，并把它明确汇报为公开收盘价数据新鲜度限制；同时保留 Render 首页正文轮询，避免仅凭 `/healthz` 提前判定公网已完成切换。

## 2026-06-18

### Session Goal

按每日收盘自动化流程重建正式 Dashboard、复核模拟盘状态、恢复本地 QA 基线，并准备推送到公网。

### Actions

- 已读取 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`、`.codex/PROJECT_CONTEXT.md`、`README.md`，并确认今日任务继续沿用只读行情与本地模拟盘边界。
- 已执行正式收盘重建命令：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close --execute-simulated-trades`。
- 本轮重建成功刷新 `dashboard/index.html`，并重新写出 `data/model_portfolio_market_2026-06-16.csv` 与 `data/model_portfolio_market_2026-06-16_summary.txt`；正式页面更新日期变为 `2026-06-18`，但当前可并入的行情/回测序列最新日期仍为 `2026-06-16`。
- `SIMULATED_TRADES` 继续保持幂等：本轮新增模拟成交 `0` 笔，`data/simulated_trades_2026-06-16.csv` 仍为既有 2 笔卖出，`data/simulated_positions_latest.csv` 更新时间刷新但持仓仍为 15 檔。
- 已核对 Dashboard 的“调仓与执行日历”：最后回测调仓日 `2026-05-28`，预计下次回测调仓 `2026-06-19`，距下次还差 `3` 个共同交易日；最后模拟盘执行日仍为 `2026-06-16`。
- 已核对策略监控表中 `2317`、`1301` 继续显示为“观察”，理由为“本日模拟调仓已落账”；页面中不再存在红色 `signal-pill sell` 残留。
- 本轮发现本地 QA 基线已随正式 Dashboard 漂移：研究摘要同步检查、关键数字回归检查和 Markdown 导出检查都仍写死旧的 `33.00% / 48.49% / +15.49%`。
- 已最小同步 QA 基线：更新 `scripts/validate_research_brief_sync.py`、`scripts/validate_research_brief_metrics.py`、`scripts/run_local_qa_checks.py` 到今日正式 Dashboard 的 `34.61% / 49.97% / +15.37%`，并把 iCloud Obsidian `台股量化基金.md` 的“最新研究摘要”同步到今日口径。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py` 通过。
- 正式重建完成：`/usr/bin/time -p` 实测 `real 15.03`，成功生成正式 `dashboard/index.html`。
- 页面检索通过：`今日 Dashboard 更新日期：2026-06-18`、`行情/回测序列最新日期：2026-06-16`、`DAILY_MARKET` 记录命中 `data/model_portfolio_market_2026-06-16.csv`、`SIMULATED_TRADES: 已落账模拟成交 0 笔`。
- HTML 只读核对通过：`signal-pill sell` 无命中；`2317`、`1301` 在策略监控表中均为“观察”，并显示“本日模拟调仓已落账，当前不再列为待确认清单。”
- `./.venv/bin/python scripts/validate_research_brief_sync.py` 通过。
- `./.venv/bin/python scripts/validate_research_brief_metrics.py` 通过，当前关键数字为 `AI 供应链权重 34.61%`、`风险贡献 49.97%`、`风险-权重差 +15.37%`、`trade_count=2`。
- `./.venv/bin/python scripts/run_local_qa_checks.py` 通过，输出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`，并确认 6 个正式监控文件 hash 前后一致。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_market_2026-06-16.csv`
- `data/model_portfolio_market_2026-06-16_summary.txt`
- `data/simulated_positions_latest.csv`
- `scripts/validate_research_brief_sync.py`
- `scripts/validate_research_brief_metrics.py`
- `scripts/run_local_qa_checks.py`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 继续每日自动化时，优先观察公开收盘价路径何时能把 `2026-06-18` 正式收盘序列并入回测；若仍停在 `2026-06-16`，需把原因明确记为数据新鲜度限制，而不是部署失败。

## 2026-06-17

### Session Goal

把策略结构变化结论直接同步到 Dashboard 研究说明区，并把每日收盘后的自动重建流程接上模拟盘落账与持仓刷新。

### Actions

- 已在 `src/risk_dashboard.py` 的研究说明区加入“策略结构变化结论”只读摘要，页面打开即可直接看到旧 4 因子与新扩展框架的差异结论。
- 已把模型盘记录补上 `ai_tilt`，确保研究摘要与实际建盘参数一致。
- 已将 `scripts/serve_dashboard.py` 与 `render.yaml` 的自动重建命令统一加入 `--execute-simulated-trades`，使收盘后重建会顺带落账模拟盘并刷新持仓状态。
- 已同步更新 `README.md` 的运行说明，说明每天收盘后的自动重建会刷新持仓、执行状态与研究说明区。
- 已把 Dashboard 的页面确认动作改成折叠待确认行，避免已确认的模拟调仓仍以待办形式挂在策略监控表里。
- 已把策略监控表与模拟盘确认状态联动，同一 `trade_id` 在确认后会同时从策略表和调仓确认表折叠。
- 已把策略监控默认读取规则改成“最新一份模拟成交档”，避免页面只看当天旧成交档而继续显示已执行卖出。
- 已把最新市值档并入回测价格序列，正式 Dashboard 已重建到 `2026-06-16`；首页日期改为读取价格序列实际最新日期，不再硬写 `2026-06-02`。
- 已将模型盘区文案改为区分“模型建仓分析区间”和“当前回测/行情序列最新日期”，避免把 6/2 建仓模型窗口误读成 Dashboard 未更新。
- 已在本地模拟盘落账 `2026-06-16` 的 2 笔卖出后复跑确认幂等：再次执行 `--execute-simulated-trades` 新增 0 笔，策略监控表中的 `2317`、`1301` 已转为“观察”。

### Verification Log

- `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py` 通过。
- 已执行 `/tmp` 冒烟：生成 `/tmp/tw_quant_dashboard.html`、`/tmp/tw_quant_dashboard_model.csv`、`/tmp/tw_quant_dashboard_trades.csv`、`/tmp/tw_quant_dashboard_positions.csv`。
- `/tmp/tw_quant_dashboard.html` 可检索到 `策略结构变化结论`，并显示 `SIMULATED_TRADES: 已落账模拟成交 0 笔`，确认页面和模拟落账链路都已接通。
- 页面确认行现在会在浏览器里自动折叠，减少“已确认但仍看见待办卖出”的误读。
- 已执行正式重建命令：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close --execute-simulated-trades`。
- `dashboard/index.html` 已验证首页显示 `2024-01-02 至 2026-06-16`，模型盘区显示 `当前回测/行情序列最新日期：2026-06-16`。
- `dashboard/index.html` 已验证没有 `建议卖出` 或 `signal-pill sell` 命中；`2317`、`1301` 显示为“观察”，理由为“本日模拟调仓已落账”。
- `data/simulated_trades_2026-06-16.csv` 保持 2 笔成交，`data/simulated_positions_latest.csv` 保持 15 檔持仓；重复重建后模拟成交 hash 未变化。
- 已验证公网旧版问题：`https://futienchun-com-dashboard.onrender.com/` 起初仍返回 `2026-06-02` 与红色 `建议卖出`，根因是 Render 仍在旧部署，不是浏览器缓存。
- 已将提交 `ed037d2` 同步推送到 `dashboard` 与 `origin` 两个远端；公网随后切到新版，返回 `今日 Dashboard 更新日期：2026-06-17`、`行情/回测序列最新日期：2026-06-16`，且 `2317`、`1301` 均为“观察”。
- 回测区已新增滚动更新记录：当前回测覆盖 `2024-04-10 至 2026-06-16`，共 `74` 次调仓，最后一次重新计算权重日期为 `2026-05-28`；由于只新增 1 个可用交易日快照，尚未走满新的 7 交易日调仓周期。
- 已新增 Dashboard“调仓与执行日历”区块，区分“回测调仓”和“模拟盘执行调仓”：最后回测调仓日 `2026-05-28`，预计下次回测调仓 `2026-06-19`，距下次还差 `3` 个共同交易日；最后模拟盘执行日 `2026-06-16`，已落账模拟成交 `2` 笔，其中卖出 `2` 笔。
- 已把本次模拟盘执行明细直接显示在 Dashboard：`2317 卖出 10 股`、`1301 卖出 53 股`。这代表用户已执行的模拟卖出会作为本地 paper portfolio 执行调仓记录展示，但不会强行改写回测模型的 7 日重新估计节奏。
- 已创建 Codex 自动化任务 `dashboard`（台股 Dashboard 每日收盘更新），每天 `18:40` 执行：重建 Dashboard、执行本地模拟盘策略、推送公网并回报结论。

### Files Changed

- `src/risk_dashboard.py`
- `scripts/serve_dashboard.py`
- `render.yaml`
- `README.md`
- `progress.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 后续若要继续细化，可把研究说明区再拆成“策略结构变化结论”和“当日持仓执行结论”两块，方便日更阅读。

## 2026-06-14

### Session Goal

用 Loop Engineering 方法，为本项目建立多 Agent 协同工作机制，设定 goal、步骤和持续执行流程。

### Actions

- 已读取项目 `README.md`。
- 已读取 `.codex/PROJECT_CONTEXT.md`。
- 已检查项目目录结构。
- 已确认当前项目不是 Git 仓库。
- 已确认敏感文件存在于忽略规则中：`.env`、`.shioaji.local.env`、`.shioaji.runtime/`。
- 已读取关键 CLI 参数：`--offline-cache`、`--model-portfolio`、`--model-method`、`--ai-tilt`、`--execute-simulated-trades`、`--update-daily-market`、`--data-source`。
- 已建立项目级 `AGENTS.md`。
- 已建立 `task_plan.md`、`findings.md`、`progress.md`。
- 已收到文档/交接 Agent 回报，并确认缺失协作文件已补齐。
- 已收到工程运行 Agent 回报，并记录主入口、运行模式和建议指标。
- 已收到量化策略与数据边界 Agent 回报，并记录策略边界、数据边界、模拟盘/实盘边界和风险闸门。

### Current State

- 协作底座已落地。
- 后台 Agent 侦察已完成。
- 下一步是执行最小验证命令，并设定第一轮可执行改进目标。

### Verification Log

- `./.venv/bin/python` 读取并 `compile()` 了 `src/risk_dashboard.py`，结果：`compile_ok`。
- 已确认 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md` 均存在且非空。
- 已搜索下单相关关键词 `place_order|cancel_order|update_order|api.Order|api.place|api.update|api.cancel`，结果：无匹配。
- 首次运行短区间离线 Dashboard 冒烟失败：`local variable 'default_trade_state_json' referenced before assignment`。
- 已最小修复 `src/risk_dashboard.py`：在模型盘分支前提供默认空交易状态。
- 修复后重跑编译：`compile_ok`。
- 修复后重跑短区间离线 Dashboard 冒烟：成功生成 `/tmp/tw_quant_loop_smoke.html`，文件大小 `4,954,833` bytes。
- 已运行短区间模型盘临时冒烟：成功生成 `/tmp/tw_quant_loop_model.html` 与 `/tmp/tw_quant_loop_model.csv`。
- 核对正式产物：`dashboard/index.html` 与 `data/model_portfolio_latest.csv` 未被本轮临时验证覆盖。
- 本轮短区间冒烟刷新了可再生缓存 `data/matrix_cache/twse_prices_82f9000b78269b97.npz`。

### Files Changed

- `AGENTS.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`
- `src/risk_dashboard.py`

### Next Loop Recommendation

- 建立完整复跑计时基线，记录 `run_total_seconds` 与 `backtest_seconds`。
- 在不改变策略结果的前提下，优先分析滚动回测 27 秒瓶颈。

### Loop Status

- Phase 1-5 已完成。
- Phase 6 验证与交接已完成到项目文件；下一轮可从性能基线开始。

## 2026-06-14 第二轮 Loop：完整复跑计时基线

### Session Goal

建立完整复跑性能基线，记录 `run_total_seconds` 与 `backtest_seconds`，再给出下一步性能优化建议。

### Scope

- 使用 `--offline-cache`，不请求外部行情。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 不使用 `--execute-simulated-trades`，不触碰实盘或模拟盘落账。
- 临时输出到 `/tmp/`，不覆盖 `dashboard/index.html` 或 `data/model_portfolio_latest.csv`。

### Baseline Command

```bash
./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate --output /tmp/tw_quant_loop_perf.html --model-output /tmp/tw_quant_loop_perf_model.csv
```

### Metrics

| Metric | Value | Evidence |
| --- | ---: | --- |
| `run_total_seconds` | 28.60 | `/usr/bin/time -p` 的 `real` |
| `backtest_seconds` | 27.9764 | 单独包住 `rolling_rebalance_backtest()` 的 `perf_counter()` |
| `rebalance_count` | 74 | 单独回测量测输出 |
| `observations` | 575 | 单独回测量测输出 |
| `assets` | 15 | 单独回测量测输出 |
| `date_range` | 2024-01-02 至 2026-06-02 | 单独回测量测输出 |

### Verification Log

- 完整复跑成功生成 `/tmp/tw_quant_loop_perf.html`。
- 单独回测计时成功，`backtest_seconds=27.9764`。
- cProfile 画像显示 `rolling_rebalance_backtest()` 耗时集中在 148 次 `min_variance_weights()`；主要瓶颈为 fallback `projected_gradient_min_variance()` 内反复调用 `project_capped_simplex()`。
- 正式产物未覆盖：本轮仅写 `/tmp/tw_quant_loop_perf.html`、`/tmp/tw_quant_loop_perf_model.csv`；dated 副本为脚本默认的 `/tmp/model_portfolio_2026-06-03.csv`。

### Files Changed

- `progress.md`
- `task_plan.md`
- `findings.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 优先优化 `src/risk_dashboard.py` 的最小方差求解路径：降低 `project_capped_simplex()` 调用成本，或让 SciPy SLSQP 成功路径可用并可验证。
- 下一轮验收建议：`run_total_seconds` 低于 10 秒、`backtest_seconds` 低于 8 秒，并对比回测净值、换手率、模型权重的数值差异是否在可接受误差内。

## 2026-06-14 第三轮 Loop：结果一致的滚动回测性能优化

### Session Goal

在不改变策略口径、交易边界和正式产物的前提下，优化滚动回测的最小方差求解热路径。

### Scope

- 只改 `src/risk_dashboard.py` 的数值求解辅助函数。
- 不新增依赖。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 不使用 `--data-source shioaji`、`--data-source auto`、`--update-daily-market`、`--execute-simulated-trades`。
- 所有验证输出写入 `/tmp/`，不覆盖正式 `dashboard/index.html` 或 `data/model_portfolio_latest.csv`。

### Actions

- 启动 3 个只读多 Agent 侦察：性能方案、验证方案、安全边界。
- 建立优化前指标文件 `/tmp/tw_quant_before_perf_metrics.json`。
- 修改 `project_capped_simplex()`：二分投影过程中当 projected sum 足够接近 1 时提前停止。
- 修改 `min_variance_weights()`：增加可选 `initial` 参数，默认行为仍为等权初始。
- 曾临时尝试 warm start，但因结果小幅漂移，正式回测调用已改回默认等权初始。
- 曾临时测试 active-set 高速求解器；因 sample 回测结果明显改变，未纳入源码。

### Metrics

| Metric | Before | After | Result |
| --- | ---: | ---: | --- |
| `run_total_seconds` | 28.60 秒 | 16.00 秒 | 通过，约 44% 降低 |
| `backtest_seconds` | 29.1977 秒 | 15.0964 秒 | 通过，约 1.93x 加速 |
| `rebalance_count` | 74 | 74 | 一致 |
| `sample_final` diff | - | `3.70e-13` | 一致 |
| `shrink_final` diff | - | `6.86e-14` | 一致 |
| `sample_max_drawdown` diff | - | `1.20e-12` | 一致 |
| `shrink_max_drawdown` diff | - | `1.03e-13` | 一致 |
| `sample_average_turnover` diff | - | `1.03e-12` | 一致 |
| `shrink_average_turnover` diff | - | `3.53e-12` | 一致 |
| `weights_max_abs_diff` | - | `4.70e-14` | 一致 |

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行完整临时复跑：`/usr/bin/time -p ./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate --output /tmp/tw_quant_loop_perf_after.html --model-output /tmp/tw_quant_loop_perf_after_model.csv`，结果成功，`real 16.00`。
- 已执行短区间 Dashboard 冒烟：输出 `/tmp/tw_quant_loop_smoke_after.html`，成功。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_loop_model_after.html` 与 `/tmp/tw_quant_loop_model_after.csv`，成功。
- 已核对正式产物未覆盖：`dashboard/index.html`、`data/model_portfolio_latest.csv`、`data/model_portfolio_2026-06-03.csv` 的修改时间和大小保持 `1781226866 / 5061422`、`1781226866 / 4299`、`1781226866 / 4299`。

### Files Changed

- `src/risk_dashboard.py`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 不建议继续在正式口径里追求 `<8s`，除非允许引入会改变数值结果的更快求解器研究分支。
- 下一轮更稳的方向是“模拟盘幂等性验证”或“Dashboard 报告解释增强”，继续保持每轮一个目标。

## 2026-06-14 第四轮 Loop：模拟盘幂等性验证

### Session Goal

验证并加固 `--execute-simulated-trades` 的同日重复落账防护，确保可用临时路径演练，不覆盖正式模拟盘 CSV。

### Scope

- 允许修改 `src/risk_dashboard.py`、`README.md` 与 Loop 交接文件。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 不使用 `--data-source shioaji`、非离线 `--data-source auto`、`--update-daily-market`。
- 所有模拟落账验证输出写入 `/tmp/`，不覆盖正式 `dashboard/index.html`、`data/model_portfolio_latest.csv` 或正式 `data/simulated_*`。

### Multi Agent Summary

- 模拟盘逻辑审计 Agent：确认已有 `(symbol, action)` 同日防重，但建议统一临时输出路径、标准化 status、避免同次重复 key。
- QA 验证方案 Agent：建议不要直接在正式目录落账；旧代码只能靠整项目沙盒，新参数落地后可用 `/tmp` 轻量验证。
- 安全边界 Agent：确认安全组合为 `--offline-cache --data-source twse --execute-simulated-trades`；禁止与 `--data-source shioaji`、非离线 `auto`、`--update-daily-market` 混跑。

### Actions

- 新增 `--simulated-trades-output`，可把模拟成交 CSV 写到临时路径。
- 新增 `--simulated-positions-output`，可把最新模拟持仓 CSV 与 dated 持仓 CSV 写到临时路径旁。
- `build_trade_signals()`、`write_simulated_trades()` 与 `render_dashboard()` 已共用可选临时成交路径。
- `load_simulated_trade_keys()` 已把 `status` 标准化为 `strip().lower()`。
- `write_simulated_trades()` 写入新成交后会同步更新 `existing_keys`，提高函数内部自防御性。
- README 已补充临时幂等性验证命令与安全边界。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 第一次临时落账命令成功，`real 15.82`，输出 `/tmp/tw_quant_idempotency_run1.html`；临时成交新增 2 笔。
- 第一次后 `/tmp/tw_quant_idempotency_trades.csv` 为 3 行，hash `848d7a6270868b59dc0c75c09b0fab942a3d9f95f6c31bb783c1de30dd2610c7`。
- 第一次后 `/tmp/tw_quant_idempotency_positions.csv` 和 `/tmp/tw_quant_idempotency_positions_2026-06-08.csv` 均为 16 行，hash `4336a4280bc05c0a0f611cf0d7d8d25e2a657f99e56f5d8970e30d90476208aa`。
- 第二次临时落账命令成功，`real 15.44`；第二次显式使用 `--model-execution-orders /tmp/tw_quant_idempotency_positions.csv` 模拟正式流程读取最新模拟持仓。
- 第二次输出显示 `已落账模拟成交 0 笔`；临时成交/持仓行数和 hash 均与第一次后保持一致。
- 交易 CSV 检查：`trade_rows=2`，`duplicate_executed_keys=0`。
- 已核对正式产物未覆盖：`dashboard/index.html`、`data/model_portfolio_latest.csv`、`data/model_portfolio_2026-06-03.csv`、`data/simulated_positions_latest.csv`、`data/simulated_trades_2026-06-08.csv` 的 mtime/size/hash 保持既有状态。

### Files Changed

- `src/risk_dashboard.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮建议做 Dashboard 报告解释增强：把“本日模拟调仓已落账”的原因、临时验证口径和 paper portfolio 边界说明得更清楚。

## 2026-06-17 小屏名称列排版修正

### Session Goal

修正 Dashboard 在小屏或窄视口下，模型盘相关表格“名称”列被压成逐字竖排的问题。

### Scope

- 只改 `src/risk_dashboard.py` 的 Dashboard HTML/CSS 生成逻辑。
- 不改策略阈值、风险模型、行情来源或模拟盘落账逻辑。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 使用既有 `data/model_portfolio_market_2026-06-16_intraday.csv` 重建，不请求新行情。

### Actions

- 为模型盘持仓表、模拟盘调仓确认表、策略监控表的“名称”单元格补上 `name-cell` 与 `asset-name`。
- 新增最小样式：名称列保留最小宽度，名称文本使用独立不换行元素，避免被压成逐字换行。
- 用既有 6/16 盘中市值档重建正式 `dashboard/index.html`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_name_layout_smoke.html` 与 `/tmp/tw_quant_name_layout_smoke.csv`，结果通过。
- 已检索临时 HTML：确认 `name-cell`、`asset-name` 已写入，且 `00881`、`00919`、`2330` 目标行已套用新结构。
- 已执行正式重建：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-16_intraday.csv --model-method multi-factor-shrink --ai-tilt moderate`，结果成功。
- 已检索正式 `dashboard/index.html`：确认模型盘持仓表、模拟盘调仓确认表、策略监控表的名称列都已套用 `name-cell` / `asset-name`。
- 当前正式 `dashboard/index.html` hash：`119a8e76857228d5749b74e62448ef6dc6989773be387ac1af904c79ae6ebaac`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 若用户仍反馈某些窄屏设备有表格挤压，再补一次浏览器实机检查，优先看 `trade-signals` 和 `manual-trading` 两张宽表。

## 2026-06-14 第五轮 Loop：Dashboard 报告解释增强

### Session Goal

增强 Dashboard 中模拟盘建议、页面确认、脚本落账和真实券商订单之间的边界解释，减少误读。

### Scope

- 只改 `src/risk_dashboard.py` 的 Dashboard 文案与交接文档。
- 不改策略阈值、权重计算、行情来源、模拟盘落账逻辑。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 验证命令只使用 `--offline-cache --data-source twse`。
- 不使用 `--execute-simulated-trades`，不写正式模拟成交/持仓 CSV。

### Multi Agent Summary

- Dashboard/Product Agent：指出“手动订单交易”“标记已执行 / 已执行”“后续再落成 CSV”容易误读，建议改成页面确认与脚本落账的边界文案。
- QA/Reviewer Agent：建议先跑 `/tmp` 短区间冒烟，再按需正式重建 Dashboard，并 grep 新旧文案。
- 安全边界 Agent：确认本轮禁止 `--data-source shioaji`、非离线 `auto`、`--update-daily-market`、`--execute-simulated-trades`；可安全使用 `--offline-cache --data-source twse`。

### Actions

- 策略监控区新增“訊號口徑”说明，区分观察、建议买卖、已落账转观察。
- 手动交易区标题从“手动订单交易”改为“模拟盘调仓确认”。
- 按钮与状态从“标记已执行 / 已执行 / 待执行”改为“页面标记已确认 / 页面已确认 / 待确认”。
- 表格列从泛化确认改为“页面复核 / 脚本落账”。
- 模型盘 footer 明确说明 Dashboard 中持仓、盈亏、建议单都只属于本地模拟盘，不是券商委托状态。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间无模型盘冒烟：`--start 2024-01 --end 2024-06 --offline-cache --data-source twse --output /tmp/tw_quant_dashboard_explain_smoke.html`，结果通过。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_dashboard_explain_model.html` 与 `/tmp/tw_quant_dashboard_explain_model.csv`，结果通过。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.19`。
- 正式 `dashboard/index.html` 已命中新文案：`模拟盘调仓确认`、`页面标记已确认`、`脚本落账`、`真正落成 CSV`、`訊號口徑`、`待确认清单`。
- 旧歧义文案已无命中：`手动订单交易`、`标记已执行`、`后续我们可以再把已执行状态落成 CSV`、`待执行模拟调仓单`、`待執行單`、`当前不再列为待执行单`。
- 正式 `dashboard/index.html` mtime 更新为 `1781426795`，大小 `5062194`，hash `c630fc3bee1ae545aaeceec938d40cecb6d13d1de9849162aa686589bbd372ef`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` mtime 随正式复跑更新为 `1781426795`，内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_positions_latest.csv` 仍为 mtime `1780928144`、hash `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`；`data/simulated_trades_2026-06-08.csv` 仍为 mtime `1780928144`、hash `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续增强报告解释，把调仓原因与风险归因做成更可读的摘要；或研究同日分批交易的 `trade_id` 设计。

## 2026-06-14 第六轮 Loop：风险归因与调仓原因摘要

### Session Goal

在不改变策略、权重、行情来源或模拟盘落账逻辑的前提下，为 Dashboard 增加更可读的风险归因与调仓原因摘要。

### Scope

- 只改 `src/risk_dashboard.py` 的 Dashboard 摘要文案与交接文档。
- 不新增模型、不改风险贡献、压力测试、建议单阈值或交易规则。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 验证命令只使用 `--offline-cache --data-source twse`。
- 不使用 `--execute-simulated-trades`，不写正式模拟成交/持仓 CSV。

### Multi Agent Summary

- Quant Explanation Agent：建议展示主要风险来源、同源风险、压力情境差异、本轮调仓触发原因和无建议时解释；强调不可包装成预测或投资建议。
- Dashboard/Product Agent：建议只加解释摘要层，复用现有变量，不改规则；补充持仓表与建议单关系说明。
- QA/安全验证 Agent：给出编译、`/tmp` 冒烟、正式重建、grep 文案和安全边界验证步骤。

### Actions

- 新增“本轮风险归因与调仓摘要”区块，展示主要风险、压力情境、调仓原因。
- 调仓摘要按状态分支：有待确认单、已有本日落账转观察、完全无新触发。
- 压力情境摘要使用正数损失口径，并明确只是解释型压力口径，不是未来预测。
- 持仓区新增“持仓状态解释”，说明持仓表、建议单、券商账户三者边界。
- 正式 Dashboard 已重建。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间无模型盘冒烟：`--start 2024-01 --end 2024-06 --offline-cache --data-source twse --output /tmp/tw_quant_risk_reason_smoke.html`，结果通过。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_risk_reason_model_smoke.html` 与 `/tmp/tw_quant_risk_reason_model.csv`，结果通过。
- `/tmp` 生成 HTML 已命中新文案：`本轮风险归因与调仓摘要`、`主要风险`、`压力情境`、`调仓原因`、`本轮调仓解释`、`持仓状态解释`。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.18`。
- 正式 `dashboard/index.html` 已命中新文案；旧歧义文案 `手动订单交易`、`标记已执行`、`后续我们可以再把已执行状态落成 CSV`、`待执行模拟调仓单` 无命中。
- 正式 `dashboard/index.html` mtime 更新为 `1781431539`，大小 `5063991`，hash `c85f36444f061531ee5acb66ed975cdf97f5e635b3bd88ccf6b1aa6e4001f359`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` mtime 随正式复跑更新为 `1781431539`，内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_positions_latest.csv` 仍为 mtime `1780928144`、hash `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`；`data/simulated_trades_2026-06-08.csv` 仍为 mtime `1780928144`、hash `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮建议研究模拟盘同日分批交易 `trade_id`，或继续把行业/AI 供应链暴露做成更清楚的风险归因摘要。

## 2026-06-14 第七轮 Loop：模拟盘稳定 trade_id

### Session Goal

为模拟盘建议单与本地成交 CSV 建立稳定 `trade_id`，让 Dashboard 页面复核、脚本落账与后续排查可以对齐。

### Scope

- 允许修改 `src/risk_dashboard.py`、`README.md` 与 Loop 交接文件。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 验证只使用 `--offline-cache --data-source twse`。
- 临时落账验证只写 `/tmp`，不覆盖正式模拟成交/持仓 CSV。
- 不改变策略阈值、权重计算、买卖触发条件或正式实盘边界。

### Multi Agent Summary

- ID 设计 Agent：建议 `trade_id` 使用稳定业务字段和版本前缀，不包含价格、股数或中文原因；建议新增稳定 `trigger_code`。
- CSV 兼容 Agent：建议新记录使用 `id:{trade_id}`，旧 CSV 继续用 `legacy:{trade_date}:{symbol}:{action}` 兼容去重。
- Dashboard/Product + QA Agent：建议页面状态和 DOM 操作改用 `trade_id`，`data-symbol` 仅保留为人工检查辅助；单号以小字显示，不抢主要决策信息。

### Actions

- `TradeSignal` 新增 `trade_id` 与 `trigger_code`。
- 新增 `stable_simulated_trade_id()` 与 `legacy_simulated_trade_key()`。
- `build_trade_signals()` 为四类触发规则生成稳定 `trigger_code` 和 `paper-...` 单号。
- `load_simulated_trade_keys()` 改为读取 `trade_id`，并保留旧 CSV fallback。
- `write_simulated_trades()` 新增 `trade_id` CSV 欄位，并用 `trade_id` + legacy key 做本轮防重。
- Dashboard 待确认行新增 `data-trade-id` 与小字“单号”；浏览器状态升级为 `risk-dashboard-manual-trades-v2-...`，状态对象按 `trade_id` 记录。
- README 已补充 `trade_id` 用途、非敏感字段边界和旧 CSV 兼容说明。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_trade_id_smoke.html` 与 `/tmp/tw_quant_trade_id_model.csv`，结果通过。
- 已执行临时预览 Dashboard：`/tmp/tw_quant_trade_id_preview.html`，命中 `data-trade-id`、`单号：paper-...`、`risk-dashboard-manual-trades-v2`，且旧 symbol 状态键无命中。
- 已执行第一次 `/tmp` 临时模拟落账：输出 `/tmp/tw_quant_trade_id_trades.csv` 与 `/tmp/tw_quant_trade_id_positions.csv`，成交 2 笔，`trade_id` 分别为 `paper-20260608-2317-sell-01-c5ac2f144a`、`paper-20260608-1301-sell-01-61defce39b`。
- 已执行第二次 `/tmp` 临时模拟落账，并把 `--model-execution-orders` 指向临时持仓；第二次后临时成交仍为 2 笔、`duplicate_trade_ids=0`、`executed_rows=2`。
- 临时成交 CSV hash 为 `d7223ab01323d6e1a3de8aa5cc7ed9df411ed69427c12f6c9878437254bcbf6c`；临时持仓 CSV hash 为 `4336a4280bc05c0a0f611cf0d7d8d25e2a657f99e56f5d8970e30d90476208aa`。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.68`。
- 正式 `dashboard/index.html` hash 更新为 `0a30ba517d3825746a5165efaf3f8cf64ecc4cfa2bf6fa60adfd752630b54a91`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_positions_latest.csv` 仍为 mtime `1780928144`、hash `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`；`data/simulated_trades_2026-06-08.csv` 仍为 mtime `1780928144`、hash `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- 旧歧义文案与旧 symbol 状态键无命中：`手动订单交易`、`标记已执行`、`待执行模拟调仓单`、`state[symbol]`、`risk-dashboard-manual-trades-2026`。

### Files Changed

- `src/risk_dashboard.py`
- `README.md`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮若继续模拟盘方向，建议明确同日分批交易 `batch_seq` 语义：何时允许同一标的同方向从 `01` 递增到 `02`，以及是否仍保留 legacy `(symbol, action)` 防重。
- 另一个稳妥方向是行业/AI 供应链风险归因摘要，把当前 `sector`、`theme`、`ai_supply_chain` 字段转成 Dashboard 的群组暴露与风险贡献解释。

## 2026-06-14 第八轮 Loop：显式分批 batch_seq

### Session Goal

定义并实现同日分批交易的 `batch_seq` 语义：默认保持幂等，只有显式指定新批次时才允许同日同标的同方向第二批模拟成交。

### Scope

- 允许修改 `src/risk_dashboard.py`、`README.md` 与 Loop 交接文件。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 验证只使用 `--offline-cache --data-source twse`。
- 临时落账验证只写 `/tmp`，不覆盖正式模拟成交/持仓 CSV。
- 不改变策略阈值、权重计算、买卖触发条件或券商边界。

### Multi Agent Summary

- batch_seq 语义 Agent：不应自动递增；推荐显式 `--simulated-trade-batch-seq`，默认固定 `01`。
- CSV/幂等性 Agent：旧无 `trade_id` 行应继续 legacy 防重；新有 `trade_id` 行应按 ID 精准幂等，允许 `01` 与 `02` 共存。
- Dashboard/Product Agent：页面和 README 需说明默认 `01` 幂等，显式新批次才是人为确认的同日分批。

### Actions

- 新增 `--simulated-trade-batch-seq` 参数，校验 `01` 到 `99`，允许 `1` 补成 `01`。
- `build_trade_signals()`、`write_simulated_trades()`、`render_dashboard()` 已接收并传递 `trade_batch_seq`。
- `stable_simulated_trade_id()` 继续把 `batch_seq` 纳入 ID，生成 `paper-YYYYMMDD-symbol-action-batch-digest`。
- `load_simulated_trade_keys()` 拆成 `trade_ids` 与 `legacy_keys`：新格式按 `trade_id` 幂等，旧无 ID CSV 才走 legacy 防重。
- 默认 `01` 批次仍检查 legacy key；显式 `02+` 不被新格式 `01` legacy 阻挡，但同样 `02` 复跑会被自己的 `trade_id` 阻挡。
- Dashboard footer 与 README 已补充默认批次、显式分批和安全边界说明。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行非法参数检查：`--simulated-trade-batch-seq 00` 以 argparse 错误退出，未生成输出。
- 第一次 `/tmp` 批次 `01` 临时落账：生成 2 笔，`trade_id` 为 `paper-20260608-2317-sell-01-c5ac2f144a`、`paper-20260608-1301-sell-01-61defce39b`。
- 第二次同样 `/tmp` 批次 `01` 复跑并读取临时持仓：成交仍 2 笔，`duplicate_trade_ids=0`，临时成交 hash `d7223ab01323d6e1a3de8aa5cc7ed9df411ed69427c12f6c9878437254bcbf6c`。
- 第一次显式 `/tmp` 批次 `02`：成交增至 4 笔，`-01-` 两笔、`-02-` 两笔；新增 `paper-20260608-2317-sell-02-5df23dedea`、`paper-20260608-1301-sell-02-9683848bef`。
- 第二次同样 `/tmp` 批次 `02` 复跑：成交仍 4 笔，`duplicate_trade_ids=0`，`executed_rows=4`；临时成交 hash 保持 `0a72785a77a23dc61c2e3f889f155872778fc8edbdb343a47e9d968d20449b4e`，临时持仓 hash 保持 `512b5454adf2238828fe80cc37c43db4d48442026d3f4da5af18e5e6ad385925`。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.70`。
- 正式 `dashboard/index.html` hash 更新为 `6c1438b55cbb79dcc4106f331e364b3b01b2a0e4bc226e185cc71b5042556275`，并命中“默认批次为 01”“同日分批”等说明。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_positions_latest.csv` 仍为 mtime `1780928144`、hash `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`；`data/simulated_trades_2026-06-08.csv` 仍为 mtime `1780928144`、hash `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- 安全边界：未使用 Shioaji、非离线 `auto`、`--update-daily-market` 或任何真实交易端；正式落账未执行。

### Files Changed

- `src/risk_dashboard.py`
- `README.md`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮建议做行业/AI 供应链风险归因摘要，把 `sector`、`theme`、`ai_supply_chain` 转为 Dashboard 群组暴露与风险贡献解释。
- 若继续模拟盘方向，可为显式分批增加 Dashboard 批次状态小结，例如显示当前批次、已落账批次和待确认批次。

## 2026-06-14 第九轮 Loop：行业/主题/AI 供应链风险归因

### Session Goal

在不改变模型权重、策略阈值、模拟盘或数据源的前提下，为 Dashboard 增加行业、主题与 AI 供应链群组风险归因。

### Scope

- 只改 `src/risk_dashboard.py` 的解释型 Dashboard 区块与交接文档。
- 不改 `config/universe_tw.csv`、权重计算、回测、建议单、模拟盘落账。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 或任何密钥。
- 验证命令只使用 `--offline-cache --data-source twse`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Quant/Risk Agent：建议复用现有权重、风险贡献和资产池分类字段，做解释型归因，不新增模型信号。
- Dashboard/Product Agent：建议归因放在风险摘要上下文，文案避免“看好/看坏/应买卖”，强调同源风险和组合暴露。
- QA/安全边界 Agent：建议编译、短区间 `/tmp` 冒烟、正式重建、grep 新文案并确认正式模拟盘 CSV 不变。

### Actions

- 新增 `aggregate_group_exposure()`，按群组汇总权重、风险贡献和檔数。
- 新增“行业、主题与 AI 供应链风险归因”区块。
- 有模型盘时使用模型盘目标权重做群组暴露，并用收缩协方差计算风险贡献；无模型盘时退回收缩协方差最小方差权重。
- 展示行业风险贡献 Top 5、主题风险贡献 Top 5、AI/非 AI 二元分组。
- 新文案明确：归因只解释同源风险与组合暴露，不代表个股买卖建议，不是未来报酬预测；ETF 成分未穿透。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间无模型盘冒烟：`--start 2024-01 --end 2024-06 --offline-cache --data-source twse --output /tmp/tw_quant_ai_risk_smoke.html`，结果通过。
- 已执行短区间模型盘冒烟：输出 `/tmp/tw_quant_ai_risk_model_smoke.html` 与 `/tmp/tw_quant_ai_risk_model.csv`，结果通过。
- `/tmp` 生成 HTML 命中：`行业风险归因`、`主题风险归因`、`AI 供应链风险归因`、`同源风险`、`组合暴露`、`不代表个股买卖建议`、`不是未来报酬预测`、`未穿透 ETF 成分`。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.68`。
- 正式 `dashboard/index.html` 新增区块显示：AI 供应链 5 檔，权重 33.00%，风险贡献 48.49%，风险贡献相对权重差 +15.49%。
- 正式 `dashboard/index.html` hash 更新为 `94a0fc520c0ded1ac58a1652f8f049d2da983222131e9e350f292d0299593d6f`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_trades_2026-06-08.csv` 仍为 hash `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`；`data/simulated_positions_latest.csv` 仍为 hash `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 仍为 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。
- 下单相关关键词 `place_order|cancel_order|update_order|api.Order|StockOrder|FutureOrder` 在 `src/risk_dashboard.py` 无命中。

### Files Changed

- `src/risk_dashboard.py`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮建议为显式分批增加 Dashboard 批次状态小结，显示当前批次、已落账批次和待确认批次。
- 另一个方向是把本轮群组归因扩展为自动研究报告段落，但仍应保持解释型，不进入预测或实盘建议。

## 2026-06-15 第十轮 Loop：Dashboard 批次状态小结

### Session Goal

为显式 `--simulated-trade-batch-seq` 增加 Dashboard 批次状态小结，让页面能说明目前批次、已写入本地模拟成交 CSV 的批次、旧格式记录与待确认批次。

### Scope

- 允许修改 `src/risk_dashboard.py`、`README.md` 与 Loop 交接文件。
- 不改变权重、回测、建议单触发、模拟落账语义或 `trade_id` 生成。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 所有 `--execute-simulated-trades` 验证输出写入 `/tmp/`，不覆盖正式模拟成交或持仓 CSV。

### Multi Agent Summary

- Quant/Data Agent：建议只读汇总现有成交 CSV，不自动递增批次；旧无 `trade_id` 行单独显示为旧格式，不硬判为 `01`。
- Dashboard/Product Agent：建议小结放在“模拟盘调仓确认”说明段落之后、待确认表格之前；文案需强调“本地模拟成交 CSV”，不要写成券商成交或委托状态。
- QA/Reviewer Agent：验证重点是 `01` 幂等、`02` 显式分批、重复 `02` 不新增、正式模拟 CSV hash 不变。

### Actions

- 新增 `SimulatedTradeBatchStatus` 与只读 helper：`simulated_trade_batch_from_id()`、`load_simulated_trade_batch_status()`。
- Dashboard “模拟盘调仓确认”区块新增“模擬盤批次狀態小結”与已落帐批次表。
- 正式旧无 `trade_id` 的模拟成交 CSV 显示为“舊格式 2 筆”，继续按交易日、标的、方向兼容防重。
- README 补充批次状态小结解读与旧格式兼容说明。
- 正式 Dashboard 已重建；未使用 `--execute-simulated-trades`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间 Dashboard 冒烟：`/tmp/tw_quant_batch_summary_smoke.html`，结果通过。
- 已执行短区间模型盘冒烟：`/tmp/tw_quant_batch_summary_model_smoke.html` 与 `/tmp/tw_quant_batch_summary_model_after_text.html`，结果通过。
- 已执行 `/tmp` 临时批次 `01` 幂等验证：第一次 2 笔，第二次仍 2 笔，`duplicate_trade_ids=0`。
- 已执行 `/tmp` 临时显式 `02` 分批验证：新增后共 4 笔，第二次同样 `02` 复跑仍 4 笔，`duplicate_trade_ids=0`；批次分布 `{'01': 2, '02': 2}`。
- 正式 `dashboard/index.html` hash：`0252d4cd62cca01bba419e4abc8eb7b168855d8b6a8ffcdee3f36263d5ce57d5`。
- `data/model_portfolio_latest.csv` hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- 下单相关关键词检查无新增实盘 API；命中的“不是券商委托状态”是边界说明。

### Files Changed

- `src/risk_dashboard.py`
- `README.md`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 优先把群组风险归因扩展成自动研究报告段落，补“本轮最大同源风险、AI 风险-权重差、调仓状态”的可复制摘要。
- 或增加一个 `/tmp` 旧格式 fixture 验证脚本，专门覆盖无 `trade_id` CSV 的批次状态展示。

## 2026-06-15 第十一轮 Loop：群组风险研究报告摘要

### Session Goal

把群组风险归因扩展为可复制的自动研究报告段落，方便粘贴到报告或 Obsidian，同时保持解释型边界，不新增交易信号或模拟落账。

### Scope

- 允许修改 `src/risk_dashboard.py`、`README.md`、`dashboard/index.html` 与 Loop 交接文件。
- 不改变模型权重、回测、建议单触发、`trade_id`、`batch_seq` 或模拟盘落账语义。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 验证命令只使用 `--offline-cache --data-source twse`；不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Quant/Risk Agent：建议复用既有 `top_sector`、`top_theme`、`ai_group`、`ai_risk_gap`、`max_pair_text`、`sample_stress`、`shrink_stress`、`trade_reason_summary`，不新增模型信号。
- Dashboard/Product Agent：建议使用只读 `textarea` 放在现有“本轮风险归因与调仓摘要”区块内，复制体验优于 `pre`，且不新增 JS 状态。
- QA/Reviewer Agent：建议先短区间 `/tmp` 冒烟，再正式重建；正式模型盘 CSV 内容 hash 与模拟盘 CSV hash 必须保持不变。

### Actions

- Dashboard “本轮风险归因与调仓摘要”区块新增“群组风险研究报告摘要”说明与只读 `textarea`。
- 摘要包含：最大风险贡献标的、最高相关资产对、最高行业/主题风险来源、AI 供应链权重/风险贡献/风险-权重差、压力情境和调仓状态。
- README 补充研究摘要用途与边界说明。
- 正式 Dashboard 已重建；未使用 `--execute-simulated-trades`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py`，结果通过。
- 已执行短区间无模型盘冒烟：`/tmp/tw_quant_group_report_smoke.html`，结果通过并命中新摘要。
- 已执行短区间模型盘冒烟：`/tmp/tw_quant_group_report_model_smoke.html` 与 `/tmp/tw_quant_group_report_model.csv`，结果通过并命中新摘要。
- 已执行正式 Dashboard 重建：完整 2024-01 至 2026-06，`--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，结果成功。
- 正式 `dashboard/index.html` hash：`fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- 正式摘要命中：AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- 旧误导文案与实盘 API 关键词检查无命中。

### Files Changed

- `src/risk_dashboard.py`
- `README.md`
- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可补无 `trade_id` 旧格式 fixture 验证，覆盖批次状态小结的旧 CSV 展示。
- 或把研究摘要同步到 Obsidian 项目卡片，形成 Dashboard -> 研究记录的交接闭环。

## 2026-06-15 第十二轮 Loop：旧格式模拟成交 fixture 验证

### Session Goal

为无 `trade_id` 的旧格式模拟成交 CSV 建立可复跑 fixture 验证，确认 Dashboard 批次状态小结把旧成交显示为“舊格式”，而不是误判为 `批次 01`。

### Scope

- 允许新增 `scripts/validate_legacy_trade_batch_status.py`，并更新 README 与 Loop 交接文件。
- 不改变模型权重、回测、建议单触发、模拟落账语义或 Dashboard 正式产物。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 只写 `/tmp` fixture 与 `/tmp` 临时 Dashboard；不覆盖正式 `data/simulated_*`。

### Multi Agent Summary

- QA/Fixture Agent：建议分两层验证：先直接断言 `load_simulated_trade_batch_status()`，再用一次 CLI 临时 Dashboard 验证页面文案；fixture 应故意不含 `trade_id`，并包含 `" executed "` 覆盖 status 标准化。

### Actions

- 新增 `scripts/validate_legacy_trade_batch_status.py`。
- 默认脚本生成 `/tmp/tw_quant_legacy_trade_fixture.csv`，断言两笔旧成交归为 `legacy` / “舊格式”。
- `--dashboard` 模式会生成 `/tmp/tw_quant_legacy_trade_fixture_dashboard.html`，断言页面显示“舊格式 2 筆”且不出现旧成交被列为 `批次 01`。
- 调整 `--simulated-trades-output` help：说明其可作为 Dashboard 验证读取路径。
- README 补充 fixture 验证命令。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py`，结果输出 `legacy_fixture_ok fixture=/tmp/tw_quant_legacy_trade_fixture.csv`。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py --dashboard`，结果输出 `legacy_dashboard_ok output=/tmp/tw_quant_legacy_trade_fixture_dashboard.html`。
- 已执行短区间模型盘冒烟：`/tmp/tw_quant_round12_model_smoke.html`，结果通过。
- `/tmp/tw_quant_legacy_trade_fixture_dashboard.html` 命中：`暫無新格式批次`、`舊格式紀錄：舊格式 2 筆`、`舊成交 CSV 無 trade_id`。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- 实盘 API 关键词检查无命中。

### Files Changed

- `scripts/validate_legacy_trade_batch_status.py`
- `src/risk_dashboard.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可把 Dashboard 的“群组风险研究报告摘要”同步到 Obsidian 项目卡片，形成研究记录闭环。
- 或继续扩展为导出 Markdown 摘要文件，但仍保持本地模拟盘与解释型边界。

## 2026-06-15 第十三轮 Loop：Obsidian 研究记录同步

### Session Goal

把 Dashboard 的“群组风险研究报告摘要”和第九至第十二轮稳定结论同步到 iCloud Obsidian 项目卡片，形成 Dashboard -> 长期研究记录的闭环。

### Scope

- 允许修改 iCloud Obsidian 项目卡片与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`README.md`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：验证 Obsidian 正确落点为 iCloud vault 的 `台股量化基金.md`，避免误写本机或历史噪音路径。
- Dashboard/Product Agent：建议直接同步 Dashboard 可复制摘要，同时保留“研究解释、非买卖建议、非实盘订单”的边界。
- QA/Reviewer Agent：建议只做文本命中、fixture 脚本复跑和正式产物 hash 检查，不重建 Dashboard。

### Actions

- 更新 iCloud Obsidian `台股量化基金.md` 的 `updated` 日期为 2026-06-15。
- 新增“最新研究摘要（2026-06-15）”小节，记录 Dashboard 研究摘要与第九至第十二轮稳定结论。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：Obsidian 卡片与交接文件文本命中检查，结果命中“最新研究摘要（2026-06-15）”、AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`、“舊格式 2 筆”与 fixture 脚本引用。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py`，结果输出 `legacy_fixture_ok fixture=/tmp/tw_quant_legacy_trade_fixture.csv`。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py --dashboard`，结果输出 `legacy_dashboard_ok output=/tmp/tw_quant_legacy_trade_fixture_dashboard.html`。
- 已执行：Obsidian 卡片结构检查，结果输出 `obsidian_note_ok`。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `/Users/tonyfu/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI-Knowledge-Wiki/02-The-Wiki/05-商业金融与量化交易/01-量化交易/03-策略实践/台股量化基金.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可建立“Dashboard 摘要 -> Markdown 摘要文件”的只读导出，优先写 `/tmp` 预览，不覆盖正式研究记录。
- 或新增一条轻量同步检查脚本，确认 Dashboard 摘要中的关键数字仍存在于 Obsidian 项目卡片。

## 2026-06-15 第十四轮 Loop：研究摘要同步一致性检查

### Session Goal

新增一条只读、可复跑的 QA 检查，确认正式 Dashboard 的群组风险研究摘要已经同步到 iCloud Obsidian 项目卡片，避免研究记录与 Dashboard 漂移。

### Scope

- 允许新增 `scripts/validate_research_brief_sync.py`，并更新 README 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：本轮选择一致性检查优先于 Markdown 导出，因为它先把第十三轮人工同步变成质量闸门。
- Dashboard/Product Agent：检查对象应是正式 Dashboard 的 `research-report` 摘要，而不是重新拼接文案，避免两个摘要来源漂移。
- QA/Reviewer Agent：脚本应只读正式 HTML 与 Obsidian 卡片，验证关键数字、边界句和旧格式兼容结论；正式产物 hash 必须保持不变。

### Actions

- 新增 `scripts/validate_research_brief_sync.py`。
- README 新增同步一致性检查命令。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/validate_research_brief_sync.py`，结果输出 `research_brief_sync_ok`，确认 Dashboard 摘要 6 行与 Obsidian 关键片段 7 项均命中。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py`，结果输出 `legacy_fixture_ok fixture=/tmp/tw_quant_legacy_trade_fixture.csv`。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/validate_research_brief_sync.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可做 `/tmp` Markdown 摘要导出预览，复用 Dashboard 摘要文本，不新增交易信号。
- 或建立一个本地 QA 汇总脚本，一次性运行研究摘要同步检查与旧格式 fixture 检查。

## 2026-06-15 第十五轮 Loop：Markdown 摘要预览导出

### Session Goal

新增一个只读导出脚本，把正式 Dashboard 的群组风险研究摘要导出为 `/tmp` Markdown 预览，方便人工复核或后续再决定是否写入长期知识库。

### Scope

- 允许新增 `scripts/export_research_brief_markdown.py`，并更新 README 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：本轮选择 `/tmp` 导出预览，不直接写 Obsidian，保持第十三轮人工同步与第十四轮一致性检查的边界。
- Dashboard/Product Agent：Markdown 预览应复用正式 Dashboard `research-report`，并保留来源、用途与研究边界。
- QA/Reviewer Agent：验证重点是导出文件存在、关键数字命中、同步检查继续通过，以及正式 Dashboard/CSV hash 不变。

### Actions

- 新增 `scripts/export_research_brief_markdown.py`。
- README 新增 Markdown 预览导出命令。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/export_research_brief_markdown.py`，结果输出 `research_brief_markdown_ok output=/tmp/tw_quant_research_brief.md brief_lines=6`。
- 已执行：`/tmp/tw_quant_research_brief.md` 文本命中检查，结果命中标题、AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`、研究边界与默认写入 `/tmp` 说明。
- 已执行：`./.venv/bin/python scripts/validate_research_brief_sync.py`，结果输出 `research_brief_sync_ok`。
- 已执行：`./.venv/bin/python scripts/validate_legacy_trade_batch_status.py`，结果输出 `legacy_fixture_ok fixture=/tmp/tw_quant_legacy_trade_fixture.csv`。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Errors Encountered

- 首次并行检查 `/tmp/tw_quant_research_brief.md` 时，内容检查早于导出脚本完成，出现一次文件不存在；顺序重跑后通过。
- 一次 `rg` 搜索模式包含反引号包住的 `/tmp`，zsh 尝试执行 `/tmp` 并提示 permission denied；改用单引号且不把反引号放进 shell 模式后通过。

### Files Changed

- `scripts/export_research_brief_markdown.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可建立本地 QA 汇总脚本，一次性运行研究摘要同步检查、Markdown 导出预览和旧格式 fixture 检查。
- 或继续扩展研究摘要导出格式，但默认仍写 `/tmp`，不要直接覆盖 Obsidian。

## 2026-06-15 第十六轮 Loop：本地 QA 汇总

### Session Goal

新增一个本地 QA 汇总脚本，把研究摘要同步检查、Markdown 导出预览和旧格式 fixture 验证收敛为单一命令，同时自动确认正式 Dashboard 与 CSV hash 前后不变。

### Scope

- 允许新增 `scripts/run_local_qa_checks.py`，并更新 README 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：本轮目标是把第十二至第十五轮分散的 QA 步骤变成单一入口，方便后续续跑和交接。
- Dashboard/Product Agent：汇总脚本应复用现有脚本，不重新拼接摘要，也不直接写 Obsidian。
- QA/Reviewer Agent：脚本必须顺序执行、先后比对正式产物 hash，并允许可选打开旧格式 fixture 的临时 Dashboard 验证。

### Actions

- 新增 `scripts/run_local_qa_checks.py`。
- README 新增本地 QA 汇总命令与当时的可选 Dashboard fixture 分支说明。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/run_local_qa_checks.py scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok`，汇总通过同步检查、Markdown 导出与旧格式 fixture helper，正式产物监控文件数为 6。
- 已执行：第十六轮的可选 Dashboard fixture 分支，结果输出 `local_qa_checks_ok ... dashboard_fixture=on`，确认可选旧格式 fixture 临时 Dashboard 分支也通过。
- 已执行：汇总脚本生成的 `/tmp/tw_quant_local_qa_research_brief.md` 文本命中检查，结果命中标题、AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`、研究边界与默认写入 `/tmp` 说明。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/run_local_qa_checks.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续增加更多只读 QA 检查项，或补一份更紧凑的本地 QA 结果摘要。
- 若回到性能目标，再讨论是否允许会改变数值结果的新求解器。

## 2026-06-16 第十七轮 Loop：固定 Dashboard Fixture 回归

### Session Goal

把旧格式 fixture 的临时 Dashboard 页面验证纳入本地 QA 汇总的默认回归，减少人为遗漏，同时保留一个较快的跳过开关。

### Scope

- 允许修改 `scripts/run_local_qa_checks.py`、`README.md` 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：这轮优先把默认覆盖面拉满，比继续加新检查项更稳。
- Dashboard/Product Agent：默认回归应覆盖旧格式 fixture 的临时 Dashboard 分支，因为这是最容易被遗忘的解释层路径。
- QA/Reviewer Agent：为避免每次都多 15 秒也没有退路，保留一个显式 `--skip-dashboard-fixture` 作为较快版本。

### Actions

- 调整 `scripts/run_local_qa_checks.py`：默认执行旧格式 fixture 的临时 Dashboard 页面验证。
- 新增 `--skip-dashboard-fixture` 选项，作为较快的本地检查开关。
- 同步更新 `README.md`、`task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/run_local_qa_checks.py scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok ... dashboard_fixture=on`，确认默认回归已覆盖旧格式 fixture 的临时 Dashboard 页面验证。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok ... dashboard_fixture=off`，确认较快模式保留同步检查、Markdown 导出和旧格式 helper 验证。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/run_local_qa_checks.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续汇总更多只读 QA 检查项，或补一个简短的本地 QA 结果摘要文件输出。
- 若回到性能目标，再讨论是否允许会改变数值结果的新求解器。

## 2026-06-16 第十八轮 Loop：QA 文案漂移清理

### Session Goal

清理本地 QA 汇总相关交接文档中残留的旧参数名，统一到当前默认回归与 `--skip-dashboard-fixture` 的说明口径，避免后续续跑时混淆。

### Scope

- 允许修改 `README.md`、`task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html`、正式 `data/*.csv` 或当前 QA 脚本行为。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。

### Multi Agent Summary

- Coordinator Agent：本轮目标是把“脚本已改但历史文案没跟上”的小漂移收干净，降低后续阅读成本。
- QA/Reviewer Agent：验证重点是项目文档与脚本检索中不再残留旧参数字符串，同时当前 QA 脚本默认/较快分支继续通过。

### Actions

- 清理交接文档中残留的旧参数表述。
- 保留第十六轮的历史语境，但明确它是旧参数名。
- 同步更新 `findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：旧参数名残留检索，结果不再命中旧参数字符串；仅保留当前有效参数 `--skip-dashboard-fixture`。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok ... dashboard_fixture=on`，确认默认完整回归仍通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok ... dashboard_fixture=off`，确认较快模式仍通过。

### Files Changed

- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续汇总更多只读 QA 检查项，或补一份更紧凑的本地 QA 结果摘要。

## 2026-06-16 第十九轮 Loop：QA 摘要文件输出

### Session Goal

为本地 QA 汇总新增一份落到 `/tmp` 的结果摘要文件，让续跑、交接与复核不再只依赖终端单行输出。

### Scope

- 允许修改 `scripts/run_local_qa_checks.py`、`README.md` 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：这轮优先补一个便于交接的轻量结果载体，不扩范围做更多新检查项。
- Dashboard/Product Agent：摘要应复用现有汇总结果与监控 hash，不再发明第二套说明口径。
- QA/Reviewer Agent：保留默认完整回归与 `--skip-dashboard-fixture` 较快模式，并确认摘要文件只写 `/tmp`。

### Actions

- 调整 `scripts/run_local_qa_checks.py`：新增 `--summary-output`，默认写 `/tmp/tw_quant_local_qa_summary.md`。
- README 补充摘要文件默认路径与覆盖内容。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/run_local_qa_checks.py scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok ... dashboard_fixture=on summary='/tmp/tw_quant_local_qa_summary.md'`，确认默认完整回归会生成摘要文件。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok ... dashboard_fixture=off summary='/tmp/tw_quant_local_qa_summary.md'`，确认较快模式也会生成摘要文件。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --summary-output /tmp/tw_quant_local_qa_summary_full.md`，结果通过；摘要命中 `检查模式：full`、`dashboard_fixture：on`、Markdown 预览路径和 6 个正式产物 SHA-256。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture --summary-output /tmp/tw_quant_local_qa_summary_fast.md`，结果通过；摘要命中 `检查模式：fast`、`dashboard_fixture：off`、Markdown 预览路径和 6 个正式产物 SHA-256。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/run_local_qa_checks.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续把更多只读检查项并入 QA 汇总，或再补一个更适合机器消费的摘要格式。

## 2026-06-16 第二十轮 Loop：QA JSON 摘要输出

### Session Goal

为本地 QA 汇总新增一份机器可读的 JSON 摘要，让后续自动巡检、多 agent 汇总或批次比对不必再解析终端单行输出或 Markdown。

### Scope

- 允许修改 `scripts/run_local_qa_checks.py`、`README.md` 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：这轮继续顺着第十九轮往前走，把“可读”补成“可机读”，仍保持极小改动。
- Dashboard/Product Agent：JSON 应复用已有 QA 结果和 hash 快照，不新造字段口径。
- QA/Reviewer Agent：验证重点是默认/较快模式都能产出 JSON，且正式产物 hash 不变。

### Actions

- 调整 `scripts/run_local_qa_checks.py`：新增 `--summary-json-output`，默认写 `/tmp/tw_quant_local_qa_summary.json`。
- README 补充 JSON 摘要默认路径与用途说明。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/run_local_qa_checks.py scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok ... dashboard_fixture=on summary_json='/tmp/tw_quant_local_qa_summary.json'`，确认默认完整回归会生成 JSON 摘要。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok ... dashboard_fixture=off summary_json='/tmp/tw_quant_local_qa_summary.json'`，确认较快模式也会生成 JSON 摘要。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --summary-json-output /tmp/tw_quant_local_qa_summary_full.json`，结果通过；JSON 点检命中 `mode=full`、`dashboard_fixture=on`、`monitored_files=6`、`hashes_unchanged=True`。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture --summary-json-output /tmp/tw_quant_local_qa_summary_fast.json`，结果通过；JSON 点检命中 `mode=fast`、`dashboard_fixture=off`、`monitored_files=6`、`hashes_unchanged=True`。
- 已执行：`./.venv/bin/python - <<'PY' ... PY` 解析 `/tmp/tw_quant_local_qa_summary.json`、`/tmp/tw_quant_local_qa_summary_full.json` 与 `/tmp/tw_quant_local_qa_summary_fast.json`，确认三份 JSON 都包含 6 个正式产物 key。
- 补充说明：中途尝试用裸 `python` 做 JSON 点检时当前 shell 无该命令，改用项目虚拟环境 `./.venv/bin/python` 后通过；不影响功能实现。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/run_local_qa_checks.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 我判断 QA 汇总闭环到这里已经够稳：单命令入口、默认/较快双模式、Markdown 摘要、JSON 摘要、正式产物 hash 守门都已具备。
- 若继续下一轮，建议改做两条之一：
  - 新增只读 QA 检查项，例如研究摘要关键数字回归表；
  - 或回到性能主线，先做不改正式口径的只读性能基线复量测。

## 2026-06-16 第二十一轮 Loop：关键数字回归检查

### Session Goal

把研究摘要里的关键数字做成显式回归断言，并纳入本地 QA 汇总默认流程，避免后续只有“文字存在”却没有“数字没漂”的盲点。

### Scope

- 允许新增只读验证脚本，并修改 `scripts/run_local_qa_checks.py`、`README.md` 与 Loop 交接文件。
- 不修改 `src/risk_dashboard.py`、`dashboard/index.html` 或正式 `data/*.csv`。
- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/`、`data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。

### Multi Agent Summary

- Coordinator Agent：这轮把 QA 从“摘要存在”推进到“关键数字不漂”，但仍维持只读和最小 Diff。
- Quant Research Agent：关键数字先锁定已知稳定值 `33.00% / 48.49% / +15.49% / 本日模拟调仓 2 笔`，避免一次放太多变量。
- QA/Reviewer Agent：新脚本应只读正式 Dashboard，并默认纳入本地 QA 汇总的 full/fast 两条路径。

### Actions

- 新增 `scripts/validate_research_brief_metrics.py`。
- 调整 `scripts/run_local_qa_checks.py`：新增研究摘要关键数字回归步骤，并把结果写入 Markdown/JSON 摘要。
- README 补充本地 QA 汇总现在包含关键数字回归检查。
- 同步更新 `task_plan.md`、`findings.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile scripts/validate_research_brief_metrics.py scripts/run_local_qa_checks.py scripts/export_research_brief_markdown.py scripts/validate_research_brief_sync.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/validate_research_brief_metrics.py`，结果输出 `research_brief_metrics_ok ... ai_weight=33.00% risk_contribution=48.49% risk_weight_gap=+15.49% observed_trade_count=2`。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok ... metrics='research_brief_metrics_ok ...' dashboard_fixture=on`，确认默认完整回归已纳入关键数字回归检查。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok ... metrics='research_brief_metrics_ok ...' dashboard_fixture=off`，确认较快模式也纳入关键数字回归检查。
- 已执行：检查 `/tmp/tw_quant_local_qa_summary.json`，结果确认 `results.metrics` 已写入关键数字回归输出，JSON 摘要与 Markdown 摘要都同步记录该闸门结果。
- 调试记录：第一次尝试把 `舊格式 2 筆` 视为研究摘要字段，随后发现它属于页面批次状态小结而非 `research-report`；已收敛为只检查摘要内实际存在的 4 个数字。
- 调试记录：中途命中过早匹配到 `00713` 的 `风险贡献 25.13%`，后续已把正则收紧到 AI 供应链那一行，避免误抓摘要中另一处风险贡献数字。
- 正式 `dashboard/index.html` hash 保持 `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- `data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
- `data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- `data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。

### Files Changed

- `scripts/validate_research_brief_metrics.py`
- `scripts/run_local_qa_checks.py`
- `README.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮可继续加“摘要关键数字趋势表”或“更多只读研究字段回归”。
- 如果要继续往 QA 深挖，我会优先做“页面关键文案 + 摘要关键数字”的组合回归，而不是再加新输出格式。

## 2026-06-16 Dashboard 正式刷新与多 Agent 能力复核

### Session Goal

按现有交接规则刷新正式 Dashboard，并复核当前多 Agent / 本地 QA 系统能为项目承担哪些稳定工作。

### Scope

- 使用既有 2026-06-08 市值档、`multi-factor-shrink` 与 `--ai-tilt moderate` 口径重建正式 Dashboard。
- 不拉取新行情，不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、`data/cache/` 或 `data/matrix_cache/`。
- 不使用 `--execute-simulated-trades`、`--update-daily-market`、`--data-source shioaji` 或非离线 `auto`。
- 不修改源码和策略逻辑；只同步本轮交接记录。

### Multi Agent Capability Review

- Coordinator Agent：适合定义每轮目标、范围、禁止触碰区域、验收标准，并维护 `task_plan.md`、`progress.md` 与 `.codex/PROJECT_CONTEXT.md`。
- Quant Research Agent：适合检查因子、风险贡献、AI 供应链暴露、摘要关键数字与策略假设，避免把解释误当交易信号。
- Data Pipeline Agent：适合检查市值档、行情新鲜度、缓存/降级状态和只读数据边界，不触碰密钥与交易端。
- Dashboard/Product Agent：适合检查 Dashboard 文案、页面解释、模拟盘状态、研究摘要和用户可复制内容是否清楚。
- QA/Reviewer Agent：适合执行本地 QA 汇总、关键数字回归、旧格式 fixture 验证、正式产物 hash 守门，并把结果写入 `/tmp` 摘要。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/run_local_qa_checks.py scripts/validate_research_brief_metrics.py scripts/validate_research_brief_sync.py scripts/export_research_brief_markdown.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行正式 Dashboard 重建：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.63`。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok`，包含摘要同步、关键数字回归、Markdown 导出、旧格式 fixture 和临时 Dashboard fixture。
- 本轮正式 Dashboard hash 更新为 `1156b60d4f3c441f6766fe5746ee2f099acfb929d0e834a9c05e39b6ac4ec268`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 保持 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`；`data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。
- 市值档未改：`data/model_portfolio_market_2026-06-08.csv` hash 保持 `e79fe75297be6c243a995bc51e29decfefc979a56d95fea0a359a0a14f750243`。
- QA 摘要输出：`/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`。

### Files Changed

- `dashboard/index.html`
- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`
- `progress.md`
- `.codex/PROJECT_CONTEXT.md`

### Next Loop Recommendation

- 下一轮最有价值的多 Agent 用法，是让 QA/Reviewer 先读取 `/tmp/tw_quant_local_qa_summary.json` 做机器汇总，再由 Quant/Dashboard 分别判断是否需要新增趋势对比或页面关键文案回归。
- 若要更新到 2026-06-16 或之后的行情，需要另起 Data Pipeline 轮次，先生成新的只读市值档，再重建 Dashboard；不要把本轮离线重建误认为已拉取最新市场行情。

## 2026-06-16 Data Pipeline 纠错：6/16 市值档未落地

### Session Goal

回应“今天已经 6 月 16 号，为什么仍用 6 月 8 号市值档”，核实本地最新市值档与可用行情源，并恢复失败尝试后的正式产物状态。

### Findings

- 本地 `data/` 里当前最新正式市值档仍是 `data/model_portfolio_market_2026-06-08.csv`，没有 `2026-06-16` 市值档。
- 之前 Dashboard 使用 6/8，是因为只做了保守离线重建，没有先启动 Data Pipeline 更新市值档；这个判断过于保守。
- `2026-06-16 10:22 CST` 仍属于盘中时段，若要当天更新，应生成 `2026-06-16_intraday` 盘中暂估档；收盘定稿需等收盘后再跑 `close`。
- 尝试运行 `--update-daily-market --market-date 2026-06-16 --market-mode intraday`，但当前 shell 缺少 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY` 环境变量；按安全规则没有读取 `.shioaji.local.env`。
- QVeris/EODHD 对 `0050.TW` 查询 `2026-06-16` 日线返回空结果；该工具是 EOD 日线，不适合作为盘中即时价来源。
- 失败的 Shioaji 尝试曾把 `data/model_portfolio_latest.csv` 写成 `not_generated` 状态；已用 `data/model_portfolio_2026-06-03.csv` 恢复，并重新以 6/8 市值档重建正式 Dashboard。

### Verification Log

- 已恢复并重建正式 Dashboard：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate`，结果成功，`real 15.78`。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok`。
- 恢复后 `dashboard/index.html` hash 为 `c7b1449c9877460b5107bb79e4553a2a089bd9cfbd50a6f14160c1659236cb74`。
- `data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` hash 均为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`。
- 正式模拟盘 CSV 未改：`data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`；`data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。

### Next Loop Recommendation

- 若要真正更新到 2026-06-16 盘中，需要用户先在当前 shell 提供 Shioaji 环境变量，然后运行只读 `--update-daily-market --market-mode intraday`。
- 若要 2026-06-16 收盘定稿，应等 EODHD/TWSE 收盘日线可用后，再生成 `data/model_portfolio_market_2026-06-16.csv` 并重建 Dashboard。

## 2026-06-16 Shioaji 盘中每日更新落地

### Session Goal

按用户确认的 Shioaji 只读行情能力，生成 2026-06-16 盘中市值档，重建 Dashboard，并同步研究摘要与 QA。

### Scope

- 使用 `.shioaji.local.env` 仅为当前命令提供 Shioaji 环境变量；不打印、不记录、不提交任何密钥。
- 只执行 `--update-daily-market --market-mode intraday` 读取行情，不执行 `--execute-simulated-trades`，不调用下单、改单或撤单。
- 使用 `data/simulated_positions_latest.csv` 作为当前模拟持仓，避免回退到初始建仓单。

### Actions

- 已运行 Shioaji 只读盘中更新，生成 `data/model_portfolio_market_2026-06-16_intraday.csv` 与 summary。
- 已重建正式 Dashboard，并显示 `2026-06-16T10:28:34` 与“盘中暂估”。
- 已同步 iCloud Obsidian 项目卡片的 Dashboard 研究摘要为 2026-06-16 盘中口径。
- 已调整 `scripts/validate_research_brief_metrics.py`，让关键数字检查同时支持“已转观察”和“待确认调仓”两种正常状态。
- 已调整 `scripts/validate_research_brief_sync.py`，移除对旧标题日期 `2026-06-15` 的硬编码。

### Verification Log

- Shioaji 更新命令成功，`real 31.05`，只读行情会话连线成功。
- `data/model_portfolio_market_2026-06-16_intraday_summary.txt`：`quote_count=15`、`missing_count=0`、`current_market_value=369609.09`、`unrealized_pnl=4445.20`、`unrealized_pnl_pct=0.012173`。
- Dashboard 命中 `2026-06-16T10:28:34`、`盘中暂估`、`data/model_portfolio_market_2026-06-16_intraday.csv`。
- 已执行：`./.venv/bin/python -m py_compile scripts/validate_research_brief_metrics.py scripts/run_local_qa_checks.py scripts/validate_research_brief_sync.py scripts/export_research_brief_markdown.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok`。
- 产物 hash：`dashboard/index.html` 为 `e8469c9af1a9bf49e955ce270302ef18ea98e43e4b419853c57bb4b7a5ddeae0`；`data/model_portfolio_market_2026-06-16_intraday.csv` 为 `8b4eb7318c5adb8a28282e9dc7ef3936f4dac990038a5f78d2b9c3f44b5a995c`。
- 模拟盘成交/持仓未落账：`data/simulated_trades_2026-06-08.csv` hash 保持 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`，`data/simulated_positions_latest.csv` hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81`。

### Risk / Follow-up

- 本轮是 2026-06-16 盘中暂估，不是收盘定稿。
- 首页重点已前移：`今日持仓与收盘盈亏`、`模拟盘调仓确认`、`策略监控与建议单` 现在位于图表和回测之前，打开 Dashboard 更先看到关键动作。
- `scripts/run_local_qa_checks.py` 已改成自动抓取最新 `model_portfolio_market_*.csv` 作为正式产物监控，不再固定停在 `2026-06-08`。
- `scripts/serve_dashboard.py` 与 `render.yaml` 已补上，Dashboard 可以用标准库 Web 服务挂出去；若公开部署，建议启用基本认证。

## 2026-06-16 Dashboard 首屏重点与公网读取

### Session Goal

把 Dashboard 里最重要的信息前移到首屏，同时补一个可公开部署的静态服务入口，让别的设备可以随时读取。

### Actions

- 将 `今日持仓与收盘盈亏`、`模拟盘调仓确认`、`策略监控与建议单` 移到 Dashboard 前半段，放在图表与长说明之前。
- 新增 `scripts/serve_dashboard.py`，使用标准库提供 `/`、`/healthz` 和静态页面读取。
- 新增 `render.yaml`，给 Render Web Service 提供部署蓝图。
- README 新增公网读取说明与可选基本认证配置。
- `scripts/run_local_qa_checks.py` 改为自动选取最新 `model_portfolio_market_*.csv`。

### Verification Log

- 已执行 `./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/run_local_qa_checks.py scripts/serve_dashboard.py scripts/validate_research_brief_metrics.py scripts/validate_research_brief_sync.py scripts/export_research_brief_markdown.py scripts/validate_legacy_trade_batch_status.py`，结果通过。
- 已执行 `./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-16_intraday.csv --model-method multi-factor-shrink --ai-tilt moderate --model-execution-orders data/simulated_positions_latest.csv --update-daily-market --market-date 2026-06-16 --market-mode intraday`，结果成功。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py`，结果输出 `local_qa_checks_ok`；正式产物监控已改为最新市值档。
- 已本地启动 `scripts/serve_dashboard.py`，`/healthz` 返回 `ok`，`/` 可直接读取 `dashboard/index.html`。
- 当前正式状态：`dashboard/index.html` hash `e8469c9af1a9bf49e955ce270302ef18ea98e43e4b419853c57bb4b7a5ddeae0`；`data/model_portfolio_market_2026-06-16_intraday.csv` hash `8b4eb7318c5adb8a28282e9dc7ef3936f4dac990038a5f78d2b9c3f44b5a995c`。
- 已调整小屏表格：`metric-table` 与 `compact-table` 在手机宽度下改为可横向滚动，并避免中文名称逐字断行；页面截图里 00713 / 00881 / 00919 一类名称不再被压成竖排。

### Next Loop Recommendation

- 下一轮可以继续把首屏再压缩成更像“工作台”的布局，例如把最新持仓、待确认调仓、关键摘要做成上方三块，再把较长图表留在下半屏。
- 如果要真正外网发布，建议把 Render 部署先走一次真实发布，再决定是否需要更严格的密码或来源限制。

## 2026-06-16 公网部署与每日重建

### Session Goal

把 Dashboard 准备成可公网访问的页面，并让服务本身每天固定用公开收盘价重建一次，不再依赖 Shioaji 密钥。

### Actions

- `src/risk_dashboard.py` 新增 `--market-source public-close`，公开收盘重建会优先使用最新已生成的市值檔，不再继续固定落到旧的 2026-06-08 口径。
- `scripts/serve_dashboard.py` 改成带后台定时重建的 Web 服务：启动即提供页面，同时按固定时间再跑一次重建命令。
- `render.yaml` 补入时区、每日重建时间与默认重建命令，便于直接发布到 Render。
- README 增加公开收盘重建与公网服务说明。
- 为避免污染数据目录，验证后清理了临时生成的 `data/model_portfolio_market_2024-06-28.csv`。

### Verification Log

- 已执行：`./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py`，结果通过。
- 已执行：`./.venv/bin/python scripts/run_local_qa_checks.py --skip-dashboard-fixture`，结果输出 `local_qa_checks_ok`。
- 已执行：`./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2024-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close --output /tmp/tw_quant_public_close.html --model-output /tmp/tw_quant_public_close.csv`，结果成功生成临时 Dashboard。
- 已本地启动 `scripts/serve_dashboard.py`，后台重建命令成功执行，`/healthz` 与 `/` 都正常返回。
- 临时生成的公开收盘市值檔已删除，避免影响后续最新市值档选择。

### Next Loop Recommendation

- 下一轮可以直接走真实 Render 发布，然后再看是否需要更细的公网访问控制或更紧的重建时间窗。

## 2026-06-17 第二十三轮 公网免费实例上线

### Session Goal

在不补卡的前提下，把 Dashboard 先用 Render 免费实例公开上线，保留每日固定重建能力。

### Actions

- 将 Render 服务实例切换为 `Free`，避开 `Add Card` 门槛。
- 重新提交 `futienchun-com-dashboard` Web Service 创建。
- 通过公开地址确认服务已可访问。

### Current State

- 公网地址已可用：`https://futienchun-com-dashboard.onrender.com/`
- 服务标题显示为 `【Codex】台灣股市投資量化模型`。
- 免费实例存在冷启动与睡眠特性，但可先满足公网读取需求。

### Verification Log

- 已确认 Render Web Service 创建成功，服务 ID 为 `srv-d8onljk8aovs7385cqo0`。
- 已确认公开首页可访问，浏览器标题返回 `【Codex】台灣股市投資量化模型`。
- 已确认健康检查端点返回 `200`。
- 已确认首页内容会在免费实例冷启动后恢复为正式 Dashboard。

### Files Changed

- `progress.md`
- `findings.md`
- `task_plan.md`
- `.codex/PROJECT_CONTEXT.md`

### Loop Status

- 第二十二轮部署目标已完成。
- 目前公网版本已先用免费实例上线，后续只需视稳定性决定是否补卡升级。

## 2026-06-17 第二十四轮 多因子框架比较脚本

### Session Goal

把“旧 4 因子 vs 新扩展多因子框架”的比较做成可复跑、只读、可交接的验证入口。

### Actions

- 新增 `scripts/compare_multi_factor_profiles.py`，只读加载 `src/risk_dashboard.py`、资产池和离线缓存，比较旧 4 因子与新扩展框架的模型盘目标权重。
- README 补充比较脚本用法与 `/tmp` 输出路径说明。
- 比较脚本默认输出 Markdown 与 JSON 摘要，便于人工复核与机器读取。

### Verification Log

- 已执行 `./.venv/bin/python -m py_compile scripts/compare_multi_factor_profiles.py`，结果通过。
- 已执行 `./.venv/bin/python scripts/compare_multi_factor_profiles.py`，结果输出 `factor_profile_compare_ok`。
- 已确认比较摘要写入 `/tmp/tw_quant_factor_profile_compare.md` 与 `/tmp/tw_quant_factor_profile_compare.json`。
- 已确认旧 4 因子 AI 群组权重为 `0.33000000`，新扩展框架 AI 群组权重为 `0.34231806`，仍在当前 `moderate` 上限内。
- 已确认本轮未覆盖正式 `dashboard/index.html`、正式模型盘 CSV 或模拟盘 CSV。

### Next Loop Recommendation

- 下一轮可把这个比较脚本纳入可选 QA 分支，或进一步补上旧/新框架的集中度、行业暴露与 Top 权重变化摘要。

## 2026-06-17 第二十五轮 多因子结构化差异摘要

### Session Goal

把旧 4 因子与新扩展框架的比较，从“个股权重差异”升级成“结构化组合差异摘要”。

### Actions

- 扩展 `scripts/compare_multi_factor_profiles.py`，新增集中度、权重变化最大标的、行业暴露变化、主题暴露变化、AI / 非 AI 暴露变化。
- README 补充比较脚本新增输出说明。

### Verification Log

- 已执行 `./.venv/bin/python -m py_compile scripts/compare_multi_factor_profiles.py`，结果通过。
- 已执行 `./.venv/bin/python scripts/compare_multi_factor_profiles.py`，结果输出 `factor_profile_compare_ok`。
- 已确认 `/tmp/tw_quant_factor_profile_compare.md` 包含“集中度变化”“权重变化最大标的”“行业暴露变化”“主题暴露变化”“AI / 非 AI 暴露变化”五个新摘要区块。
- 已确认新扩展框架相较旧 4 因子：HHI 从 `0.07919146` 降到 `0.07721507`，有效持仓数从 `12.6276` 升到 `12.9508`，前三大权重合计从 `0.31167766` 降到 `0.28972039`。
- 已确认当前权重变化最大的标的是 `00713`、`2303`、`2454`、`00881`、`2881`。
- 已确认本轮仍未覆盖正式 Dashboard、正式模型盘 CSV 或模拟盘 CSV。

### Next Loop Recommendation

- 下一轮可继续把这些结构化摘要接入可选 QA 分支，或再加一层“风险贡献变化”而不只是权重暴露变化。

## 2026-06-17 第二十六轮 多因子风险贡献差异摘要

### Session Goal

把旧 4 因子与新扩展框架的比较，从“权重和暴露变化”补齐到“风险贡献变化”。

### Actions

- 扩展 `scripts/compare_multi_factor_profiles.py`，新增行业、主题、AI / 非 AI 的风险贡献差异摘要。
- README 补充“风险贡献变化”已纳入比较脚本输出。

### Verification Log

- 已执行 `./.venv/bin/python -m py_compile scripts/compare_multi_factor_profiles.py`，结果通过。
- 已执行 `./.venv/bin/python scripts/compare_multi_factor_profiles.py`，结果输出 `factor_profile_compare_ok`。
- 已确认 `/tmp/tw_quant_factor_profile_compare.md` 现包含“行业风险贡献变化”“主题风险贡献变化”“AI / 非 AI 风险贡献变化”三个新区块。
- 已确认当前 AI 主题风险贡献从 `0.484916` 升到 `0.498265`，非 AI 风险贡献从 `0.515084` 降到 `0.501735`。
- 已确认当前行业风险贡献变化较大的方向包括 `半导体/IC设计` 上升、`科技/5G ETF` 下降、`低波高息ETF` 下降。
- 已确认本轮仍未覆盖正式 Dashboard、正式模型盘 CSV 或模拟盘 CSV。

### Next Loop Recommendation

- 下一轮最自然的方向是把这个比较脚本接入可选 QA 分支，或继续补“压力情境变化”与“相关性重叠变化”。

## 2026-06-17 第二十七轮 多因子压力情境与重叠摘要

### Session Goal

把旧 4 因子与新扩展框架的比较，补成“压力情境变化 + 高相关重叠变化”的完整基线。

### Actions

- 扩展 `scripts/compare_multi_factor_profiles.py`，新增压力情境变化与高相关重叠变化。
- README 补充比较脚本输出范围，纳入压力情境与高相关重叠。

### Verification Log

- 已执行 `./.venv/bin/python -m py_compile scripts/compare_multi_factor_profiles.py`，结果通过。
- 已执行 `./.venv/bin/python scripts/compare_multi_factor_profiles.py`，结果输出 `factor_profile_compare_ok`。
- 已确认 `/tmp/tw_quant_factor_profile_compare.md` 现包含“压力情境变化”“高相关重叠变化”两个新区块。
- 已确认旧 4 因子压力估计损失为 `-0.202641`，新扩展框架为 `-0.203092`，变化 `-0.000452`。
- 已确认两版框架的最高相关配对均为 `006208 / 00881`，相关性 `0.9354`，高相关配对数均为 `14`。
- 已确认本轮仍未覆盖正式 Dashboard、正式模型盘 CSV 或模拟盘 CSV。

### Next Loop Recommendation

- 下一轮可以把这份比较脚本接入可选 QA 分支，或把同样口径直接摘要到 Dashboard 的研究说明区。
