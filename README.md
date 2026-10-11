# grill-form

Claude Code 用のスキルです。計画や設計を詰めるための質問（grilling）を、ターミナルではなくブラウザの HTML フォームで行います。

- 質問は「候補から選ぶ」「自由に書く」「保留にする」「聞き返す」で答えられます。
- 決めることがなくなるまで質問を重ね、最後に SPEC（概要・流れ・受入条件・非目標・リスク・決定ログ）にまとめます。
- 承認された SPEC だけが `spec.md` として残り、作業用ファイルは自動で削除されます。

## 必要なもの

- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- Python 3.8 以上（標準ライブラリのみ）
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)（ローカルの HTML を `file://` で開くために使います）

## インストール

### 1. スキルを配置する

```bash
git clone https://github.com/asama0101/grill-form.git ~/.claude/skills/grill-form
```

- 特定のプロジェクトだけで使う場合は、そのプロジェクトの `.claude/skills/grill-form` に clone します。
- 更新は `git pull` で行います。反映には Claude Code の再起動が必要です。

### 2. Playwright MCP を登録する

```bash
claude mcp add playwright --scope user -- npx @playwright/mcp@latest --allow-unrestricted-file-access --output-dir "$HOME/.playwright-mcp"
```

- `--allow-unrestricted-file-access`: `file://` の HTML を開くために必要です。
- `--output-dir`: Playwright MCP が保存する記録（`page-*.yml`）の置き場所です。指定しないと作業フォルダに `.playwright-mcp/` ができることがあります。
- ブラウザを指定するときは `--browser chrome` などを追加します。

すでに `playwright` を登録している場合、`claude mcp add` は上書きしません。`claude mcp get playwright` で現在の引数とスコープを確認し、`claude mcp remove playwright --scope <スコープ>` で削除してから、元の引数を残したまま登録し直してください。

## 使い方

Claude Code で次のように頼みます。

```
grill-form で <テーマ> を詰めたい
```

「grill して」だけでは起動しません。`grill-form` や「HTML で grilling」と明示したときだけ使われます。

1. **事前確認（Round 0）**: 目的とゴール、障壁、制約を確認します。
2. **質問ラウンド**: Claude が質問の HTML を生成してブラウザで開きます。回答して「送信」を押すと、Claude が自動で検知して次へ進みます（ターミナルへの入力は不要です）。
3. **最終確認**: 決めることがなくなったら SPEC 案を表示します。「承認」で確定、「修正あり」ならコメントを反映して再提示します。

各質問には推奨案と理由が付きます。分からないときは「聞き返し」欄に書いて送信すると、次のラウンドで Claude が説明か補足質問を返します。

## ファイルの保存先

| 種類 | 場所 | 寿命 |
| --- | --- | --- |
| 作業用ファイル（質問 JSON・HTML・回答 Markdown） | OS の一時フォルダ配下 `grill-form/<日時>_<テーマ>/` | 承認後に自動削除。未承認で中断したものは 3 日後に削除 |
| 承認された SPEC | `<親>/<日時>_grill-form_<テーマ>/spec.md` | 残る。別セッションに SPEC を渡すときはこのファイルを使う |

SPEC の親フォルダは次の順で決まります。

1. `init` の `--parent` 引数
2. 環境変数 `GRILL_FORM_DIR`（相対パスはカレントフォルダから解決）
3. `docs`（既定。カレントフォルダ直下）

常に同じ場所に保存したい場合は、`settings.json` で環境変数を設定します。

```json
{
  "env": {
    "GRILL_FORM_DIR": "00_inbox"
  }
}
```

SPEC の保存先をプロジェクトに置く場合、`.gitignore` に `*_grill-form_*/` を加えると、コミット対象から外せます。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `SKILL.md` | スキルの定義と手順 |
| `grill_form.py` | `init`（一時セッションの作成と古いものの削除）、`render`（HTML 生成）、`cleanup`（一時セッションの削除） |
| `grill_form_template.html` | 質問フォームのテンプレート（外部リソースなし） |
| `THIRD_PARTY_NOTICES.md` | 取り込んだルールの出典とライセンス |

## トラブルシューティング

- **`file://` が開けない**: Playwright MCP に `--allow-unrestricted-file-access` が付いているか確認してください。
- **送信が検知されない**: 約 30 分待っても送信がない場合、Claude が続行方法を聞きます。フォームのコピーボタンで回答 Markdown を貼ることもできます。

## ライセンス

[MIT](LICENSE)

`SKILL.md` の「ルール」節は、Matt Pocock 氏の [grilling スキル](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT）を要約・翻案したものです。元のライセンス表記は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にあります。
