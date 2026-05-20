# bonsaidev

盆栽のように少しずつ整える自律コーディングエージェント — CLI ランナー抽象 + Supervisor-Worker-Reviewer の 3 ロール協調でサブスク Claude を最大活用するコーディング自動化フレームワーク。

CLI エントリポイント名は `bonsai`。既存 [start-auto-dev](https://github.com/tori-create-7991/00_my_env/tree/main/global-config-sync/skills/start-auto-dev) スキルから内部的に `bonsai` を呼び出す。

## なぜ "bonsai"

| 盆栽の特性 | このプロジェクトの特性 |
|-------------|-------------------|
| 毎日少しずつ剪定する | Worker が小さなコミット単位で改善する |
| 完成は永遠にない | review round を回し続けて少しずつ良くなる |
| 幹 / 枝 / 葉の 3 要素を整える | Supervisor / Worker / Reviewer の 3 ロール |
| 鋏 / 針金 / 鉢を使い分ける | runner 抽象 (Claude / Codex / Aider / Gemini) |
| 老木の年輪 = 観察と記録の蓄積 | events.jsonl の append-only ログ |

## 設計思想

- **追加課金ゼロ厳守**: サブスク Claude Max を tmux 経由で完全活用 (`tmux_rpc` 主軸)
- **CLI ランナー抽象**: `Runner` Protocol で claude / codex / aider / gemini を統一切替
- **Supervisor-Worker-Reviewer**: 3 ロールが tmux session で分離稼働
- **ファイル経由状態管理**: `.plans/<name>/plan.md` (人間) + `.auto-dev/<name>/` (ツール) の責務分離
- **HITL チェックポイント**: PR merge のみデフォルト人間承認

詳細設計は [.plans/auto-dev-new-repo-design.md](https://github.com/tori-create-7991/00_my_env/blob/main/.plans/auto-dev-new-repo-design.md) (親リポ、命名は旧称) を参照。

## ステータス

Phase 1 MVP 実装完了。

## インストール

```bash
# ローカル開発版
uv tool install -e /path/to/bonsaidev

# リポジトリから直接
uv tool install git+https://github.com/tori-create-7991/bonsaidev.git
```

## 使い方 (Phase 1 MVP)

```bash
# plan.md の内容を確認 (実行なし)
bonsai start .plans/my-feature/plan.md --dry-run

# tmux_rpc runner (Claude Max サブスク経由) で実行
bonsai start .plans/my-feature/plan.md

# claude_p runner (claude -p コマンド経由) で実行
bonsai start .plans/my-feature/plan.md --runner claude_p

# 実行中の Worker セッションにアタッチ
bonsai attach my-feature

# Worker セッションを停止
bonsai kill my-feature

# バックグラウンド起動 (tmux detach で自動)
scripts/bonsai-launch.sh .plans/my-feature/plan.md
```

### プランファイルの形式

```markdown
# my-feature

- [ ] Task 1: implement X
- [ ] Task 2: add tests
- [x] Task 3: already done
```

Worker が各タスクをこなすと `- [x]` に更新され、
完了時に `## Status: completed` が末尾に追記されます。

## ライセンス

MIT
