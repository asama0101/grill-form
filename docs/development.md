# 開発者向けメモ

grill-form の仕組みとテストです。使い方は [README.md](../README.md) を見てください。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `README.md` | 利用者向けの説明。リポジトリ直下に 1 つだけ置き、プラグインのフォルダの中には置かない（出典の注記は `plugins/grill-form/NOTICE`） |
| `.claude-plugin/marketplace.json` | マーケットプレイスの定義 |
| `plugins/grill-form/.claude-plugin/plugin.json` | プラグインのメタ（version は `grill_form.py` の `__version__` と一致させる） |
| `plugins/grill-form/skills/grill-form/SKILL.md` | スキルの定義と手順 |
| `plugins/grill-form/scripts/grill_form.py` | 補助スクリプト。サブコマンドは下の表 |
| `plugins/grill-form/scripts/folder_scan.py` | 入力フォーム用に、作業フォルダのフォルダとファイルを調べる（深さ 3、1 フォルダ 200 件、全体 5,000 件、隠し・リンク・`.git` などは除外） |
| `plugins/grill-form/scripts/grill_form_template.html` | フォームのテンプレート（単一 HTML、外部リソースなし、`innerHTML` は使わない） |
| `plugins/grill-form/NOTICE` | 取り込んだルールの出典とライセンス |
| `tests/` | pytest のテスト |

### `grill_form.py` のサブコマンド

| サブコマンド | 内容 |
| --- | --- |
| `init --theme T` | 一時セッションを作り、パスを 1 行で出力する。3 日より古い一時セッションを削除する |
| `spec-path --theme T [--parent P]` | SPEC の保存先 `<親>/SPEC-<テーマ>-<日付>.md` を決めて出力する（ファイルは作らない）。同名があれば連番を付ける。親が既存のファイルなら終了コード 2 |
| `render` | 質問 JSON（`--round N --input J.json`）、最終確認（`--final`）、入力フォーム（`--intake [--input J.json] [--answers A.md]`）の HTML を生成する。入力フォームは、作業フォルダの一覧（`folder_scan.py`）を埋め込む。`--answers` は、入力フォームの回答（`## 更新` つき）から入力を復元して作り直す |
| `cleanup --session-dir D --spec S [--yes]` | 一時セッションを削除する。SPEC（S）がなければ何もしない |

## 一時ファイル

作業用のファイルは、OS の一時フォルダに置かれます。

| 種類 | 場所 | 寿命 |
| --- | --- | --- |
| 作業用ファイル（質問 JSON・HTML・回答 Markdown） | 一時フォルダ配下 `grill-form/<日時>_<テーマ>/` | 承認後に自動削除。未承認で中断したものは 3 日後に削除 |
| Playwright MCP の記録 | 一時フォルダ配下 `playwright-mcp/` | OS の一時フォルダの掃除に任せる |

## ローカルで試す

インストールせずに、clone したフォルダのプラグインを読み込んで起動します。

```bash
claude --plugin-dir ./plugins/grill-form
```

## テストと検査

プラグインの形式（SKILL.md の frontmatter、絶対パス・相対パスを書いていないこと、`${CLAUDE_PLUGIN_ROOT}` が指すファイルの実在、MCP を同梱していないこと、version の一致、`claude plugin validate`）、`grill_form.py` の各サブコマンド、フォームの HTML の構造を、pytest で検査します。スキル本体（実行時）には依存がありません。テストの依存は `requirements-dev.txt` に固定しています。

```bash
python -m venv <一時フォルダ>/grill-form-venv   # プロジェクトの外に作る
<一時フォルダ>/grill-form-venv/Scripts/python -m pip install -r requirements-dev.txt
<一時フォルダ>/grill-form-venv/Scripts/python -m pytest
<一時フォルダ>/grill-form-venv/Scripts/python -m ruff check .
<一時フォルダ>/grill-form-venv/Scripts/python -m ruff format --check .
```

- フォームの動き（キー操作、次の質問へ移る動き）は、自動テストの対象外です。ブラウザで目視して確かめてください。
- 入力フォームのツリー、Shift の範囲選択、「フォルダを読み直す」も、自動テストの対象外です。`render --intake` で作ったページを、ブラウザで操作して確かめてください。
