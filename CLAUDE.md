# CLAUDE.md

<!-- @claude-metadata
github_project:
notion_project_page: 3662f591-0ab7-81f6-8f13-f4284b26d93b
-->

グローバルルールは `~/.claude/rules/` を参照。

## このリポジトリ

`bonsaidev` — CLI エントリ名は `bonsai`。CLI ランナー抽象 + Supervisor-Worker-Reviewer の 3 ロール協調による自律コーディングエージェント。

設計プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md` (D1〜D19 + レビュー反映済み。命名は旧 D13 のまま `kaizen-agent` / `auto-dev` だが、再検討の結果 `bonsaidev` / `bonsai` に変更。経緯は `.research_output/research_naming_20260521/` 参照)

## Phase 1 スコープ (実装中)

- `src/bonsai/runners/{base,tmux_rpc,claude_p}.py`
- `src/bonsai/roles/{worker,supervisor,reviewer}.py`
- `src/bonsai/state/{schemas,plan,heartbeat,permissions,events}.py`
- `src/bonsai/integrations/tmux.py` (Notion/GitHub はスタブ + bash bridge)
- `src/bonsai/cli.py` (`start` / `attach` / `kill`)
- 状態は案 B: `.plans/<name>/plan.md` + `.auto-dev/<name>/`
- HITL デフォルト = PR merge のみ人間承認
