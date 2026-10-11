# roundtable

Claude Code 用のスキルです。grilling（質問攻めで合意を作る手法）を、ブラウザの HTML フォームで行います。候補選択・自由入力・保留で内容を詰め、最後に SPEC 形式（概要・流れ・受入条件・非目標・リスク・決定ログ）でまとめます。

## 必要なもの

- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- Python 3.8 以上（標準ライブラリのみ使用）
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)（`--allow-unrestricted-file-access` 付き。ローカルの `file://` を開くため）

grilling の進め方は `SKILL.md` に含まれているため、[grilling スキル](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling) のインストールは不要です（併用もできます）。

## インストール

### 1. スキルを配置する

全プロジェクトで使う場合（ユーザースキル）:

```bash
git clone https://github.com/asama0101/roundtable.git ~/.claude/skills/roundtable
```

特定のプロジェクトだけで使う場合は、そのプロジェクトの `.claude/skills/roundtable` に clone します。

更新は `git pull` で行います。

### 2. Playwright MCP を登録する

```bash
claude mcp add playwright --scope user -- npx @playwright/mcp@latest --allow-unrestricted-file-access --output-dir "$HOME/.playwright-mcp"
```

- `--allow-unrestricted-file-access`: ローカルの `file://` の HTML を開くために必要です。
- `--output-dir`: Playwright MCP がページを開くたびに保存する記録（`page-*.yml`）の置き場所です。指定しないと、作業フォルダに `.playwright-mcp/` ができることがあります。roundtable はこの記録を使わないので、作業フォルダの外にまとめます。必要なら `.gitignore` に `.playwright-mcp/` を追加してください。
- ブラウザを指定する場合は `--browser chrome` などを追加します。

#### すでに Playwright MCP を登録している場合

`claude mcp add` は既存の登録を上書きしないため、一度削除してから登録し直します。

```bash
# 今の設定（スコープと引数）を確認する
claude mcp get playwright

# 確認したスコープで削除し、--output-dir を加えて登録し直す
claude mcp remove playwright --scope user
claude mcp add playwright --scope user -- npx @playwright/mcp@latest --allow-unrestricted-file-access --output-dir "$HOME/.playwright-mcp"
```

- 元の引数（`--browser chrome` など）は残してください。
- スコープが `user` 以外（`local` / `project`）の場合は、`--scope` をそれに合わせます。
- 反映には Claude Code の再起動が必要です。

## 使い方

Claude Code で次のように頼みます。

```
roundtable で <テーマ> を詰めたい
```

1. Claude がラウンドごとに質問の HTML を生成し、ブラウザで開きます。
2. 回答して「送信」を押します（Claude が送信を自動で検知して次へ進むので、ターミナルへの入力は不要です）。
3. 決めることがなくなるまでラウンドを繰り返し、最後に SPEC 案を確認・承認します。

通常の「grill」では起動しません（`roundtable` や「HTML で grilling」と明示したときだけ使います）。

質問が分からないときや確認したいときは、各質問の「聞き返し」欄に書いて送信します（状態は「要確認」）。次のラウンドで Claude が説明か補足質問を返します。選択肢のない質問は、自由記述だけで答えます。

## ファイルの保存先と削除

作業用のファイル（質問の HTML・回答の Markdown・質問 JSON）は、OS の一時フォルダ（Windows は `%TEMP%oundtable\<日時>_<テーマ>\`）に作られ、プロジェクトには何も作られません。

承認された SPEC だけが、次の場所に `spec.md` として保存されます。別の Claude Code セッションに SPEC を渡すときは、このファイルを渡します。

```
<親>/<日時>_roundtable_<テーマ>/spec.md
```

親フォルダは次の順で決まります。

1. `init` の `--parent` 引数
2. 環境変数 `ROUNDTABLE_DIR`（相対パスはカレントフォルダから解決）
3. `docs`（既定。カレントフォルダ直下）

常に同じ場所へ保存したい場合は、Claude Code の `settings.json` で環境変数を設定します。

```json
{
  "env": {
    "ROUNDTABLE_DIR": "00_inbox"
  }
}
```

一時ファイルは次のタイミングで自動削除されます。

- SPEC の承認後: 確認なしで一時セッションを丸ごと削除します（内部では `roundtable.py cleanup --session-dir <D> --spec <S> --yes` を実行。`spec.md` がないとき、と一時セッション以外は何もしません）。手動で確認したいときは `--yes` なしで実行すると、削除対象の表示だけです。
- 次のセッション開始時: 3 日より古い一時セッション（承認せずに中断したもの）を削除します。中断したセッションを再開できるのは 3 日以内です。

Windows の「記憶域センサー」で一時ファイルの自動クリーンアップを有効にすると、OS 側でも掃除されます（任意）。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `SKILL.md` | スキルの定義と手順 |
| `roundtable.py` | 一時セッション作成と古いものの削除（`init`）、HTML 生成（`render`）、一時セッションの削除（`cleanup`） |
| `roundtable_template.html` | 質問フォームのテンプレート（外部リソースなし） |
| `THIRD_PARTY_NOTICES.md` | 取り込んだルールの出典とライセンス |

## ライセンス

[MIT](LICENSE)

`SKILL.md` の「ルール」節は、Matt Pocock 氏の [grilling スキル](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT）を要約・翻案したものです。元のライセンス表記は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にあります。
