"""grill-form スキル用のスクリプト。

サブコマンド:
  init   --theme T            一時セッションフォルダ（OS の一時フォルダ配下）を作り、
                              そのパスを1行で出力する
                              （HTML・回答・質問 JSON を置く）。
                              作成時に、3 日より古い一時セッションを削除する
  spec-path --theme T [--parent P]
                              SPEC の保存先 <親>/SPEC-<テーマ>-<日付>.md を
                              決めて出力する（ファイルは作らない）。
                              親は --parent、なければ作業フォルダ
                              （このスクリプトのカレントフォルダ）。
                              相対パスは作業フォルダから解決する。
                              同名のファイルがあれば末尾に連番を付ける
  pick-file                   OS のファイルを選ぶダイアログ（複数選択可）を開き、選んだ
                              ファイルのパスを1行ずつ出力する（初期位置は作業フォルダ）。
                              取り消しは終了コード 1、ダイアログを開けない
                              （tkinter がない・画面がない）ときは 3
  render --session-dir D --round N [--final] --input J.json
                              質問 JSON から round-N.html を生成し、パスを出力する。
                              --final のときは N を最終確認の版番号とし、
                              final-N.html を生成する
                              （修正のたびに版を上げ、前の版を上書きしない）
  render --session-dir D --intake [--input J.json]
                              入力フォーム（依頼文・ファイルパス）intake.html を
                              生成する。J.json は {"title","intro","request","dest"} で
                              省略可（request は依頼文欄の初期入力、dest は
                              保存先欄の初期値で、省略すると作業フォルダ）
  cleanup --session-dir D --spec S [--yes]
                              一時セッション D を削除対象として表示する。
                              --yes を付けたときだけ D を削除する。
                              SPEC（S）がなければ何もしない（承認前は消さない）

質問 JSON:
  {"title": "...", "intro": "...", "questions": [
     {"id": "Q1", "title": "...", "body": "...", "multi": false,
      "options": [{"key": "A", "label": "...", "desc": "..."}],
      "recommended": ["A"], "reason": "..."}]}
final の JSON:
  {"title": "...", "intro": "...", "summary": "（SPEC 案の本文）"}
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

__version__ = "1.0.0"
SPEC_PREFIX = "SPEC"
TEMP_ROOT_NAME = "grill-form"
KEEP_DAYS = 3
TEMPLATE = Path(__file__).with_name("grill_form_template.html")
INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def temp_root() -> Path:
    return Path(tempfile.gettempdir()).resolve() / TEMP_ROOT_NAME


def prune_old(root: Path) -> None:
    # 古い一時セッションを削除する（中断したセッションの掃除）
    limit = time.time() - KEEP_DAYS * 86400
    if not root.is_dir():
        return
    for d in root.iterdir():
        if d.is_dir() and d.stat().st_mtime < limit:
            shutil.rmtree(d, ignore_errors=True)


def normalize_theme(theme: str) -> str:
    return INVALID.sub("-", theme).strip("-") or "untitled"


def spec_path(
    theme: str,
    parent: str | None = None,
    today: datetime.date | None = None,
) -> Path:
    # 作業フォルダ基準で SPEC のパスを決める。既存のファイルは上書きしない
    base = Path(parent).expanduser() if parent else Path()
    base = (Path.cwd() / base).resolve() if not base.is_absolute() else base
    day = (today or datetime.date.today()).isoformat()
    stem = f"{SPEC_PREFIX}-{normalize_theme(theme)}-{day}"
    cand, n = base / f"{stem}.md", 2
    while cand.exists():
        cand = base / f"{stem}-{n}.md"
        n += 1
    return cand


def cmd_init(args) -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    root = temp_root()
    prune_old(root)
    tmp = root / f"{stamp}_{normalize_theme(args.theme)}"
    tmp.mkdir(parents=True, exist_ok=True)
    print(tmp)
    return 0


def cmd_spec_path(args) -> int:
    path = spec_path(args.theme, args.parent)
    if path.parent.exists() and not path.parent.is_dir():
        print(f"保存先の親がフォルダではありません: {path.parent}", file=sys.stderr)
        return 2
    print(path)
    return 0


def run_dialog(pick):
    # OS の選択ダイアログ（tkinter）を最前面で開き、pick(filedialog, root) の結果を返す
    import tkinter
    from tkinter import filedialog

    try:
        root = tkinter.Tk()
    except tkinter.TclError as e:
        raise RuntimeError(str(e)) from e
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return pick(filedialog, root)
    finally:
        root.destroy()


def ask_files(initial: Path) -> tuple:
    # 複数選択できる。取り消しは空のタプルを返す
    return tuple(
        run_dialog(
            lambda fd, root: fd.askopenfilenames(initialdir=str(initial), parent=root)
        )
    )


def cmd_pick_file(args) -> int:
    try:
        chosen = ask_files(Path.cwd())
    except (ImportError, RuntimeError) as e:
        print(f"ファイルを選ぶダイアログを開けません: {e}", file=sys.stderr)
        return 3
    if not chosen:
        print("ファイルの選択が取り消されました。", file=sys.stderr)
        return 1
    for f in chosen:
        print(Path(f))
    return 0


def embed(data: dict) -> str:
    # <script> 内に埋め込むため、終了タグと行区切り文字を無害化する
    text = json.dumps(data, ensure_ascii=False)
    return (
        text.replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def cmd_render(args) -> int:
    d = Path(args.session_dir)
    d.mkdir(parents=True, exist_ok=True)
    if args.intake:
        payload = (
            json.loads(Path(args.input).read_text(encoding="utf-8"))
            if args.input
            else {}
        )
        payload["mode"] = "intake"
        payload["round"] = 0
        payload.setdefault("dest", str(Path.cwd()))
        payload.setdefault("title", "入力（依頼文・ファイルパス）")
        out = d / "intake.html"
    else:
        if args.round is None or not args.input:
            print("--round と --input が必要です（--intake を除く）。", file=sys.stderr)
            return 2
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        payload["round"] = args.round
        payload["mode"] = "final" if args.final else "round"
        if not payload.get("title"):
            payload["title"] = (
                f"最終確認（第{args.round}版）"
                if args.final
                else f"ラウンド {args.round}"
            )
        out = d / (
            f"final-{args.round}.html" if args.final else f"round-{args.round}.html"
        )
    payload["session"] = d.name
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", embed(payload))
    out.write_text(html, encoding="utf-8")
    print(out)
    return 0


def cmd_cleanup(args) -> int:
    d = Path(args.session_dir).resolve()
    # 一時セッション以外（プロジェクト内など）は消さない
    if d.parent != temp_root():
        print(
            f"{d} は grill-form の一時セッションではないため何もしません。",
            file=sys.stderr,
        )
        return 1
    if not Path(args.spec).exists():
        print("SPEC がないため何もしません（承認前は削除しません）。", file=sys.stderr)
        return 1
    if not d.is_dir():
        print("削除対象はありません。")
        return 0
    print(f"削除対象{'' if args.yes else '（--yes で削除）'}: {d}")
    if args.yes:
        try:
            shutil.rmtree(d)
        except OSError as e:
            print(
                f"削除できませんでした: {e}\n"
                "シェルのカレントフォルダが一時セッション内にないか確認してください。"
                "SPEC は保存済みで、残った一時セッションは次回の init で"
                "古いものから自動削除されます。",
                file=sys.stderr,
            )
            return 1
        print("削除しました。SPEC は残っています。")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--version", action="version", version=f"grill-form {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--theme", required=True)
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("spec-path")
    p.add_argument("--theme", required=True)
    p.add_argument(
        "--parent",
        help="SPEC を保存する親フォルダ（既定: 作業フォルダ）",
    )
    p.set_defaults(fn=cmd_spec_path)

    p = sub.add_parser("pick-file")
    p.set_defaults(fn=cmd_pick_file)

    p = sub.add_parser("render")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--round", type=int)
    p.add_argument("--final", action="store_true")
    p.add_argument(
        "--intake", action="store_true", help="入力フォーム intake.html を生成する"
    )
    p.add_argument("--input")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("cleanup")
    p.add_argument("--session-dir", required=True)
    p.add_argument(
        "--spec", required=True, help="承認済み SPEC のパス（spec-path の出力）"
    )
    p.add_argument("--yes", action="store_true", help="一覧だけでなく実際に削除する")
    p.set_defaults(fn=cmd_cleanup)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
