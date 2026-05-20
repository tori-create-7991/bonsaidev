# bonsaidev Phase 1 MVP 実装プラン

作成日: 2026-05-21
完了目標: 2026-06-05 まで（約 2 週間）
対象: 新リポジトリ `bonsaidev` (CLI 名 `bonsai`) の Python ハイブリッド実装
親プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md` (D1〜D19 + code-reviewer レビュー反映済み、確定済み。命名は再検討で `bonsaidev` / `bonsai` に変更 — 経緯は `.research_output/research_naming_20260521/`)

## 背景

既存 bash auto-dev (`~/Repositories/my/00_my_env/global-config-sync/scripts/auto-dev/`) を Python + bash 薄シムで再実装する。MVP は **tmux_rpc ランナーを主軸**にサブスク Claude Max を活用しつつ、2026-06-15 の Agent SDK credit 制移行に備え `claude_p` ランナーも Phase 1 で事前実装する (D17)。

Phase 1 スコープ外: Codex / Gemini / Aider+Ollama / OTel / HITL per-action 拡張 / Eval recorder / Notion-GitHub フル Python 化。

## 設計指針 (親プランから抜粋)

- **D3 ランナー抽象**: `Runner` Protocol + 実装クラス
- **D4 状態管理**: 案 B (`.plans/<name>/plan.md` + `.auto-dev/<name>/`)
- **D7 HITL**: デフォルト=PR merge のみ人間承認
- **D14 デフォルトロール構成**: 全ロール tmux_rpc (Claude Max)
- **D18 自動化レート制限**: send-keys 最低 2-3 秒間隔・並列 ≤ 3
- **must 1**: `Runner.stream()` 例外セマンティクス明示 + `RunnerError` 型
- **must 2**: ANSWER ファイル atomic rename プロトコル
- **must 3**: Notion/GitHub はスタブ + bash bridge
- **should 2**: `extra="ignore"` 互換読み込みモード
- **should 4**: `RunnerRequest.skills_dir` フィールド
- **question 2 (heartbeat)**: 案 A 独立スレッド更新

## 実装ステップ

### A. プロジェクト土台 (TDD 環境整備)

- [ ] A1: `src/bonsai/__init__.py` + パッケージレイアウト雛形 (空ファイル含む) を作成
- [ ] A2: `uv sync --dev` で依存解決を確認 (pyproject.toml は scaffolding 済み)
- [ ] A3: `.pre-commit-config.yaml` を追加 (ruff format + ruff check + gitleaks)
- [ ] A4: `pre-commit install` 実行
- [ ] A5: `.github/workflows/ci.yml` を追加 (uv sync → ruff → mypy → pytest)
- [ ] A6: `tests/conftest.py` 追加 (pytest-asyncio mode=auto 確認)

### B. State 層 (Pydantic v2 スキーマ + I/O) — TDD: RED → GREEN

- [ ] B1: `tests/unit/test_schemas.py` を先に書く (Heartbeat / PlanState / Permissions / Event)
- [ ] B2: `src/bonsai/state/schemas.py` 実装 — `extra="forbid"` (write) と `extra="ignore"` 読み込みヘルパ (should 2)
- [ ] B3: `tests/unit/test_plan_parser.py` を書く (チェックボックス進捗 / `## Status:` 行抽出 / Pending Question 抽出)
- [ ] B4: `src/bonsai/state/plan.py` 実装 — `parse_plan(path) -> PlanState`
- [ ] B5: `tests/unit/test_events.py` を書く (append-only / model_validate ラウンドトリップ)
- [ ] B6: `src/bonsai/state/events.py` 実装 — `EventLogger.append(event)` (file lock 不要、追記のみ)
- [ ] B7: `tests/unit/test_permissions.py` を書く (Worker / SUPERVISOR_ONLY / REVIEWER_ONLY セクション分離)
- [ ] B8: `src/bonsai/state/permissions.py` 実装 — 既存 bash 形式 (lib/permissions.sh) を Python で再現
- [ ] B9: `tests/unit/test_heartbeat.py` を書く (独立タスクでの定期更新 / stop_event 即時終了)
- [ ] B10: `src/bonsai/state/heartbeat.py` 実装 — `heartbeat_loop(plan_dir, stop_event)` (案 A, §6.5)
- [ ] B11: `tests/unit/test_state_io.py` で atomic rename (`.answer.tmp → .answer`, must 2) を検証

### C. Runner 層 — TDD: RED → GREEN

- [ ] C1: `src/bonsai/runners/base.py` 実装 — `Runner` Protocol / `RunnerRequest` / `RunnerResult` / `RunnerEvent` / `RunnerError` (must 1, should 4)
- [ ] C2: `tests/unit/test_runners.py` に Mock Runner を書き、Protocol 適合性を検証
- [ ] C3: `tests/unit/test_runner_error_semantics.py` — `stream()` で `RunnerError` が raise されることを検証 (must 1)
- [ ] C4: `src/bonsai/integrations/tmux.py` 実装 — `start_session` / `send_keys` / `capture_pane` / `pipe_pane` / `kill_session` (subprocess.run 同期)
- [ ] C5: `tests/unit/test_tmux_integration.py` — tmux 未起動環境でも動くようサブプロセス mock テスト
- [ ] C6: `tests/unit/test_rate_limiter.py` を書く (`send_keys` 間隔 ≥ 2.5s 強制, D18)
- [ ] C7: `src/bonsai/runners/tmux_rpc.py` 実装 — `RateLimiter` 内蔵 / `.ready` ハンドシェイク / ANSI 除去 / idle 検知
- [ ] C8: `tests/integration/test_tmux_rpc_runner.py` — モック tmux で完了検知シーケンスを検証
- [ ] C9: `src/bonsai/runners/claude_p.py` 実装 (D17 事前実装) — `claude -p --output-format stream-json --append-system-prompt ...` subprocess
- [ ] C10: `tests/unit/test_claude_p_runner.py` — Max credit 消費を避けるため subprocess を mock
- [ ] C11: `src/bonsai/runners/registry.py` — 名前 → クラス解決 + フォールバックチェーン (Phase 1 は tmux_rpc / claude_p のみ登録)

### D. Role 層 (Worker / Supervisor / Reviewer 移植)

- [ ] D1: `src/bonsai/roles/worker.py` 実装 — `run_worker(plan, perms, runner_cfg)`
  - heartbeat タスク起動 (B10)
  - ANSWER ファイル読み込みプロトコル (must 2 / §6.4 Worker 側)
  - Runner.stream() を await し events.jsonl に書き込む
  - plan.md の `## Status:` を更新
- [ ] D2: `tests/unit/test_worker.py` — モックランナーで 1 サイクルを検証
- [ ] D3: `src/bonsai/roles/supervisor.py` 実装 — `Supervisor` クラス + `async loop()` (§6.3)
  - state machine: INIT → RUNNING → (STALLED / NEEDS_INPUT / REVIEW_LOOP) → DONE
  - heartbeat 古い & tmux 死亡 → restart (max 5)
  - ANSWER atomic rename 書き込み (must 2 / §6.4 Supervisor 側)
- [ ] D4: `tests/integration/test_supervisor_loop.py` — モックランナーで全状態遷移を網羅 (§6.2)
- [ ] D5: `src/bonsai/roles/reviewer.py` 実装 — 単一ラウンドレビュー / CLEAR or ISSUES 判定
- [ ] D6: `tests/integration/test_review_round.py` — 1〜3 ラウンドで CLEAR / ISSUES 経路を検証

### E. Integrations (スタブ + bash bridge)

- [ ] E1: `src/bonsai/integrations/notion.py` — `update_status(task_id, status)` / `add_active_session(...)` 関数を bash の `notion.sh` を subprocess 呼び出しでブリッジ (must 3)
- [ ] E2: `tests/unit/test_notion_integration.py` — subprocess mock + 引数組み立てのみ検証
- [ ] E3: `src/bonsai/integrations/github.py` — `create_pr(branch, title, body)` を `gh pr create` の subprocess ラッパに (must 3)
- [ ] E4: `tests/unit/test_github_integration.py` — subprocess mock

### F. CLI (Typer) と起動シム

- [ ] F1: `src/bonsai/cli.py` 実装 — Typer ベース、`start` / `attach` / `kill` サブコマンド
  - `bonsai start --project <dir> --plan <plan.md> --notion-task <id> --issue <num> [--worker-model ...] [--worker-runner ...]`
  - `bonsai attach --role worker|supervisor|reviewer <plan-name>` → tmux attach
  - `bonsai kill <plan-name>` → tmux kill-session 全ロール
- [ ] F2: `tests/unit/test_cli.py` — Typer の `CliRunner` で引数パースを検証
- [ ] F3: `scripts/bonsai-launch.sh` 追加 — tmux 起動 + `uv tool run bonsai start` 呼び出し薄シム
- [ ] F4: `bonsai start` のスモークテストを `tests/integration/test_cli_smoke.py` に追加 (実 tmux 起動はせず dry-run モード)

### G. ドキュメントと締め

- [ ] G1: `README.md` に「Phase 1 MVP の使い方」セクション追加 (uv tool install + bonsai start の最小例)
- [ ] G2: `docs/architecture.md` 新規作成 — 親プラン §6 の状態機械図 + 案 B レイアウトを転記
- [ ] G3: `docs/migration-from-bash.md` 新規作成 — 旧 bash auto-dev からの移行手順 (Phase 2 ブリッジ準備)
- [ ] G4: CHANGELOG.md 追加 (v0.1.0-mvp エントリ)
- [ ] G5: `uv tool install -e .` でローカルインストール確認 (`bonsai --help` で動作)
- [ ] G6: PR 作成 (`Closes #<issue-number>` 付き)

## 検証項目 (PR 作成前)

- [ ] `uv run pytest` 全 pass
- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy src/`
- [ ] `pre-commit run --all-files` pass
- [ ] CI (GitHub Actions) pass
- [ ] `uv tool install -e .` 後に `bonsai --help` が動作
- [ ] `bonsai start --help` で必須/任意引数が正しく表示
- [ ] dry-run モード (`--dry-run`) で tmux 起動なしに引数解析と plan parse まで完走

## 前提条件 (実装着手前にチェック)

- [x] bonsaidev リポジトリが Public で作成済み (https://github.com/tori-create-7991/bonsaidev)
- [x] 初期 scaffolding (README/LICENSE/.gitignore/pyproject.toml/mise.toml/CLAUDE.md) push 済み (ed11d99)
- [x] Python 3.12 + uv が mise で利用可能
- [x] 設計プラン D1〜D19 + レビュー反映が確定済み
- [x] 既存 bash auto-dev は並行稼働継続 (ロールバック保険)
- [x] 命名再検討完了 — kaizen-agent / auto-dev → bonsaidev / bonsai (`.research_output/research_naming_20260521/`)

## 関連資料

- 親設計プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md`
- 命名再検討レポート: `.research_output/research_naming_20260521/final_report.md`
- 移植元 bash 実装: `~/Repositories/my/00_my_env/global-config-sync/scripts/auto-dev/`
- 移植元 lib: `lib/{ai_runner,common,permissions,pr,review}.sh`

## Status: running
