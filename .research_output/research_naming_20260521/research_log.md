# 調査ログ: kaizen-agent / auto-dev リポジトリ名再検討

調査実施日: 2026-05-21
調査者: Claude (Gemini CLI クォータ枯渇のためWebSearch/WebFetchで代替)

---

## 切り口1: `kaizen-agent` という名前の妥当性

### 英語圏OSSでの "kaizen" 使用前例

**致命的な発見: PyPI に `kaizen-agent` は既登録**

- パッケージ名: `kaizen-agent`
- バージョン: 0.1.9
- 著者: Yuto Suzuki (@yuto_ai_)
- 最終更新: **2025年7月16日**（活発に開発中）
- GitHub: https://github.com/Kaizen-agent/kaizen-agent (★44, Python 98%)
- 説明: "An AI debugging engineer that continuously tests, analyzes, and improves your AI agents and LLM applications"
- ライセンス: MIT

このパッケージは `pip install kaizen-agent` でインストール可能であり、コンセプトも「AIエージェントを継続的に改善する」ということで、「改善ループ(kaizen)」の名前と実態が一致している。

**関連するnpmパッケージ**:
- `kaizen-cli` (npmjs.com) — 別プロジェクト
- `kaizen` (PyPI) — 別パッケージ

### 名前と実態の乖離度

既存の `kaizen-agent` (Yuto Suzuki版) は「LLMアプリのテスト・改善」に特化しており、kaizanという名前と実態が整合している。

一方、今回検討中の `kaizen-agent` リポジトリは:
- 本質: **マルチエージェントオーケストレーター** (Supervisor-Worker-Reviewer協調)
- CLI名: `auto-dev` (自律開発フレームワーク)
- "kaizen" 要素: 改善ループは**機能の一部**に過ぎない

この乖離は2重の問題を生む:
1. PyPI既存パッケージとの**直接衝突**（同名パッケージが存在）
2. 名前が実態（オーケストレーター）よりも改善ツールを連想させる**ミスリード**

### SEO・発見可能性

`kaizen` で検索すると：
- 製造業・リーン開発の改善手法 (KaiNexus, SafetyCulture等のSaaSが上位)
- 既存の `kaizen-agent` (Yuto Suzuki版) が競合
- 「マルチエージェントオーケストレーター」を探すユーザーには到達されない

**結論: `kaizen-agent` は採用不可（PyPI既登録、実態ミスリード、SEO混線の三重苦）**

---

## 切り口2: 名前空間の衝突調査

### `kaizen-agent` / `kaizenagent`

| プラットフォーム | 状況 |
|----------------|------|
| PyPI | `kaizen-agent` **登録済み** (v0.1.9, 活発に開発中) |
| GitHub | `Kaizen-agent/kaizen-agent` **存在** (★44) |
| npm | `kaizen-agent` は見当たらず、`kaizen-cli` は別途存在 |

### `auto-dev` / `autodev`

| プラットフォーム | 状況 |
|----------------|------|
| PyPI | `autodev` v0.0.1 **登録済み** (2021年12月, 非活発, Python 3.7-3.10) |
| PyPI | `ai-autodev` 登録済み |
| GitHub | `phodal/auto-dev` **★4.5k** (Kotlin製, IDE プラグイン + CLIの大型プロジェクト) |
| GitHub | `github.com/auto-dev` org — 公開リポジトリなし（空org、誰かが保持） |
| npm | `@xiuper/cli` (phodal/auto-devの派生) |

**`auto-dev` はCLIコマンド名として使うのは問題ないが、PyPIパッケージ名としての登録は要確認（`autodev` は取られている）。`auto-dev` (ハイフン付き) のPyPI登録状況は別途確認が必要。**

### 主要競合・類似OSSとの命名衝突

**最重要な競合: `awslabs/cli-agent-orchestrator` (CAO)**

```
★600 (急成長中), Apache-2.0
- tmux でエージェントプロセスを分離
- Supervisor-Worker パターン
- Claude Code, Codex, Gemini CLI etc. をオーケストレート
- CLI名: `cao`
- uv tool install で配布
- v2.1.1 (2026-04-28)
```

このプロジェクトは今回設計中の `kaizen-agent` / `auto-dev` と**ほぼ同一のアーキテクチャ**を持つ。差別化ポイントの明確化が必要。

---

## 切り口3: Anthropic/OpenAI 周辺の命名規約

### Anthropic 公式

- `claude-code` (CLI名), `anthropics/claude-code` (GitHub)
- `anthropics/skills` (GitHub)
- MCP: `Model Context Protocol`

### OpenAI 公式

- `openai/codex` (GitHub), CLI名: `codex`
- `openai/openai-agents-python` (GitHub)

### 業界命名トレンド (2024-2026)

**成功しているOSS CLI エージェントの命名パターン:**

| パターン | 例 | 特徴 |
|---------|-----|------|
| 短い英単語 | aider, goose, pi, cline | 覚えやすい、発音しやすい |
| 2語結合 | opencode, OpenHands | 機能・哲学を表現 |
| 動物・比喩 | goose, roo, claw | キャラクター性、親しみやすさ |
| 頭字語 | cao (CLI Agent Orchestrator) | 説明的名前の短縮 |
| 人名・造語 | bernstein, aider | ユニーク性、検索で被らない |

**避けられているパターン:**
- 過度に説明的・汎用的な名前 ("multi-agent-orchestrator" など)
- 既存の著名ツールと混同される名前

---

## 切り口4: 候補名の比較

### 現状分析まとめ

| 候補 | PyPI | GitHub | 実態との整合 | SEO | 総合 |
|------|------|--------|------------|-----|------|
| `kaizen-agent` | 登録済み (衝突!) | 活発なプロジェクト存在 | ミスリード | 製造業混線 | **不採用** |
| `auto-dev` (CLI名固定) | `autodev` 取られ済み | phodal/auto-dev ★4.5k | まあ整合 | 競合多い | CLI名としてはOK |

### 代替候補案

**案A: `devloop` (リポ名) + `auto-dev` (CLI名)**
- 意味: 開発ループ、継続的な開発サイクル
- PyPI `devloop`: 未確認（要調査）
- 連想: "loop" = 反復改善サイクル、オーケストレーション
- 懸念: DevOps系ツールと混同の可能性

**案B: `conductor` (リポ名) + `auto-dev` (CLI名)**
- 意味: 指揮者（オーケストレーターの比喩として完璧）
- PyPI `conductor`: Netflixのworkflow orchestratorが既に有名
- GitHub: Netflix/conductor が★17k超 → **衝突致命的**

**案C: `forge-agent` または `agentforge` (リポ名) + `auto-dev` (CLI名)**
- 意味: エージェントを鍛造する、構築する
- PyPI `agentforge`: 要確認
- 懸念: "forge" 系は多い (Forge, AgentForge等)

**案D: `devplex` (リポ名) + `auto-dev` (CLI名)**
- 意味: dev(開発) + plex(複数・複雑系)、マルチエージェントを暗示
- PyPI: 未確認、おそらく空き
- 連想: ユニーク、覚えやすい

**案E: `polyphony` (リポ名) + `auto-dev` (CLI名)**
- 意味: 多声音楽 → 複数エージェントが協調する比喩
- PyPI: `polyphony` は音楽関連で既存あり
- 詩的すぎて直感的でない可能性

**案F: リポ名を `auto-dev` に統一 (CLI名と同一)**
- 意味: 自律的な開発
- PyPI: `auto-dev` (ハイフン付き) の登録状況未確認
- 懸念: phodal/auto-dev (★4.5k, Kotlin) と混同される
- メリット: リポ名とCLI名が一致してわかりやすい

---

## 切り口5: リポ名とCLI名の乖離について

**現状**: `kaizen-agent` (リポ) vs `auto-dev` (CLI)

この乖離は一般的ではあるが、混乱を招くリスクがある。

**乖離の是非:**

| 観点 | 一致 (auto-dev = auto-dev) | 別名 (kaizen-agent + auto-dev) |
|------|--------------------------|-------------------------------|
| ユーザー体験 | 直感的 | 「なぜ名前が違う？」という疑問 |
| SEO | `auto-dev` で一本化 | リポ名で検索しても辿りにくい |
| PyPI パッケージ名 | `auto-dev` に統一 | 別名にする場合は2ブランド管理 |
| 命名実績 | aider=aider, goose=goose | claude-code (CLI) / anthropic-claude-code (pkg) |
| ロールモデル | 多い | 少なくない (cline/roo-codeはリポ名=CLI名) |

**推奨方向性**: リポ名とCLI名は一致させるべき。ただし `auto-dev` はphodal/auto-devとの混同リスクがある。

---

## 切り口6: 命名ベストプラクティスと後悔パターン

### 1〜2年後に後悔する命名パターン

1. **PyPI/GitHub に既存衝突がある名前** → `kaizen-agent` がまさにこれ
2. **汎用的すぎる名前** → "agent-framework", "dev-tool" 等
3. **SEOが弱い名前** → 検索結果が別分野で埋まる
4. **リポ名とCLI名の乖離** → ブランドの分散
5. **リネーム後の依存関係破綻** → PyPIパッケージをリネームするとpip installが壊れる

### GitHub リネームのコスト (現時点では低い)

今回は **実装着手前** であり、スター数・フォーク数・PyPIパッケージ公開もゼロ。
リネームコストは最小限: GitHub上でのリネーム（自動リダイレクトあり）+ .plans/ + skill docs の更新のみ。

PyPIパッケージ未公開なので、PyPI側のコストはゼロ。

### エージェント系OSS rename 事例

一般的なOSSリネームの苦労: 既存ユーザーのpip install破綻、GitHub Actionsの参照切れ、ドキュメントURLの404等。ただし、これらは**既にリリースされているプロジェクト**に限られる。
