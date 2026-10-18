"""grill-form スキル用のスクリプト。

サブコマンド:
  init   --theme T [--parent P]  一時セッションフォルダ（OS の一時フォルダ配下）を作り、次の2行を出力する。
                              1行目: 一時セッションのパス（HTML・回答・質問 JSON を置く）
                              2行目: SPEC の保存先 <親>/<日時>_<テーマ>/SPEC.md（承認時に書く）
                              （親フォルダの決め方: --parent > 環境変数 GRILL_FORM_DIR > grill-specs。
                               相対パスは git のルート（なければカレントフォルダ）から解決する）
                              作成時に、3 日より古い一時セッションを削除する
  render --session-dir D --round N [--final] --input J.json
                              質問 JSON から round-N.html を生成し、パスを出力する。
                              --final のときは N を最終確認の版番号とし、final-N.html を生成する
                              （修正のたびに版を上げ、前の版を上書きしない）
  render --session-dir D --intake [--input J.json]
                              入力フォーム（依頼文・ファイル・パス）intake.html を生成する。
                              J.json は {"title","intro","request"} で省略可（request は依頼文欄の初期入力）
  stage  --session-dir D --file SRC [--name N]
                              入力ファイル SRC を D/inputs/ に取り込む（承認時に SPEC と同じフォルダへ残る）。
                              --name は元のファイル名（SPEC.md・request.md と重なる名前や重複は自動で別名にする）
  cleanup --session-dir D --spec S [--yes]
                              一時セッション D を削除対象として表示する。--yes を付けたときだけ、
                              D/request.md と D/inputs/ の中身を SPEC（S）と同じフォルダへ移してから D を削除する。
                              SPEC（S）がなければ何もしない（承認前は消さない）

質問 JSON:
  {"title": "...", "intro": "...", "questions": [
     {"id": "Q1", "title": "...", "body": "...", "multi": false,
      "options": [{"key": "A", "label": "...", "desc": "..."}],
      "recommended": ["A"], "reason": "..."}]}
final の JSON:
  {"title": "...", "intro": "...", "summary": "（SPEC 案の本文）"}
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

__version__ = "1.0.0"
ENV_DIR = "GRILL_FORM_DIR"
DEFAULT_DIR = "grill-specs"
SPEC_NAME = "SPEC.md"
REQUEST_NAME = "request.md"
INPUTS_NAME = "inputs"
RESERVED = {SPEC_NAME, REQUEST_NAME}
TEMP_ROOT_NAME = "grill-form"
KEEP_DAYS = 3
TEMPLATE = Path(__file__).with_name("grill_form_template.html")
INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def base_dir() -> Path:
    # 相対パスの基準。git のルート、なければカレントフォルダ
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
        return Path(top)
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def session_root(parent) -> Path:
    root = Path(parent or os.environ.get(ENV_DIR) or DEFAULT_DIR).expanduser()
    return root if root.is_absolute() else (base_dir() / root).resolve()


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


def cmd_init(args) -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    theme = INVALID.sub("-", args.theme).strip("-") or "untitled"
    root = temp_root()
    prune_old(root)
    tmp = root / f"{stamp}_{theme}"
    tmp.mkdir(parents=True, exist_ok=True)
    spec = session_root(args.parent) / f"{stamp}_{theme}" / SPEC_NAME
    print(tmp)
    print(spec)
    return 0


def embed(data: dict) -> str:
    # <script> 内に埋め込むため、終了タグと行区切り文字を無害化する
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def cmd_render(args) -> int:
    d = Path(args.session_dir)
    d.mkdir(parents=True, exist_ok=True)
    if args.intake:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8")) if args.input else {}
        payload["mode"] = "intake"
        payload["round"] = 0
        payload.setdefault("title", "入力（依頼文・ファイル）")
        out = d / "intake.html"
    else:
        if args.round is None or not args.input:
            print("--round と --input が必要です（--intake を除く）。", file=sys.stderr)
            return 2
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        payload["round"] = args.round
        payload["mode"] = "final" if args.final else "round"
        if not payload.get("title"):
            payload["title"] = f"最終確認（第{args.round}版）" if args.final else f"ラウンド {args.round}"
        out = d / (f"final-{args.round}.html" if args.final else f"round-{args.round}.html")
    payload["session"] = d.name
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", embed(payload))
    out.write_text(html, encoding="utf-8")
    print(out)
    return 0


def unique_name(name: str, taken) -> str:
    # SPEC.md・request.md と重なる名前や、取り込み済みの名前と重複する名前を別名にする
    name = Path(name).name or "input"
    if name in RESERVED:
        name = f"input-{name}"
    stem, suffix = Path(name).stem, Path(name).suffix
    cand, n = name, 2
    while cand in taken:
        cand = f"{stem}-{n}{suffix}"
        n += 1
    return cand


def cmd_stage(args) -> int:
    d = Path(args.session_dir).resolve()
    if d.parent != temp_root() or not d.is_dir():
        print(f"{d} は grill-form の一時セッションではありません。", file=sys.stderr)
        return 1
    src = Path(args.file)
    if not src.is_file():
        print(f"ファイルがありません: {src}", file=sys.stderr)
        return 1
    dest_dir = d / INPUTS_NAME
    dest_dir.mkdir(exist_ok=True)
    name = unique_name(args.name or src.name, {p.name for p in dest_dir.iterdir()})
    shutil.copy2(src, dest_dir / name)
    print(name)
    return 0


def keep_inputs(d: Path, spec: Path) -> None:
    # 依頼文と入力ファイルを、SPEC と同じフォルダへ移す
    dest = spec.parent
    req = d / REQUEST_NAME
    if req.is_file():
        shutil.copy2(req, dest / REQUEST_NAME)
    src_dir = d / INPUTS_NAME
    if src_dir.is_dir():
        for f in sorted(src_dir.iterdir()):
            if f.is_file():
                shutil.copy2(f, dest / unique_name(f.name, {p.name for p in dest.iterdir()}))


def cmd_cleanup(args) -> int:
    d = Path(args.session_dir).resolve()
    # 一時セッション以外（プロジェクト内など）は消さない
    if d.parent != temp_root():
        print(f"{d} は grill-form の一時セッションではないため何もしません。", file=sys.stderr)
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
            keep_inputs(d, Path(args.spec))
            shutil.rmtree(d)
        except OSError as e:
            print(
                f"削除できませんでした: {e}\n"
                "シェルのカレントフォルダが一時セッション内にないか確認してください。"
                "SPEC は保存済みで、残った一時セッションは次回の init で古いものから自動削除されます。",
                file=sys.stderr,
            )
            return 1
        print("削除しました。SPEC と入力ファイルは残っています。")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"grill-form {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--theme", required=True)
    p.add_argument("--parent", help=f"SPEC を保存する親フォルダ（既定: 環境変数 {ENV_DIR}、なければ {DEFAULT_DIR}）")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("render")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--round", type=int)
    p.add_argument("--final", action="store_true")
    p.add_argument("--intake", action="store_true", help="入力フォーム intake.html を生成する")
    p.add_argument("--input")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("stage")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--file", required=True, help="取り込むファイル")
    p.add_argument("--name", help="元のファイル名（省略時は --file のファイル名）")
    p.set_defaults(fn=cmd_stage)

    p = sub.add_parser("cleanup")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--spec", required=True, help="承認済み SPEC のパス（init の2行目）")
    p.add_argument("--yes", action="store_true", help="一覧だけでなく実際に削除する")
    p.set_defaults(fn=cmd_cleanup)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
