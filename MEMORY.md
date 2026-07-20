# Project Memory

## Purpose

This file preserves durable project context for the Taiwan equity risk dashboard. It complements `AGENTS.md`; project rules in `AGENTS.md` take precedence.

## Architecture Decisions

- The shared source of truth is this iCloud Workspace. Code, documentation, generated Dashboard artifacts, model CSVs, and handoff records are written here.
- Each device keeps its own `.venv`, `.shioaji.local.env`, Shioaji runtime state, `data/cache/`, and `data/matrix_cache/`. These paths are local-only and must not be committed.
- The system uses public close data by default. Shioaji is an optional read-only market-data source; no real order, modification, cancellation, or account-trading operation is permitted.
- Daily close updates use `multi-factor-shrink`, `ai_tilt moderate`, `market-source public-close`, `market-mode close`, and `--execute-simulated-trades` for the local paper portfolio only.
- Public delivery is a separate deployment path from the shared Workspace `origin`. A release is complete only after the public Dashboard body and cache version are verified.

## Operations

- The recurring automation id is `dashboard`, named `台股 Dashboard 每日收盘更新`, and runs against this Workspace after Taiwan market close.
- The watchdog automation id is `dashboard-4`, named `台股 Dashboard 更新漏跑补偿`, and runs on weekdays at 16:30 Asia/Shanghai to detect stale or empty daily runs and retry the full trading-day update when needed.
- Each daily run must update `dashboard/index.html`, refresh the paper-portfolio artifacts when applicable, push the deployment repository, and verify the public URL.
- Daily and watchdog automations should treat the public Dashboard as the user-facing report surface. After cloud verification, keep the Codex thread response minimal and put detailed daily / review summaries in the Dashboard daily update summary, handoff docs, and automation memory.
- Paper-portfolio actions are automatic when the daily run includes `--execute-simulated-trades`: strategy-triggered virtual trades are written to local CSV artifacts without user confirmation. Dashboard buttons are review/audit markers stored in the browser only and must not gate CSV ledgering.
- The public server sends no-cache headers and a content-derived `ETag` / `X-Dashboard-Version`. A changed Dashboard content hash is the release cache version, allowing every device to revalidate the current release. Every public Dashboard publish must update and verify this cache version through `/version.json`, `ETag`, and `X-Dashboard-Version`.
- For month boundaries, update the `--end` window to the current month. Keeping an old month can roll the common price series backward.
- The daily automation must be gated by the Taiwan trading calendar. On a weekend or exchange holiday it publishes no artifacts and returns a Chinese status summary; on a trading day it rebuilds, publishes, and returns the same summary fields with the new verification results.
- If TWSE 202607-style monthly data becomes complete after an earlier same-day rebuild, rerun the public-close command with `--offline-cache --allow-stale-cache` to bypass the aggregate matrix cache and read the refreshed monthly JSON cache directly.

## Known Constraints

- Do not read, print, or store secret values. This file only records the location and boundary of local-only configuration.
- A Codex project/thread path binding does not migrate automatically when a folder moves. New project entries and recurring automations must explicitly point to this Workspace.
- Render availability and deployment state must be checked independently from local generation; a successful local build alone does not prove public availability.
- The SSH host alias `github-worldcup` is only a GitHub authentication alias on this machine. It is not a World Cup project dependency. When publishing this dashboard, sync only this Taiwan equity project directory into the `futienchun-com-dashboard` deployment repository.

## User Corrections

- 2026-07-12: The iCloud Workspace is the only project directory. The former `/Users/tonyfu/Documents/稳健投资组合量化模型构建` directory was a two-file placeholder, not a project source, and was removed to prevent future path confusion.
- 2026-07-13: The `dashboard` automation triggered at 13:46 and ended after about 17 minutes with `last_agent_message=null`; no files, commits, or public Dashboard version changed. Treat this as an automation empty-run failure, not a market-data issue. The weekday 16:30 watchdog `dashboard-4` was added to check for stale output and compensate automatically.
- 2026-07-13: The Dashboard UI should present paper-portfolio trading as automatic local ledgering plus review/audit, not a manual confirmation workflow. Real broker order placement remains out of scope and prohibited.
