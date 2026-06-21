# Loop Engineering Findings

## 2026-06-21 周末日更与 public-close 刷新修复

- 今日自动化正式重建成功，`dashboard/index.html` 已刷新为 `今日 Dashboard 更新日期：2026-06-21`；由于今天是周日，公开收盘价共同交易日未前进，行情/回测序列最新日期仍为 `2026-06-18`。
- 本轮 `--execute-simulated-trades` 保持幂等：新增模拟成交 `0` 笔，Dashboard 仍显示最后模拟盘执行日 `2026-06-18`、已落账模拟成交 `3` 笔，其中卖出 `3` 笔；策略监控表没有红色 `signal-pill sell` 或 `建议卖出` 残留。
- 本轮暴露并修复 `public-close` 主动刷新路径的三个问题：`months` 未绑定会导致刷新失败；刷新完整历史月份会拖慢每日自动化；用完整回测加载器判定最近月日期会被 60 日观察值门槛误伤。
- 修复后的口径：最近公开收盘日只刷新最近月份，并用各资产月资料日期交集判定；TWSE 返回“无资料”时不会覆盖既有 OK 月缓存，允许使用缓存降级。
- 今日正式市值档仍为 `data/model_portfolio_market_2026-06-18.csv`，`quote_count=15`、`missing_count=0`，快照时间更新到 `2026-06-21T22:31:58`；当前持仓市值 `NT$356,913.78`，未实现盈亏 `NT$9,817.66`。
- 本地 QA 汇总继续通过，研究摘要关键数字未漂移：`AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`。
- 提交 `7f6f47e` 已推送到 `dashboard` 与 `origin`；Render 公网首页正文第 4 轮轮询切到 `2026-06-21`，同时 `signal_sell_count=0`。后续仍应继续用首页正文判断公网是否完成切换。

## 2026-06-20 public-close 数据修复与新一轮调仓落账

- `public-close` 之所以连续两天都停在 `2026-06-16`，根因不是页面没重建，而是 `--offline-cache` 在复用不完整的 `202606` TWSE 月缓存；当时 15 檔里多档资产只到 `2026-06-02`，共同交易日被卡死。
- `src/risk_dashboard.py` 现已补上更稳的 `public-close` 行为：进入该路径时会先主动刷新 TWSE 当月公开收盘资料，再回到既有缓存/矩阵流程；矩阵缓存 key 本身就包含源文件 `mtime`，因此月缓存一更新，新矩阵会自动换 key，不需要手删缓存。
- 今天实测中，`00713` 首轮刷新曾因 TWSE `read timeout` 回退旧缓存；单独重试后成功补到 `2026-06-18`。这说明后续若再卡住，优先看“是否只剩个别标的月档没补齐”。
- 补齐 15 檔 `202606` 月缓存后，共同最新日期已推进到 `2026-06-18`；正式 Dashboard 现在显示 `行情/回测序列最新日期：2026-06-18`，不再停在 `2026-06-16`。
- 这轮推进后，回测已发生新的重新计算权重：最后回测调仓日更新为 `2026-06-17`，预计下次回测调仓为 `2026-06-26`，距下次还差 `6` 个共同交易日。
- 本轮已新增本地模拟盘执行落账 `3` 笔：`2317 卖出 7 股`、`2881 卖出 48 股`、`2882 卖出 49 股`；页面“调仓原因”已更新为“已有 3 笔本日模拟调仓转为观察”，并继续没有红色 `signal-pill sell` 残留。
- Dashboard 的过期提示逻辑也已补稳：当推算出的“预计下次回测调仓日”已经早于今天、但正式共同交易日仍未追上时，页面会降级为“待新正式行情后重算”，避免把过期日期误当当前事实。
- 研究摘要与 QA 新基线现为：`AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`；本地 QA 与 iCloud Obsidian 项目卡片都已同步。

## 2026-06-19 Dashboard 日更与 Render 延迟复核

- 今日自动化正式重建成功，`dashboard/index.html` 已刷新为 `今日 Dashboard 更新日期：2026-06-19`，并已由提交 `a02dba2` 推送到 `dashboard` 与 `origin` 两个远端。
- 当前公开收盘价路径这次仍只复用了 `data/model_portfolio_market_2026-06-16.csv`，所以“行情/回测序列最新日期”继续停在 `2026-06-16`；这是数据新鲜度限制，不是重建失败。
- 本轮真正发生变化的正式产物只有 3 个：`dashboard/index.html`、`data/model_portfolio_market_2026-06-16.csv` 与 `data/model_portfolio_market_2026-06-16_summary.txt`。差异主要是页面日期与 `quote_time` 刷新到 `2026-06-19T23:31:34`，当前持仓市值与未实现盈亏维持 `NT$366,451.18` / `NT$7,198.15`。
- `--execute-simulated-trades` 本轮继续保持幂等：Dashboard 仍显示最后模拟盘执行日 `2026-06-16`、已落账模拟成交 `2` 笔、其中卖出 `2` 笔；`2317`、`1301` 没有重新变回红色卖出建议。
- Render 这轮再次验证出“健康检查先好、正文后切”的延迟特征：`/healthz` 已返回 `HTTP/2 200`，但首页正文前 5 次轮询仍是 `2026-06-18`，第 6 次才切到 `2026-06-19`。后续公网验证必须继续分开看健康检查与正文内容。

## 2026-06-18 Dashboard 日更与 QA 基线刷新

- 今日自动化正式重建成功，`dashboard/index.html` 已刷新为 `今日 Dashboard 更新日期：2026-06-18`。
- 当前公开收盘价重建路径这次仍只把 `data/model_portfolio_market_2026-06-16.csv` 并入回测价格序列，所以“行情/回测序列最新日期”继续停在 `2026-06-16`；这是数据新鲜度限制，不是页面没更新。
- `--execute-simulated-trades` 本轮继续保持幂等：`SIMULATED_TRADES` 新增 0 笔，`data/simulated_trades_2026-06-16.csv` 仍保留既有 2 笔卖出，`data/simulated_positions_latest.csv` 更新时间刷新但持仓数仍为 15 檔。
- Dashboard“调仓与执行日历”未漂移：最后回测调仓日仍为 `2026-05-28`，预计下次回测调仓 `2026-06-19`，距下次还差 `3` 个共同交易日；最后模拟盘执行日仍为 `2026-06-16`。
- 策略监控表已再次确认没有已落账卖出仍显示红色建议卖出：`2317 鴻海` 与 `1301 台塑` 均为“观察”，并标记“本日模拟调仓已落账”。
- 本轮暴露出一个稳定维护点：研究摘要 QA 基线会随正式 Dashboard 日更而漂移。今天正式摘要关键数字已变为 `AI 供应链权重 34.61%`、`风险贡献 49.97%`、`风险-权重差 +15.37%`，因此本地 QA 与 Obsidian 同步卡片都需要一起更新，才能继续保持 `run_local_qa_checks.py` 通过。

## 2026-06-17 Dashboard 策略结论与收盘自动执行

- Dashboard 研究说明区已直接显示“策略结构变化结论”，内容来自旧 4 因子与新扩展框架的对照结果，不需要再翻其他文件才能看到结论。
- 模型盘记录已补入 `ai_tilt`，因此研究摘要会跟实际建盘参数一致，不会只停留在近似口径。
- 每日收盘后的自动重建命令已加入 `--execute-simulated-trades`，意味着重建时会顺带把本轮建议单落账到模拟盘，并刷新持仓与执行状态。
- 本轮验证使用 `/tmp` 输出，确认页面中可检索到 `策略结构变化结论`，同时模拟成交落账仍保持本地闭环，不触碰券商端。
- 页面里的“页面标记已确认”现在会把该行从待确认清单折叠，减少已确认卖出还留在建议单中的视觉误读。
- 同一 `trade_id` 现在会同步影响策略监控表与模拟盘调仓确认表，避免“已经确认但策略表还在显示建议卖出”的分裂感。
- 策略监控现在会优先读取仓库里最新的模拟成交档，不再只读当天旧档，因此已执行卖出更容易从建议单里退出。
- 本轮确认 Dashboard 之前确实存在展示口径漂移：回测/行情序列已经可并入 `2026-06-16` 市值快照，但首页仍硬写 `2026-06-02`，容易被误读为滚动回测未更新。
- 已修正首页日期为动态读取价格序列首尾日期，并把模型盘区改成同时显示“模型建仓分析区间”和“当前回测/行情序列最新日期”；这能保留 6/2 建仓模型窗口，同时明确 Dashboard 已重建到 6/16。
- `2026-06-16` 本地模拟成交已落账 2 笔：`2317 鴻海` 卖出 10 股、`1301 台塑` 卖出 53 股；再次正式重建新增 0 笔，说明模拟盘幂等防重有效。
- 当前仍需区分：历史行情缓存本体尚未证明已完整刷新到 6 月中旬；本轮完成的是把最新可用市值档并入回测价格序列并重建 Dashboard。
- 公网旧版问题已复现并修复：公开 URL 一开始仍返回旧 HTML，所以用户刷新页面仍看到红色 `建议卖出` 是真实部署滞后，不是误看。推送 `ed037d2` 到两个远端后，公网返回新版。
- 滚动回测的“日期更新”和“调仓次数增加”需要分开解释：当前回测曲线已覆盖到 `2026-06-16`，但 7 交易日调仓节奏下最后一次重新计算权重是 `2026-05-28`，因此调仓次数仍为 `74`。
- “调仓”必须拆成两个口径展示：回测调仓是模型按 7 个共同交易日重新估计权重；模拟盘执行调仓是用户/脚本已经写入本地模拟成交 CSV 的动作。`2026-06-16` 的 `2317`、`1301` 卖出应算作模拟盘执行调仓，并已显示在 Dashboard。
- 每日收盘后公网可见性不能只依赖本地重建；每日流程必须包含推送远端与抓取公开 URL 验证，否则用户可能继续看到旧 Render 实例。

## 2026-06-14 初始发现

- 项目路径：`/Users/tonyfu/Documents/稳健投资组合量化模型构建`。
- 当前项目已有 `README.md` 与 `.codex/PROJECT_CONTEXT.md`，但初始没有项目级 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`。
- 项目不是 Git 仓库；原版 autoresearch 要求 Git 分支、提交与 reset，因此不能原样使用。
- 可采用 Loop Engineering 的核心思想：目标设定、基线记录、小步实验、度量、保留/放弃、交接。
- 当前核心脚本为 `src/risk_dashboard.py`。
- 当前 Dashboard 路径为 `dashboard/index.html`。
- 默认资产池为 `config/universe_tw.csv`，包含 `sector`、`theme`、`ai_supply_chain` 字段。
- 项目安全边界已明确：只读行情、本地模拟盘、不连接券商交易端、不读取密钥。
- 常用模型方法包含 `drawdown-risk` 与 `multi-factor-shrink`。
- AI 供应链倾斜参数为 `--ai-tilt none|moderate|strong`，当前项目上下文记录使用 `moderate`。
- 模拟盘建议单落账通过 `--execute-simulated-trades` 写本地 CSV，不连接券商。
- 当前性能线索：完整 2024-01 至 2026-06 复跑约 33 秒，其中滚动回测约 27 秒。

## Skill 与 Agent 发现

- 已使用 `agent-teams-playbook` 方法定义多 Agent 协作。
- 已使用 `planning-with-files` 方法建立持久化计划文件。
- 台股/Shioaji 场景匹配 `shioaji` skill，但本项目当前默认不触碰真实交易。
- 台股分析可参考 `tw-stocker-consultant` 的数据驱动原则，但不替代本项目现有脚本。
- 原版 `autoresearch` 需要 Git 仓库，不适合作为当前直接执行机制。

## 2026-06-14 Agent 侦察汇总

- 文档/交接 Agent 确认：初始项目已有 `README.md` 与 `.codex/PROJECT_CONTEXT.md`，缺少 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`；当前已补齐。
- 工程运行 Agent 确认：主入口是 `src/risk_dashboard.py`，输出为 `dashboard/index.html`。
- 工程运行 Agent 确认：主要运行模式包括研究仪表盘、`--model-portfolio` 模拟模型盘、`--update-daily-market` 每日行情市值档；`--execute-simulated-trades` 只做本地模拟落账。
- 工程运行 Agent 确认：关键 CLI 参数包含 `--offline-cache`、`--allow-stale-cache`、`--data-source twse|shioaji|auto`、`--model-method drawdown-risk|shrink-minvar|multi-factor-shrink`、`--ai-tilt none|moderate|strong`。
- 工程运行 Agent 建议：完整复跑总耗时与滚动回测耗时应作为 Loop Engineering 的首要性能指标。
- 工程运行 Agent 建议：后续应记录 `data_freshness_date`、`dashboard_generated_ok`、`simulated_trade_idempotency`、`model_weight_sum`、`max_single_weight`。
- 量化/数据边界 Agent 确认：当前是台股稳健组合研究与 paper portfolio，不是实盘交易系统。
- 量化/数据边界 Agent 确认：`--model-portfolio`、`--update-daily-market`、`--execute-simulated-trades` 均不应连接券商交易端；源码关键词搜索未发现 `place_order/cancel_order/update_order` 等下单调用。
- 量化/数据边界 Agent 确认：数据源参数层是 `twse/shioaji/auto`；QVeris/EODHD 是项目上下文中的市值档 fallback 来源，不是主脚本 `--data-source` 选项。
- 量化/数据边界 Agent 确认：当前股票池是 15 檔人工核心资产池，不是全市场扫描；`ai_supply_chain=true` 不穿透 ETF 成分。
- 量化/数据边界 Agent 建议：增加 Risk Control Agent 与模拟盘执行 Agent 的职责边界，避免策略研究误触落账或交易端。

## 2026-06-14 第一轮 Loop 发现

- 短区间离线 Dashboard 冒烟暴露问题：不传 `--model-portfolio` 时，页面脚本仍引用 `default_trade_state_json`，但该变量只在模型盘分支内赋值。
- 最小修复：在进入 `model_portfolio` 分支前设置 `default_trade_state_json = "{}"`。
- 修复不改变策略、数据源、模拟盘落账或 Dashboard 正式产物，仅修复无模型盘页面生成路径。
- 修复后短区间离线 Dashboard 可生成到 `/tmp/tw_quant_loop_smoke.html`，输出大小约 4.95 MB。

## 2026-06-14 第二轮性能基线发现

- 完整复跑命令使用 `--offline-cache --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，并输出到 `/tmp/tw_quant_loop_perf.html` 与 `/tmp/tw_quant_loop_perf_model.csv`，未覆盖正式 Dashboard 或正式模型盘 CSV。
- 完整复跑 `run_total_seconds=28.60`，命令成功生成临时仪表盘。
- 单独量测滚动回测 `backtest_seconds=27.9764`，样本为 15 檔资产、575 个收益观察值、74 次调仓。
- cProfile 画像显示回测内 148 次 `min_variance_weights()` 几乎占满全部耗时；其中 fallback 路径 `projected_gradient_min_variance()` 与 `project_capped_simplex()` 的重复 `np.clip()` / `sum()` 是主要瓶颈。
- 当前性能优化应优先减少每次最小方差求解的迭代成本；在未做结果一致性对照前，不建议调整回测窗口、调仓间隔或策略口径来“变快”。

## 2026-06-14 第三轮性能优化发现

- 已采用安全优化：`project_capped_simplex()` 在投影权重和接近 1 时提前停止，最终仍执行 clip、sum 检查和归一化兜底。
- `min_variance_weights()` 已支持可选 `initial` 参数，但正式滚动回测仍使用默认等权初始，避免 warm start 改变 fallback 迭代收敛路径。
- 安全优化后，单独回测 `backtest_seconds` 从本轮实测基线 `29.1977` 秒降至 `15.0964` 秒，约 `1.93x` 加速。
- 完整临时复跑 `run_total_seconds` 从上一轮记录 `28.60` 秒降至 `16.00` 秒。
- 结果一致性对照通过：sample/shrink 期末净值、最大回撤、平均换手率差异均在 `1e-12` 量级；sample/shrink 当前权重最大绝对差异约 `4.7e-14`。
- warm start 临时版本虽把回测降至约 `14.79` 秒，但净值与换手率出现小幅漂移，已撤回正式回测调用。
- 临时 active-set 求解器可把单独回测降至约 `0.06` 秒，但 sample 回测结果明显改变；该方案只适合作为后续研究分支，不应直接替换正式口径。

## 2026-06-14 第四轮模拟盘幂等性发现

- 新增 `--simulated-trades-output` 与 `--simulated-positions-output`，只在 `--execute-simulated-trades` 时用于重定向模拟成交与最新持仓输出；默认行为仍写正式 `data/simulated_*`。
- `build_trade_signals()` 与 Dashboard 渲染已支持同一个临时成交输出路径，避免临时验证被正式 `data/simulated_trades_交易日.csv` 历史记录压住。
- `load_simulated_trade_keys()` 已把 `status` 做 `strip().lower()` 标准化；`write_simulated_trades()` 同次写入时会同步更新 `existing_keys`，避免同次重复 key。
- 临时幂等性闭环通过：第一次 `/tmp` 落账新增 2 笔，第二次使用同一临时成交文件并把 `--model-execution-orders` 指向临时最新持仓，新增 0 笔。
- 第二次后 `/tmp/tw_quant_idempotency_trades.csv` 行数仍为 3 行、成交记录仍为 2 笔，`duplicate_executed_keys=0`；临时成交 hash 保持 `848d7a6270868b59dc0c75c09b0fab942a3d9f95f6c31bb783c1de30dd2610c7`。
- 第二次后 `/tmp/tw_quant_idempotency_positions.csv` 与 dated positions hash 均保持 `4336a4280bc05c0a0f611cf0d7d8d25e2a657f99e56f5d8970e30d90476208aa`，确认持仓未继续减少。
- 安全边界：验证命令使用 `--offline-cache --data-source twse`，未使用 `--data-source shioaji`、非离线 `auto`、`--update-daily-market` 或任何真实交易端参数。

## 2026-06-14 第五轮 Dashboard 报告解释发现

- Dashboard 最容易误读的点是“手动订单交易”“标记已执行 / 已执行”：这些看起来像真实订单或正式 CSV 落账，但实际只是浏览器 `localStorage` 页面检查状态。
- 已把手动交易区标题改为“模拟盘调仓确认”，按钮与状态改为“页面标记已确认 / 页面已确认 / 待确认”，表格列改为“页面复核 / 脚本落账”。
- 已在策略监控区加入“訊號口徑”说明：建议买入/卖出只代表本地模拟盘待确认，不会送到券商；已落账标的会转为观察，避免重复列为待确认清单。
- 已把模型盘 footer 明确为研究用途 paper portfolio：持仓、盈亏和建议单都只属于本地模拟盘，不是券商委托状态。
- 正式 `dashboard/index.html` 已重建，新增文案在生成 HTML 中可检索；旧歧义文案 `手动订单交易`、`标记已执行`、`后续我们可以再把已执行状态落成 CSV` 已无命中。
- 验证全程使用 `--offline-cache --data-source twse`；未使用 Shioaji、`--update-daily-market` 或 `--execute-simulated-trades`。

## 2026-06-14 第六轮风险归因与调仓摘要发现

- 已新增 Dashboard 区块“本轮风险归因与调仓摘要”，位置在资产池策略说明之后、风险图表之前，先给使用者 3 个短结论：主要风险、压力情境、调仓原因。
- 摘要复用既有变量：`top_shrink_risk_index`、`shrink_rc`、`max_pair_text`、`sample_stress`、`shrink_stress`、`actionable_signals`、`settled_signal_count`，不新增模型、不改变策略或交易规则。
- 主要风险文案明确：最大风险贡献标的和最高相关资产对用于识别同源风险，不代表个股买卖建议。
- 压力情境文案改为正数损失口径：普通协方差估计损失约 19.62%，收缩协方差估计损失约 19.56%；明确不是未来预测。
- 调仓原因文案支持三种状态：有待确认单、已有本日落账转观察、完全无新触发。
- 持仓区新增“持仓状态解释”，说明当前市值/未实现盈亏来自本地模拟持仓和市值档，不是券商账户资料；持仓表和建议单不是同一件事。
- 正式 `dashboard/index.html` 已重建，新文案可检索；未使用 Shioaji、`--update-daily-market` 或 `--execute-simulated-trades`，正式模拟成交/持仓 CSV 未改。

## 2026-06-14 第七轮模拟盘稳定 trade_id 发现

- 模拟盘建议单新增稳定 `trade_id`，格式为 `paper-YYYYMMDD-symbol-action-01-digest`；digest 来自 `paper-v1`、交易日、建仓日、模型方法、标的、方向、稳定 `trigger_code` 与默认批次 `01`。
- `trade_id` 不包含 `latest_price`、`proposed_shares` 或中文 `reason`，避免行情、持仓数量或说明文案微调导致同一建议换 ID。
- 已把四类触发分支转成稳定 `trigger_code`：`market_loss_stop_25`、`cost_or_trend_stop_25`、`profit_take_hot_20`、`pullback_add_15`。
- `load_simulated_trade_keys()` 现在读取新 CSV 的 `trade_id`，同时保留 `legacy:{trade_date}:{symbol}:{action}`，旧模拟成交 CSV 没有 `trade_id` 时仍能阻止同日重复落账。
- `write_simulated_trades()` 写入新成交时会新增 `trade_id` 欄位；既有旧行若无该列，会在重写时补空值，不影响旧 CSV 读取。
- Dashboard 的“模拟盘调仓确认”待确认行新增 `data-trade-id`，页面状态 localStorage key 升级为 `risk-dashboard-manual-trades-v2-...`，状态对象按 `trade_id` 记录；`data-symbol` 仅保留作人工检查辅助。
- 临时预览 Dashboard 可看到 `单号：paper-20260608-2317-sell-01-c5ac2f144a` 与 `paper-20260608-1301-sell-01-61defce39b`；正式 Dashboard 因本日正式模拟成交已落账，当前没有待确认行，但脚本结构已升级为 v2。
- 本轮没有改变“同日同标的同方向只落账一次”的模拟盘语义；若未来要真正支持同日分批，需要另一定义 `batch_seq` 何时从 `01` 递增到 `02`。

## 2026-06-14 第八轮显式分批 batch_seq 发现

- 不采用自动递增 `batch_seq`：自动找下一批会破坏幂等性，最坏情况是同一命令重复执行不断新增 `02/03/04`。
- 新增 CLI 参数 `--simulated-trade-batch-seq`，校验规则为 `01` 到 `99`；允许输入 `1` 自动补成 `01`，拒绝 `00`、非数字与超过两位。
- 默认批次为 `01`，继续保留旧无 `trade_id` CSV 的 legacy `(trade_date, symbol, action)` 防重，避免旧资料无法识别批次时重复落账。
- 新格式 CSV 若已有 `trade_id`，不再把 legacy key 作为全局阻挡；显式 `02` 可与 `01` 同日同标的同方向共存，但第二次同样 `02` 会被相同 `trade_id` 阻挡。
- `load_simulated_trade_keys()` 已拆成 `trade_ids` 与 `legacy_keys` 两组：有 `trade_id` 的新行走精准 ID 幂等；没有 `trade_id` 的旧行才进入 legacy 保护。
- Dashboard footer 与 README 已说明：默认批次 `01` 保持幂等，只有明确使用新的模拟成交批次号才视为同日分批；分批是人为确认的第二/第三批，不是绕过重复落账保护。
- `/tmp` 验证结果：`01` 第一次生成 2 笔、第二次仍 2 笔；显式 `02` 后共 4 笔，其中 `-01-` 两笔、`-02-` 两笔；第二次同样 `02` 复跑仍 4 笔，`duplicate_trade_ids=0`。
- 正式 `dashboard/index.html` 已重建并包含默认批次说明；正式模拟成交/持仓 CSV hash 未变化。

## 2026-06-14 第九轮行业/AI 供应链风险归因发现

- 已新增解释型群组归因，不改变模型权重、回测、策略阈值、建议单或模拟盘落账逻辑。
- 归因口径：若有模型盘，使用模型盘目标权重作为群组暴露，并用收缩协方差计算风险贡献；没有模型盘时退回收缩协方差最小方差权重。
- Dashboard 新增“行业、主题与 AI 供应链风险归因”区块，位置在“本轮风险归因与调仓摘要”之后、风险图表之前。
- 新区块包含行业 Top 5、主题 Top 5 和 AI/非 AI 二元分组，展示檔数、权重、风险贡献和“风险-权重”差值。
- 正式口径下，AI 供应链直接标记标的共 5 檔，模型盘目标权重 33.00%，风险贡献 48.49%，风险贡献相对权重差 +15.49%。
- 已明确边界：群组归因只用于解释同源风险与组合暴露，不代表个股买卖建议，也不是未来报酬预测；AI 供应链只按标的本身分类，不穿透 ETF 成分。
- 正式 `dashboard/index.html` 已重建并命中新文案；模型盘 CSV 内容 hash 不变，正式模拟成交/持仓 CSV 未改。

## 2026-06-15 第十轮 Dashboard 批次状态小结发现

- 批次状态小结应是解释层，不应改变 `trade_id`、`batch_seq`、建议单触发或模拟落账语义。
- 已新增只读批次汇总：从本地模拟成交 CSV 的 `trade_id` 解析批次；没有 `trade_id` 的旧记录单独归为“舊格式”，不硬判为 `01`。
- Dashboard “模拟盘调仓确认”区块现在显示“模擬盤批次狀態小結”，包含目前批次、已写入本地模拟成交 CSV 的批次、旧格式记录与目前待确认。
- 正式 2026-06-08 模拟成交 CSV 仍是旧格式，Dashboard 显示“舊格式 2 筆”，标的为 `1301、2317`，方向为 `sell`。
- `/tmp` 临时验证确认：批次 `01` 两次保持 2 笔；显式 `02` 后共 4 笔；第二次同样 `02` 仍 4 笔，`duplicate_trade_ids=0`。
- 正式 `dashboard/index.html` 已重建；`data/model_portfolio_latest.csv` 内容 hash 不变，正式模拟成交/持仓 CSV hash 不变。
- 页面文案强调：页面确认只保存在当前浏览器，真正写入本地模拟成交 CSV 仍需执行 Python 主脚本；不代表券商成交或委托状态。

## 2026-06-15 第十一轮群组风险研究报告摘要发现

- 研究报告摘要应复用既有群组归因、相关性、压力情境和模拟盘状态，不新增模型信号、不改变权重、不改变建议单触发或模拟落账。
- Dashboard “本轮风险归因与调仓摘要”区块新增只读 `textarea`，标题为“群组风险研究报告摘要”，方便复制到报告或 Obsidian。
- 正式摘要显示：AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`，与第九轮群组归因表一致。
- 摘要边界已明确：仅用于本地模拟盘研究记录，不代表未来报酬预测、个股买卖建议、实盘订单或券商账户状态；不会新增交易信号，不会写入模拟成交 CSV，也不连接券商。
- 正式 `dashboard/index.html` 已重建；`data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 内容 hash 不变，正式模拟成交/持仓 CSV hash 不变。
- README 已补充：研究摘要复用当前权重、收缩协方差风险贡献、行业/主题/AI 供应链归因、相关性、压力情境和本地模拟盘状态。

## 2026-06-15 第十二轮旧格式 fixture 验证发现

- 新增 `scripts/validate_legacy_trade_batch_status.py`，用 `/tmp/tw_quant_legacy_trade_fixture.csv` 生成无 `trade_id` 的旧格式模拟成交 fixture，不读取或覆盖正式 `data/simulated_*`。
- 默认脚本验证 `load_simulated_trade_batch_status()`：两笔旧成交归为 `batch_seq == "legacy"`、`label == "舊格式"`、`trade_count == 2`、标的为 `1301、2317`、方向为 `sell`。
- fixture 第二笔 `status` 使用 `" executed "`，覆盖 `strip().lower()` 标准化兼容。
- 带 `--dashboard` 时会临时重建 `/tmp/tw_quant_legacy_trade_fixture_dashboard.html`，断言页面显示“暫無新格式批次”“舊格式紀錄：舊格式 2 筆”“舊成交 CSV 無 trade_id”，且不出现 `<td>批次 01</td><td>2</td>`。
- `--simulated-trades-output` 的 help 已调整为“模拟成交 CSV 路径；落账时写入，Dashboard 验证时可读取指定路径”，与当前渲染验证用途一致。
- 本轮未重建正式 Dashboard；正式 Dashboard、模型盘 CSV、正式模拟成交/持仓 CSV hash 均保持第十一轮结果不变。

## 2026-06-15 第十三轮 Obsidian 研究记录同步发现

- iCloud Obsidian 正确落点已验证为 `/Users/tonyfu/Library/Mobile Documents/iCloud~md~obsidian/Documents/AI-Knowledge-Wiki/02-The-Wiki/05-商业金融与量化交易/01-量化交易/03-策略实践/台股量化基金.md`；本机 `/Users/tonyfu/Documents/Obsidian` 与历史噪音路径未找到同名项目卡片。
- `00-索引-MOC.md` 已包含 `[[03-策略实践/台股量化基金|台股量化基金]]`，本轮无需修改索引。
- 已把 Dashboard 群组风险研究报告摘要同步到项目卡片，包含最大风险贡献、最高相关资产对、AI 供应链权重 33.00%、风险贡献 48.49%、风险-权重差 +15.49%、压力情境与模拟盘状态。
- Obsidian 卡片已同步第九至第十二轮稳定结论：群组风险归因不穿透 ETF 成分、旧格式模拟成交显示“舊格式 2 筆”、fixture 验证只写 `/tmp`。
- 本轮只改研究记录与交接文档，不改源码、不重建 Dashboard、不覆盖正式模型盘或模拟盘 CSV。

## 2026-06-15 第十四轮研究摘要同步检查发现

- 新增 `scripts/validate_research_brief_sync.py`，默认只读取正式 `dashboard/index.html` 与 iCloud Obsidian `台股量化基金.md`，不重建 Dashboard、不写入 `data/`、不触碰 Shioaji。
- 脚本会从 Dashboard 的 `research-report` 只读 textarea 抽取研究摘要，逐行确认这些摘要已存在于 Obsidian 项目卡片。
- 脚本额外检查关键边界与数字：AI 供应链权重 33.00%、风险贡献 48.49%、风险-权重差 +15.49%、旧格式模拟成交“舊格式 2 筆”、不代表未来报酬预测或券商账户状态。
- 本轮把 Dashboard -> Obsidian 的人工同步结果升级为可复跑 QA 闸门；正式 Dashboard、模型盘 CSV、模拟成交与持仓 CSV 均未改。

## 2026-06-15 第十五轮 Markdown 摘要预览导出发现

- 新增 `scripts/export_research_brief_markdown.py`，复用 `validate_research_brief_sync.extract_research_brief()` 从正式 `dashboard/index.html` 抽取 `research-report` 摘要，避免重复维护两套解析逻辑。
- 默认输出 `/tmp/tw_quant_research_brief.md`，只作为 Markdown 预览；不写入 Obsidian，不重建 Dashboard，不覆盖正式 `data/`。
- 导出内容包含来源 Dashboard、用途、研究边界和 Obsidian callout 形式的摘要，保留“不代表未来报酬预测、个股买卖建议、实盘订单或券商账户状态”的边界。
- 本轮把“复制摘要”从手动页面操作扩展为可复跑临时产物，但仍保持本地模拟盘与解释型研究边界。

## 2026-06-15 第十六轮本地 QA 汇总发现

- 新增 `scripts/run_local_qa_checks.py`，把 `validate_research_brief_sync.py`、`export_research_brief_markdown.py` 与 `validate_legacy_trade_batch_status.py` 串成一条顺序执行的本地 QA 汇总命令。
- 汇总脚本会在执行前后分别计算正式 `dashboard/index.html`、模型盘 CSV、模拟成交/持仓 CSV 与市值档的 SHA-256，确保本地 QA 检查没有改动正式产物。
- 脚本默认只生成 `/tmp/tw_quant_local_qa_research_brief.md` 与旧格式 fixture CSV；在第十六轮时，若显式启用当时的可选 Dashboard fixture 参数，才会额外跑旧格式 fixture 的临时 Dashboard 页面验证。

## 2026-06-16 第十八轮 QA 文案漂移清理发现

- 已把本地 QA 汇总相关交接文档中的旧参数名统一更新为当前口径：默认包含旧格式 fixture 的临时 Dashboard 页面验证，较快模式使用 `--skip-dashboard-fixture`。
- 本轮只清理脚本说明与交接文案，不改变 `scripts/run_local_qa_checks.py` 的当前行为，不改正式 Dashboard，不改模型盘或模拟盘 CSV。
- 本轮把第十二至第十五轮分散的验证脚本变成单一入口，降低续跑成本，同时继续守住“只读行情、本地模拟盘、正式产物不改”的边界。

## 2026-06-16 第十七轮固定 Dashboard Fixture 回归发现

- `scripts/run_local_qa_checks.py` 现已把旧格式 fixture 的临时 Dashboard 页面验证纳入默认回归，避免每次手动记得加参数才覆盖该分支。
- 为了保留较快检查路径，新增 `--skip-dashboard-fixture`，在需要快速本地检查时可跳过临时 HTML 生成，但默认仍走覆盖面更完整的回归。
- 本轮只调整 QA 汇总脚本与说明文档，不改研究摘要内容、不改正式 Dashboard、不改模型盘或模拟盘 CSV。

## 2026-06-16 第十九轮 QA 摘要文件输出发现

- 本地 QA 汇总原先只有终端单行 `local_qa_checks_ok`，续跑时若没保留终端上下文，不够适合交接与复核。
- 新增 `--summary-output`，默认把摘要写到 `/tmp/tw_quant_local_qa_summary.md`；内容包含执行时间、检查模式、Markdown 预览路径、三段检查结果和正式产物 SHA-256。
- 摘要文件只写 `/tmp`，不改正式 Dashboard、不改模型盘或模拟盘 CSV，也不改变默认/较快模式的 QA 行为。

## 2026-06-16 第二十轮 QA JSON 摘要输出发现

- 第十九轮的 Markdown 摘要更适合人看，但若要给后续 agent、脚本或自动巡检复用，仍缺一个稳定的机器可读载体。
- 新增 `--summary-json-output`，默认写 `/tmp/tw_quant_local_qa_summary.json`；内容包含时间、模式、`dashboard_fixture` 开关、Markdown/Markdown 摘要路径、三段检查结果与正式产物 hash。
- JSON 摘要和 Markdown 摘要一样只写 `/tmp`，不改正式 Dashboard、不改模型盘或模拟盘 CSV，也不改变既有 QA 检查顺序。

## 2026-06-16 第二十一轮关键数字回归检查发现

- 现有 QA 已能检查摘要存在、同步一致、可导出，但还没有把最关键的稳定数字做成显式断言。
- 新增 `scripts/validate_research_brief_metrics.py`，直接从正式 Dashboard 的 `research-report` 摘要解析并校验 4 个关键值：`AI 供应链权重 33.00%`、`风险贡献 48.49%`、`风险-权重差 +15.49%`、`已有 2 笔本日模拟调仓转为观察`。
- 该脚本只读正式 Dashboard，不重建页面、不改正式 CSV；接入 `scripts/run_local_qa_checks.py` 后，关键数字回归会成为本地 QA 汇总的默认闸门。

## 2026-06-16 第二十二轮公网部署与每日重建发现

- `src/risk_dashboard.py` 现在支持 `--market-source public-close`，会用公开收盘价重建每日市值檔，并优先读取最新已生成的 `model_portfolio_market_*.csv`，避免继续固定落到旧市值档。
- `scripts/serve_dashboard.py` 已改成“先提供首页、后台按时重建”的 Web 服务：启动时会先跑一次重建命令，之后按固定时刻继续重建。
- Render 蓝图已同步默认环境：`Asia/Shanghai`、每日 `18:30`、公开收盘重建命令，适合直接把生成后的 Dashboard 挂到公网。
- 本轮已验证：`py_compile` 通过；`scripts/run_local_qa_checks.py --skip-dashboard-fixture` 通过；`--market-source public-close` 的临时 Dashboard 成功生成；`/healthz` 与 `/` 端点正常返回。
- 本轮临时验证时写出的 `data/model_portfolio_market_2024-06-28.csv` 已清理，避免污染后续“最新市值档”选择。

## 2026-06-17 第二十三轮公网免费实例上线发现

- Render 的 Web Service 创建页支持在同一仓库下直接选择 `Free` 实例，不必先补卡才能把 Dashboard 挂到公网。
- `futienchun-com-dashboard` 已在 Render 上成功创建为 Web Service，服务 ID 为 `srv-d8onljk8aovs7385cqo0`。
- 公网地址已可访问：`https://futienchun-com-dashboard.onrender.com/`。
- 免费实例会冷启动，启动时会先显示 Render 的 loading/interstitial 页面，稍等后会恢复为正式 Dashboard。
- 健康检查端点 `https://futienchun-com-dashboard.onrender.com/healthz` 返回 `200`。
- 当前公开页标题显示为 `【Codex】台灣股市投資量化模型`，说明服务已经跑到正式 Dashboard 首页。

## 2026-06-17 第二十四轮多因子框架比较发现

- 已新增 `scripts/compare_multi_factor_profiles.py`，把“旧 4 因子 vs 新扩展多因子框架”的比较做成只读脚本，不覆盖正式 Dashboard、正式模型盘或模拟盘 CSV。
- 比较脚本默认输出 `/tmp/tw_quant_factor_profile_compare.md` 与 `/tmp/tw_quant_factor_profile_compare.json`，可直接交接给后续 agent 或人工复核。
- 脚本当前固定使用 `offline-cache + TWSE` 路径、`2026-06-03` 建仓日与 `moderate` AI 倾斜，适合作为第一轮扩因子后的稳定基线比较。
- 实测比较结果：旧 4 因子 AI 群组权重 `0.33000000`，新扩展框架 AI 群组权重 `0.34231806`，仍在 `moderate` 群组上限 `35%` 内。
- 该脚本已确认新扩展框架不是“只多写几个分数字段”，而是实际改变了目标权重结构；它适合继续扩展集中度、行业暴露和 Top 权重变化摘要。

## 2026-06-17 第二十五轮多因子结构化差异发现

- `scripts/compare_multi_factor_profiles.py` 已扩展为结构化组合差异摘要，而不只是列出几个重点标的。
- 当前比较摘要已稳定包含 5 类结构化输出：集中度变化、权重变化最大标的、行业暴露变化、主题暴露变化、AI / 非 AI 暴露变化。
- 实测结果显示，新扩展框架相对旧 4 因子更分散：HHI 从 `0.07919146` 降到 `0.07721507`，有效持仓数从 `12.6276` 升到 `12.9508`，前三大权重合计从 `0.31167766` 降到 `0.28972039`。
- 当前权重变化最大的标的是 `00713`、`2303`、`2454`、`00881`、`2881`；这说明扩因子后的结构变化并非只集中在单一 AI 标的。
- 当前行业暴露变化最大的是 `低波高息ETF`、`半导体/IC设计`、`科技/5G ETF`、`半导体/晶圆代工`、`金融`。
- 当前主题暴露变化最大的是 `low-vol-dividend`、`ai-supply-chain`、`financial`、`dividend`、`defensive`；AI 主题总权重从 `0.330000` 升到 `0.342318`，仍低于 `moderate` 上限。

## 2026-06-17 第二十六轮多因子风险贡献差异发现

- `scripts/compare_multi_factor_profiles.py` 已补齐“风险贡献变化”层，不再只比较权重和暴露结构。
- 当前比较摘要会额外输出 3 类风险贡献差异：行业风险贡献变化、主题风险贡献变化、AI / 非 AI 风险贡献变化。
- 当前 AI 主题风险贡献从 `0.484916` 升到 `0.498265`，非 AI 风险贡献从 `0.515084` 降到 `0.501735`；说明新扩展框架虽然仍受 `moderate` 上限约束，但风险更偏向 AI 主题。
- 当前行业风险贡献变化较大的方向包括：`半导体/IC设计` 上升、`科技/5G ETF` 下降、`低波高息ETF` 下降、`半导体/晶圆代工` 上升、`金融` 上升。
- 当前主题风险贡献变化较大的方向包括：`ai-supply-chain` 上升、`low-vol-dividend` 下降、`financial` 上升、`dividend` 小幅上升、`defensive` 小幅下降。

## 2026-06-17 第二十七轮多因子压力情境与重叠发现

- `scripts/compare_multi_factor_profiles.py` 已补齐压力情境变化与高相关重叠变化，不再只看权重/暴露/风险贡献。
- 当前比较摘要会额外输出两类稳定指标：压力情境损失变化与高相关配对变化。
- 当前旧 4 因子压力估计损失为 `-0.202641`，新扩展框架为 `-0.203092`，变化 `-0.000452`，表示新框架在该压力设定下略差，但差距很小。
- 两版框架的高相关配对数均为 `14`，最高相关配对均为 `006208 / 00881`，相关性 `0.9354`，平均配对相关性均为 `0.4942`，说明这组资产的核心共振风险并未因扩因子而改变。
- 该结果提醒我们：扩因子更像是在调权重与群组风险，而不是自动消除高相关资产之间的结构性重叠；这点对后续策略解释很重要。
