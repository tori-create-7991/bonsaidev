# bonsaidev Phase 1 MVP 実装プラン

作成日: 2026-05-21 / 改訂: 2026-05-21 (最終ゴール反映 — dogfooding-first にスリム化)
完了目標: 2026-06-05 まで（約 2 週間）
対象: `bonsaidev` (CLI 名 `bonsai`) の Python ハイブリッド実装
親プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md` (D1〜D19 確定。命名再検討で `bonsaidev` / `bonsai`)

## 最終ゴール (この Phase が貢献する先)

> **「自分が毎日使う、複数の CLI エージェントを cost × quality で見定めて指揮できる、bonsai 哲学が貫かれた個人ツール。他人にも使われれば嬉しい。生存は副産物として満たす」**

優先順位: **B 個人生産性 > C マルチランナー > E 哲学 > D OSS > A 生存**

### この優先順位から導かれる Phase 1 の判断軸

1. **dogfooding ファースト** — 「自分が今日明日 bonsai を使えるか」が唯一の Done 判定。早期に走るほうが docs より勝つ。
2. **Runner Protocol = moat** — 後で変えにくい API なので C1 はじっくり設計に時間を割く。
3. **bonsai 哲学を意思決定軸に** — 「小さく / 継続的に / 考えて剪定」を YAGNI/DRY の上位に置く権利を持つ。
4. **OSS 配布前提のドキュメント・CI は最小限** — G2/G3 は Phase 1.6 (OSS prep) に送る。
5. **claude_p は panic 用ではなく平時の選択肢** — 6/15 サバイバルへの過度な防御を捨て、生産性 5-10x が credit を正当化する。

## 設計指針 (親プランから抜粋)

- D3 ランナー抽象 / D4 状態管理案 B / D7 HITL = PR merge のみ / D14 全ロール tmux_rpc / D18 RateLimiter / must 1 RunnerError / must 2 ANSWER atomic rename / must 3 Notion/GitHub bash bridge / should 2 `extra="ignore"` 互換 / should 4 `skills_dir` フィールド / question 2 heartbeat 案 A

## ドッグフード・マイルストーン (この順で「自分が使える」が広がる)

### 🌱 M1: Worker walks (Day 1-4) — 「Worker が tmux で動いて events.jsonl 書ける」
**達成条件**: `bonsai start --dry-run ...` で plan を parse、`bonsai start ...` (実起動) で Worker を tmux に起動して 1 タスクをこなして停止する。events.jsonl と heartbeat が書かれている。

依存タスク: A1〜A4 + B1〜B6 (schemas/plan/events) + B9〜B10 (heartbeat) + **C0 + C1** (Runner Protocol 設計+実装) + C4 (tmux integration) + C6〜C7 (RateLimiter + tmux_rpc) + D1 (worker role) + F1 部分 (CLI start)

🎯 **M1 完了直後に dogfooding spike**: bonsai を使って 00_my_env で軽微な修正タスクを 1 件完走させる。**何が壊れるか観察**して B2-C0 に戻る。

### 🌿 M2: Supervisor walks (Day 5-8) — 「Supervisor が状態機械を回せる」
**達成条件**: Worker が止まると Supervisor が restart する。`## Status: needs_input` → ANSWER 書き込み → Worker 再起動が機能する。`## Status: completed` で次フェーズに進む。

依存タスク: B7〜B8 (permissions) + B11 (atomic rename) + D3 (supervisor) + E1〜E2 (notion ブリッジ) + F1 残り

🎯 **M2 完了直後**: bonsai に "夜間タスク" を 1 件任せて翌朝結果を見る。

### 🌳 M3: Reviewer round (Day 9-12) — 「最後まで自走して PR ができる」
**達成条件**: completed 後に Reviewer が走り、CLEAR なら Supervisor が gh で PR 作成、ISSUES なら Worker 再起動して修正。

依存タスク: D5〜D6 (reviewer) + E3〜E4 (github ブリッジ) + C9〜C10 (claude_p 事前実装) + C11 (runner registry)

🎯 **M3 完了直後**: bonsai を使って bonsai 自身のリファクタタスクを 1 件回す (= 究極の dogfooding)。

### 🎍 M4: Polish & ship (Day 13-14) — 「README で人に見せられる + Issue #1 close」
**達成条件**: README 更新 / pre-commit gitleaks 含む / CI が test pass する / PR `Closes #1`。

依存タスク: A5 (CI 最小) + G1 (README 使い方) + G6 (PR)

## 実装ステップ (約 35 タスク、TDD で test → impl)

### A. プロジェクト土台
- [ ] A1: `src/bonsai/__init__.py` + パッケージレイアウト雛形 (空ファイル含む)
- [ ] A2: `uv sync --dev` で依存解決確認
- [ ] A3: `.pre-commit-config.yaml` (ruff format + check + gitleaks)
- [ ] A4: `pre-commit install`
- [ ] A5: `.github/workflows/ci.yml` — **最小限** (uv sync + ruff check + pytest のみ。mypy/release は後回し)
- [ ] A6: `tests/conftest.py` (pytest-asyncio mode=auto)

### B. State 層 (Pydantic v2)
- [ ] B1: `tests/unit/test_schemas.py`
- [ ] B2: `src/bonsai/state/schemas.py` (`extra="forbid"` write + `extra="ignore"` read, should 2)
- [ ] B3: `tests/unit/test_plan_parser.py`
- [ ] B4: `src/bonsai/state/plan.py` (`parse_plan(path) -> PlanState`)
- [ ] B5: `tests/unit/test_events.py`
- [ ] B6: `src/bonsai/state/events.py` (`EventLogger.append`)
- [ ] B7: `tests/unit/test_permissions.py`
- [ ] B8: `src/bonsai/state/permissions.py`
- [ ] B9: `tests/unit/test_heartbeat.py`
- [ ] B10: `src/bonsai/state/heartbeat.py` (案 A 独立 asyncio タスク, §6.5)
- [ ] B11: `tests/unit/test_state_io.py` で `.answer.tmp → .answer` atomic rename (must 2)

### C. Runner 層 — **moat 層、じっくり設計**
- [ ] **C0: Runner Protocol API 設計レビュー** (新規・最重要)
  - `Runner` Protocol の責務境界を docstring で言語化
  - `RunnerRequest` / `RunnerResult` / `RunnerEvent` / `RunnerError` 各フィールドの「変えにくさ」を意識
  - Mock Runner で「Claude / Codex / Aider / Gemini が将来全部実装できるか」を thought experiment で検証
  - architect-reviewer agent に API レビューを 1 回依頼
- [ ] C1: `src/bonsai/runners/base.py` 実装 (must 1, should 4)
- [ ] C2: `tests/unit/test_runners.py` (Mock Runner で Protocol 適合性)
- [ ] C3: `tests/unit/test_runner_error_semantics.py` (`stream()` で `RunnerError` raise, must 1)
- [ ] C4: `src/bonsai/integrations/tmux.py` (start_session / send_keys / capture_pane / pipe_pane / kill_session)
- [ ] C5: `tests/unit/test_tmux_integration.py` (subprocess mock)
- [ ] C6: `tests/unit/test_rate_limiter.py` (`send_keys` ≥ 2.5s, D18)
- [ ] C7: `src/bonsai/runners/tmux_rpc.py` (`RateLimiter` 内蔵 / `.ready` ハンドシェイク / ANSI 除去 / idle 検知)
- [ ] C8: `tests/integration/test_tmux_rpc_runner.py` (モック tmux で完了検知)
- [ ] C9: `src/bonsai/runners/claude_p.py` (D17、**平時の選択肢として実装**)
- [ ] C10: `tests/unit/test_claude_p_runner.py` (subprocess mock、Max credit 節約)
- [ ] C11: `src/bonsai/runners/registry.py` (名前→クラス + フォールバックチェーン)

### D. Role 層
- [ ] D1: `src/bonsai/roles/worker.py` — heartbeat タスク起動 / ANSWER 読込 / Runner.stream() / plan.md Status 更新
- [ ] D2: `tests/unit/test_worker.py` (Mock Runner で 1 サイクル)
- [ ] D3: `src/bonsai/roles/supervisor.py` — state machine (§6.2-6.3) / restart (max 5) / ANSWER atomic write
- [ ] D4: `tests/integration/test_supervisor_loop.py` (全状態遷移網羅)
- [ ] D5: `src/bonsai/roles/reviewer.py` (1 ラウンド CLEAR/ISSUES 判定)
- [ ] D6: `tests/integration/test_review_round.py` (1〜3 ラウンド経路)

### E. Integrations (DAU 必須、bash bridge)
- [ ] E1: `src/bonsai/integrations/notion.py` (既存 `notion.sh` を subprocess ブリッジ, must 3)
- [ ] E2: `tests/unit/test_notion_integration.py` (subprocess mock)
- [ ] E3: `src/bonsai/integrations/github.py` (`gh pr create` ラッパ, must 3)
- [ ] E4: `tests/unit/test_github_integration.py` (subprocess mock)

### F. CLI (Typer + 起動シム) — **dogfooding 必須**
- [ ] F1: `src/bonsai/cli.py` Typer `start` / `attach` / `kill`
- [ ] F2: `tests/unit/test_cli.py` (Typer CliRunner で引数パース)
- [ ] F3: `scripts/bonsai-launch.sh` (tmux + `uv tool run bonsai start` 薄シム)
- [ ] **F4: `bonsai start --dry-run` モード** (必須 — M1 dogfooding に効く。tmux 起動なしで引数解析 + plan parse)

### G. ドキュメントと締め (slim)
- [ ] G1: README に「Phase 1 MVP の使い方」最小例 (uv tool install + bonsai start)
- [ ] G5: `uv tool install -e .` ローカルインストール確認 (`bonsai --help`)
- [ ] G6: PR 作成 (`Closes #1`)

**送り (Phase 1.6 OSS prep へ)**: G2 `docs/architecture.md` / G3 `docs/migration-from-bash.md` / G4 CHANGELOG.md

## 検証項目 (PR 作成前)

- [ ] `uv run pytest` 全 pass
- [ ] `uv run ruff format --check .` / `uv run ruff check .`
- [ ] `pre-commit run --all-files` pass (gitleaks 含む)
- [ ] GitHub Actions CI pass (最小: ruff + pytest)
- [ ] `uv tool install -e .` 後に `bonsai --help`
- [ ] `bonsai start --dry-run ...` で plan parse まで完走
- [ ] **🎍 dogfooding ゴール: bonsai を使って bonsai 自身のリファクタタスクを 1 件回せた** (M3 達成証明)

## スコープ外 (明示)

- Codex / Gemini / Aider+Ollama (Phase 1.5)
- OTel / HITL per-action 拡張 / Eval recorder (Phase 1.5)
- Notion-GitHub フル Python 化 (Phase 1.5)
- `docs/architecture.md` / `docs/migration-from-bash.md` / CHANGELOG (Phase 1.6 OSS prep)
- mypy CI 統合 / release workflow (Phase 1.6+)
- スター獲得施策 / コミュニティドキュメント (Phase 3+)

## 前提条件 (実装着手前にチェック)

- [x] bonsaidev リポジトリ Public 作成 + 初期 scaffolding push 済み (ed11d99)
- [x] Python 3.12 + uv が mise で利用可能
- [x] 設計プラン D1〜D19 + レビュー反映確定
- [x] 既存 bash auto-dev は並行稼働継続 (ロールバック保険)
- [x] 命名再検討完了 — kaizen-agent / auto-dev → bonsaidev / bonsai
- [x] **最終ゴール確認済み** (B > C > E > D > A)

## 関連資料

- 親設計プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md`
- 命名再検討レポート: `.research_output/research_naming_20260521/final_report.md`
- 移植元 bash: `~/Repositories/my/00_my_env/global-config-sync/scripts/auto-dev/`
- 移植元 lib: `lib/{ai_runner,common,permissions,pr,review}.sh`

## Status: running
