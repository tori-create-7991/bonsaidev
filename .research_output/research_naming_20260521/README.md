# Research Project: kaizen-agent / auto-dev リポジトリ名の再検討

## 調査概要

- **日付**: 2026-05-21
- **目的**: 個人OSS Python製マルチエージェントCLIフレームワークのリポジトリ名を実装着手前に確定する
- **現状**: `kaizen-agent` (GitHub Public作成済み) + CLI名 `auto-dev` (固定)

## リポジトリの実態

- Python製 CLI フレームワーク
- Supervisor-Worker-Reviewer 3ロール協調
- CLI ランナー抽象 (Claude / Codex / Aider / Gemini を統一インターフェースで切替)
- ファイル経由状態管理 + tmux でプロセス分離
- 配布は `uv tool install`
- CLI 名は `auto-dev` で固定（変更不可）
- 哲学的キーワード: 改善ループ (kaizen) / 自律エージェント / オーケストレーション / マルチランナー

## 調査の切り口

1. **`kaizen-agent` 名前の妥当性**: 英語圏OSS使用前例・実態との乖離・SEO観点
2. **名前空間の衝突調査**: GitHub / PyPI / npm での `kaizen-agent`, `auto-dev` 等の現状
3. **類似OSS命名規約**: aider / claude-squad / claude-flow / opencode 等の傾向
4. **候補名の比較**: 3〜6個の代替案を意味・衝突・ドメイン・PyPI空き状況で評価
5. **リポ名とCLI名の乖離**: 別名維持 vs 同一名統一のメリデメ
6. **命名ベストプラクティス**: 1〜2年後に後悔するパターン・エージェント系OSS rename事例

## 調査ソース

- GitHub Search: `kaizen-agent`, `kaizenagent`, `auto-dev`, `autodev`, `kaizen`
- PyPI: `kaizen-agent`, `kaizen`, `auto-dev`, `autodev`
- npm: 同上
- ドメイン: `kaizen-agent.dev/.io`, `auto-dev.dev/.io`
- Anthropic/OpenAI公式GitHub orgの命名傾向
- Hacker News / Reddit r/ClaudeAI / r/LocalLLaMA

## 出力ファイル

- `README.md` (本ファイル)
- `research_log.md` (Geminiが生成する調査ログ)
- `sources.md` (Geminiが生成する情報源一覧)
- `agenda.md` (最終レポート構成)
- `final_report.md` (最終レポート)
