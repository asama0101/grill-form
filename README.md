# grill-form

バージョン: 1.0.0（`python grill_form.py --version` でも確認できます）

計画や設計を、ブラウザのフォームで答えながら詰めて、最後に SPEC（仕様書）にまとめる Claude Code 用のスキルです。

- Claude からの質問を、ターミナルではなくブラウザのフォームで答えます。「候補から選ぶ」「コメントで答える」「保留にする」「聞き返す」が使えます。
- 各質問には推奨案と理由が付きます。決めることがなくなるまで、質問を重ねます。
- 依頼文や資料（PDF・PowerPoint・Excel など）を、最初に渡せます。
- 承認した内容は、SPEC・依頼文・資料が 1 つのフォルダに残ります。

## クイックスタート

必要なものは、[Claude Code](https://docs.claude.com/en/docs/claude-code)、Python 3.8 以上（標準ライブラリのみ）、[Playwright MCP](https://github.com/microsoft/playwright-mcp) です。Playwright MCP は、ローカルの HTML を開いて送信を検知するために使います。このスキルには同梱していないので、自分で登録します。

### 1. スキルを配置する

```bash
git clone https://github.com/asama0101/grill-form.git ~/.claude/skills/grill-form
```

- 特定のプロジェクトだけで使うときは、そのプロジェクトの `.claude/skills/grill-form` に clone します。
- 更新は `git pull` で行います。反映には Claude Code の再起動が必要です。

### 2. Playwright MCP を登録する

```bash
claude mcp add playwright --scope user -- npx @playwright/mcp@latest --allow-unrestricted-file-access --output-dir "$(python -c 'import tempfile; print(tempfile.gettempdir())')/playwright-mcp"
```

- `--allow-unrestricted-file-access`: `file://` の HTML を開くために必要です。
- `--output-dir`: Playwright MCP が保存する記録とダウンロードの置き場所です。指定しないと作業フォルダに `.playwright-mcp/` ができるので、OS の一時フォルダ配下にします。上のコマンドは OS の一時フォルダを Python で調べて埋めるため、Windows・macOS・Linux で同じ書き方です。
- ブラウザを指定するときは、`--browser chrome` などを追加します。
- すでに `playwright` を登録している場合は、上書きされません。[トラブルシューティング](#トラブルシューティング)の手順で登録し直してください。

登録したら、Claude Code を再起動します。

### 3. 使ってみる

Claude Code で、次のように頼みます。

```
grill-form で <テーマ> を詰めたい
```

「grill して」だけでは起動しません。`grill-form` や「HTML で grilling」と明示したときだけ使われます。

## 使い方

質問の流れは次のとおりです。ブラウザで「送信」を押せば、Claude が自動で検知して次へ進みます。ターミナルへの入力は要りません。途中でやめるときは、どのフォームでも「中止」を 2 回押します（SPEC は作られません）。

1. **入力フォーム**: 依頼文、ファイル、ファイルパスを渡します。どれか 1 つだけでも構いません。
2. **事前確認（Round 0）**: 入力を踏まえて、目的とゴール、障壁、制約を確認します。Claude が推奨案を埋めるので、確認と修正だけです。
3. **質問ラウンド**: Claude が質問のフォームをブラウザで開きます。決めることがなくなるまで、何度か繰り返します。
4. **最終確認**: SPEC 案が表示されます。「承認」で確定します。「修正あり」を選ぶと、コメントを反映した案が再提示されます。

### 入力フォームの欄

| 欄 | 内容 |
| --- | --- |
| 依頼文 | 何を詰めたいか、背景、分かっている制約など |
| ファイル | 参考資料を複数選べます。送信時にブラウザがダウンロードし、Claude が受け取ります |
| ファイルパス | 1 行に 1 つ。大きいファイルや、保存場所が決まっているファイルに向いています。Claude が直接読みます |

- PDF・PowerPoint・Excel は、Claude が pdf・pptx・xlsx スキルで読みます。
- 図形が多い資料は、ページを画像にして見る必要があります。画像にするツール（`soffice`、`pdftoppm` など）が環境にないと、文字と図形の構造しか読めません。

### 質問への答え方

- 候補から選ぶか、コメント欄に書きます。候補を選んだときのコメントは理由・条件の補足、候補を選ばずに書いたコメントはそれ自体が回答になります。候補にない回答は、候補を選ばずコメントに書いてください。
- 今決められないときは「あとで決める（保留）」にチェックします。
- 質問の意味が分からないときは「聞き返し」欄に書いて送信します。次のラウンドで、Claude が説明か補足質問を返します。聞き返しが残っている間は、質問は終わりません。

## 残るもの

承認すると、次のフォルダが残ります。

```
grill-specs/<日時>_<テーマ>/
├─ SPEC.md       承認された SPEC（概要に、依頼文の要約と入力ファイルの一覧を含む）
├─ request.md    入力フォームに書いた依頼文の原文
└─ <入力ファイル>  渡したファイル（パスで指定したものもコピーされる）
```

- SPEC は、概要・流れ・受入条件・非目標・リスク・決定ログで構成されます。
- 質問と回答の履歴は残りません。
- 別のセッションに引き継ぐときは、このフォルダを渡します。
- 入力ファイルの名前が `SPEC.md` や `request.md` と重なるときは、先頭に `input-` が付きます。同じ名前が複数あるときは、連番が付きます。

### 保存先を変える

保存先の親フォルダは、次の順で決まります。

1. `init` の `--parent` 引数
2. 環境変数 `GRILL_FORM_DIR`（相対パスは git のルート、なければカレントフォルダから解決）
3. `grill-specs`（既定。git のルート直下）

常に同じ場所に保存したいときは、`settings.json` で環境変数を設定します。

```json
{
  "env": {
    "GRILL_FORM_DIR": "00_inbox"
  }
}
```

入力ファイルも、そのままコミット対象になります。機密資料や大きいファイルを渡すときは、`GRILL_FORM_DIR` でリポジトリ外のフォルダを指定するか、`grill-specs/` を `.gitignore` に加えてください。

## トラブルシューティング

**スキルが起動しない**
- 「grill-form で〜」や「HTML で grilling」と明示して頼んでください。「grill して」だけでは、通常の `grilling` スキルが使われます。
- 配置した直後は、Claude Code を再起動してください。

**Playwright MCP のツール（`browser_*`）がないと言われる**
- 「クイックスタート」の手順 2 で登録し、Claude Code を再起動してください。`claude mcp list` で `playwright` を確認できます。

**すでに `playwright` を登録していて、`claude mcp add` が効かない**
1. `claude mcp get playwright` で、現在の引数とスコープを確認します。
2. `claude mcp remove playwright --scope <スコープ>` で削除します。
3. 元の引数を残したまま、`--allow-unrestricted-file-access` と `--output-dir` を付けて登録し直します。
4. Claude Code を再起動します。

**`file://` のページが開けない**
- Playwright MCP に `--allow-unrestricted-file-access` が付いているか確認してください。

**送信が検知されない**
- ブラウザの「送信」を押したあと、「送信しました」と表示されるか確認してください。
- 約 30 分待っても送信がないと、Claude が続行方法を聞きます。フォームの「Markdown をコピー」で回答を貼る方法もあります。
- コピーした回答には、選んだファイルは含まれません。ファイルは「ファイルパス」欄で渡してください。

**選んだファイルが取り込まれない**
- Playwright MCP の `--output-dir` にダウンロードが保存されます。出力先が書き込める場所か確認してください。
- うまくいかないときは、「ファイルパス」欄に書いて渡してください。

**ファイルパスが読めない**
- 存在しないパスや、フォルダのパスは取り込めません。ファイルのパスを書いてください。Claude から再入力を求められます。

**PDF・PowerPoint の図形が読めない**
- 画像にするツールが環境にないためです。ツール（LibreOffice の `soffice`、poppler の `pdftoppm` など）を入れるか、図の内容を依頼文に書いてください。

**SPEC が想定外の場所にできた**
- 保存先は、`--parent`、環境変数 `GRILL_FORM_DIR`、`grill-specs` の順で決まります。`GRILL_FORM_DIR` が設定されていないか確認してください。

**一時フォルダの削除に失敗した**
- シェルのカレントフォルダが、一時セッションの中にないか確認してください。SPEC と入力ファイルは保存済みです。残った一時フォルダは、次回の実行時に 3 日より古いものから自動で削除されます。

**日本語のテーマ名が文字化けする**
- テーマ名は ASCII の短い名前（例: `api-design`）にしてください。

**`python` コマンドが見つからない**
- `python3` と読み替えます。Claude は自動で読み替えます。

## 仕組み

| ファイル | 内容 |
| --- | --- |
| `SKILL.md` | スキルの定義と手順 |
| `grill_form.py` | `init`（一時セッションの作成と古いものの削除）、`render`（HTML 生成）、`stage`（入力ファイルの取り込み）、`cleanup`（入力ファイルを SPEC のフォルダへ移し、一時セッションを削除） |
| `grill_form_template.html` | フォームのテンプレート（外部リソースなし） |
| `THIRD_PARTY_NOTICES.md` | 取り込んだルールの出典とライセンス |

作業用のファイルは、OS の一時フォルダに置かれます。

| 種類 | 場所 | 寿命 |
| --- | --- | --- |
| 作業用ファイル（質問 JSON・HTML・回答 Markdown・取り込んだ入力ファイル） | 一時フォルダ配下 `grill-form/<日時>_<テーマ>/` | 承認後に自動削除。未承認で中断したものは 3 日後に削除 |
| Playwright MCP の記録とダウンロード | 一時フォルダ配下 `playwright-mcp/` | OS の一時フォルダの掃除に任せる |

## ライセンス

[MIT](LICENSE)

`SKILL.md` の「ルール」節は、Matt Pocock 氏の [grilling スキル](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT）を要約・翻案したものです。元のライセンス表記は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にあります。
