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
- Each daily run must update `dashboard/index.html`, refresh the paper-portfolio artifacts when applicable, push the deployment repository, and verify the public URL.
- The public server sends no-cache headers and a content-derived `ETag` / `X-Dashboard-Version`. A changed Dashboard content hash is the release cache version, allowing every device to revalidate the current release.
- For month boundaries, update the `--end` window to the current month. Keeping an old month can roll the common price series backward.

## Known Constraints

- Do not read, print, or store secret values. This file only records the location and boundary of local-only configuration.
- A Codex project/thread path binding does not migrate automatically when a folder moves. New project entries and recurring automations must explicitly point to this Workspace.
- Render availability and deployment state must be checked independently from local generation; a successful local build alone does not prove public availability.
