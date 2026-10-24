"""grill_form.py のパス決定・cleanup・入力フォームを検査する。"""

import datetime
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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
        ".files",
        "ダウンロード",
    ],
)
def test_入力フォームにファイル選択欄の名残がない(gone, tmp_path, monkeypatch, capsys):
    assert gone not in render_intake(monkeypatch, tmp_path, capsys)


def test_入力フォームの回答はファイルパス節だけを持つ(tmp_path, monkeypatch, capsys):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "## ファイルパス" in html
    assert "\\n\\n## ファイル\\n" not in html
    assert "依頼文かファイルパスのどちらかを入力してください。" in html


def test_入力フォームに保存先欄があり回答の節を持つ(tmp_path, monkeypatch, capsys):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "保存先（親フォルダ）" in html
    assert "\\n## 保存先\\n" in html


def test_入力フォームの保存先にダイアログで選ぶチェックがある(
    tmp_path, monkeypatch, capsys
):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "ダイアログで選ぶ" in html
    assert "Claude がフォルダ選択ダイアログを開きます" in html


def test_pick_dirは選んだフォルダのパスを出力する(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(grill_form, "ask_directory", lambda initial: str(tmp_path))
    assert run(monkeypatch, "pick-dir") == 0
    assert capsys.readouterr().out.strip() == str(tmp_path)


def test_pick_dirは取り消しで終了コード1になり何も出力しない(monkeypatch, capsys):
    monkeypatch.setattr(grill_form, "ask_directory", lambda initial: "")
    assert run(monkeypatch, "pick-dir") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "取り消" in captured.err


def test_pick_dirはダイアログが使えないとき終了コード3になる(monkeypatch, capsys):
    def unavailable(initial):
        raise ImportError("No module named 'tkinter'")

    monkeypatch.setattr(grill_form, "ask_directory", unavailable)
    assert run(monkeypatch, "pick-dir") == 3
    assert "ダイアログ" in capsys.readouterr().err


def test_pick_dirは作業フォルダを初期位置にする(workdir, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(
        grill_form,
        "ask_directory",
        lambda initial: seen.append(initial) or str(initial),
    )
    run(monkeypatch, "pick-dir")
    assert seen == [workdir]


def test_入力フォームのファイルパスにもダイアログで選ぶチェックがある(
    tmp_path, monkeypatch, capsys
):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "Claude がファイルを選ぶダイアログを開きます" in html


def test_pick_fileは選んだファイルを1行ずつ出力する(tmp_path, monkeypatch, capsys):
    a, b = tmp_path / "a.pdf", tmp_path / "b c.xlsx"
    monkeypatch.setattr(grill_form, "ask_files", lambda initial: (str(a), str(b)))
    assert run(monkeypatch, "pick-file") == 0
    assert capsys.readouterr().out.splitlines() == [str(a), str(b)]


def test_pick_fileは取り消しで終了コード1になり何も出力しない(monkeypatch, capsys):
    monkeypatch.setattr(grill_form, "ask_files", lambda initial: ())
    assert run(monkeypatch, "pick-file") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "取り消" in captured.err


def test_pick_fileはダイアログが使えないとき終了コード3になる(monkeypatch, capsys):
    def unavailable(initial):
        raise RuntimeError("no display")

    monkeypatch.setattr(grill_form, "ask_files", unavailable)
    assert run(monkeypatch, "pick-file") == 3
    assert "ダイアログ" in capsys.readouterr().err


def test_pick_fileは作業フォルダを初期位置にする(workdir, monkeypatch):
    seen = []
    monkeypatch.setattr(
        grill_form, "ask_files", lambda initial: seen.append(initial) or ("x",)
    )
    run(monkeypatch, "pick-file")
    assert seen == [workdir]


def test_入力フォームの保存先にフォルダを選ぶボタンがある(
    tmp_path, monkeypatch, capsys
):
    html = render_intake(monkeypatch, tmp_path, capsys)
    assert "showDirectoryPicker" in html
    assert "作業フォルダ直下のフォルダだけ" in html


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
