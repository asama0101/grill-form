# 開発者向けメモ

grill-form の仕組み、テスト、設計書の置き場所です。使い方は [README.md](../README.md) を見てください。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `SKILL.md` | スキルの定義と手順 |
| `grill_form.py` | 補助スクリプト。サブコマンドは下の表 |
| `grill_form_template.html` | フォームのテンプレート（単一 HTML、外部リソースなし、`innerHTML` は使わない） |
| `tests/` | pytest のテスト |
| `docs/superpowers/specs/` | 設計書 |
| `docs/superpowers/plans/` | 実装計画 |
| `THIRD_PARTY_NOTICES.md` | 取り込んだルールの出典とライセンス |

### `grill_form.py` のサブコマンド

| サブコマンド | 内容 |
| --- | --- |
| `init --theme T` | 一時セッションを作り、パスを 1 行で出力する。3 日より古い一時セッションを削除する |
| `spec-path --theme T [--parent P]` | SPEC の保存先 `<親>/SPEC-<テーマ>-<日付>.md` を決めて出力する（ファイルは作らない）。同名があれば連番を付ける。親が既存のファイルなら終了コード 2 |
| `pick-dir` | OS のフォルダ選択ダイアログ（tkinter）を開き、選んだパスを出力する。取り消しは終了コード 1、開けないときは 3 |
| `pick-file` | OS のファイルを選ぶダイアログ（複数選択可）を開き、選んだパスを 1 行ずつ出力する。終了コードは `pick-dir` と同じ |
| `render` | 質問 JSON（`--round N --input J.json`）、最終確認（`--final`）、入力フォーム（`--intake`）の HTML を生成する |
| `cleanup --session-dir D --spec S [--yes]` | 一時セッションを削除する。SPEC（S）がなければ何もしない |

## 一時ファイル

作業用のファイルは、OS の一時フォルダに置かれます。

| 種類 | 場所 | 寿命 |
| --- | --- | --- |
| 作業用ファイル（質問 JSON・HTML・回答 Markdown） | 一時フォルダ配下 `grill-form/<日時>_<テーマ>/` | 承認後に自動削除。未承認で中断したものは 3 日後に削除 |
| Playwright MCP の記録 | 一時フォルダ配下 `playwright-mcp/` | OS の一時フォルダの掃除に任せる |

## テストと検査

SKILL.md の形式（frontmatter の `name`、絶対パス・相対パスを書いていないこと、`${CLAUDE_SKILL_DIR}` が指すファイルの実在）、`grill_form.py` の各サブコマンド、フォームの HTML の構造を、pytest で検査します。スキル本体（実行時）には依存がありません。テストの依存は `requirements-dev.txt` に固定しています。

```bash
python -m venv <一時フォルダ>/grill-form-venv   # プロジェクトの外に作る
<一時フォルダ>/grill-form-venv/Scripts/python -m pip install -r requirements-dev.txt
<一時フォルダ>/grill-form-venv/Scripts/python -m pytest
<一時フォルダ>/grill-form-venv/Scripts/python -m ruff check .
<一時フォルダ>/grill-form-venv/Scripts/python -m ruff format --check .
```

- フォームの動き（キー操作、次の質問へ移る動き）は、自動テストの対象外です。ブラウザで目視して確かめてください。
- 選択ダイアログの表示も、自動テストの対象外です。`python grill_form.py pick-dir` と `pick-file` を実行して確かめてください。

## 設計書

保存先と残すものの見直しの設計は、[docs/superpowers/specs/2026-10-24-output-layout-design.md](superpowers/specs/2026-10-24-output-layout-design.md) にあります。実装計画は [docs/superpowers/plans/2026-10-24-output-layout.md](superpowers/plans/2026-10-24-output-layout.md) です。
