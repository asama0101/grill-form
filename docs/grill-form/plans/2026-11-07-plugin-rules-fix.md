---
status: 完了
spec: docs/grill-form/specs/2026-11-07-plugin-rules-fix-design.md
---

# plugin-rules.md 準拠の差異を直す 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** README を規則 E3・E6 に合わせ、H5（空白・日本語を含むパス）をテストで確かめる。

**Architecture:** 変更は README とテストだけ。H5 のテストが落ちた場合に限り、`grill_form.py` を直す。README の仕様は、`tests/test_skill.py` の README 検査に追加して固定する。

**Tech Stack:** Python 3、pytest 9.1.1、ruff 0.17.2、`claude plugin validate`。

**Spec:** `docs/grill-form/specs/2026-11-07-plugin-rules-fix-design.md`

## Global Constraints

- バージョンは `1.0.0` のまま。plugin.json・SKILL.md は変えない。
- `docs/development.md` は変えない（README からのリンクを外すだけ）。
- テストは pytest の関数形式。テキストの読み書きは `encoding="utf-8"` を明示する。
- スキップは既存の 1 件（`tests/test_folder_scan.py:96`）のみ。
- 作業ブランチ: `docs/plugin-rules-fix-spec`（SPEC をコミット済み）。

## Review Focus

- 作業フォルダとセッションフォルダの両方に空白と日本語が入る: `init` → `render --intake` が終了コード 0 で終わり、HTML が書かれる。（Task 2）
- `--input` のファイルのパスに空白と日本語が入る: 入力が HTML に復元される。（Task 2）
- 一時フォルダ（`TEMP`）のパスに空白と日本語が入る: `init` が成功する。（Task 2）
- README の「開発者向け」を消したあと、章の並びの検査が弱まる: 期待値の `README_SECTIONS` からも消し、並びの検査は残す。（Task 1）

---

### Task 1: README を E3・E6 に合わせる

**Files:**
- Modify: `README.md`（「開発者向け」節の削除、「設定」節への追記）
- Modify: `tests/test_skill.py`（`README_SECTIONS` から「開発者向け」を削除。README の新しい検査を 2 つ追加）

**Interfaces:**
- Produces: なし（Task 2 は独立）。

- [ ] **Step 1: 失敗するテストを書く**（`tests/test_skill.py`、`test_READMEは未検証の明記を本文に書かない` の後ろ）

```python
def test_READMEに開発者向けの案内がない():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "development.md" not in text
    assert "## 開発者向け" not in text


def test_READMEにscriptsの置き場が書かれている():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "plugins/grill-form/scripts/" in text
```

- [ ] **Step 2: 赤を確認する**

Run: `PYTHONUTF8=1 python -m pytest tests/test_skill.py -k "開発者向け or scripts" -ra`
Expected: 2 件が FAIL（赤の出力を完了報告に添える）

- [ ] **Step 3: README を直す**
  - 「## 開発者向け」の見出しと、本文 1 行（`docs/development.md` へのリンク）を削除する（`README.md:166` 付近。前後の空行は 1 行に整える）。
  - 「## 設定」節（`README.md:119` 付近）に、箇条書きを 1 つ足す: `- **構成**: コードと資源は `plugins/grill-form/scripts/` にあります（フォーム生成と作業フォルダの走査のスクリプト、フォームのテンプレート）。`
  - 「設定ファイルはありません。」の文は残す。

- [ ] **Step 4: 章の期待値を直す**（`tests/test_skill.py` の `README_SECTIONS`）
  - 要素 `"開発者向け",` を削除する。`test_READMEの章は規則の順番に並ぶ` 本体は変えない。

- [ ] **Step 5: 青を確認する**

Run: `PYTHONUTF8=1 python -m pytest tests/test_skill.py -ra`
Expected: すべて PASS（`claude plugin validate` のテストを含む）

- [ ] **Step 6: Commit**

```bash
git add README.md tests/test_skill.py
git commit -m "docs: README から開発者向けの案内を外し、scripts の置き場を書く"
```

（コミットメッセージの末尾に Co-Authored-By の行を付ける。）

---

### Task 2: 空白・日本語を含むパスの統合テスト（H5）

**Files:**
- Modify: `tests/test_grill_form.py`（末尾に追加）
- Modify（テストが落ちた場合のみ）: `plugins/grill-form/scripts/grill_form.py`

**Interfaces:**
- Consumes: CLI `grill_form.py init --theme <T>`（標準出力 1 行にセッションのパス）、`render --session-dir <D> --intake [--input <JSON>]`（標準出力 1 行に HTML のパス）。
- 既存のヘルパー `intake_data(html: str) -> dict`（`tests/test_grill_form.py`）を使う。使えない形のときは、既存のテストの HTML 読み取りに合わせる。

- [ ] **Step 1: 失敗しうるテストを書く**

関数名: `test_空白と日本語を含むパスで実コマンドのinitとrenderが通る(tmp_path)`。

- `subprocess.run([sys.executable, str(SCRIPT), ...], cwd=work, env=env, capture_output=True, text=True, encoding="utf-8")` で実コマンドを起動する（`SCRIPT` は `ROOT / "plugins" / "grill-form" / "scripts" / "grill_form.py"`）。
- `work = tmp_path / "作業 フォルダ"`（作成する）。`env` は `os.environ` のコピーに、`TEMP`・`TMP` を `tmp_path / "一時 temp"`（作成する）にして、`PYTHONUTF8=1` を足す。
- `intake = work / "入力 intake.json"` に `{"request": "依頼 本文"}` を UTF-8 で書く。
- 検査: (1) `init --theme demo` の終了コードが 0 で、出力のパスが `tmp_path / "一時 temp"` の下のフォルダ。(2) `render --session-dir <出力> --intake --input <intake>` の終了コードが 0 で、出力された HTML のパスが存在し、`intake_data` で取り出した `request` が `"依頼 本文"`。

- [ ] **Step 2: 実行して結果を見る**

Run: `PYTHONUTF8=1 python -m pytest tests/test_grill_form.py -k "実コマンド" -ra`
- PASS の場合: 本体は変更不要。H5 は確認済みとして、赤は出ないことを完了報告に書く。
- FAIL の場合: 失敗の出力を残し、Step 3 へ。

- [ ] **Step 3（FAIL の場合のみ）: 本体を直す**

失敗の原因を示す標準エラーに基づき、`grill_form.py` のパス処理だけを最小限直す。直す内容が 5 行を超える、または SKILL.md の手順に影響するときは、直す前にユーザーへ確認する。

- [ ] **Step 4: 青を確認する**

Run: `PYTHONUTF8=1 python -m pytest tests/test_grill_form.py -ra`
Expected: すべて PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_grill_form.py
git commit -m "test: 空白と日本語を含むパスで init と render が通ることを確かめる"
```

（本体を直したときは `plugins/grill-form/scripts/grill_form.py` も add し、件名を `fix:` にする。Co-Authored-By の行を付ける。）

---

### Task 3: 全体の検査と SPEC・計画の状態更新

**Files:**
- Modify: `docs/grill-form/plans/2026-11-07-plugin-rules-fix.md`（先頭の `status`）

- [ ] **Step 1: 全検査を実行する**

Run: `PYTHONUTF8=1 python -m pytest -ra`
Expected: 全件 PASS、スキップは既存の 1 件のみ

Run: `ruff check . && ruff format --check .`
Expected: エラーなし

Run: `claude plugin validate plugins/grill-form --strict`
Expected: `Validation passed`

Run: `git diff --check main`
Expected: 出力なし

- [ ] **Step 2: 受入条件を照合する**

SPEC の「受入条件」6 項目を 1 つずつ確かめる。変更したファイルが `README.md`・`tests/`・`docs/grill-form/`（と、H5 で落ちた場合の `grill_form.py`）だけであることは `git diff --stat main` で確かめる。

- [ ] **Step 3: 状態を更新する**
  - この計画の先頭を `status: 完了` にする（SPEC は計画の保存時に `完了` にして、`plan:` を書き済み）。

- [ ] **Step 4: Commit**

```bash
git add docs/grill-form
git commit -m "docs: plugin-rules.md 準拠の計画を完了にする"
```

（Co-Authored-By の行を付ける。push と PR は、ユーザーに確認してから行う。）
