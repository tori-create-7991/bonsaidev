# CLAUDE.md

<!-- @claude-metadata
github_project:
notion_project_page:
-->

グローバルルールは `~/.claude/rules/` を参照。

## このリポジトリ

`kaizen-agent` — CLI エントリ名は `auto-dev`。CLI ランナー抽象 + Supervisor-Worker パターンの自律開発フレームワーク。

設計プラン: `~/Repositories/my/00_my_env/.plans/auto-dev-new-repo-design.md` (D1〜D19 + レビュー反映済み、確定済み)

## Phase 1 スコープ (実装中)

- `src/auto_dev/runners/{base,tmux_rpc,claude_p}.py`
- `src/auto_dev/roles/{worker,supervisor,reviewer}.py`
- `src/auto_dev/state/{schemas,plan,heartbeat,permissions,events}.py`
- `src/auto_dev/integrations/tmux.py` (Notion/GitHub はスタブ + bash bridge)
- `src/auto_dev/cli.py` (`start` / `attach` / `kill`)
- 状態は案 B: `.plans/<name>.md` + `.auto-dev/<name>/`
- HITL デフォルト = PR merge のみ人間承認
