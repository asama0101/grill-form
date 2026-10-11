"""roundtable スキル用のスクリプト。

サブコマンド:
  init   --theme T [--parent P]  一時セッションフォルダ（OS の一時フォルダ配下）を作り、次の2行を出力する。
                              1行目: 一時セッションのパス（HTML・回答・質問 JSON を置く）
                              2行目: SPEC の保存先 <親>/<日時>_roundtable_<テーマ>/spec.md（承認時に書く）
                              （親フォルダの決め方: --parent > 環境変数 ROUNDTABLE_DIR > docs。
                               相対パスはカレントフォルダから解決する）
                              作成時に、3 日より古い一時セッションを削除する
  render --session-dir D --round N [--final] --input J.json
                              質問 JSON から round-N.html を生成し、パスを出力する。
                              --final のときは N を最終確認の版番号とし、final-N.html を生成する
                              （修正のたびに版を上げ、前の版を上書きしない）
  cleanup --session-dir D --spec S [--yes]
                              一時セッション D を削除対象として表示する。--yes を付けたときだけ削除する。
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
import sys
import tempfile
import time
from pathlib import Path

ENV_DIR = "ROUNDTABLE_DIR"
DEFAULT_DIR = "docs"
TEMP_ROOT_NAME = "roundtable"
KEEP_DAYS = 3
TEMPLATE = Path(__file__).with_name("roundtable_template.html")
INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def session_root(parent) -> Path:
    root = parent or os.environ.get(ENV_DIR) or DEFAULT_DIR
    return Path(root).expanduser().resolve()


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
    spec = session_root(args.parent) / f"{stamp}_roundtable_{theme}" / "spec.md"
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
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    payload["session"] = d.name
    payload["round"] = args.round
    payload["mode"] = "final" if args.final else "round"
    if not payload.get("title"):
        payload["title"] = f"最終確認（第{args.round}版）" if args.final else f"ラウンド {args.round}"
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", embed(payload))
    out = d / (f"final-{args.round}.html" if args.final else f"round-{args.round}.html")
    out.write_text(html, encoding="utf-8")
    print(out)
    return 0


def cmd_cleanup(args) -> int:
    d = Path(args.session_dir).resolve()
    # 一時セッション以外（プロジェクト内など）は消さない
    if d.parent != temp_root():
        print(f"{d} は roundtable の一時セッションではないため何もしません。", file=sys.stderr)
        return 1
    if not Path(args.spec).exists():
        print("spec.md がないため何もしません（承認前は削除しません）。", file=sys.stderr)
        return 1
    if not d.is_dir():
        print("削除対象はありません。")
        return 0
    print(f"削除対象{'' if args.yes else '（--yes で削除）'}: {d}")
    if args.yes:
        shutil.rmtree(d)
        print("削除しました。残り: spec.md")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--theme", required=True)
    p.add_argument("--parent", help=f"SPEC を保存する親フォルダ（既定: 環境変数 {ENV_DIR}、なければ {DEFAULT_DIR}）")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("render")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--final", action="store_true")
    p.add_argument("--input", required=True)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("cleanup")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--spec", required=True, help="承認済み SPEC のパス（init の2行目）")
    p.add_argument("--yes", action="store_true", help="一覧だけでなく実際に削除する")
    p.set_defaults(fn=cmd_cleanup)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
