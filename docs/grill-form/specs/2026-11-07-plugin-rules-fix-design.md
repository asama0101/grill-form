---
status: 完了
plan: docs/grill-form/plans/2026-11-07-plugin-rules-fix.md
---

# plugin-rules.md 準拠の差異を直す SPEC

## 概要

`~/.claude/reference/plugin-rules.md` に照らした点検（2026-11-07）で、必須項目の違反はなく、推奨項目の差異が見つかった。これを直す。

### 入力

- 点検レポート（この会話）。参考資料のファイルはなし。
- 規則: `C:\Users\sioay\.claude\reference\plugin-rules.md`（E3・E6・H5）。
- 対象: `README.md`、`tests/test_skill.py`、`tests/test_grill_form.py`。

### 直す項目

1. **E3**: README の「開発者向け」節と、`docs/development.md` へのリンクを削除する。README は利用者向けだけにする。
2. **E6**: コード・資源の置き場 `scripts/` の名前と役割を、README に 1 行で書く。
3. **H5**: 空白・日本語を含むパスで `grill_form.py` が動くことを、テストで確かめる。

## 流れ

1. README から「開発者向け」節（見出しとリンク）を削除する。→ 確認: README に `development.md` が出ない。
2. README に `scripts/` の説明を 1 行足す。置き場所は実装時に決める。→ 確認: README に `scripts/` と役割が書かれている。
3. `tests/test_skill.py` の `test_READMEの章は規則の順番に並ぶ` が、節の削除後も通るよう期待値を直す。→ 確認: pytest が通る。
4. 空白・日本語を含む一時フォルダで `init` → `render` を通すテストを `tests/test_grill_form.py` に足す。失敗したら、スクリプトのパス処理を直す。→ 確認: 新しいテストが通る。
5. 全体を検査する。→ 確認: `pytest` が全件通り、`claude plugin validate plugins/grill-form --strict` が通る。

## 受入条件

- README に「開発者向け」節がなく、`docs/development.md` へのリンクがない。
- README に `scripts/` の名前と役割が書かれている。
- 空白・日本語を含むパスで `init` と `render` が終了コード 0 で終わるテストがあり、通る。
- `pytest` が全件通る（スキップは既存の 1 件のみ）。
- `claude plugin validate plugins/grill-form --strict` が通る。
- 変更は README とテストだけ。plugin.json、SKILL.md、スクリプト本体は、H5 のテストが失敗した場合を除いて変えない。

## 非目標

- C4（SKILL.md の `references/` 分割）。114 行で基準内なので対象外。
- H3（`schema_version`）。設定ファイルがないので対象外。
- `docs/development.md` の内容の変更や削除。README からのリンクを外すだけ。
- SKILL.md の挙動、フォームの仕様、バージョンの変更（1.0.0 のまま）。

## リスク

- README から `docs/development.md` に辿れなくなる。開発者は `docs/` を直接探す必要がある。規則（E3）がそれを求めているので受け入れる。
- H5 のテストで本体の不具合が見つかると、スクリプトの修正が増える。その場合は修正内容を別途確認する。
- `test_READMEの章は規則の順番に並ぶ` の期待値を直すとき、章の順序の検査を弱めないこと。

## 決定ログ

| 決定 | 理由 |
|---|---|
| E3 は節ごと削除する | 規則が README に開発者向けの案内を書かないとしているため。リンクだけ残す案は趣旨に合わない。 |
| E6 は README に 1 行書くだけにする | 規則が求めるのは「名前を決めて README に書く」ことだけで、ディレクトリ構成は変えない。 |
| H5 はテスト追加から始める | 現状の動作が未確認なので、まず確かめ、失敗したときだけ本体を直す。 |
| C4・H3 は直さない | 推奨項目で、守らない理由がある（C4: 114 行で基準内、H3: 設定ファイルなし）。 |

## 後続の手順

1. 実装計画を作るときは、保存先を `docs/grill-form/plans/2026-11-07-plugin-rules-fix.md` にする（フォルダがなければ作る）。計画の先頭に `status: 未対応` と `spec: docs/grill-form/specs/2026-11-07-plugin-rules-fix-design.md` を書く。
2. 計画を保存したら、この SPEC の先頭を `status: 完了` にし、`plan:` に `docs/grill-form/plans/2026-11-07-plugin-rules-fix.md` を書く。
3. 計画の実装がすべて終わったら、計画の先頭を `status: 完了` にする。
