# リポジトリ名再検討 調査レポート

**テーマ**: kaizen-agent / auto-dev リポジトリ名の確定
**日付**: 2026-05-21
**調査方法**: WebSearch + WebFetch（Gemini CLI クォータ枯渇のため代替）

---

## 1. エグゼクティブサマリー

**推奨案: リポジトリ名を `auto-dev` に統一（CLI名と一致させる）**

ただし、PyPI パッケージ名は `autodev-cli` または `auto-dev-cli` を使い、既存の `autodev` パッケージ（非活発, 2021年）との衝突を回避する。

**次点: `devloop`（リポ名）+ `auto-dev`（CLI名）**

**`kaizen-agent` は採用不可**。PyPI に同名の活発なパッケージが存在し、GitHub org まで存在する。加えて名前と実態（マルチエージェントオーケストレーター）が乖離しており、三重の問題を抱える。

---

## 2. 調査の前提

対象プロジェクト:
- **実態**: Python製マルチエージェントCLIフレームワーク。Supervisor-Worker-Reviewer 3ロール協調、CLIランナー抽象（Claude / Codex / Aider / Gemini を統一インターフェース）、tmuxでプロセス分離、ファイル経由状態管理
- **配布**: `uv tool install`
- **CLI名**: `auto-dev`（固定、変更不可）
- **現状**: `kaizen-agent` (GitHub Public作成済み)、実装未着手

---

## 3. 致命的発見：`kaizen-agent` の現状

### 3.1 PyPI・GitHub での衝突

調査の結果、**`kaizen-agent` はPyPIに既登録**であることが判明した。

| 項目 | 内容 |
|------|------|
| PyPIパッケージ名 | `kaizen-agent` |
| バージョン | 0.1.9 |
| 著者 | Yuto Suzuki |
| 最終更新 | 2025年7月16日（**活発に開発中**） |
| GitHub | https://github.com/Kaizen-agent/kaizen-agent（★44、Python 98%、467コミット） |
| ライセンス | MIT |
| 説明 | "An AI debugging engineer that continuously tests, analyzes, and improves your AI agents and LLM applications" |
| 配布 | `pip install kaizen-agent` |

この `kaizen-agent` (Yuto Suzuki版) は "LLMアプリのテスト・改善を自動化する" ツールであり、YAMLでテスト基準を定義しAIが自動評価・改善PRを作成する。
`kaizen-agent` という GitHub org (`https://github.com/Kaizen-agent`) まで存在する。

PyPIに同名の活発なパッケージが存在する以上、`uv tool install kaizen-agent` は別プロジェクトをインストールすることになる。これは**採用不可の致命的障害**である。

### 3.2 名前と実態の乖離

既存の `kaizen-agent` (Yuto Suzuki版) は「改善ループ」コンセプトと名前が整合している。
対して、今回のプロジェクトの本質は「**マルチエージェントオーケストレーション**」であり、"kaizen" (改善) は機能の一部に過ぎない。

ユーザーが `kaizen-agent` という名前から連想するのは「何かを改善するツール」であり、「複数のCLIエージェントを指揮するオーケストレーター」ではない。既存ツールとの混同に加え、実態のミスリードも重なる。

### 3.3 SEO上の問題

"kaizen" で検索すると以下が上位を占める:
1. 製造業・リーン開発の改善手法（KaiNexus、SafetyCulture 等のSaaS製品）
2. 既存の `kaizen-agent` (Yuto Suzuki版)
3. `kaizen.io`（別のSaaS）

「マルチエージェントオーケストレーター」を探すエンジニアが `kaizen-agent` にたどり着く検索経路が存在しない。

---

## 4. 名前空間の衝突マトリクス

### `kaizen-agent` / `kaizenagent`

| プラットフォーム | 状況 | 判定 |
|----------------|------|------|
| PyPI `kaizen-agent` | v0.1.9 **登録済み・活発** | 採用不可 |
| GitHub `Kaizen-agent/kaizen-agent` | ★44、活発 | 採用不可 |
| GitHub org `kaizen-agent` | 存在する | 採用不可 |
| npm `kaizen-agent` | 未検出（ただし `kaizen-cli` あり） | 競合なし |

### `auto-dev` / `autodev`

| プラットフォーム | 状況 | 判定 |
|----------------|------|------|
| PyPI `autodev` | v0.0.1 **登録済み** (2021年12月、非活発、Python 3.7-3.10) | 名前変更が必要（`auto-dev-cli` 等） |
| PyPI `auto-dev` (ハイフン付き) | 未確認（別途要チェック） | 要確認 |
| PyPI `ai-autodev` | 別プロジェクトが存在 | 参考情報 |
| GitHub `phodal/auto-dev` | ★4.5k、Kotlin製、IDE プラグイン | 混同リスクあり（ただし言語・目的が異なる） |
| GitHub org `auto-dev` | 存在するが公開リポなし | 問題なし |

### 主要競合・類似ツールとの位置関係

最も注目すべき競合: **`awslabs/cli-agent-orchestrator` (CAO, ★600)**

| 比較項目 | CAO (AWS) | 今回のプロジェクト |
|---------|-----------|------------------|
| アーキテクチャ | tmux + Supervisor-Worker + MCP | tmux + Supervisor-Worker-Reviewer |
| 対応CLI | Claude Code, Kiro, Amazon Q等 | Claude / Codex / Aider / Gemini |
| CLI名 | `cao` | `auto-dev` |
| 配布 | `uv tool install` | `uv tool install` |
| 言語 | Python | Python |
| ライセンス | Apache-2.0 | 未定 |

アーキテクチャがほぼ同一。**差別化ポイントの明確化が命名にも影響する**（例: "reviewer" ロールへの強調、Claude Max最大活用という哲学等）。

---

## 5. エージェント系OSS命名規約の傾向

### 成功している命名パターン

| パターン | 例 | 評価 |
|---------|-----|------|
| 短い英単語（動詞・名詞） | aider, goose, pi | 最強：覚えやすく検索性高い |
| 2語結合 | opencode, OpenHands | 強：機能が伝わり独自性あり |
| 動物・比喩 | goose, roo, claw | 強：キャラクター性・親しみやすさ |
| 頭字語 | cao (CLI Agent Orchestrator) | 中：説明的名前の短縮として機能 |
| 人名・造語 | bernstein | 中：ユニーク性高いが意味不明 |

### 避けるべきパターン

1. **汎用的すぎる名前**: "agent-framework", "dev-tool", "multi-agent-orchestrator" → 検索結果に埋もれる
2. **既存ツールと1文字差**: 誤検索・混同
3. **カテゴリ語 + agent**: "kaizen-agent", "code-agent" → 後半の "agent" が差別化にならない
4. **リポ名とCLI名が大きく乖離**: "kaizen-agent" (リポ) + "auto-dev" (CLI) → ブランドが2つに分散

### Anthropic/OpenAI 命名傾向

- Anthropic: `claude-code` (CLI名 = パッケージ名 = GitHub リポ名に近い)
- OpenAI: `codex` (短い既存語の転用)
- Google: `gemini-cli` (ブランド名 + "cli" の直球)

---

## 6. 候補名の比較評価

### 評価基準

1. PyPI 名空き（必須）
2. GitHub での衝突なし（必須）
3. 実態（マルチエージェントオーケストレーター）との整合性
4. CLI名 `auto-dev` との距離感（近い方が良い）
5. SEO発見可能性
6. 記憶のしやすさ・発音

### 各候補の評価

**候補1: `auto-dev`（リポ名とCLI名を統一）**

| 評価項目 | 評価 | 備考 |
|---------|------|------|
| PyPI空き | 要確認（`autodev` は登録済み、`auto-dev` 未確認） | `auto-dev-cli` での登録が現実的 |
| GitHub衝突 | phodal/auto-dev (★4.5k, Kotlin) | 言語・目的が大きく異なるため許容範囲 |
| 実態整合 | 中（"自律的な開発" は伝わる） | オーケストレーターとしての印象は弱い |
| CLI名との距離 | ゼロ（完全一致） | 最大のメリット |
| SEO | 競合多め | phodal/auto-dev が上位に来る可能性 |
| 記憶性 | 高い | 直感的 |
| **総合** | **推奨** | CLI名との統一が最大メリット |

**候補2: `devloop`**

| 評価項目 | 評価 | 備考 |
|---------|------|------|
| PyPI空き | 要確認 | |
| GitHub衝突 | 軽微 | 非活発なプロジェクトはいくつかある |
| 実態整合 | 高（継続的な開発ループを暗示） | |
| CLI名との距離 | 中 | ループ = 反復という連想 |
| SEO | 中 | DevOps系と混同の可能性 |
| 記憶性 | 高い | |
| **総合** | **次点** | |

**候補3: `agentflow`**

| 評価項目 | 評価 | 備考 |
|---------|------|------|
| PyPI空き | 要確認 | |
| GitHub衝突 | claude-flow (claude-flow/claude-flow) が存在 | 類似名 |
| 実態整合 | 高（エージェントのフロー制御） | |
| CLI名との距離 | 遠い | |
| SEO | 競合多め | |
| **総合** | 非推奨 | claude-flowとの混同 |

**候補4: `polydev`**

| 評価項目 | 評価 | 備考 |
|---------|------|------|
| PyPI空き | おそらく空き | |
| GitHub衝突 | 軽微 | |
| 実態整合 | 中（poly = 複数のエージェント） | |
| CLI名との距離 | 中 | |
| SEO | 良 | ほぼ競合なし |
| 記憶性 | 中 | |
| **総合** | 参考案 | |

**候補5: `devherd`（群れを率いる比喩）**

| 評価項目 | 評価 | 備考 |
|---------|------|------|
| PyPI空き | おそらく空き | |
| GitHub衝突 | ほぼなし | |
| 実態整合 | 高（複数エージェントの群れを指揮） | |
| CLI名との距離 | 遠い | |
| 記憶性 | 中（"herd" は一般的でない） | |
| **総合** | 参考案 | |

---

## 7. リポ名とCLI名の乖離問題

`kaizen-agent` (リポ) + `auto-dev` (CLI) という構成は、以下の問題を持つ:

1. **ブランドの分散**: GitHubで "kaizen-agent" を見つけたユーザーが、CLIのコマンドを `auto-dev` と知らない
2. **READMEの冗長化**: "このリポジトリ (`kaizen-agent`) の CLI ツール名は `auto-dev` です" という説明が必須
3. **PyPIパッケージ名の問題**: PyPIパッケージを何という名前にするか（`kaizen-agent` は取られているので使えない、`auto-dev` または `autodev` も要確認）

**業界慣例との比較:**
- cline → CLI名 `cline`、リポ名 `cline/cline`（完全一致）
- aider → CLI名 `aider`、リポ名 `Aider-AI/aider`（実質一致）
- claude-code → CLI名 `claude`（パッケージ名 `@anthropic-ai/claude-code`）

リポ名とCLI名が乖離しているプロジェクトは主流ではない。

**推奨**: リポ名を `auto-dev` に統一し、以下の構成にする:
- GitHub: `<user>/auto-dev`
- CLI: `auto-dev`
- PyPI: `auto-dev-cli`（`autodev` 取られているため）または `uv tool install git+...` でのみ配布

---

## 8. リネームコスト試算（現時点）

現時点は**実装着手前**であり、以下の点でリネームコストは最小:

| 項目 | コスト | 詳細 |
|------|--------|------|
| GitHub リポ名変更 | 低 | 設定画面から1クリック、自動リダイレクトあり |
| PyPI パッケージ | ゼロ | 未公開のため |
| .plans/ ファイル | 低 | `auto-dev-new-repo-design.md` の記述更新 |
| Notion タスク | 低 | タスク名・説明の更新 |
| skill ドキュメント | 低 | `start-auto-dev` スキルの参照先URL更新 |
| CLAUDE.md | 低 | リポジトリ名の記載更新 |
| @claude-metadata | 低 | `notion_project_page` 等は変わらない |

**「今変えなければ損」**: PyPIパッケージ公開後・スター獲得後・ドキュメント公開後のリネームは桁違いにコストが高い。今が変更の最良タイミング。

---

## 9. 最終結論

### 推奨案: リポジトリ名を `auto-dev` に変更

**理由:**

1. **現状の `kaizen-agent` は採用不可** — PyPI既登録（活発なプロジェクト）、GitHub org存在、実態ミスリード、SEO混線の四重苦
2. **CLI名との統一が最強** — `auto-dev` (リポ) = `auto-dev` (CLI コマンド) = ユーザー体験が最もシンプル
3. **phodal/auto-dev との混同は許容範囲** — Kotlin製IDEプラグイン vs Python製CLIフレームワークという言語・目的の差異が明確。実際のユーザー導線（GitHub検索, PyPI検索）で競合する可能性は低い
4. **コスト最小** — 実装着手前の今が変更の最良タイミング

**実施手順:**
1. GitHub で `kaizen-agent` → `auto-dev` にリポ名変更（Settings > Rename）
2. CLAUDE.md の `kaizen-agent` 記述を `auto-dev` に更新
3. `.plans/auto-dev-new-repo-design.md` のリポ名参照箇所を確認・更新
4. PyPI パッケージ名は `auto-dev-cli` で登録（`autodev` は取得済みのため）
5. `@claude-metadata` の `github_project` を更新

### 次点: `devloop`（リポ名）+ `auto-dev`（CLI名）

**採用する場合の理由:** 「継続的な開発ループ」という哲学がリポ名に込められ、"kaizen" の改善ループ哲学を引き継ぎつつ製造業との混線を避けられる。phodal/auto-devとの混同を完全回避したい場合の選択肢。

**採用手順:** PyPI `devloop` の空き状況確認が必須（本調査では確認未済）。

### 既存名 `kaizen-agent` を維持しない理由

「kaizen-agent という名前のまま進める」という選択肢は以下の理由で推奨しない:
- PyPI の `kaizen-agent` パッケージ（Yuto Suzuki版）との衝突を回避できない。`uv tool install kaizen-agent` は既存の別ツールをインストールする
- 実装が進むほどリネームコストが増大する
- 名前と実態（オーケストレーター）の乖離がREADMEやドキュメントに説明コストを生み続ける

---

## 付記: 調査上の限界

- PyPI `auto-dev`（ハイフン付き）の登録状況は本調査で直接確認できていない（`autodev` は確認済みで登録済み）
- ドメイン `auto-dev.dev` / `auto-dev.io` の取得可能性は未確認
- `devloop` のPyPI登録状況も未確認
- Gemini CLI クォータ枯渇のため、WebSearch/WebFetchによる調査に限定した（一部ページが読み込みエラーで取得不可）
