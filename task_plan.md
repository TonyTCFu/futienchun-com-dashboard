# Loop Engineering 多 Agent 工作计划

## Goal

为“台股_稳健投资组合量化模型构建”建立可持续的多 Agent 协同工作机制，并用 Loop Engineering 方法持续推进项目：每轮都有目标、基线、执行、度量、复核和交接。

## Current Status

| Phase | Status | Owner | Deliverable |
| --- | --- | --- | --- |
| 0. 环境与上下文读取 | complete | Coordinator | 已读取 README、PROJECT_CONTEXT、目录结构、关键 CLI 参数 |
| 1. 协作底座建立 | complete | Coordinator | `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md` |
| 2. 多 Agent 蓝图 | complete | Coordinator | 角色、职责、质量闸门、并行规则 |
| 3. 基线与指标设定 | complete | QA/Reviewer | 当前运行命令、验证命令、性能/状态指标 |
| 4. 第一轮项目审计 | complete | Quant/Data/Dashboard Agents | 策略、数据、安全、Dashboard 缺口 |
| 5. 第一轮改进执行 | complete | Coordinator | 修复无模型盘 Dashboard 冒烟失败 |
| 6. 验证与交接 | complete | Coordinator + QA | 验证记录、稳定结论、PROJECT_CONTEXT 更新 |
| 7. 第三轮性能优化 | complete | Coordinator + QA | `project_capped_simplex()` 提前停止，完整复跑从 28.60 秒降至 16.00 秒 |
| 8. 第四轮模拟盘幂等性验证 | complete | Coordinator + QA | 新增临时模拟成交/持仓输出参数，验证同日重复落账新增 0 笔 |
| 9. 第五轮 Dashboard 报告解释增强 | complete | Dashboard/Product + QA | 区分页面确认、脚本落账与券商真实订单；正式 Dashboard 已重建 |
| 10. 第六轮风险归因与调仓摘要 | complete | Quant + Dashboard/Product + QA | 新增 Dashboard 摘要区，解释主要风险、压力情境、调仓原因与持仓状态 |
| 11. 第七轮模拟盘稳定 trade_id | complete | Coordinator + QA | 模拟建议单与成交 CSV 新增稳定 `trade_id`，Dashboard 页面确认改用单号追踪 |
| 12. 第八轮显式分批 batch_seq | complete | Coordinator + QA | 新增 `--simulated-trade-batch-seq` 显式分批闸门，验证 `01` 幂等与 `02` 可分批且可重复 |
| 13. 第九轮行业/AI 风险归因 | complete | Quant + Dashboard/Product + QA | Dashboard 新增行业、主题与 AI 供应链群组风险归因 |
| 14. 第十轮批次状态小结 | complete | Dashboard/Product + QA | Dashboard 新增模拟盘批次状态小结，显示目前批次、已写入本地模拟成交 CSV 的批次、旧格式记录与待确认状态 |
| 15. 第十一轮研究报告摘要 | complete | Quant + Dashboard/Product + QA | Dashboard 新增可复制的群组风险研究报告摘要，复用既有归因与调仓状态，不新增交易信号 |
| 16. 第十二轮旧格式 fixture 验证 | complete | QA/Reviewer | 新增 `/tmp` 旧格式模拟成交 fixture 验证脚本，确认无 `trade_id` 成交显示为“舊格式 2 筆”而非 `批次 01` |
| 17. 第十三轮 Obsidian 研究记录同步 | complete | Coordinator + QA | 已把 Dashboard 群组风险研究摘要同步到 iCloud Obsidian 项目卡片 |
| 18. 第十四轮研究摘要同步检查 | complete | QA/Reviewer | 新增只读检查脚本，确认正式 Dashboard 研究摘要已同步到 Obsidian 项目卡片 |
| 19. 第十五轮 Markdown 摘要预览导出 | complete | Dashboard/Product + QA | 新增 `/tmp` Markdown 导出脚本，复用正式 Dashboard 研究摘要，不写正式知识库 |
| 20. 第十六轮本地 QA 汇总 | complete | QA/Reviewer | 新增本地 QA 汇总脚本，顺序运行研究摘要同步检查、Markdown 导出和旧格式 fixture 验证 |
| 21. 第十七轮固定 Dashboard Fixture 回归 | complete | QA/Reviewer | 本地 QA 汇总默认纳入旧格式 fixture 的临时 Dashboard 页面验证，并保留跳过开关 |
| 22. 第十八轮 QA 文案漂移清理 | complete | Coordinator + QA | 清理交接文档里残留的旧参数名，统一为当前默认回归与 `--skip-dashboard-fixture` 口径 |
| 23. 第十九轮 QA 摘要文件输出 | complete | QA/Reviewer | 为本地 QA 汇总新增 `/tmp` 摘要文件输出，保留默认/较快模式并记录正式产物 hash |
| 24. 第二十轮 QA JSON 摘要输出 | complete | QA/Reviewer | 为本地 QA 汇总新增机器可读 JSON 摘要，便于自动巡检与多 agent 汇总 |
| 25. 第二十一轮关键数字回归检查 | complete | QA/Reviewer | 新增研究摘要关键数字回归检查，并接入本地 QA 汇总 |
| 26. 第二十二轮公网部署与每日重建 | complete | Coordinator + Dashboard/Product + Data Pipeline | 将 Dashboard 挂到公网，并按固定时间自动用公开收盘价重建 |
| 27. 第二十三轮公网免费实例上线 | complete | Coordinator + Dashboard/Product | 以免费实例公开上线 Dashboard，先满足公网读取，再视稳定性决定是否升级 |
| 28. 每日更新恢复与缓存版本验收 | complete | Coordinator + QA | 已恢复 `dashboard` 自动化；公网首页提供内容版本与缓存验证端点 |

## Team Blueprint

| Agent | Role | Scope | Default Output |
| --- | --- | --- | --- |
| Coordinator | 主协调 | 目标、范围、计划、合并、交付 | 计划更新与最终说明 |
| Quant Research Agent | 量化研究 | 因子、风险模型、回测假设、AI tilt | 策略发现与风险说明 |
| Data Pipeline Agent | 数据管线 | TWSE/Shioaji/QVeris、缓存、市值档 | 数据状态与降级策略 |
| Risk Control Agent | 风控审查 | 单一资产上限、AI 群组上限、现金池、最小交易日、回撤降级 | 风控闸门清单 |
| Dashboard/Product Agent | 仪表盘体验 | Dashboard 文案、结构、使用路径 | 用户可见改进建议 |
| QA/Reviewer Agent | 验证复核 | 编译、冒烟、回归风险、文档同步 | 验证结果与风险清单 |

## Loop Metrics

默认每轮至少记录以下指标：

- Dashboard 是否可成功生成。
- `src/risk_dashboard.py` 是否通过 Python 编译。
- 短区间 `--offline-cache` 是否成功。
- 短区间 `--model-portfolio` 是否成功。
- 完整区间重建耗时，如执行。
- 当前 Dashboard 对应行情日期和市值档。
- 模拟持仓是否优先读取 `data/simulated_positions_latest.csv`。
- 是否触碰敏感配置或真实交易边界。

当前建议的量化指标：

| Metric | Current Baseline | Direction | Notes |
| --- | --- | --- | --- |
| `run_total_seconds` | 16.00 秒 | lower is better | 第三轮安全优化后完整临时复跑，原基线 28.60 秒 |
| `backtest_seconds` | 15.10 秒 | lower is better | 第三轮安全优化后单独回测，原本轮实测 29.20 秒 |
| `dashboard_generated_ok` | pass | pass/fail | 临时输出 `/tmp/tw_quant_loop_perf_after.html` 成功生成 |
| `matrix_cache_hit_rate` | 待后续量测 | higher is better | `--offline-cache` 聚合矩阵缓存命中 |
| `data_freshness_date` | 2026-06-08 | newer/stable | 当前项目上下文记录市值档日期 |
| `simulated_trade_idempotency` | pass | zero duplicate | 第四轮临时路径复跑：第一次 2 笔，第二次 0 笔；成交/持仓 hash 不变 |
| `simulated_trade_id` | pass | stable/nonblank | 第七轮临时落账 2 笔均写入 `paper-...` 单号，第二次复跑仍为 2 笔、无重复 ID |
| `simulated_trade_batch_seq` | pass | explicit batch only | 第八轮验证：`01` 两次仍 2 笔；显式 `02` 后共 4 笔；第二次 `02` 仍 4 笔、无重复 ID |
| `simulated_trade_batch_summary` | pass | explanatory only | 第十轮新增 Dashboard 批次状态小结；正式旧 CSV 显示为“舊格式 2 筆”，不硬判为 `01` |
| `legacy_trade_batch_fixture` | pass | legacy only | 第十二轮脚本验证：无 `trade_id` 的 2 笔成交归为 `legacy` / “舊格式”，临时 Dashboard 不显示为 `批次 01` |
| `group_risk_attribution` | pass | explanatory only | 第九轮新增模型盘目标权重 + 收缩协方差风险贡献的行业/主题/AI 供应链归因 |
| `group_risk_research_brief` | pass | explanatory only | 第十一轮新增可复制研究摘要；正式 AI 供应链权重 33.00%、风险贡献 48.49%、风险-权重差 +15.49% |
| `obsidian_research_sync` | pass | documented | 第十三轮同步至 iCloud Obsidian `台股量化基金.md`，未改 Dashboard/正式 CSV |
| `research_brief_sync_check` | pass | read-only | 第十四轮新增 `scripts/validate_research_brief_sync.py`，只读检查 Dashboard 摘要与 Obsidian 卡片一致 |
| `research_brief_markdown_export` | pass | tmp only | 第十五轮新增 `scripts/export_research_brief_markdown.py`，默认输出 `/tmp/tw_quant_research_brief.md` |
| `local_qa_checks` | pass | aggregated | 第十六轮新增 `scripts/run_local_qa_checks.py`，顺序运行本地验证脚本并确认正式产物 hash 不变 |
| `local_qa_dashboard_fixture_default` | pass | aggregated | 第十七轮把旧格式 fixture 的临时 Dashboard 页面验证纳入本地 QA 默认回归 |
| `qa_doc_flag_consistency` | pass | documented | 第十八轮清理旧参数名残留，统一为默认回归与 `--skip-dashboard-fixture` |
| `local_qa_summary_output` | pass | tmp only | 第十九轮新增 `/tmp` QA 摘要输出，记录模式、结果与正式产物 SHA-256 |
| `local_qa_summary_json_output` | pass | tmp only | 第二十轮新增 `/tmp` JSON 摘要输出，记录模式、结果与正式产物 SHA-256 |
| `research_brief_metric_regression` | pass | read-only | 第二十一轮把 AI 权重、风险贡献、风险-权重差与摘要内的本日调仓笔数做成显式回归断言 |
| `model_weight_sum` | 100% | equals 100% | 模型目标权重合计 |
| `max_single_weight` | 25% 上限 | <= 25% | 单一资产目标权重上限 |

## Constraints

- 不读取 `.env`、`.shioaji.local.env`、`.shioaji.runtime/` 内容。
- 不执行真实下单、改单、撤单。
- 不默认新增依赖。
- 不做大规模重构；每轮只做一个可验证目标。
- 非 Git 仓库，不能依赖 git 分支、提交或 reset 回滚。

## Risk Gates

| Gate | Rule |
| --- | --- |
| 实盘闸门 | 任何新增 Shioaji 下单、改单、撤单、账户交易端调用，必须停止并请求确认 |
| 凭证闸门 | 禁止读取、打印、提交 `.env`、`.shioaji.local.env`、`.shioaji.runtime/`、Token、Secret |
| 数据闸门 | `quote_status` 缺失、共同交易日少于 60、数据口径混用未标记时，不得生成可执行建议 |
| 策略闸门 | AI tilt 不得突破群组上限；单一资产不得突破 25%；基本面因子未有稳定数据源前不得并入正式权重 |
| 模拟盘闸门 | `--execute-simulated-trades` 只能写本地模拟成交和持仓 CSV；同日重复落账必须保持幂等 |
| 回测闸门 | 滚动回测不足时只能标记未执行，不能把单期优化结果包装成回测结论 |

## Immediate Next Steps

1. 完成协作底座文件创建。
2. 汇总后台 Agent 的只读侦察结果。
3. 第一轮已完成：修复无 `--model-portfolio` 时 Dashboard 脚本变量未赋值的问题。
4. 第二轮已完成：建立完整复跑计时基线，拆解 `backtest_seconds` 与 `run_total_seconds`。
5. 第三轮已完成：优化 capped simplex 投影提前停止，保留策略结果一致性。
6. 第四轮已完成：模拟盘幂等性验证通过，并支持临时输出路径演练。
7. 第五轮已完成：Dashboard 报告解释增强，正式 `dashboard/index.html` 已重建。
8. 第六轮已完成：Dashboard 新增“本轮风险归因与调仓摘要”与持仓/调仓解释，正式 `dashboard/index.html` 已重建。
9. 第七轮已完成：模拟盘建议单与成交 CSV 新增稳定 `trade_id`；Dashboard 页面确认状态改用 `trade_id`，旧 CSV 仍用 legacy key 兼容去重。
10. 第八轮已完成：`--simulated-trade-batch-seq` 接入主流程；默认 `01` 保持幂等，显式 `02/03` 才视为人工确认的同日分批。
11. 第九轮已完成：Dashboard 新增行业、主题与 AI 供应链风险归因，正式 AI 供应链目标权重 33.00%、风险贡献 48.49%。
12. 第十轮已完成：Dashboard 新增模拟盘批次状态小结；正式 2026-06-08 旧格式模拟成交显示为“舊格式 2 筆”，新格式临时验证显示 `01/02` 批次。
13. 第十一轮已完成：Dashboard 新增可复制群组风险研究报告摘要，位于“本轮风险归因与调仓摘要”区块内，使用只读 textarea。
14. 第十二轮已完成：新增 `scripts/validate_legacy_trade_batch_status.py`，验证旧格式模拟成交 CSV 的 helper 与临时 Dashboard 展示。
15. 第十三轮已完成：把 Dashboard 群组风险研究摘要同步到 iCloud Obsidian 项目卡片，形成 Dashboard -> 长期研究记录闭环。
16. 第十四轮已完成：新增只读一致性检查脚本，确认正式 Dashboard 摘要已同步到 Obsidian 项目卡片。
17. 第十五轮已完成：新增 Dashboard 研究摘要的 `/tmp` Markdown 预览导出脚本。
18. 第十六轮已完成：新增本地 QA 汇总脚本，顺序运行研究摘要同步检查、Markdown 导出预览和旧格式 fixture 验证。
19. 第十七轮已完成：本地 QA 汇总默认纳入旧格式 fixture 的临时 Dashboard 页面验证，并新增 `--skip-dashboard-fixture` 作为较快检查开关。
20. 第十八轮已完成：清理交接文档里残留的旧参数名，统一为当前 QA 汇总口径。
21. 第十九轮已完成：本地 QA 汇总现可额外写出 `/tmp` 摘要文件，记录模式、结果与正式产物 SHA-256。
22. 第二十轮已完成：本地 QA 汇总现可额外写出 `/tmp` JSON 摘要，方便后续自动巡检与多 agent 汇总。
23. 我判断 QA 汇总闭环目前已够用：已有单命令执行、默认/较快双模式、人工可读 Markdown 摘要、机器可读 JSON 摘要，以及正式产物 hash 守门。
24. 第二十一轮已完成：研究摘要关键数字回归检查已接入本地 QA 汇总，默认/较快两条路径都覆盖。
25. 第二十二轮已完成：公网服务入口与每日定时重建已落地，目标是把 Dashboard 挂到公网并避免继续依赖固定旧市值档。
26. 第二十三轮已完成：公网服务已先用 Render 免费实例上线，公网地址可直接读取，后续仅需视稳定性决定是否升级付费档。
27. 若继续下一轮，建议优先扩展更多只读检查项，例如摘要趋势比较或页面关键文案回归。

## Errors Encountered

| Time | Error | Attempt | Resolution |
| --- | --- | --- | --- |
| 2026-06-14 | 项目不是 Git 仓库 | 检查 `git rev-parse` 无输出 | 不使用依赖 Git 的 autoresearch 原版流程，改用文件级 Loop Engineering |
| 2026-06-14 | 短区间离线 Dashboard 冒烟失败：`default_trade_state_json` 赋值前引用 | 运行 `--offline-cache --output /tmp/tw_quant_loop_smoke.html` | 在 `src/risk_dashboard.py` 的 HTML 生成逻辑中加入默认空状态 `{}`，重跑通过 |
| 2026-06-14 | warm start 让回测耗时降到约 14.79 秒，但 sample/shrink 净值与换手率出现小幅漂移 | 尝试用上一期权重作为下一期初始值 | 未采用该调用方式，回测仍使用默认等权初始；只保留不改变结果的投影提前停止 |
| 2026-06-14 | 临时 active-set 求解器耗时约 0.06 秒，但 sample 回测结果明显改变 | 临时脚本验证候选高速求解器 | 不纳入源码；记录为后续研究分支，正式替换前需用户确认 |
| 2026-06-14 | 临时幂等性验证第二次若不指定 `--model-execution-orders`，会重新读取正式 `data/simulated_positions_latest.csv` 并重写临时持仓 | 第二次只指定临时成交/持仓输出路径 | 第二次复跑同时指定 `--model-execution-orders /tmp/tw_quant_idempotency_positions.csv`，模拟正式流程优先读取最新模拟持仓 |
| 2026-06-14 | zsh 下 `/tmp/tw_quant_batch_seq_run*.html` 空通配符报 `no matches found` | 用 `rm -f` 清理不存在的临时文件 | 改用 `find /tmp -maxdepth 1 ... -delete` 清理临时验证文件 |
