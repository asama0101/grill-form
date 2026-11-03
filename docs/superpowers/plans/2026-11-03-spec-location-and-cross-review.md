# SPEC の保存先の統一とクロスレビューの追加 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** grill-form の SPEC の保存先を `docs/grill-form/specs/` に固定し、状態（status）の規約と、5 観点のクロスレビューを SKILL.md に入れる。

**Architecture:** 保存先の決定は `grill_form.py` の `spec_path` と `spec-path` サブコマンドに閉じる。入力フォームの保存先欄と回答の `## 保存先` 節は削除する。status とクロスレビューは実行時のコードを持たず、SKILL.md の手順（Claude への指示）として書き、`tests/test_skill.py` の語句検査で守る。

**Tech Stack:** Python 3（標準ライブラリのみ）、単一 HTML テンプレート（素の JavaScript）、pytest、ruff。

**Spec:** `docs/superpowers/specs/2026-11-03-spec-location-and-cross-review-design.md`（以下「設計書」）。実装者は設計書も読む。

## Global Constraints

- SPEC の保存先: `<作業フォルダ>/docs/grill-form/specs/YYYY-MM-DD-<テーマ>-design.md`。同名があれば末尾に `-2`、`-3`（例: `2026-11-03-api-design-design-2.md`）。既存のファイルは上書きしない。
- 計画の置き場（規約。grill-form は計画を作らない）: `docs/grill-form/plans/YYYY-MM-DD-<テーマ>.md`。計画名は SPEC のファイル名から `-design` を除いたもの（日付と連番は引き継ぐ）。
- status の値は `未対応` と `完了` の 2 つだけ。SPEC は計画が保存された時点で `完了`、計画は実装が終わった時点で `完了`。SPEC の frontmatter は `status:` と `plan:`、計画の frontmatter は `status:` と `spec:`。
- クロスレビューは 5 観点・5 体: 要件の網羅 / 計画への落とし込み / 受入条件と矛盾 / シンプルさ / リスクと非目標。再レビューは 1 回まで（ユーザーの判断で質問に戻ったら回数を 0 に戻す）。
- `spec-path` の終了コード: `--parent` は削除（argparse の引数エラーで 2）。`docs/grill-form/specs/` を作れないときは標準エラーに出して 1。
- 版: `__version__` と `plugin.json` の version は変えない（設計書にない）。
- ファイルは UTF-8・LF。`ruff check .` と `ruff format --check .` が通る（`pyproject.toml` の設定に従う）。
- 一時ファイルはプロジェクト内に置かない。テストは `tmp_path` を使う。
- コミットは、ユーザーの確認を得てから行う（確認なしにはしない）。形式は既存に合わせ、`type: 日本語の件名`。本文の末尾に `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` を付ける。
- 検証コマンド（以下 `$PY`）: `python -m venv "$TMP/grill-form-venv"` で OS の一時フォルダに作った venv の `Scripts/python`。`$PY -m pip install -r requirements-dev.txt` で導入済みにする。

## Review Focus

- `docs` が既存のファイルのとき、`spec-path` は標準出力に何も出さず、標準エラーに理由を出して終了コード 1 で止まる（Task 1 でテスト）。
- `docs/grill-form/specs/` が既にあるとき、`spec-path` を 2 回呼んでも失敗しない（Task 1 でテスト）。
- 古い形式の回答（`## 保存先` 節を含む）を `render --intake --answers` に渡しても、依頼文・参考資料が壊れずに復元される（Task 1 でテスト）。
- 記号だけのテーマは `untitled` になる（既存の挙動を新しい名前の形式で保つ。Task 1 でテスト）。
- 入力フォームの描画の JavaScript が、削除した変数（`outSel`・`outPath`・`outTree`）を参照して実行時に落ちない（Task 2 でテスト: 参照の文字列が残っていないこと。ブラウザでの操作は手で確かめる）。

---

### Task 1: `spec_path` と `spec-path`、回答の解析から保存先を取り除く

**Files:**
- Modify: `plugins/grill-form/scripts/grill_form.py`
- Modify: `tests/test_grill_form.py`

**Interfaces:**
- Produces: `spec_path(theme: str, today: datetime.date | None = None) -> Path`（`<cwd>/docs/grill-form/specs/<日付>-<正規化したテーマ>-design.md`、連番つき。ファイルもフォルダも作らない）。`parse_intake_answers(md: str) -> dict`（キー `dest` なし）。`spec-path --theme T`（`--parent` なし）は、保存先のフォルダを作ってから、パスを 1 行で出力する。

- [ ] **Step 1: 変更前のテストを実行して、通っている状態を確かめる**

Run: `$PY -m pytest -ra`
Expected: すべて PASS（`claude` CLI がなければ `test_claude_plugin_validateが通る` は SKIPPED）。失敗があれば、変更前から失敗していたものとして控える。

- [ ] **Step 2: 失敗するテストを書く（`tests/test_grill_form.py`）**

`spec_path` に関する次のテストを、新しい仕様に書き換える。期待値はリテラルで書く。
- `test_spec_pathは作業フォルダのdocs配下にテーマ_日付_designを返す`: `grill_form.spec_path("api-design", today=TODAY) == workdir / "docs" / "grill-form" / "specs" / "2026-10-24-api-design-design.md"`
- `test_spec_pathは既存ファイルがあれば連番を進める`: 上と同じフォルダに `2026-10-24-api-design-design.md` と `2026-10-24-api-design-design-2.md` を作っておくと、`...-design-3.md` を返し、既存の中身は変わらない。
- `test_spec_pathは記号だけのテーマをuntitledにする`: `.name == "2026-10-24-untitled-design.md"`
- `test_spec_pathはファイルもフォルダも作らない`: 呼んだあと `list(workdir.iterdir()) == []`
- `test_spec_pathサブコマンドは絶対パスを1行で出力する`: 終了コード 0、出力は 1 行、`Path(line).parent == workdir / "docs" / "grill-form" / "specs"`、`Path(line).name` が `-demo-design.md` で終わる。
- 新規 `test_spec_pathサブコマンドは保存先のフォルダを作るがSPECは作らない`: 実行後に `(workdir / "docs/grill-form/specs").is_dir()` かつそのフォルダが空。
- 新規 `test_spec_pathサブコマンドは保存先のフォルダがあっても2回続けて成功する`: 2 回とも終了コード 0。
- 新規 `test_spec_pathサブコマンドはdocsがファイルなら終了コード1で止まる`: `workdir / "docs"` をファイルにして実行すると終了コード 1、`captured.out == ""`、`captured.err` が空でない。
- 新規 `test_spec_pathサブコマンドは_parentを受け付けない`: `run(monkeypatch, "spec-path", "--theme", "t", "--parent", "x")` が `SystemExit` を送出し、`.value.code == 2`。
- 削除: `parent` を使う 3 テスト（相対・絶対・チルダ）と、`test_spec_pathは親が既存のファイルなら終了コード2で止まる`、`test_spec_pathは存在しない親ならそのままパスを返す`。

回答の解析に関するテストを、`dest` なしに書き換える。
- `parse_intake_answers` を呼ぶ 3 テスト（テキストの依頼文・欠けた節・更新の印）と `render --answers` のテストの期待する辞書から、`"dest"` のキーと、入力 Markdown の `## 保存先` 節を取り除く。
- `test_入力フォームに保存先欄があり回答の節を持つ` と `test_入力フォームの保存先は作業フォルダを初期値にする` を、`test_入力フォームに保存先欄がない` に置き換える: `render --intake` の HTML に `"保存先" not in html` と `"in-pick one" not in html`。
- `test_render_intakeは空の回答で_inputの値を消さない` の `--input` の JSON から `"dest"` を取り除き、`"dest" not in data` を確かめる。
- 新規 `test_parse_intake_answersは古い形式の保存先の節を無視する`: `## 依頼文`・`## 参考資料`（`- C:\w\a.pdf`）・`## 保存先\nC:\w` を含む Markdown の結果が、`## 保存先` 節だけを除いた同じ Markdown の結果と等しく、`"dest" not in` 結果。

- [ ] **Step 3: テストを実行して、失敗を確かめる**

Run: `$PY -m pytest tests/test_grill_form.py -ra`
Expected: 上で書き換えた・足したテストが FAIL（`spec_path()` の引数、`dest` キー、`--parent` の扱いによる）。出力を控える。

- [ ] **Step 4: `grill_form.py` を実装する**

- `spec_path(theme: str, today: datetime.date | None = None) -> Path` に変える。`parent` を削除する。基準フォルダは `Path.cwd() / "docs" / "grill-form" / "specs"`、`stem` は `f"{day}-{normalize_theme(theme)}-design"`、連番は今の `while cand.exists()` の形のまま。定数 `SPEC_PREFIX` は使われなくなるので削除する。
- `cmd_spec_path(args) -> int`: `path = spec_path(args.theme)` のあと、`path.parent.mkdir(parents=True, exist_ok=True)` を `try`、`except OSError` で標準エラーに `保存先のフォルダを作れません: {path.parent} ({e})` を出して `return 1`。成功したら `print(path)`、`return 0`。
- `main()` から `spec-path` の `--parent` を削除する。
- `INTAKE_SECTIONS` から `"保存先"` を、`parse_intake_answers` の `state` から `"dest"` と、`state["dest"] = ...` の代入を削除する。
- `cmd_render` の `payload["dest"] = ...` の行を削除し、`title` の既定を `"入力（依頼文・参考資料）"` にする。
- モジュール先頭の docstring を更新する: `spec-path --theme T` の説明を「SPEC の保存先 `<作業フォルダ>/docs/grill-form/specs/<日付>-<テーマ>-design.md` を決め、フォルダを作って、パスを出力する（ファイルは作らない）。同名があれば末尾に連番を付ける」に、`render --intake` の `J.json` の説明から `dest` と保存先に関する記述を削除する。

- [ ] **Step 5: テストを実行して、通ることを確かめる**

Run: `$PY -m pytest -ra && $PY -m ruff check . && $PY -m ruff format --check .`
Expected: すべて PASS。ただし `tests/test_skill.py` は、SKILL.md を Task 3 で更新するまでの間、`## 保存先` を求めるテストが FAIL してよい（Task 3 で直す）。それ以外が通ること。

- [ ] **Step 6: コミット（ユーザーの確認後）**

```bash
git add plugins/grill-form/scripts/grill_form.py tests/test_grill_form.py
git commit -m "feat: SPEC の保存先を docs/grill-form/specs/ に固定し、保存先の指定を廃止する"
```

---

### Task 2: 入力フォームから保存先の欄を削除する

**Files:**
- Modify: `plugins/grill-form/scripts/grill_form_template.html`
- Modify: `tests/test_grill_form.py`

**Interfaces:**
- Consumes: Task 1 で、`render --intake` のデータに `dest` が入らなくなる。
- Produces: 入力フォームは、依頼文・参考資料・「フォルダを読み直す」だけを持つ。回答 Markdown は `## 依頼文`（と `## 保留の依頼文`）・`## 参考資料` の節で終わる。

- [ ] **Step 1: 失敗するテストを書く（`tests/test_grill_form.py`）**

`test_入力フォームの描画から保存先用の変数が消えている`: テンプレートの文字列に、`"outSel"`・`"outPath"`・`"outTree"`・`"outSum"`・`"extraOut"`・`"保存先"`・`"in-pick one"` がどれも含まれない（`parametrize` で 1 語ずつ）。

- [ ] **Step 2: テストを実行して、失敗を確かめる**

Run: `$PY -m pytest tests/test_grill_form.py -k 保存先用の変数 -ra`
Expected: FAIL（7 件）。

- [ ] **Step 3: `grill_form_template.html` を編集する**

- `intakeMarkdown` の `md += '\n## 保存先\n' + ...` の行を削除する（直前の参考資料の行が `\n` で終わるので、末尾は `return md;` のまま）。
- `renderIntake` から削除する: `outSel`・`extraOut` の宣言、`data.dest` を読む `if` ブロック、`expandTo` に渡す配列の `outSel.sel`、`// 保存先` から `content.appendChild(scard);` までのブロック、`current()` の `dest`、`draw()` の `drawTree(outTree, ...)` と `outSum.textContent = ...`、`[reqPath, outPath].forEach(...)`（`reqPath.addEventListener('input', draw)` にする）。
- `drawTree` の引数 `radio` と、`if (radio) { ... }` のブロックを削除し、呼び出し 2 か所から最後の引数 `false` を取り除く。コメント「ツリー（radio: 保存先用…）」を「ツリー」に直す。
- CSS から `.in-pick.one` の 2 行を削除する。
- コメント「入力フォーム: 依頼文・参考資料・保存先」を「入力フォーム: 依頼文・参考資料」に直す。

- [ ] **Step 4: テストを実行して、通ることを確かめる**

Run: `$PY -m pytest tests/test_grill_form.py -ra && $PY -m ruff check . && $PY -m ruff format --check .`
Expected: PASS。

- [ ] **Step 5: ブラウザで入力フォームを目視する（自動テストの対象外）**

任意のフォルダで `$PY plugins/grill-form/scripts/grill_form.py render --session-dir <一時フォルダ>/s --intake` を実行し、出力された `intake.html` を Playwright MCP で開く。依頼文・参考資料・「フォルダを読み直す」が動き、保存先の欄がなく、コンソールにエラーが出ないことを確かめる（`browser_console_messages`）。「送信」後の `window.__answersMd` に `## 保存先` がないことも確かめる（`browser_evaluate`）。

- [ ] **Step 6: コミット（ユーザーの確認後）**

```bash
git add plugins/grill-form/scripts/grill_form_template.html tests/test_grill_form.py
git commit -m "feat: 入力フォームから保存先の欄を削除する"
```

---

### Task 3: SKILL.md に保存先・status・クロスレビューの手順を書く

**Files:**
- Modify: `plugins/grill-form/skills/grill-form/SKILL.md`
- Modify: `tests/test_skill.py`

**Interfaces:**
- Consumes: Task 1 の `spec-path --theme T`（`--parent` なし）の出力。
- Produces: 設計書の「決定事項」2・3 と「実装の細部」を、Claude への指示として書いた SKILL.md。

- [ ] **Step 1: 失敗するテストを書く（`tests/test_skill.py`）**

置き換えるテスト:
- `test_SKILLは保存先を入力フォームで受け取りRound0は3点のまま` → `test_SKILLは保存先を聞かずRound0は3点のまま`: `"`## 保存先`" not in text`、`"次の3点を" in text`、`"次の4点を" not in text`。
- `test_SKILLは保存先のフォルダの存在を確認する` と `test_SKILLは保存先の確認を承認より前の入力フォームの手順で行う` を削除する（保存先の確認は不要になる）。
- 点検の語句テストの `present` を、`"点検1"`、`"保留（「あとで決める」）が残っていない"`、`"判断がぶれる言葉"`、`"判定できる"`、`"クロスレビュー"`、`"文脈を持たない新しいサブエージェント"`、`"矛盾がないか"` に変える。
- `test_SKILLの点検1は手順9より前にあり_点検2は…` → `…クロスレビューは最終確認のフォームを開く前にある`: `text.index("クロスレビュー") < text.index("`render --final")`。

足すテスト:
- `test_SKILLに点検2の記述が残っていない`: `"点検2" not in text`。
- `test_SKILLのクロスレビューに5観点がある`: `parametrize` で `要件の網羅`・`計画への落とし込み`・`受入条件と矛盾`・`シンプルさ`・`リスクと非目標` が `text` にある。
- `test_SKILLのクロスレビューは再レビューを1回までにする`: `"再レビューは 1 回まで" in text`。
- `test_SKILLに保存先とstatusと後続の手順の規約がある`: `parametrize` で `docs/grill-form/specs`・`docs/grill-form/plans`・`status: 未対応`・`status: 完了`・`## 後続の手順`・`plan:`・`spec:` が `text` にある。
- `test_SKILLのspec_pathに_parentを付けない`: `"--parent" not in text`。

- [ ] **Step 2: テストを実行して、失敗を確かめる**

Run: `$PY -m pytest tests/test_skill.py -ra`
Expected: 足した・置き換えたテストが FAIL。

- [ ] **Step 3: SKILL.md の手順2を編集する**

- 見出し行を「入力フォーム（毎回行う）: 依頼文・参考資料を集める。」にする。
- 手順2の説明のフォームの内容から「保存先（ツリーで 1 つ。外のパスはパス欄）」を削除する。
- 次の 3 つの箇条書きを削除する: `## 保存先` の読み方、「保存先がフォルダの指定に読めない文章のときは…」、「ここで、そのフォルダが存在するフォルダか確認する…」。
- 手順1の「SPEC の保存先（以下 `<S>`）は、手順10で決める。」はそのまま。

- [ ] **Step 4: SKILL.md の手順9の点検2を、次の内容のクロスレビューに置き換える**

箇条書き 3 つ（「フォームを開く前に、点検2をする…」「見る点は…」「指摘のうち…」）を、次の文面の箇条書きに置き換える。1 行は 400 字以内にする。

```
   - フォームを開く前に、クロスレビューをする。この会話の文脈を持たない新しいサブエージェントを 5 体、同時に起動する。互いの結果は見せない。各体に渡すのは、依頼文・SPEC 案・その体の観点だけ。依頼文と SPEC 案に秘密情報があれば、マスクしてから渡す。
   - 5 つの観点は次のとおり。
     1. 要件の網羅: 依頼文・参考資料の要求が、SPEC のどこで答えられているか。抜けがないか。
     2. 計画への落とし込み: SPEC に決まっていないことが残らず、writing-plans が計画を作れるか。計画を作るときに推測が要る箇所はないか。
     3. 受入条件と矛盾: 受入条件を第三者が「できた／できていない」と判定できるか。概要・流れ・受入条件・非目標・リスク・決定ログのあいだに矛盾がないか。
     4. シンプルさ: 同じ目的を、より少ない決定・手順・ロジックで達成できないか。依頼にない機能が入っていないか。
     5. リスクと非目標: リスクと非目標に漏れがないか。
   - 指摘のうち、自分だけで直せるものは直す。ユーザーの判断が要るものは、手順4に戻って質問にする。回答後は手順8の点検1からやり直す。観点どうしで指摘が衝突するとき（特に、シンプルさの削減提案が要件の網羅と衝突するとき）は、自分で選ばず、質問にする。
   - 直したあとの再レビューは 1 回まで。指摘があった観点のレビュアーだけに行う。手順4に戻ったときは、再レビューの回数を 0 に戻す。再レビューのあとに残る指摘は、SPEC のリスクに書く。
   - サブエージェントが使えないときは、同じ 5 つの観点で、自分で SPEC 案を順に読む。
   - クロスレビューの結果は、最終確認のフォームには出さない。
```

手順9の見出し行の文言（「合意内容を SPEC 案にまとめて、最終確認のフォームを開く」）と、フォームを開く以降の箇条書き（`render --final` など）は変えない。

- [ ] **Step 5: SKILL.md の手順10を編集する**

- `spec-path` の行から `[--parent "<フォルダ>"]` を削除し、「出力を SPEC の保存先 `<S>`（`<作業フォルダ>/docs/grill-form/specs/<日付>-<テーマ>-design.md`）とする。`spec-path` は保存先のフォルダがなければ作る」にする。
- 「`--parent` は、手順2の `## 保存先` があるときだけ付ける…」の箇条書きを削除する。
- 「承認された版の `summary` をそのまま `<S>` に書く（Write）」を次の内容に置き換える。

```
   - 承認された版の `summary` を、次の形で `<S>` に書く（Write）。frontmatter と「後続の手順」は、最終確認のフォームの `summary` には含めず、ここで足す。
     1. 先頭に、`---`・`status: 未対応`・`plan: （未作成）`・`---` の 4 行（frontmatter）を書く。
     2. 続けて `summary` をそのまま書く。
     3. 末尾に `## 後続の手順` の節を書く。内容は次の 3 項目。`<計画のパス>` は、`<S>` のファイル名から末尾の `-design` を除いたもの（日付と連番は同じ）を、`docs/grill-form/plans/` の下に置いた相対パスとして、保存時に具体的に埋める。
        - 1. 実装計画を作るときは、保存先を `<計画のパス>` にする（フォルダがなければ作る）。計画の先頭に `status: 未対応` と `spec: <この SPEC の相対パス>` を書く。
        - 2. 計画を保存したら、この SPEC の先頭を `status: 完了` にし、`plan:` に計画のパスを書く。
        - 3. 計画の実装がすべて終わったら、計画の先頭を `status: 完了` にする。
```

- 「別のセッションに SPEC を渡すときは、このファイルを使う。」は残す。

- [ ] **Step 6: テストを実行して、通ることを確かめる**

Run: `$PY -m pytest -ra && $PY -m ruff check . && $PY -m ruff format --check .`
Expected: すべて PASS（特に `test_SKILLの本文は1行が長すぎない`、`test_SKILLに廃止した語が残っていない`）。

- [ ] **Step 7: コミット（ユーザーの確認後）**

```bash
git add plugins/grill-form/skills/grill-form/SKILL.md tests/test_skill.py
git commit -m "feat: SPEC の status 規約と 5 観点のクロスレビューを SKILL.md に追加する"
```

---

### Task 4: README と開発者向けメモを更新する

**Files:**
- Modify: `README.md`
- Modify: `docs/development.md`
- Test: `tests/test_skill.py`（既存の README 検査。変更なし）

**Interfaces:**
- Consumes: Task 1〜3 で決まった保存先・名前・status・クロスレビュー。

- [ ] **Step 1: 古い記述の位置を洗い出す**

Run: `grep -n "保存先\|SPEC-\|点検\|--parent\|親フォルダ" README.md docs/development.md`
Expected: README の「使い方」の手順 1 と 4、入力フォームの表の「保存先（親フォルダ）」行、「残るもの」、「設定」の保存先、「困ったとき」の「SPEC が想定外の場所にできた」、`docs/development.md` の `spec-path` の行。

- [ ] **Step 2: README を編集する**

- 使い方の手順 1: 「依頼文、参考資料を渡します。」にする。手順 4: 点検の説明を「出す前に、観点の違う 5 つのレビュアーが、要件の網羅・計画への落とし込み・受入条件と矛盾・シンプルさ・リスクと非目標を確かめます。」にする。
- 入力フォームの表から「保存先（親フォルダ）」の行を削除し、箇条書きの「作業フォルダの外のファイルやフォルダは、各欄の下のパス欄に…」を、依頼文と参考資料に合う文面にする。
- 「残るもの」: パスを `<作業フォルダ>/docs/grill-form/specs/<日付>-<テーマ>-design.md` にし、例を `2026-11-03-api-design-design.md`、連番を `-design-2` の形にする。先頭の `status: 未対応 / 完了` の意味（SPEC は計画が保存されたら `完了`）と、実装計画の置き場 `docs/grill-form/plans/`（計画づくりは別のスキルで行い、実装が終わったら計画を `完了` にする）を、箇条書きで足す。
- 「設定」: 保存先の項目を削除し、「設定ファイルはありません。」に直す（「入力フォームで、毎回指定します」は、指定する項目がなくなるので削除）。保存先が git の管理対象になる注意は、「残るもの」に移す。
- 「困ったとき」: 「SPEC が想定外の場所にできた」を、「SPEC は、Claude Code を起動したフォルダの `docs/grill-form/specs/` にできます。サブフォルダで起動していないか確認してください。」に直す。

- [ ] **Step 3: `docs/development.md` を編集する**

`spec-path` の行を「`spec-path --theme T`」「SPEC の保存先 `<作業フォルダ>/docs/grill-form/specs/<日付>-<テーマ>-design.md` を決め、フォルダを作って出力する（ファイルは作らない）。同名があれば連番を付ける。フォルダを作れなければ終了コード 1」に直す。

- [ ] **Step 4: 検証する**

Run: `$PY -m pytest -ra && grep -n "親フォルダ\|--parent\|SPEC-<" README.md docs/development.md plugins/grill-form/skills/grill-form/SKILL.md plugins/grill-form/scripts/grill_form.py`
Expected: pytest が PASS（README の章の順と、廃止した語の検査を含む）。grep の出力が空。

- [ ] **Step 5: コミット（ユーザーの確認後）**

```bash
git add README.md docs/development.md
git commit -m "docs: 保存先の固定と status・クロスレビューを README に反映する"
```

---

## Self-Review の結果

- 設計書の目標 4 つ（保存先の固定、計画の置き場の規約、status、クロスレビュー）と非目標（`--parent`・保存先欄の削除、既存 SPEC を移行しない）は、Task 1〜4 のどれかに対応する。
- 型と名前: `spec_path(theme, today)`、`cmd_spec_path`、`parse_intake_answers` は Task 1 で定義し、Task 3 は `spec-path --theme T` だけを使う。
- 計画の長さは設計書の約 1.5 倍で、コードの本体は書かず、署名・テスト名・SKILL.md の文面だけを書いている。
