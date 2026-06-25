# 稳健投资组合量化模型构建 项目上下文

## 一、项目目标

本项目是稳健型量化基金和台股组合管理系统。核心目标是识别资产共同风险，比较普通样本协方差与稳健协方差估计对组合权重、风险贡献、回撤和压力情境的影响。

## 二、当前状态

- 已完成静态风险仪表盘 MVP。
- 支持台股与台股 ETF 资产池。
- 支持 TWSE 与 Shioaji 两种数据源。
- 已安装 QVeris CLI：`qveris/0.6.0`，可直接用 `qveris` 命令；已确认 `eodhd.eod_historical_data.retrieve.v1.a43f3b91` 可查询台股日线，例如 `0050.TW`。
- 已包含滚动再平衡回测、手动模型盘、策略监控与建议单。
- 每日行情更新流程只读行情，不自动下单，不连接券商交易端。
- 2026-06-05 收盘市值檔已生成：`data/model_portfolio_market_2026-06-05.csv`，共 15 檔，`quote_status=ready`。其中 14 檔来自 QVeris/EODHD `qveris_eodhd_close`，`00881` 因 QVeris 无资料，已用 TWSE 官方月资料补 `twse_close_fallback`，收盘价 54.10。
- 2026-06-05 市值檔统计：当前持仓市值 `NT$366,794.74`，未实现盈亏 `NT$-6,163.68`。
- 已修复离线重建卡顿：`--offline-cache` 会生成并复用 `data/matrix_cache/` 聚合行情矩阵，源 JSON 缓存变动后会自动生成新矩阵；首次聚合时仍会逐档读取 `data/cache/`，但会输出进度。
- `dashboard/index.html` 已于 2026-06-06 重建为 2026-06-05 收盘市值口径，已套用 `data/model_portfolio_market_2026-06-05.csv`。
- 2026-06-08 收盘市值檔已生成：`data/model_portfolio_market_2026-06-08.csv`，共 15 檔，`quote_status=ready`。其中 14 檔来自 QVeris/EODHD，`00881` 用 TWSE 官方月资料补 `twse_close_fallback`，收盘价 52.40。
- 2026-06-08 市值檔统计：当前持仓市值 `NT$354,011.64`，未实现盈亏 `NT$-18,946.78`。已修正建议单连续天数逻辑，最近每日市值檔会纳入 `persistence_days`。
- 2026-06-08 已执行模拟成交落账：`data/simulated_trades_2026-06-08.csv` 记录卖出 `2317 鴻海` 13 股、`1301 台塑` 71 股；`data/simulated_positions_latest.csv` 已更新为 `2317` 剩 37 股、`1301` 剩 210 股。Dashboard 已重建，当前没有待确认的模拟调仓单。
- 2026-06-14 已为模拟盘建议单与新模拟成交 CSV 加入稳定 `trade_id`：单号由交易日、建仓日、模型方法、标的、方向、稳定 `trigger_code` 与批次 `01` 生成，不包含价格、股数、中文原因或敏感凭证。旧成交 CSV 没有 `trade_id` 时，仍用交易日、标的和方向做兼容去重。
- 2026-06-14 已接入显式分批 `batch_seq`：默认批次 `01` 保持幂等；只有明确传 `--simulated-trade-batch-seq 02`、`03` 等新批次时，才视为人为确认的同日分批模拟成交。旧无 `trade_id` CSV 仍保守使用交易日、标的和方向防重。
- 2026-06-14 已完成行业/主题/AI 供应链风险归因：Dashboard 使用模型盘目标权重与收缩协方差风险贡献解释群组暴露。正式口径下 AI 供应链 5 檔，权重 33.00%，风险贡献 48.49%，不穿透 ETF 成分。
- 2026-06-15 已完成 Dashboard 批次状态小结：在“模拟盘调仓确认”区块显示目前批次、已写入本地模拟成交 CSV 的批次、旧格式记录与目前待确认。旧无 `trade_id` 的正式 2026-06-08 模拟成交显示为“舊格式 2 筆”，不硬判为 `01`。
- 2026-06-15 已完成群组风险研究报告摘要：Dashboard 在“本轮风险归因与调仓摘要”区块内新增只读可复制摘要，复用群组归因、相关性、压力情境和模拟盘状态；不新增交易信号、不写入模拟成交 CSV、不连接券商。
- 2026-06-15 已完成旧格式模拟成交 fixture 验证：新增 `scripts/validate_legacy_trade_batch_status.py`，用 `/tmp` 无 `trade_id` CSV 验证旧成交归为 `legacy` / “舊格式”，临时 Dashboard 不把旧成交误显示为 `批次 01`。
- 2026-06-17 已把“策略结构变化结论”同步到 Dashboard 研究说明区，并把每日收盘后的自动重建命令接入 `--execute-simulated-trades`；页面现在会直接显示旧 4 因子与新扩展框架的对照结论，收盘重建也会顺带刷新模拟持仓与执行状态。
- 2026-06-17 已修正 Dashboard 日期与建议单联动漂移：正式页面首页显示 `2024-01-02 至 2026-06-16`，模型盘区明确区分 `模型建仓分析区间：2025-05-12 至 2026-06-02` 与 `当前回测/行情序列最新日期：2026-06-16`；策略监控中 `2317`、`1301` 已从“建议卖出”转为“观察”，理由为本日模拟调仓已落账。
- 2026-06-17 已把新版推到公网部署：提交 `ed037d2` 已推送到 `dashboard` 与 `origin`；公开 URL 已验证返回 `今日 Dashboard 更新日期：2026-06-17`、`行情/回测序列最新日期：2026-06-16`，不再显示红色 `建议卖出`。
- 2026-06-18 已完成新一轮正式日更：用 `--market-source public-close --market-mode close --execute-simulated-trades` 重建成功，`dashboard/index.html` 更新日期为 `2026-06-18`，但本轮可并入的行情/回测序列最新日期仍为 `2026-06-16`；这代表页面已更新，但公开收盘价路径本次未产出更晚的正式序列。
- 2026-06-18 本地模拟盘继续保持幂等：`SIMULATED_TRADES` 新增 0 笔；`data/simulated_trades_2026-06-16.csv` 仍为既有 2 笔卖出，`data/simulated_positions_latest.csv` 维持 15 檔持仓；Dashboard 中 `2317`、`1301` 均继续显示“观察”。
- 2026-06-18 本地 QA 基线已同步到今日正式 Dashboard：研究摘要关键数字现为 `AI 供应链权重 34.61%`、`风险贡献 49.97%`、`风险-权重差 +15.37%`；`scripts/validate_research_brief_sync.py`、`scripts/validate_research_brief_metrics.py`、`scripts/run_local_qa_checks.py` 与 iCloud Obsidian `台股量化基金.md` 均已更新，`scripts/run_local_qa_checks.py` 再次通过。
- 2026-06-19 已完成下一轮正式日更：`./.venv/bin/python -m py_compile src/risk_dashboard.py scripts/serve_dashboard.py` 通过后，再用 `--market-source public-close --market-mode close --execute-simulated-trades` 正式重建成功，`/usr/bin/time -p` 实测 `real 15.11`。
- 2026-06-19 正式页面更新日期已切到 `2026-06-19`，但公开收盘价路径本次仍只复用 `data/model_portfolio_market_2026-06-16.csv`；因此“行情/回测序列最新日期”继续停在 `2026-06-16`，应继续解释为数据新鲜度限制，而不是页面没有重建。
- 2026-06-19 本轮正式产物差异仅限 `dashboard/index.html`、`data/model_portfolio_market_2026-06-16.csv` 与 `data/model_portfolio_market_2026-06-16_summary.txt`：页面日期与 `quote_time` 刷新到 `2026-06-19T23:31:34`，当前持仓市值与未实现盈亏仍为 `NT$366,451.18` / `NT$7,198.15`。
- 2026-06-19 本地模拟盘状态未回退：最后模拟盘执行日仍为 `2026-06-16`，已落账模拟成交 `2` 笔、其中卖出 `2` 笔；Dashboard 与公网 HTML 都再次确认 `signal-pill sell` 无命中。
- 2026-06-19 已将提交 `a02dba2` 推送到 `dashboard` 与 `origin`；Render `/healthz` 先返回 `HTTP/2 200`，但首页正文前 5 次轮询仍停在 `2026-06-18`，第 6 次才切换为 `2026-06-19`，所以公网验证必须持续以首页正文为准。
- 2026-06-20 已继续追查 `public-close` 卡住原因：根因确认是 `--offline-cache` 复用了不完整的 `202606` TWSE 月缓存，导致共同交易日长期停在旧日期；现已在 `src/risk_dashboard.py` 为 `public-close` 路径补上主动刷新 TWSE 当月公开收盘资料的逻辑。
- 2026-06-20 本地已把 15 檔资产的 `202606` 月缓存全部补齐到 `2026-06-18`；刷新后共同最新日期已推进到 `2026-06-18`，新的矩阵缓存自动写为 `data/matrix_cache/twse_prices_9e0879afc9e7fb86.npz`。
- 2026-06-20 正式 Dashboard 已重建到 `行情/回测序列最新日期：2026-06-18`，并推动回测进入新的调仓节点：最后回测调仓日 `2026-06-17`，预计下次回测调仓 `2026-06-26`，距下次还差 `6` 个共同交易日。
- 2026-06-20 新增本地模拟盘卖出 `3` 笔：`2317 卖出 7 股`、`2881 卖出 48 股`、`2882 卖出 49 股`；`data/simulated_trades_2026-06-18.csv` 与 `data/simulated_positions_2026-06-18.csv` 已生成，`data/simulated_positions_latest.csv` 已切到本轮状态。
- 2026-06-20 Dashboard 已补上过期调仓提示保护：若推算出的“预计下次回测调仓日”早于今天而正式共同交易日仍未追上，页面会显示“待新正式行情后重算”，不再把过期日期当成当前事实。
- 2026-06-20 研究摘要与 QA 基线现为 `AI 供应链权重 34.46%`、`风险贡献 49.89%`、`风险-权重差 +15.43%`、`trade_count=3`；`scripts/validate_research_brief_sync.py`、`scripts/validate_research_brief_metrics.py`、`scripts/run_local_qa_checks.py` 与 iCloud Obsidian `台股量化基金.md` 均已同步并通过。
- 2026-06-21 周末日更已完成：Dashboard 更新日期切到 `2026-06-21`，但公开收盘价共同交易日未前进，行情/回测序列最新日期仍为 `2026-06-18`；最后回测调仓日 `2026-06-17`，预计下次回测调仓 `2026-06-26`，距下次还差 `6` 个共同交易日。
- 2026-06-21 已修复 `public-close` 主动刷新路径：最近公开收盘日判定只刷新最近月份，使用轻量日期交集，不再套完整回测的 60 日观察值门槛；TWSE 返回无资料时不覆盖既有 OK 月缓存，避免假日或接口空响应导致月缓存回退。
- 2026-06-21 本地模拟盘继续幂等：本轮新增成交 `0` 笔，最后模拟盘执行日仍为 `2026-06-18`，累计已落账 `3` 笔卖出；`signal-pill sell=0`、`建议卖出=0`，研究摘要关键数字仍为 `34.46% / 49.89% / +15.43% / trade_count=3`。
- 2026-06-21 提交 `7f6f47e` 已推送到 `dashboard` 与 `origin`；Render 公网首页正文第 4 轮切到 `今日 Dashboard 更新日期：2026-06-21`，公网 `signal_sell_count=0`。
- 2026-06-22 已新增 Dashboard“今日市场与更新摘要”区块：显示 TWSE 加权指数、项目已做事项、当前状态与短期下一步；今日加权指数收 `47,741.51`，上涨 `1,276.31` 点、`+2.75%`，台积电收 `2,510`、上涨 `100`。
- 2026-06-22 正式重建已推进到 `行情/回测序列最新日期：2026-06-22`，模型盘市值日 `2026-06-22`；本轮新增本地模拟卖出 `3` 笔：`2317` 5 股、`2881` 38 股、`2882` 39 股，执行后待确认调仓 `0` 笔。
- 2026-06-22 Dashboard 摘要显示当前持仓市值 `NT$351,391`、未实现盈亏 `NT$13,768`；最后模拟盘执行日 `2026-06-22`，已落账模拟成交 `3` 笔。QA 汇总通过，Obsidian 项目卡片已同步新研究摘要结论。
- 2026-06-22 提交 `e40ce2f` 已推送到 `dashboard` 与 `origin`；Render 公网首页正文已验证 `今日市场与更新摘要`、`今日 Dashboard 更新日期：2026-06-22`、`行情/回测序列最新日期：2026-06-22`，公网 `signal_sell_count=0`。
- 2026-06-22 已按用户要求在固定排程外即时补跑收盘日更：完整 public-close 重建耗时 `real 33.69`，页面仍为 `2026-06-22` 收盘定稿，模拟盘 3 笔卖出保持幂等无重复；研究摘要 QA 基线同步为 `34.38% / 49.90% / +15.52% / trade_count=3`。
- 2026-06-23 已按用户要求刷新今日 Dashboard：完整 public-close 重建耗时 `real 72.19`，页面今日更新日期切到 `2026-06-23`，但正式行情/回测序列最新日期仍为 `2026-06-22`，未生成 `data/model_portfolio_market_2026-06-23.csv`；这是 TWSE public-close 数据未共同前进，不是页面生成失败。
- 2026-06-23 本轮模拟盘继续幂等：最后模拟盘执行日仍为 `2026-06-22`，已落账模拟成交仍为 `3` 笔，`signal-pill sell=0`、`建议卖出=0`；本地 QA 汇总通过，Obsidian `台股量化基金.md` 已同步研究摘要。
- 2026-06-24 已完成每日收盘自动化：完整 public-close 重建耗时 `real 35.97`，页面今日更新日期切到 `2026-06-24`，但公开收盘价共同交易日仍停在 `2026-06-23`，未生成 `data/model_portfolio_market_2026-06-24.csv`；`data/model_portfolio_market_2026-06-23.csv` 为本轮刷新产物，15 檔成功、缺失 0 檔。
- 2026-06-24 本轮模拟盘继续幂等：新增模拟成交 `0` 笔，最后模拟盘执行日仍为 `2026-06-23`，已落账模拟成交 `3` 笔，其中卖出 `3` 笔；当前 `2317` 剩 `11` 股、`2881` 剩 `120` 股、`2882` 剩 `124` 股；`signal-pill sell=0`、可见 `建议卖出=0`。
- 2026-06-24 调仓日历为：最后回测调仓日 `2026-06-17`，预计下次回测调仓 `2026-06-29`，距下次还差 `4` 个共同交易日；研究摘要 QA 基线同步为 `34.38% / 49.89% / +15.51% / trade_count=3`，本地 QA 汇总通过。
- 2026-06-25 已完成每日收盘自动化：完整 public-close 重建耗时 `real 29.43`，页面今日更新日期切到 `2026-06-25`，公开收盘价共同交易日推进到 `2026-06-24`，正式生成 `data/model_portfolio_market_2026-06-24.csv`；本轮需带 `PYTHONPATH=$HOME/Library/Python/3.9/lib/python/site-packages` 复用 user-site `scipy`。
- 2026-06-25 本轮新增本地模拟卖出 `2` 笔：`2317` 卖出 `3` 股、`2881` 卖出 `24` 股；执行后 `2317` 剩 `8` 股、`2881` 剩 `96` 股、`2882` 维持 `124` 股；`signal-pill sell=0`、可见 `建议卖出=0`。
- 2026-06-25 调仓日历为：最后回测调仓日 `2026-06-17`，预计下次回测调仓 `2026-06-29`，距下次还差 `4` 个共同交易日；研究摘要 QA 基线同步为 `33.00% / 52.71% / +19.71% / trade_count=2`，本地 QA 汇总通过。
- 2026-06-17 回测区已新增滚动更新解释：当前回测覆盖 `2024-04-10 至 2026-06-16`，共 `74` 次调仓，最后一次重新计算权重日期为 `2026-05-28`。如果只补进 1 个可用交易日快照，回测曲线会更新到新日期，但不会新增 7 日调仓周期。
- 2026-06-17 Dashboard 已新增“调仓与执行日历”：最后回测调仓日 `2026-05-28`，预计下次回测调仓 `2026-06-19`，距下次还差 `3` 个共同交易日；最后模拟盘执行日 `2026-06-16`，显示 `2317 卖出 10 股`、`1301 卖出 53 股`。回测调仓与模拟盘执行调仓必须分开解释，但都要出现在 Dashboard。
- 2026-06-17 已创建 Codex 自动化 `dashboard`，并在 2026-06-22 按用户偏好改为每天 `13:45` 固定更新：执行本地重建、模拟盘落账、远端推送、公网抓取验证，并在当前线程用中文回报结论。每日更新必须以公网 URL 验证作为完成条件。
- 2026-06-17 本地模拟盘已落账 2 笔卖出：`2317 鴻海` 卖出 10 股、`1301 台塑` 卖出 53 股；重复执行正式重建时 `SIMULATED_TRADES` 新增 0 笔，`data/simulated_trades_2026-06-16.csv` 仍保持 2 笔，说明同批次幂等防重有效。
- 2026-06-17 需保留一个重要区分：历史行情缓存本体尚未证明已完整刷新到 6 月中旬；当前已完成的是把最新可用 `2026-06-16` 市值档并入回测价格序列并重建 Dashboard。
- 2026-06-08 已新增台股多因子收缩优化模型方法 `multi-factor-shrink`：使用中期动量、低波、回撤防御、流动性四类价格/量能因子生成保守预期收益，再搭配 Ledoit-Wolf 收缩协方差做仅做多、单一资产 25% 上限的目标权重。基本面 ROE/PE/殖利率暂未纳入，等待稳定数据源。
- 2026-06-17 已完成第一轮扩因子落地：`multi-factor-shrink` 现已扩成三层框架，价格层新增 `趋势强度`，并加入行业/主题相对强弱、AI 产业暴露、资金流代理与风险偏好代理分数；正式模型盘 CSV 会额外写出 `price_factor_score`、`industry_ai_score`、`macro_external_score`、`composite_score` 与 `trend_strength_score`。
- 2026-06-17 已新增只读比较脚本 `scripts/compare_multi_factor_profiles.py`，可比较旧 4 因子与新扩展框架的目标权重差异；默认输出 `/tmp/tw_quant_factor_profile_compare.md` 与 `/tmp/tw_quant_factor_profile_compare.json`。
- 比较脚本当前稳定基线为 `offline-cache + TWSE`、`build_date=2026-06-03`、`ai_tilt=moderate`；实测旧 4 因子 AI 群组权重 `0.33000000`，新扩展框架 AI 群组权重 `0.34231806`，仍低于 `35%` 上限。
- 2026-06-17 比较脚本已升级为结构化差异摘要：会额外输出集中度变化、权重变化最大标的、行业暴露变化、主题暴露变化与 AI / 非 AI 暴露变化。当前实测显示，新扩展框架的 HHI 从 `0.07919146` 降到 `0.07721507`，有效持仓数从 `12.6276` 升到 `12.9508`，前三大权重合计从 `0.31167766` 降到 `0.28972039`。
- 2026-06-17 比较脚本已进一步补齐风险贡献差异：会输出行业、主题、AI / 非 AI 的风险贡献变化。当前实测 AI 主题风险贡献从 `0.484916` 升到 `0.498265`，非 AI 风险贡献从 `0.515084` 降到 `0.501735`；说明新扩展框架在维持上限约束下，风险暴露仍更偏向 AI 主题。
- 2026-06-17 比较脚本已再补压力情境与高相关重叠：会输出压力估计损失变化与高相关配对摘要。当前实测旧 4 因子压力估计损失为 `-0.202641`，新扩展框架为 `-0.203092`，变化 `-0.000452`；两版框架的最高相关配对均为 `006208 / 00881`，相关性 `0.9354`，高相关配对数均为 `14`。
- `dashboard/index.html`、`data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` 已用 `multi-factor-shrink`、2026-06-08 市值档重新生成；目标权重合计 100%，0050 目标权重为 0 但旧模拟持仓仍保留显示，避免持仓总览漏算。
- 2026-06-08 已加入股票池分类字段：`config/universe_tw.csv` 包含 `sector`、`theme`、`ai_supply_chain`。已新增 `--ai-tilt` 参数，`moderate` 会把 AI 供应链软目标提高到约 33%、群组上限 35%；`strong` 软目标约 38%、群组上限 40%。
- 当前仪表板和模型盘已用 `--ai-tilt moderate` 重新生成；直接 AI 供应链目标权重为 33.00%。该口径未穿透 ETF 成分，只按标的本身分类。
- Obsidian 长期卡片：`/Users/tonyfu/Documents/Obsidian 項目/30-项目库/项目卡片/稳健投资组合量化模型构建 项目卡片.md`。

## 三、关键文件

- `README.md`：安装、运行、数据源和验证说明。
- `src/risk_dashboard.py`：主脚本。
- `config/universe_tw.csv`：默认资产池。
- `dashboard/index.html`：生成后的静态仪表盘。
- `data/model_portfolio_latest.csv`：最近一次模型盘建仓计划。

## 四、下一步建议

1. 新会话先读取本文件，再读取 `README.md`、`src/risk_dashboard.py`、`config/universe_tw.csv`。
2. 常用复跑命令如下；若源行情缓存没有变化，会直接读取 `data/matrix_cache/`，避免大量小 JSON 读取延迟：
   `./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-05.csv`
   当前多因子策略复跑命令：
   `./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink`
   当前 AI 供应链倾斜复跑命令：
   `./.venv/bin/python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate`
   当前旧/新多因子框架比较命令：
   `./.venv/bin/python scripts/compare_multi_factor_profiles.py`
3. 后续模拟盘复跑默认会优先读取 `data/simulated_positions_latest.csv`；若要把新建议单落账，使用同一复跑命令并加 `--execute-simulated-trades`。
4. 2026-06-14 已完成第三轮 Loop 性能优化：`project_capped_simplex()` 支持投影和足够接近 1 时提前停止；完整 2024-01 至 2026-06 临时复跑从 `run_total_seconds=28.60` 降至 `16.00` 秒，单独回测从本轮实测 `29.1977` 秒降至 `15.0964` 秒。
5. 结果一致性已验证：sample/shrink 回测期末净值、最大回撤、平均换手率差异均在 `1e-12` 量级，权重最大绝对差异约 `4.7e-14`；正式 `dashboard/index.html` 与模型盘 CSV 未覆盖。
6. warm start 与 active-set 高速求解器都已临时评估但未纳入正式口径：前者有小幅结果漂移，后者 sample 回测结果明显改变；如要继续追求 `<8s`，应作为研究分支先讨论。
7. 2026-06-14 已完成第四轮 Loop 模拟盘幂等性验证：新增 `--simulated-trades-output` 与 `--simulated-positions-output`，可把模拟成交/持仓落到 `/tmp` 演练，默认正式输出不变。
8. 第四轮验证结果：第一次临时落账新增 2 笔，第二次同日复跑新增 0 笔；临时成交 CSV 和临时持仓 CSV 行数/hash 保持不变，`duplicate_executed_keys=0`；正式 Dashboard、模型盘 CSV 和正式模拟盘 CSV 未覆盖。
9. 模拟盘安全验证必须使用 `--offline-cache --data-source twse`；不要与 `--data-source shioaji`、非离线 `auto` 或 `--update-daily-market` 混跑。
10. 2026-06-14 已完成第五轮 Loop Dashboard 报告解释增强：把“手动订单交易”改为“模拟盘调仓确认”，把页面按钮状态改为“页面标记已确认 / 页面已确认 / 待确认”，并在策略监控区加入“訊號口徑”说明。
11. 第五轮正式 Dashboard 已重建：`dashboard/index.html` hash `c630fc3bee1ae545aaeceec938d40cecb6d13d1de9849162aa686589bbd372ef`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
12. 2026-06-14 已完成第六轮 Loop 风险归因与调仓摘要：Dashboard 新增“本轮风险归因与调仓摘要”，说明主要风险、压力情境和调仓原因；持仓区新增“持仓状态解释”。
13. 第六轮正式 Dashboard 已重建：`dashboard/index.html` hash `c85f36444f061531ee5acb66ed975cdf97f5e635b3bd88ccf6b1aa6e4001f359`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
14. 2026-06-14 已完成第七轮 Loop 模拟盘稳定 `trade_id`：`dashboard/index.html` hash `0a30ba517d3825746a5165efaf3f8cf64ecc4cfa2bf6fa60adfd752630b54a91`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
15. 第七轮验证结果：临时 `/tmp` 落账第一次 2 笔，第二次仍为 2 笔且 `duplicate_trade_ids=0`；正式模拟盘 CSV hash 保持 `1c74615a475b57e960eb716c98acf86d7ed435ea32bddba206cfb88e97111f81` 与 `821074fe726846a7caa2c8843dc6e465fb9bf88fade7bcab4ea7759b0ebdb391`。
16. 2026-06-14 已完成第八轮 Loop 显式分批 `batch_seq`：`dashboard/index.html` hash `6c1438b55cbb79dcc4106f331e364b3b01b2a0e4bc226e185cc71b5042556275`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
17. 第八轮验证结果：临时 `/tmp` 批次 `01` 两次保持 2 笔；显式批次 `02` 后共 4 笔，第二次同样 `02` 复跑仍 4 笔且 `duplicate_trade_ids=0`。
18. 2026-06-14 已完成第九轮 Loop 行业/主题/AI 供应链风险归因：`dashboard/index.html` hash `94a0fc520c0ded1ac58a1652f8f049d2da983222131e9e350f292d0299593d6f`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
19. 第九轮验证结果：短区间 `/tmp` 冒烟通过；正式 Dashboard 命中新文案；AI 供应链权重 33.00%、风险贡献 48.49%；未使用 Shioaji、`--update-daily-market` 或 `--execute-simulated-trades`。
20. 2026-06-15 已完成第十轮 Loop Dashboard 批次状态小结：`dashboard/index.html` hash `0252d4cd62cca01bba419e4abc8eb7b168855d8b6a8ffcdee3f36263d5ce57d5`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
21. 第十轮验证结果：`01` 临时复跑保持 2 笔；显式 `02` 后共 4 笔；第二次同样 `02` 仍 4 笔，`duplicate_trade_ids=0`；正式旧格式模拟成交在 Dashboard 显示“舊格式 2 筆”。
22. 2026-06-15 已完成第十一轮 Loop 群组风险研究报告摘要：`dashboard/index.html` hash `fff6680597e09f3962e461ba3b39d8bb0fb3c3faaa1f8ea0f3345f9a9be0f117`；模型盘 CSV 内容 hash 不变；正式模拟成交/持仓 CSV 未改。
23. 第十一轮验证结果：短区间 `/tmp` 冒烟通过；正式摘要显示 AI 供应链权重 `33.00%`、风险贡献 `48.49%`、风险-权重差 `+15.49%`；旧误导文案与实盘 API 关键词无命中。
24. 2026-06-15 已完成第十二轮 Loop 旧格式模拟成交 fixture 验证：新增 `scripts/validate_legacy_trade_batch_status.py`；正式 Dashboard/模型盘 CSV/模拟成交与持仓 CSV hash 未改。
25. 第十二轮验证结果：`validate_legacy_trade_batch_status.py` 与 `--dashboard` 模式均通过；临时 Dashboard 命中“暫無新格式批次”“舊格式紀錄：舊格式 2 筆”，并断言旧成交不显示为 `<td>批次 01</td><td>2</td>`。
26. 2026-06-15 已完成第十三轮 Loop Obsidian 研究记录同步：Dashboard 群组风险研究报告摘要已写入 iCloud Obsidian `台股量化基金.md`，并同步 AI 供应链权重 33.00%、风险贡献 48.49%、风险-权重差 +15.49% 与旧格式模拟成交兼容结论。
27. 第十三轮验证范围：只做文本命中、旧格式 fixture 复跑和正式产物 hash 检查；未修改源码、未重建正式 Dashboard、未覆盖正式模型盘或模拟盘 CSV。
28. 2026-06-15 已完成第十四轮 Loop 研究摘要同步一致性检查：新增 `scripts/validate_research_brief_sync.py`，只读确认正式 Dashboard `research-report` 摘要已存在于 iCloud Obsidian 项目卡片。
29. 第十四轮验证范围：编译新增脚本、运行同步检查、回归旧格式 fixture，并检查正式 Dashboard/模型盘/模拟盘 CSV hash；未修改源码主流程、未重建正式 Dashboard、未覆盖正式数据。
30. 2026-06-15 已完成第十五轮 Loop Markdown 摘要预览导出：新增 `scripts/export_research_brief_markdown.py`，默认把正式 Dashboard 研究摘要写到 `/tmp/tw_quant_research_brief.md`，不写正式知识库。
31. 第十五轮验证范围：编译新增脚本、运行 `/tmp` Markdown 导出、检查关键数字与边界句、回归同步一致性检查，并检查正式 Dashboard/模型盘/模拟盘 CSV hash。
32. 2026-06-15 已完成第十六轮 Loop 本地 QA 汇总：新增 `scripts/run_local_qa_checks.py`，顺序运行研究摘要同步检查、Markdown 导出预览和旧格式 fixture 验证，并确认正式产物 hash 前后不变。
33. 第十六轮验证范围：编译汇总脚本、执行本地 QA 汇总默认分支与当时的可选 Dashboard fixture 分支、检查 `/tmp` Markdown 预览关键数字与边界句，并复核正式 Dashboard/模型盘/模拟盘 CSV hash。
34. 2026-06-16 已完成第十七轮 Loop 固定 Dashboard fixture 回归：`scripts/run_local_qa_checks.py` 默认纳入旧格式 fixture 的临时 Dashboard 页面验证，并新增 `--skip-dashboard-fixture` 作为较快检查开关。
35. 第十七轮验证范围：编译 QA 汇总脚本，执行默认分支与 `--skip-dashboard-fixture` 分支，并复核正式 Dashboard/模型盘/模拟盘 CSV hash。
36. 2026-06-16 已完成第十九轮 Loop QA 摘要文件输出：`scripts/run_local_qa_checks.py` 新增 `--summary-output`，默认写 `/tmp/tw_quant_local_qa_summary.md`，记录检查模式、Markdown 预览路径、三段检查结果与 6 个正式产物 SHA-256。
37. 第十九轮验证结果：默认完整回归与 `--skip-dashboard-fixture` 较快模式都能生成摘要；额外以 `/tmp/tw_quant_local_qa_summary_full.md` 与 `/tmp/tw_quant_local_qa_summary_fast.md` 验证 full/fast 两种模式内容正确，正式 Dashboard/模型盘/模拟盘 CSV hash 未改。
38. 2026-06-16 已完成第二十轮 Loop QA JSON 摘要输出：`scripts/run_local_qa_checks.py` 新增 `--summary-json-output`，默认写 `/tmp/tw_quant_local_qa_summary.json`，记录时间、模式、`dashboard_fixture`、结果与 6 个正式产物 SHA-256。
39. 第二十轮验证结果：默认完整回归与 `--skip-dashboard-fixture` 较快模式都能生成 JSON 摘要；额外以 `/tmp/tw_quant_local_qa_summary_full.json` 与 `/tmp/tw_quant_local_qa_summary_fast.json` 验证 full/fast 两种模式字段正确，正式 Dashboard/模型盘/模拟盘 CSV hash 未改。
40. 到第二十轮为止，本地 QA 闭环已具备单命令入口、默认/较快双模式、人工可读 Markdown 摘要、机器可读 JSON 摘要与正式产物 hash 守门；继续加摘要格式的边际收益已下降。
41. 2026-06-16 已完成第二十一轮 Loop 研究摘要关键数字回归检查：新增 `scripts/validate_research_brief_metrics.py`，从正式 Dashboard 的 `research-report` 摘要校验 `AI 供应链权重 33.00%`、`风险贡献 48.49%`、`风险-权重差 +15.49%` 与 `已有 2 笔本日模拟调仓转为观察`。
42. 第二十一轮验证结果：关键数字回归脚本单独通过，且已纳入 `scripts/run_local_qa_checks.py` 的默认/较快两条路径；Markdown/JSON 摘要都会记录 `metrics` 结果，正式 Dashboard/模型盘/模拟盘 CSV hash 未改。
43. 2026-06-16 已按既有 2026-06-08 市值档正式刷新 Dashboard：使用 `--offline-cache --data-source twse --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate`，重建成功，`real 15.63`。
44. 本轮刷新后 `dashboard/index.html` hash 为 `1156b60d4f3c441f6766fe5746ee2f099acfb929d0e834a9c05e39b6ac4ec268`；模型盘 CSV 内容 hash 仍为 `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`；正式模拟成交/持仓 CSV 未改。
45. 本轮本地 QA 汇总通过：`scripts/run_local_qa_checks.py` 输出 `local_qa_checks_ok`，覆盖摘要同步、关键数字回归、Markdown 导出、旧格式 fixture 和临时 Dashboard fixture；摘要写入 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`。
46. 当前多 Agent 系统的实用分工已稳定：Coordinator 负责目标/边界/交接，Quant 负责风险与策略数字，Data Pipeline 负责行情与市值档只读检查，Dashboard/Product 负责页面解释与研究摘要，QA/Reviewer 负责本地 QA、fixture、hash 守门与 JSON 汇总。
47. 2026-06-16 已复核为什么仍用 6/8 市值档：本地没有 `2026-06-16` 市值档；当前时间 `10:22 CST` 仍属盘中，QVeris/EODHD 对 `0050.TW` 的 2026-06-16 日线返回空结果，Shioaji 盘中路径因当前 shell 缺少 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY` 未能落地。
48. 失败的 6/16 盘中更新尝试曾把 `data/model_portfolio_latest.csv` 写成 `not_generated` 状态；已用 `data/model_portfolio_2026-06-03.csv` 恢复，并重新用 6/8 市值档重建 Dashboard，QA 汇总通过。
49. 恢复后正式状态：`dashboard/index.html` hash `c7b1449c9877460b5107bb79e4553a2a089bd9cfbd50a6f14160c1659236cb74`；模型盘 CSV hash `2ecf252e782d3ba05b97816cb96326043169fcfa862fb380c9ca455cd320e623`；正式模拟成交/持仓 CSV 未改。
50. 用户确认 Shioaji 可用于只读行情后，2026-06-16 盘中每日更新已落地：生成 `data/model_portfolio_market_2026-06-16_intraday.csv`，`quote_count=15`、`missing_count=0`、当前市值 `369609.09`、未实现盈亏 `4445.20`、盈亏率 `1.2173%`。
51. 2026-06-16 盘中 Dashboard 已重建，页面显示 `2026-06-16T10:28:34` 与“盘中暂估”；Dashboard hash 为 `e8469c9af1a9bf49e955ce270302ef18ea98e43e4b419853c57bb4b7a5ddeae0`，盘中市值档 hash 为 `8b4eb7318c5adb8a28282e9dc7ef3936f4dac990038a5f78d2b9c3f44b5a995c`。
52. 2026-06-16 盘中研究摘要已同步到 iCloud Obsidian 项目卡片；`validate_research_brief_metrics.py` 已支持“已转观察”和“待确认调仓”两种调仓状态，`validate_research_brief_sync.py` 已移除旧日期标题硬编码；本地 QA 汇总通过。
53. 本轮未执行 `--execute-simulated-trades`，正式模拟成交/持仓 CSV 未改；当前 2 笔卖出只是 Dashboard 待确认模拟调仓，不是已落账成交。
54. 若继续下一轮，优先修复 `scripts/run_local_qa_checks.py` 的监控列表：它仍固定包含 `data/model_portfolio_market_2026-06-08.csv`，应改成自动识别 Dashboard 当前套用的最新市值档。
55. 若要 2026-06-16 收盘定稿，应等收盘后再跑 `--market-mode close` 生成 `data/model_portfolio_market_2026-06-16.csv` 并重建 Dashboard。
56. 长任务结束前，把稳定结论同步到本文件和 Obsidian 项目卡片。

## 五、安全边界

- Shioaji 密钥只允许保留在本地敏感配置中。
- 禁止读取、打印、保存或提交 API Key、Secret Key、Token、密码或敏感载荷。
- `.shioaji.local.env`、`.shioaji.runtime/`、`.venv/`、`data/cache/`、`data/matrix_cache/` 只记录路径和用途，不记录内容。

## 六、Loop Engineering 与多 Agent 协作入口

- 2026-06-14 起，本项目采用 Loop Engineering 工作法：观察、定义、建基线、小步实现、度量、复核、交接。
- 新会话先读 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`，再读本文件、`README.md` 和相关源码。
- 多 Agent 默认角色：Coordinator、Quant Research Agent、Data Pipeline Agent、Dashboard/Product Agent、QA/Reviewer Agent。
- 每轮必须有明确目标、指标、范围、禁止触碰区域和验证方式；没有指标时不进入自动优化循环。
- 当前项目不是 Git 仓库，因此不使用依赖 git branch/commit/reset 的 autoresearch 原版流程；改用文件级计划、基线记录和人工可审查的最小 Diff。
- 稳定结论、关键命令、性能数字、数据产物和 blocker 必须同步回 `progress.md`；形成长期事实时同步本文件。
- 2026-06-14 已建立项目级 `AGENTS.md`、`task_plan.md`、`findings.md`、`progress.md`，并完成第一轮 Loop：修复无 `--model-portfolio` 时短区间 Dashboard 冒烟失败的 `default_trade_state_json` 默认值问题。
- 第一轮验证结果：`src/risk_dashboard.py` 编译通过；短区间 `--offline-cache` 临时 Dashboard 输出通过；短区间 `--model-portfolio` 临时输出通过；正式 `dashboard/index.html` 与 `data/model_portfolio_latest.csv` 未被覆盖。
- 第二轮验证结果：完整 2024-01 至 2026-06 临时复跑成功，`run_total_seconds=28.60`；单独滚动回测 `backtest_seconds=27.9764`，确认主要瓶颈在最小方差求解与 capped simplex 投影。
- 第三轮验证结果：安全优化后完整临时复跑 `run_total_seconds=16.00`，单独滚动回测 `backtest_seconds=15.0964`；结果一致性差异在 `1e-12` 量级，正式 Dashboard/CSV 未覆盖。
- 第四轮验证结果：模拟盘幂等性验证通过；临时路径第一次落账 2 笔、第二次 0 笔，成交/持仓 hash 不变；正式 Dashboard/模型盘/模拟盘 CSV 未覆盖。
- 第五轮验证结果：Dashboard 报告解释增强完成并正式重建；新增文案可在 `dashboard/index.html` 检索，旧歧义文案无命中；未使用 Shioaji、`--update-daily-market` 或 `--execute-simulated-trades`。
- 第六轮验证结果：Dashboard 风险归因与调仓原因摘要完成并正式重建；新增文案可在 `dashboard/index.html` 检索；未使用 Shioaji、`--update-daily-market` 或 `--execute-simulated-trades`。
- 第七轮验证结果：模拟盘建议单与新成交 CSV 新增稳定 `trade_id`；Dashboard 页面确认状态改用 `trade_id`；临时 `/tmp` 两次落账保持 2 笔且无重复 ID；正式模拟成交/持仓 CSV 未改。
- 第八轮验证结果：显式 `batch_seq` 接入主流程；默认 `01` 保持幂等，显式 `02` 可新增第二批且同样 `02` 重跑新增 0 笔；正式模拟成交/持仓 CSV 未改。
- 第九轮验证结果：Dashboard 新增行业、主题与 AI 供应链风险归因；正式 AI 供应链权重 33.00%、风险贡献 48.49%；模型盘 CSV 内容 hash 不变，正式模拟成交/持仓 CSV 未改。
- 第十轮验证结果：Dashboard 新增模擬盤批次狀態小結；正式旧格式模拟成交显示“舊格式 2 筆”；`01/02` 临时批次复跑验证通过，正式模拟成交/持仓 CSV 未改。
- 第十一轮验证结果：Dashboard 新增只读可复制的群组风险研究报告摘要；正式摘要与群组归因表一致，AI 供应链权重 33.00%、风险贡献 48.49%；正式模拟成交/持仓 CSV 未改。
- 第十二轮验证结果：新增旧格式模拟成交 fixture 验证脚本，确认无 `trade_id` 成交显示为“舊格式”而不是 `批次 01`；正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 第十三轮验证结果：Dashboard 研究说明区已直接显示“策略结构变化结论”；每日收盘自动重建命令已接入 `--execute-simulated-trades`；`/tmp` 冒烟验证中页面可检索到新结论，且模拟成交落账链路正常。
- 第十三轮验证结果：Dashboard 群组风险研究报告摘要已同步到 iCloud Obsidian 项目卡片；本轮只改研究记录与交接文档，正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 第十四轮验证结果：新增只读同步一致性检查脚本，确认正式 Dashboard 摘要已同步到 Obsidian 项目卡片；正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 第十五轮验证结果：新增 `/tmp` Markdown 摘要导出脚本，复用正式 Dashboard 摘要；正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 第十六轮验证结果：新增本地 QA 汇总脚本，默认分支与当时的可选 Dashboard fixture 分支均通过，且正式产物 hash 不变；正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 2026-06-16 已完成第十八轮 Loop QA 文案漂移清理：交接文档中的旧参数名已统一为当前口径，默认回归包含临时 Dashboard fixture，较快模式使用 `--skip-dashboard-fixture`。
- 第十七轮验证结果：本地 QA 汇总默认分支已固定覆盖旧格式 fixture 的临时 Dashboard 页面，`--skip-dashboard-fixture` 较快分支也通过；正式 Dashboard/模型盘/模拟盘 CSV 未改。
- 2026-06-16 Dashboard 正式刷新结果：用既有 2026-06-08 市值档、`multi-factor-shrink`、`--ai-tilt moderate` 离线重建成功，`dashboard/index.html` hash 更新为 `1156b60d4f3c441f6766fe5746ee2f099acfb929d0e834a9c05e39b6ac4ec268`；模型盘 CSV 内容 hash 不变，正式模拟盘 CSV 未改。
- 2026-06-16 Data Pipeline 纠错：本地没有 6/16 市值档；Shioaji 盘中更新因当前 shell 缺少环境变量未落地，QVeris/EODHD 对当天日线返回空；失败尝试后已恢复 `data/model_portfolio_latest.csv` 并用 6/8 市值档重建 Dashboard，QA 通过，当前 Dashboard hash 为 `c7b1449c9877460b5107bb79e4553a2a089bd9cfbd50a6f14160c1659236cb74`。
- 2026-06-16 Shioaji 盘中每日更新已落地：生成 `data/model_portfolio_market_2026-06-16_intraday.csv`，15 檔全 ready，Dashboard 显示 6/16 盘中暂估；本地 QA 通过，但 QA 监控列表下一轮应从固定 6/8 改成自动识别当前市值档。
- 2026-06-16 已把 `今日持仓与收盘盈亏`、`模拟盘调仓确认`、`策略监控与建议单` 前移到 Dashboard 上半段，打开首页先看到关键动作，再看到回测与图表。
- `scripts/run_local_qa_checks.py` 已自动选取最新 `model_portfolio_market_*.csv`；`scripts/serve_dashboard.py` 与 `render.yaml` 已补好，可把生成后的 Dashboard 用标准库静态服务或 Render Web Service 挂出去。
- 2026-06-16 已把公网服务升级成自动重建版：`scripts/serve_dashboard.py` 会在启动后先重建一次，再按 `Asia/Shanghai` 每天 `13:45` 继续重建；`--market-source public-close` 会用公开收盘价路径重建每日市值檔，并优先读取最新已生成的市值档。
- 2026-06-16 Render 蓝图已同步默认环境变量：`DASHBOARD_TIMEZONE=Asia/Shanghai`、`DASHBOARD_REBUILD_TIME=13:45`、`DASHBOARD_REBUILD_COMMAND=python src/risk_dashboard.py --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close`。
- 2026-06-16 已修正小屏表格排版：`metric-table` 与 `compact-table` 在手机宽度下改为横向滚动，避免中文名称在窄列里逐字换行成竖排，提升首屏可读性。
- 2026-06-17 已进一步修正模型盘相关宽表的名称列：在持仓表、模拟盘调仓确认表、策略监控表的“名称”单元格加入 `name-cell` / `asset-name`，让名称保留最小宽度并以不换行元素渲染，避免 `00881`、`00919`、`2330` 这类中文名称在窄视口下被压成逐字竖排。
- 2026-06-17 已用既有 `data/model_portfolio_market_2026-06-16_intraday.csv` 正式重建 Dashboard，当前 `dashboard/index.html` hash 为 `119a8e76857228d5749b74e62448ef6dc6989773be387ac1af904c79ae6ebaac`；`data/model_portfolio_latest.csv` 与 `data/model_portfolio_2026-06-03.csv` hash 同为 `1eccb9719d3ad944d3e4e5883b5b93a4f506139180497e25d4c61b10400e2b67`。
- 2026-06-17 公网已先用 Render 免费实例上线：`https://futienchun-com-dashboard.onrender.com/`；服务 ID 为 `srv-d8onljk8aovs7385cqo0`；健康检查 `200`，公开页标题返回 `【Codex】台灣股市投資量化模型`。
- 2026-06-17 免费实例会冷启动与睡眠；当前策略是先满足公网读取，再视稳定性决定是否升级付费档。
- 当前多 Agent 最适合的下一步：QA/Reviewer 先读 `/tmp/tw_quant_local_qa_summary.json` 做机器汇总，Quant 与 Dashboard/Product 再分别判断是否需要趋势对比或页面关键文案回归；Data Pipeline 只在要更新新行情时启动。
- 下一轮建议：继续汇总更多只读 QA 检查项；若继续追求 `<8s`，需先确认是否允许研究会改变数值结果的新求解器。
