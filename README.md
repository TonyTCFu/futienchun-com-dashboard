# 台股稳健投资组合风险仪表盘 MVP

这个项目用于研究一个核心问题：台股与台股 ETF 的组合是否真的分散，以及不同协方差估计方法会不会让组合在压力环境下更稳健。

第一版聚焦最小可行研究：

- 下载台股与台股 ETF 的公开日行情。
- 比较普通样本协方差与 Ledoit-Wolf 收缩协方差。
- 生成最小方差组合、风险贡献、相关性热力图、回撤与压力情境摘要。
- 执行滚动再平衡回测，比较两种协方差估计下的净值、回撤、波动和换手率。
- 输出一个可直接打开的三栏式静态仪表盘：`dashboard/index.html`，左侧导航、中间风险研究、右侧模型盘建仓与调仓执行摘要。

## 安装

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 运行

默认读取 `config/universe_tw.csv` 的资产池，并生成仪表盘：

```bash
python src/risk_dashboard.py
```

常用参数：

```bash
python src/risk_dashboard.py --start 2021-01 --end 2026-05
python src/risk_dashboard.py --universe config/universe_tw.csv --output dashboard/index.html
python src/risk_dashboard.py --allow-stale-cache
python src/risk_dashboard.py --offline-cache
python src/risk_dashboard.py --data-source auto
python src/risk_dashboard.py --rebalance-window 60 --rebalance-step 7
python src/risk_dashboard.py --model-portfolio
```

## 数据规则

- 数据源优先使用 TWSE 官方公开资料。
- 股票与 ETF 均按 TWSE 代码下载月度日成交资料。
- 下载成功后会缓存到 `data/cache/`，方便后续复跑。
- 使用 `--offline-cache` 时会自动生成并复用 `data/matrix_cache/` 的聚合行情矩阵，避免每次重建都读取大量小 JSON；源缓存变动后会自动生成新的矩阵缓存。
- 若接口失败且存在缓存，脚本会使用缓存并在仪表盘中标注数据问题。
- 若某资产有效交易日不足，会从本轮分析剔除并显示原因。

## Shioaji 数据源

如果你有永丰金 Shioaji API Key，可以用它绕过 TWSE 限流。脚本不会读取 `.env`，也不会保存或打印密钥；请在本机 shell 里用环境变量提供：

```bash
export SHIOAJI_API_KEY="你的 API Key"
export SHIOAJI_SECRET_KEY="你的 Secret Key"
python src/risk_dashboard.py --data-source shioaji --start 2024-01 --end 2024-06
```

也可以使用本地引导脚本，让你自己在终端中输入密钥，并保存到已忽略的本地文件：

```bash
bash scripts/configure_shioaji_env.sh
source .shioaji.local.env
python src/risk_dashboard.py --data-source shioaji --start 2024-01 --end 2024-06
```

也可以使用自动模式，优先 Shioaji，失败时回退 TWSE：

```bash
python src/risk_dashboard.py --data-source auto --allow-stale-cache
```

Shioaji 是可选依赖；若要使用，请安装：

```bash
pip install shioaji
```

脚本会默认把 Shioaji token/cache 放在项目内 `.shioaji.runtime/`，该目录已加入 `.gitignore`，用于避免默认 `~/.shioaji` token 池冲突。

### 新路径 Shioaji 行情缓存初始化

多设备运行时，项目 Workspace 固定放在：

```bash
/Users/tonyfu/Library/Mobile Documents/iCloud~md~obsidian/Documents/Codex/projects/台股_稳健投资组合量化模型构建
```

本机敏感配置不放进 Workspace，保留在本机目录：

```bash
/Users/tonyfu/Documents/Codex本地/稳健投资组合量化模型构建 2/.shioaji.local.env
/Users/tonyfu/Documents/Codex本地/稳健投资组合量化模型构建 2/.shioaji.runtime/token_pool/
```

`token_pool/` 只保留空目录结构；实际 token、`.shioaji.local.env`、`.venv/`、`data/cache/` 和 `data/matrix_cache/` 都是每台设备自己的本地状态，不进入 Git、不进入共享 Workspace。新设备从共用仓库拉下项目后，先在该设备本地准备 Shioaji 环境变量并重建月度行情缓存，再运行 `--offline-cache` 的 Dashboard / QA 流程。

首次初始化建议流程：

```bash
cd "/Users/tonyfu/Library/Mobile Documents/iCloud~md~obsidian/Documents/Codex/projects/台股_稳健投资组合量化模型构建"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install shioaji
source "/Users/tonyfu/Documents/Codex本地/稳健投资组合量化模型构建 2/.shioaji.local.env"
python scripts/init_shioaji_market_cache.py --start 2024-01 --end 2026-06
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-26.csv --model-method multi-factor-shrink --ai-tilt moderate --output /tmp/tw_quant_new_path_smoke.html --model-output /tmp/tw_quant_new_path_model.csv
```

说明：

- 初始化脚本只调用 Shioaji 历史 K 线行情，不呼叫下单、改单、撤单或账户查询。
- 脚本只从当前 shell 的 `SHIOAJI_API_KEY` / `SHIOAJI_SECRET_KEY` 读取凭证，不读取、不打印、不提交 `.shioaji.local.env`。
- 若新设备尚未建立本机敏感配置，可先运行 `bash scripts/configure_shioaji_env.sh` 生成 `.shioaji.local.env`，再把该文件移到本机 `Codex本地` 对应目录；不要把它留在共享 Workspace。
- 脚本会写入 TWSE 兼容格式的 `data/cache/{symbol}_{YYYYMM}.json`，供既有 `--offline-cache` 逻辑复用。
- 若只想先看会处理哪些文件，可运行 `python scripts/init_shioaji_market_cache.py --start 2024-01 --end 2026-06 --dry-run`。
- 若要补单一标的或重跑某段月份，可使用 `--symbols 0050,2330 --start 2026-06 --end 2026-06 --force`。

## 首版模型边界

第一版只实现最小方差组合、滚动再平衡研究与手动模拟建仓，不包含实盘交易、券商 API、下单、风险平价、Black-Litterman 或换手率约束。当前已新增一个保守的台股多因子收缩优化模型，用于和原本回撤风险加权模型并行比较。

这个边界是刻意选择：先验证“短期样本协方差是否容易制造脆弱权重，以及收缩协方差是否改善极端仓位和风险集中”。

脚本只硬依赖 `numpy`、`plotly`、`requests`。若本机可用 `scikit-learn`，会优先使用 `LedoitWolf`；若不可用，则自动使用 25% 对角收缩协方差，并在仪表盘中标记模型降级。若本机可用 `scipy`，会优先尝试 SLSQP 优化；若不可用，则使用 NumPy 投影梯度优化器。若安装并配置 Shioaji，可作为行情数据源。

仪表盘使用内嵌 Plotly 资源，生成后的 HTML 可离线打开，不需要再从 CDN 下载图表脚本。

当前 15 檔股票池是 MVP 的人工核心资产池，不是每日自动从全市场扫描产生。设计逻辑是先覆盖台股宽基 ETF、高股息/低波 ETF、科技主题 ETF，以及半导体、电子制造、金融、电信和传统产业龙头；模型可在这个池内根据回撤风险分数，或根据台股多因子分数搭配收缩协方差分配权重。`config/universe_tw.csv` 现在包含 `sector`、`theme`、`ai_supply_chain` 字段，用于解释行业暴露和控制 AI 供应链倾斜。仪表盘中的“股票池策略与机制”区块会说明这层人工资产池、风险加权和执行约束。

## 再平衡回测

仪表盘会默认使用 60 个交易日作为滚动估计窗口，并每 7 个交易日重新计算一次权重：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2024-06 --offline-cache
```

可调整参数：

```bash
python src/risk_dashboard.py --rebalance-window 80 --rebalance-step 20
```

若样本期短于估计窗口，脚本仍会生成仪表盘，并在“数据问题记录”中说明本轮无法执行滚动回测。

## 手动模型盘

模型盘是研究用 paper portfolio，不会自动建仓，不会连接券商，也不会实盘下单。手动触发后，脚本默认以 `2026-06-03` 为计划建仓日，今天可以开始手动建仓；并优先根据过去 5 年最大回撤、年化波动和回撤持续时间计算回撤风险权重。若 5 年共同交易日不足，会自动改用 2 年回撤资料；若 2 年仍不足，会回到当前可用资料，例如本地缓存从 2024 年 1 月开始时，就用 2024 年 1 月至最后可用交易日的数据。

需要特别区分两件事：历史价格只用于分析选股策略与目标权重，真正建仓价格必须使用今日开盘价或手动执行价。执行价尚未录入时，模型盘只输出目标权重和目标金额，`execution_price`、`shares`、`market_value` 会留空，并在仪表盘中显示“待执行价”。等执行价可用后，再用目标金额除以执行价换算整数股；支持零股，但股数必须为整数。

手动建仓成本口径：买进端只扣成交金额与券商手续费估算，不预留政府证券交易税；证券交易税只在未来卖出或调仓卖出时作为成本参考。若 `data/manual_build_orders_建仓日.csv` 存在，仪表盘会自动套用这份手动建仓单并显示买进手续费、买进后剩余现金与未来卖出税估算。

当前正式模型盘口径采用较保守的 75% 建仓比例，剩余 25% 作为策略现金池，用于处理滑价、零股成交差异和后续调仓，不是证券交易税预留。可通过 `--model-invest-ratio` 调整到 0.70 到 0.80 之间。

```bash
python src/risk_dashboard.py --data-source shioaji --start 2021-06 --end 2026-06 --model-portfolio --model-build-date 2026-06-03 --model-method drawdown-risk
```

也可以使用台股多因子收缩优化模型。当前第一轮正式版本采用三层框架：

- 价格层：中期动量、低波动、回撤防御、流动性、趋势强度
- 代理产业层：行业/主题相对强弱、AI 产业暴露
- 代理外部层：资金流代理、风险偏好代理

第一轮仍只使用仓库内现有价格、成交金额、行业/主题与 AI 分类，不直接抓外部 API；后续可把汇率、真实资金流、产业外部指标与社交媒体情绪按同一接口逐步替换代理项。当前分数会先映射成保守预期收益，再搭配 Ledoit-Wolf 收缩协方差求解仅做多、单一资产上限 25% 的目标权重：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-method multi-factor-shrink
```

若希望在保持稳健约束的前提下提高 AI 相关供应链权重，可使用 AI 倾斜参数。`moderate` 会把 AI 供应链软目标提高到约 33%，群组上限 35%；`strong` 会把软目标提高到约 38%，群组上限 40%。默认 `none` 不做倾斜：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-method multi-factor-shrink --ai-tilt moderate
```

基本面质量与价值因子暂未纳入正式权重，因为当前项目还没有稳定的 ROE、本益比、股价净值比或殖利率数据源；后续补齐数据源后，可把质量和价值并入多因子分数。第一轮新增的模型盘 CSV 会额外写出 `price_factor_score`、`industry_ai_score`、`macro_external_score`、`composite_score` 与 `trend_strength_score`，方便比较扩因子前后的权重变化与解释性。

若要直接比较“旧 4 因子”与“新扩展框架”的权重差异，可运行只读比较脚本。该脚本只读取本地缓存与资产池，不会覆盖正式 Dashboard、正式模型盘或模拟盘 CSV；默认把比较摘要写到 `/tmp`：

```bash
python scripts/compare_multi_factor_profiles.py
```

执行后会输出：

- `/tmp/tw_quant_factor_profile_compare.md`
- `/tmp/tw_quant_factor_profile_compare.json`

其中会列出旧/新框架的权重合计、单一资产上限、AI 群组权重，以及 `0050`、`2412`、`00881`、`2330`、`2317`、`2454`、`2303` 等重点标的权重变化。
新版比较摘要还会额外输出：

- 集中度变化：HHI、有效持仓数、前三大权重合计、活跃持仓数
- 权重变化最大标的
- 行业暴露变化
- 主题暴露变化
- AI / 非 AI 暴露变化
- 行业 / 主题 / AI 的风险贡献变化
- 压力情境变化与高相关重叠变化

每日行情更新使用 Shioaji snapshot，只读取行情，不呼叫下单 API。盘中刷新会生成 `_intraday` 市值檔并在仪表盘标示“盘中暂估”；收盘定稿会生成正式市值檔并标示“收盘定稿”：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --update-daily-market --market-date 2026-06-04 --market-mode intraday --model-build-date 2026-06-03 --model-invest-ratio 0.75
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --update-daily-market --market-date 2026-06-04 --market-mode close --model-build-date 2026-06-03 --model-invest-ratio 0.75
```

盘中快照会更新持仓市值、未实现损益和策略监控量能；若当天尚未进入历史 K 线，仪表盘会提示“今日快照尚未纳入滚动回测和长期回撤序列”。

如果你不想依赖 Shioaji，也可以用公开收盘价重建每日市值檔。这个模式会直接从公开行情重新写出 `data/model_portfolio_market_YYYY-MM-DD.csv`，适合放到公网服务里自动每日重建：

```bash
python src/risk_dashboard.py --offline-cache --model-portfolio --model-method multi-factor-shrink --ai-tilt moderate --market-source public-close --market-mode close
```

可调整初始虚拟资金、建仓比例和输出位置：

```bash
python src/risk_dashboard.py --model-portfolio --model-cash 500000 --model-invest-ratio 0.75 --model-output data/model_portfolio_latest.csv --model-method drawdown-risk
```

生成后会在仪表盘右侧显示模型盘建仓、手动执行价状态、调仓周期和建仓执行清单，并输出 CSV：

- `data/model_portfolio_latest.csv`
- `data/model_portfolio_2026-06-03.csv`

仪表盘顶部的“手动执行检查”按钮会展开复核面板，检查建仓股数、整数股规则、资金使用、买进税费口径、今日盈亏和后续调仓节奏。这个按钮只做本地页面检查，不会连接券商或送出订单。

仪表盘中的热力图、风险贡献、普通/收缩方差权重、净值曲线、回撤曲线、滚动回测对比和组合明细区块，都会根据本轮数据自动生成分析建议。说明文字会在每次重新生成仪表盘时随数据变化，用于解释当前集中风险、同源风险、权重变化、回撤差异、换手率和后续调仓参考。

仪表盘的“本轮风险归因与调仓摘要”区块会生成一段可复制的群组风险研究报告摘要。该摘要复用当前权重、收缩协方差风险贡献、行业/主题/AI 供应链归因、相关性、压力情境和本地模拟盘状态；它只用于研究记录和人工复核，不新增交易信号，不写入模拟成交 CSV，也不代表未来报酬预测、个股买卖建议或券商委托状态。

若要确认正式 Dashboard 研究摘要已经同步到 iCloud Obsidian 项目卡片，可运行只读一致性检查。该脚本只读取 `dashboard/index.html` 与 Obsidian 卡片，不重建 Dashboard、不写模拟盘 CSV：

```bash
python scripts/validate_research_brief_sync.py
```

若要先导出 Markdown 预览，可把同一段 Dashboard 研究摘要写到 `/tmp`。该命令只读取正式 Dashboard，并默认输出 `/tmp/tw_quant_research_brief.md`，不会写入 Obsidian 或正式数据：

```bash
python scripts/export_research_brief_markdown.py
```

若要把本地 QA 检查一次跑完，可执行汇总脚本。默认会顺序运行研究摘要同步检查、研究摘要关键数字回归检查、Markdown 预览导出、旧格式 fixture helper 验证，以及旧格式 fixture 的临时 Dashboard 页面验证，并确认正式 Dashboard/模型盘/模拟盘 CSV hash 前后不变：

```bash
python scripts/run_local_qa_checks.py
```

执行后会额外写出 `/tmp/tw_quant_local_qa_summary.md` 与 `/tmp/tw_quant_local_qa_summary.json`：前者适合人工交接，后者适合机器读取；两者都会记录本次 QA 模式、各检查结果、Markdown 预览路径与正式产物 SHA-256。若要改路径，可加 `--summary-output /tmp/your_summary.md --summary-json-output /tmp/your_summary.json`。

若只想跑较快版本、跳过旧格式 fixture 的临时 Dashboard 页面，可加 `--skip-dashboard-fixture`；这仍会保留 helper 验证和正式产物 hash 检查：

```bash
python scripts/run_local_qa_checks.py --skip-dashboard-fixture
```

QA 汇总会自动监控当前最新的 `data/model_portfolio_market_*.csv`，不再固定某一个历史市值档。

## 公网读取

如果你希望从别的设备随时读取 Dashboard，建议把生成后的 `dashboard/index.html` 用一个 Web 服务挂出去。仓库里已经补了一个标准库静态服务入口：

```bash
python scripts/serve_dashboard.py --host 0.0.0.0 --port 8000
```

这个服务默认把 `/` 指向 `dashboard/index.html`，并提供 `/healthz`。如果你要公开部署，建议设置基本认证：

```bash
export DASHBOARD_BASIC_AUTH_USER="dashboard"
export DASHBOARD_BASIC_AUTH_PASSWORD="你的密码"
python scripts/serve_dashboard.py --host 0.0.0.0 --port 8000
```

仓库根目录的 `render.yaml` 也给了一个 Render Web Service 蓝图，适合直接发布到公网。公开部署时建议保留密码，避免模型盘与模拟盘信息裸露。

这个 Web 服务现在还会在后台按固定时间重建一次 Dashboard，默认是 `Asia/Shanghai` 每天 `13:45`，并使用公开收盘价路径，不依赖 Shioaji 密钥。你只要把 Render 的环境变量保留好，服务就会持续更新首页内容。

仪表盘中的“策略监控与建议单”区块会对 15 檔股票池逐一计算 20 日均线、60 日均线、14 日 RSI、成交量比、20 日平均成交金额、多因子分数与建仓后报酬。这个区块用于长期持续监控，不是单日主观判断；只有条件连续成立至少 2 天，才会进入手工建议单。MVP 规则如下：

- 买入建议：价格较建仓成本回落约 3%，但仍在 60 日趋势上方，RSI 介于 35 到 55，且量能未明显萎缩，表示回落但未明显转弱。
- 卖出建议：价格较建仓成本下跌约 6%，或跌破 60 日趋势且持仓转弱，并连续观察至少 2 天，先建议减码 25%。
- 获利卖出：价格较建仓成本上涨约 8%，且 RSI 高于 70，并连续观察至少 2 天，先建议分批卖出 20%。
- 观察：未触发以上条件时不产生手工订单，只保留技术状态与原因。

多因子分数目前由趋势、动能、风险和量能四类组成：趋势因子看 20 日/60 日均线，动能因子看 20 日与 60 日报酬，风险因子看建仓后损益阈值，量能因子看今日成交量相对 20 日均量。分数用于排序和解释，真正进入手工订单仍需满足明确触发条件。

仪表盘中的“模拟盘调仓确认”区块只显示未来新的待确认买入或卖出建议。2026-06-03 初始建仓单按虚拟盘成交口径视为已执行，不再作为待处理订单显示；对应持仓数量、成本和盈亏会在“今日持仓与收盘盈亏”区块展示。页面按钮只更新当前浏览器的本地状态，不会连接券商、不具备真实交易能力。每笔待确认建议会显示一个稳定单号（`trade_id`），用于对齐页面复核、脚本落账和本地模拟成交 CSV；单号不包含价格、股数、中文原因或任何券商凭证。

若要把本轮建议单真正落入模拟盘，使用 `--execute-simulated-trades`。脚本会写入 `data/simulated_trades_交易日.csv`，并更新 `data/simulated_positions_latest.csv` 与 `data/simulated_positions_交易日.csv`；后续仪表盘会优先读取最新模拟持仓，而不是重复使用初始建仓单。新写入的模拟成交 CSV 会包含 `trade_id` 欄位；旧 CSV 没有此栏位时，脚本仍会用交易日、标的和方向做兼容去重。现在每日收盘后的自动重建流程也会带上这个开关，所以 Dashboard 会同步刷新持仓、执行状态与研究说明区。

默认行为是幂等落账：未指定批次时，模拟成交批次视为 `01`；同一交易日、同一标的、同一方向、同一触发规则重复执行，不会重复写入成交，也不会再次减少持仓。若确实需要同日分批，必须明确指定新的批次号，例如 `--simulated-trade-batch-seq 02`、`03`，并在交接中说明这是人为确认的第二批或第三批模拟成交；不要用分批绕过重复落账保护。

Dashboard 的“模拟盘调仓确认”区块会显示批次状态小结：目前批次、已写入本地模拟成交 CSV 的批次、旧格式纪录与目前待确认批次。旧模拟成交 CSV 若没有 `trade_id`，会单独显示为“旧格式”，并继续按交易日、标的和方向相容防重；页面确认只保存在当前浏览器，真正写入本地模拟成交 CSV 仍需执行 Python 主脚本。

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --execute-simulated-trades
```

如需验证模拟盘落账幂等性或做临时演练，可把成交与持仓输出重定向到 `/tmp`，避免覆盖正式模拟盘 CSV：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate --execute-simulated-trades --simulated-trade-batch-seq 01 --simulated-trades-output /tmp/tw_quant_idempotency_trades.csv --simulated-positions-output /tmp/tw_quant_idempotency_positions.csv
```

第二次复跑临时验证时，记得同时把 `--model-execution-orders` 指向上一轮临时持仓，模拟正式流程“优先读取最新模拟持仓”的行为：

```bash
python src/risk_dashboard.py --start 2024-01 --end 2026-06 --offline-cache --data-source twse --model-portfolio --model-build-date 2026-06-03 --model-invest-ratio 0.75 --model-execution-orders /tmp/tw_quant_idempotency_positions.csv --model-market-values data/model_portfolio_market_2026-06-08.csv --model-method multi-factor-shrink --ai-tilt moderate --execute-simulated-trades --simulated-trade-batch-seq 01 --simulated-trades-output /tmp/tw_quant_idempotency_trades.csv --simulated-positions-output /tmp/tw_quant_idempotency_positions.csv
```

验收标准：第二次输出应显示本轮新增模拟成交为 0；临时成交 CSV 行数不增加；临时持仓 CSV 不因重复落账继续减少股数。若要验证同日第二批，把两次命令都改为 `--simulated-trade-batch-seq 02` 并使用同一组临时成交/持仓输出；第一次应新增第二批成交，第二次同样 `02` 复跑应新增 0 笔。模拟落账验证必须使用 `--offline-cache --data-source twse`，不要与 `--data-source shioaji`、非离线 `--data-source auto` 或 `--update-daily-market` 混跑。

若要专门验证旧格式模拟成交 CSV 的批次状态展示，可使用本地 fixture 脚本。该脚本只写 `/tmp`，不会覆盖正式 `data/simulated_*`；默认验证 `load_simulated_trade_batch_status()` 会把无 `trade_id` 的两笔成交归为“舊格式”，带 `--dashboard` 时会临时重建 Dashboard 并确认页面显示“舊格式 2 筆”，且不会把旧格式误显示为“批次 01”：

```bash
python scripts/validate_legacy_trade_batch_status.py
python scripts/validate_legacy_trade_batch_status.py --dashboard
```

若本地离线缓存不足 5 年，脚本会先降级为 2 年回撤；若 2 年仍不足，会改用建仓日前所有可用资料。只有可用共同交易日少于 60 天时，才会在“数据问题记录”中说明模型盘未生成。

## 验证方式

建议按顺序执行：

```bash
python -m py_compile src/risk_dashboard.py
python src/risk_dashboard.py --offline-cache
python src/risk_dashboard.py --start 2024-01 --end 2024-06 --offline-cache
python src/risk_dashboard.py --start 2024-01 --end 2024-06 --offline-cache --model-portfolio
```

如果公开行情接口限流或失败，可先确认 `data/cache/` 是否已有缓存，再使用：

```bash
python src/risk_dashboard.py --allow-stale-cache
```

本项目不需要 `.env`、API Key、Token 或账号凭证。
