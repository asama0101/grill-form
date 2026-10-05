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
claude mcp add playwright --scope user -- npx @playwright/mcp@latest --allow-unrestricted-file-access
```

ブラウザを指定する場合は `--browser chrome` などを追加します。

## 使い方

Claude Code で次のように頼みます。

```
roundtable で <テーマ> を詰めたい
```

1. Claude がラウンドごとに質問の HTML を生成し、ブラウザで開きます。
2. 回答して「送信」を押し、ターミナルに「完了」と入力します。
3. 決めることがなくなるまでラウンドを繰り返し、最後に SPEC 案を確認・承認します。

通常の「grill」では起動しません（`roundtable` や「HTML で grilling」と明示したときだけ使います）。

## セッションの保存先

質問の HTML と回答の Markdown は、次の順で決まるフォルダの下に `<日時>_roundtable_<テーマ>/` として保存されます。

1. `init` の `--parent` 引数
2. 環境変数 `ROUNDTABLE_DIR`（相対パスはカレントフォルダから解決）
3. カレントフォルダ（既定。HTML や回答を直接開けるよう、隠しフォルダにはしない）

常に同じ場所へ保存したい場合は、Claude Code の `settings.json` で環境変数を設定します。

```json
{
  "env": {
    "ROUNDTABLE_DIR": "00_inbox"
  }
}
```

Git リポジトリ内で使う場合は、必要に応じて `*_roundtable_*/` を `.gitignore` に追加してください。

## ファイル構成

| ファイル | 内容 |
| --- | --- |
| `SKILL.md` | スキルの定義と手順 |
| `roundtable.py` | セッション作成（`init`）、HTML 生成（`render`）、索引作成（`index`） |
| `roundtable_template.html` | 質問フォームのテンプレート（外部リソースなし） |
| `THIRD_PARTY_NOTICES.md` | 取り込んだルールの出典とライセンス |

## ライセンス

[MIT](LICENSE)

`SKILL.md` の「ルール」節は、Matt Pocock 氏の [grilling スキル](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling)（MIT）を要約・翻案したものです。元のライセンス表記は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) にあります。
