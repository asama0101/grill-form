"""grill_form.py のパス決定・cleanup・入力フォームを検査する。"""

import datetime
import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins" / "grill-form" / "scripts"))

import grill_form  # noqa: E402

TODAY = datetime.date(2026, 10, 24)


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    # 作業フォルダ（スクリプトのカレントフォルダ）
    d = tmp_path / "work dir 作業"
    d.mkdir()
    monkeypatch.chdir(d)
    return d


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    # OS の一時フォルダを tmp_path 配下に向ける
    t = tmp_path / "os-temp"
    t.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(t))
    return t


def run(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["grill_form.py", *argv])
    return grill_form.main()


def test_spec_pathは作業フォルダ直下にSPEC_テーマ_日付を返す(workdir):
    assert grill_form.spec_path("api-design", today=TODAY) == (
        workdir / "SPEC-api-design-2026-10-24.md"
    )


def test_spec_pathは既存ファイルがあれば連番を進める(workdir):
    (workdir / "SPEC-api-design-2026-10-24.md").write_text("1", encoding="utf-8")
    (workdir / "SPEC-api-design-2026-10-24-2.md").write_text("2", encoding="utf-8")
    assert grill_form.spec_path("api-design", today=TODAY) == (
        workdir / "SPEC-api-design-2026-10-24-3.md"
    )
    assert (workdir / "SPEC-api-design-2026-10-24.md").read_text("utf-8") == "1"


def test_spec_pathは記号だけのテーマをuntitledにする(workdir):
    assert grill_form.spec_path("///", today=TODAY).name == (
        "SPEC-untitled-2026-10-24.md"
    )


def test_spec_pathの相対parentは作業フォルダ基準になる(workdir):
    assert grill_form.spec_path("t", parent="out", today=TODAY) == (
        workdir / "out" / "SPEC-t-2026-10-24.md"
    )


def test_spec_pathの絶対parentはそのまま使う(workdir, tmp_path):
    other = tmp_path / "other"
    assert grill_form.spec_path("t", parent=str(other), today=TODAY) == (
        other / "SPEC-t-2026-10-24.md"
    )


def test_spec_pathのparentは先頭のチルダを展開する(workdir, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert grill_form.spec_path("t", parent="~/x", today=TODAY) == (
        tmp_path / "x" / "SPEC-t-2026-10-24.md"
    )


def test_spec_pathはファイルもフォルダも作らない(workdir):
    grill_form.spec_path("t", parent="out", today=TODAY)
    assert list(workdir.iterdir()) == []


def test_spec_pathサブコマンドは絶対パスを1行で出力する(workdir, monkeypatch, capsys):
    assert run(monkeypatch, "spec-path", "--theme", "demo") == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert Path(lines[0]).parent == workdir
    assert Path(lines[0]).name.startswith("SPEC-demo-")


def test_initは一時セッションのパスだけを1行で出力する(temp_home, monkeypatch, capsys):
    assert run(monkeypatch, "init", "--theme", "demo") == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert Path(lines[0]).is_dir()
    assert Path(lines[0]).parent == temp_home.resolve() / "grill-form"


def make_session(temp_home, monkeypatch, capsys):
    run(monkeypatch, "init", "--theme", "demo")
    return Path(capsys.readouterr().out.strip())


def test_cleanupはSPECがなければ何も消さない(temp_home, workdir, monkeypatch, capsys):
    d = make_session(temp_home, monkeypatch, capsys)
    code = run(
        monkeypatch,
        "cleanup",
        "--session-dir",
        str(d),
        "--spec",
        str(workdir / "none.md"),
        "--yes",
    )
    assert code == 1
    assert d.is_dir()


def test_cleanupは_yesなしでは消さない(temp_home, workdir, monkeypatch, capsys):
    d = make_session(temp_home, monkeypatch, capsys)
    spec = workdir / "SPEC-demo.md"
    spec.write_text("x", encoding="utf-8")
    code = run(monkeypatch, "cleanup", "--session-dir", str(d), "--spec", str(spec))
    assert code == 0
    assert d.is_dir()


def test_cleanupは_yesで一時セッションだけを消してSPECは残す(
    temp_home, workdir, monkeypatch, capsys
):
    d = make_session(temp_home, monkeypatch, capsys)
    spec = workdir / "SPEC-demo.md"
    spec.write_text("x", encoding="utf-8")
    code = run(
        monkeypatch, "cleanup", "--session-dir", str(d), "--spec", str(spec), "--yes"
    )
    assert code == 0
    assert not d.exists()
    assert spec.read_text("utf-8") == "x"
    assert sorted(p.name for p in workdir.iterdir()) == ["SPEC-demo.md"]


def test_cleanupは一時セッション以外を消さない(temp_home, workdir, monkeypatch):
    other = workdir / "other"
    other.mkdir()
    spec = workdir / "SPEC-demo.md"
    spec.write_text("x", encoding="utf-8")
    code = run(
        monkeypatch,
        "cleanup",
        "--session-dir",
        str(other),
        "--spec",
        str(spec),
        "--yes",
    )
    assert code == 1
    assert other.is_dir()


def render_intake(monkeypatch, tmp_path, capsys) -> str:
    run(monkeypatch, "render", "--session-dir", str(tmp_path / "s"), "--intake")
    return Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "gone",
    [
        "type = 'file'",
        "grill-in-",
        "downloadPicked",
        "ダウンロード",
    ],
)
def test_入力フォームにファイル選択欄の名残がない(gone, tmp_path, monkeypatch, capsys):
    assert gone not in render_intake(monkeypatch, tmp_path, capsys)


def test_入力フォームの回答は参考資料節と更新節を持つ(tmp_path, monkeypatch, capsys):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "## 参考資料" in html
    assert "## 更新" in html
    assert "## ファイルパス" not in html
    assert "依頼文か参考資料のどちらかを入力してください。" in html


@pytest.mark.parametrize(
    "present",
    [
        "フォルダを読み直す",
        "r.name = 'kind'",
        "依頼文のファイル",
        "Shift",
    ],
)
def test_入力フォームに新しい操作の部品がある(present, tmp_path, monkeypatch, capsys):
    assert present in render_intake(monkeypatch, tmp_path, capsys)


@pytest.mark.parametrize(
    "gone",
    ["ダイアログで選ぶ", "pick-file", "ファイルパス（1 行 1 つ）"],
)
def test_入力フォームに旧いファイルパス欄の名残がない(
    gone, tmp_path, monkeypatch, capsys
):
    assert gone not in render_intake(monkeypatch, tmp_path, capsys)


def test_テンプレートはinnerHTMLを使わない():
    text = (
        ROOT / "plugins" / "grill-form" / "scripts" / "grill_form_template.html"
    ).read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if "innerHTML" in ln]
    assert len(lines) == 1
    assert lines[0].strip().startswith("//")  # 「使わない」という注釈の 1 行だけ


def test_入力フォームに保存先欄があり回答の節を持つ(tmp_path, monkeypatch, capsys):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "保存先（親フォルダ）" in html
    assert "\\n## 保存先\\n" in html


def test_入力フォームの保存先は作業フォルダを初期値にする(
    workdir, tmp_path, monkeypatch, capsys
):
    html = render_intake(monkeypatch, tmp_path, capsys)
    start = html.index('<script id="data" type="application/json">') + len(
        '<script id="data" type="application/json">'
    )
    data = json.loads(html[start : html.index("</script>", start)])
    assert data["dest"] == str(workdir)


def test_入力フォームにフォルダを選ぶボタンはない(tmp_path, monkeypatch, capsys):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "フォルダを選ぶ" not in html
    assert "showDirectoryPicker" not in html


def test_入力フォームの保存先にダイアログで選ぶチェックはない(
    tmp_path, monkeypatch, capsys
):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "フォルダ選択ダイアログ" not in html


def test_pick_fileサブコマンドは廃止されている(monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, "pick-file")


def intake_data(html: str) -> dict:
    start = html.index('<script id="data" type="application/json">') + len(
        '<script id="data" type="application/json">'
    )
    return json.loads(html[start : html.index("</script>", start)])


def test_parse_intake_answersはテキストの依頼文を読む():
    md = (
        "---\nsession: s\nintake: 1\n---\n"
        "## 依頼文\n- 種別: テキスト\n計画を詰めたい\n2 行目\n\n"
        "## 参考資料\n- C:\\work dir\\資料\\a.pdf\n- D:\\外\\b.xlsx\n\n"
        "## 保存先\nC:\\work dir\n"
    )
    assert grill_form.parse_intake_answers(md) == {
        "refresh": False,
        "kind": "text",
        "request": "計画を詰めたい\n2 行目",
        "request_file": "",
        "paths": ["C:\\work dir\\資料\\a.pdf", "D:\\外\\b.xlsx"],
        "dest": "C:\\work dir",
    }


def test_parse_intake_answersはファイルの依頼文を引用符を外して読む():
    md = (
        "---\nsession: s\nintake: 1\n---\n"
        '## 依頼文\n- 種別: ファイル\n"C:\\work\\依頼書.docx"\n\n'
        "## 参考資料\n\n## 保存先\nC:\\work\n"
    )
    got = grill_form.parse_intake_answers(md)
    assert got["kind"] == "file"
    assert got["request_file"] == "C:\\work\\依頼書.docx"
    assert got["request"] == ""
    assert got["paths"] == []


def test_parse_intake_answersは更新の印を読む():
    md = (
        "---\nsession: s\nintake: 1\n---\n"
        "## 更新\n- 読み直し: はい\n\n## 保存先\nC:\\w\n"
    )
    got = grill_form.parse_intake_answers(md)
    assert got["refresh"] is True
    assert got["dest"] == "C:\\w"


def test_parse_intake_answersは節が欠けても既定値を返す():
    assert grill_form.parse_intake_answers("---\nintake: 1\n---\n") == {
        "refresh": False,
        "kind": "text",
        "request": "",
        "request_file": "",
        "paths": [],
        "dest": "",
    }


def test_render_intakeは作業フォルダのツリーを埋め込む(
    workdir, tmp_path, monkeypatch, capsys
):
    (workdir / "資料").mkdir()
    (workdir / "資料" / "a.pdf").write_text("x", encoding="utf-8")
    data = intake_data(render_intake(monkeypatch, tmp_path, capsys))
    assert data["cwd"] == str(workdir)
    assert data["tree"]["name"] == "work dir 作業"
    assert data["tree"]["dirs"][0]["name"] == "資料"
    assert data["tree"]["dirs"][0]["files"] == ["a.pdf"]
    assert data["kind"] == "text"


def test_render_intakeは回答から入力を復元する(workdir, tmp_path, monkeypatch, capsys):
    answers = tmp_path / "intake.answers.md"
    answers.write_text(
        "---\nsession: s\nintake: 1\n---\n## 更新\n- 読み直し: はい\n\n"
        "## 依頼文\n- 種別: ファイル\nD:\\外\\依頼書.docx\n\n"
        "## 参考資料\n- D:\\外\\x.pdf\n\n## 保存先\nD:\\外\\out\n",
        encoding="utf-8",
    )
    run(
        monkeypatch,
        "render",
        "--session-dir",
        str(tmp_path / "s"),
        "--intake",
        "--answers",
        str(answers),
    )
    html = Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")
    data = intake_data(html)
    assert data["kind"] == "file"
    assert data["request_file"] == "D:\\外\\依頼書.docx"
    assert data["paths"] == ["D:\\外\\x.pdf"]
    assert data["dest"] == "D:\\外\\out"


def test_parse_intake_answersは保留の依頼文から他方の入力を復元する():
    md = (
        "---\nintake: 1\n---\n## 更新\n- 読み直し: はい\n\n"
        "## 依頼文\n- 種別: ファイル\nC:\\w\\依頼書.docx\n\n"
        "## 保留の依頼文\n- 種別: テキスト\n書きかけの依頼文\n2 行目\n\n"
        "## 保存先\nC:\\w\n"
    )
    got = grill_form.parse_intake_answers(md)
    assert got["kind"] == "file"
    assert got["request_file"] == "C:\\w\\依頼書.docx"
    assert got["request"] == "書きかけの依頼文\n2 行目"


def test_parse_intake_answersは保留のファイルからも復元する():
    md = (
        "---\nintake: 1\n---\n## 依頼文\n- 種別: テキスト\n本文\n\n"
        "## 保留の依頼文\n- 種別: ファイル\nC:\\w\\x.docx\n"
    )
    got = grill_form.parse_intake_answers(md)
    assert got["kind"] == "text"
    assert got["request"] == "本文"
    assert got["request_file"] == "C:\\w\\x.docx"


def test_parse_intake_answersは依頼文の中の見出し風の行を本文として読む():
    md = (
        "---\nintake: 1\n---\n## 依頼文\n- 種別: テキスト\n"
        "前置き\n## 背景\n詳細\n\n## 保存先\nC:\\w\n"
    )
    got = grill_form.parse_intake_answers(md)
    assert got["request"] == "前置き\n## 背景\n詳細"
    assert got["dest"] == "C:\\w"


def test_render_intakeは空の回答で_inputの値を消さない(
    workdir, tmp_path, monkeypatch, capsys
):
    answers = tmp_path / "a.md"
    answers.write_text(
        "---\nintake: 1\n---\n## 依頼文\n- 種別: テキスト\n\n## 保存先\n",
        encoding="utf-8",
    )
    j = tmp_path / "in.json"
    j.write_text(
        json.dumps({"request": "初期の依頼文", "dest": "D:\\out"}),
        encoding="utf-8",
    )
    run(
        monkeypatch,
        "render",
        "--session-dir",
        str(tmp_path / "s"),
        "--intake",
        "--input",
        str(j),
        "--answers",
        str(answers),
    )
    html = Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")
    data = intake_data(html)
    assert data["request"] == "初期の依頼文"
    assert data["dest"] == "D:\\out"
    assert "refresh" not in data


def test_テンプレートはゼロ幅スペースで依頼文を加工しない():
    text = (
        ROOT / "plugins" / "grill-form" / "scripts" / "grill_form_template.html"
    ).read_text(encoding="utf-8")
    assert "u200b" not in text.lower()
    assert "​" not in text


def test_入力フォームの描画はintroを表示する():
    text = (
        ROOT / "plugins" / "grill-form" / "scripts" / "grill_form_template.html"
    ).read_text(encoding="utf-8")
    body = text[text.index("function renderIntake") :]
    body = body[: body.index("function lines")]
    assert "data.intro" in body


def test_埋め込みはscript終了タグを無害化する():
    out = grill_form.embed({"tree": {"name": "a</script>b"}})
    assert "</script>" not in out
    assert "<\\/script>" in out


def render_round(monkeypatch, tmp_path, capsys) -> str:
    q = tmp_path / "q.json"
    q.write_text(
        '{"questions":[{"id":"Q1","title":"t","options":[{"key":"A","label":"a"}]}]}',
        encoding="utf-8",
    )
    run(
        monkeypatch,
        "render",
        "--session-dir",
        str(tmp_path / "s"),
        "--round",
        "1",
        "--input",
        str(q),
    )
    return Path(capsys.readouterr().out.strip()).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "present",
    ['id="side"', "いま答えている質問", "classList.toggle('active'", "advance("],
)
def test_質問画面に一覧と現在の質問の表示と自動で進む処理がある(
    present, tmp_path, monkeypatch, capsys
):
    assert present in render_round(monkeypatch, tmp_path, capsys)


def test_推奨の候補を左の線で示していない(tmp_path, monkeypatch, capsys):
    assert "inset 4px 0 0" not in render_round(monkeypatch, tmp_path, capsys)
    assert "border-left: 4px solid var(--rec)" not in render_round(
        monkeypatch, tmp_path, capsys
    )


def test_spec_pathは親が既存のファイルなら終了コード2で止まる(
    workdir, monkeypatch, capsys
):
    (workdir / "a.txt").write_text("x", encoding="utf-8")
    assert run(monkeypatch, "spec-path", "--theme", "t", "--parent", "a.txt") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "フォルダではありません" in captured.err


def test_spec_pathは存在しない親ならそのままパスを返す(workdir, monkeypatch, capsys):
    assert run(monkeypatch, "spec-path", "--theme", "t", "--parent", "new") == 0
    assert Path(capsys.readouterr().out.strip()).parent == workdir / "new"


def test_ツリーの切り捨て通知はフォルダだけに限らない文面にする():
    text = (
        ROOT / "plugins" / "grill-form" / "scripts" / "grill_form_template.html"
    ).read_text(encoding="utf-8")
    assert "一部のフォルダだけ" not in text
    assert (
        text.count("件数が多いため一部だけ表示しています。パス欄を使ってください。")
        == 2
    )
