# kaizen-agent

改善ループ × 自律エージェント — CLI ランナー抽象 + Supervisor-Worker パターンでサブスク Claude を最大活用するコーディング自動化フレームワーク。

CLI エントリポイント名は `auto-dev` (既存 [start-auto-dev](../my/00_my_env/global-config-sync/skills/start-auto-dev) スキルとの統合維持のため)。

## 設計思想

- **追加課金ゼロ厳守**: サブスク Claude Max を tmux 経由で完全活用 (`tmux_rpc` 主軸)
- **CLI ランナー抽象**: `Runner` Protocol で claude / codex / aider / gemini を統一切替
- **Supervisor-Worker-Reviewer**: 3 ロールが tmux session で分離稼働
- **ファイル経由状態管理**: `.plans/<name>.md` (人間) + `.auto-dev/<name>/` (ツール) の責務分離
- **HITL チェックポイント**: PR merge のみデフォルト人間承認

詳細設計は [.plans/auto-dev-new-repo-design.md](https://github.com/tori-create-7991/00_my_env/blob/main/.plans/auto-dev-new-repo-design.md) (親リポ) を参照。

## ステータス

設計確定 (D1〜D19 + レビュー反映済み)。Phase 1 MVP 実装中。

## インストール (将来)

```bash
uv tool install git+https://github.com/tori-create-7991/kaizen-agent.git
```

## ライセンス

MIT
