"""roundtable スキル用のスクリプト。

サブコマンド:
  init   --theme T [--parent P]  セッションフォルダを作り、パスを1行で出力する
                              （親フォルダの決め方: --parent > 環境変数 ROUNDTABLE_DIR > カレントフォルダ。
                               相対パスはカレントフォルダから解決する）
  render --session-dir D --round N [--final] --input J.json
                              質問 JSON から round-N.html を生成し、パスを出力する。
                              --final のときは N を最終確認の版番号とし、final-N.html を生成する
                              （修正のたびに版を上げ、前の版を上書きしない）
  index  --session-dir D      フォルダ内の HTML と回答を並べた index.md を（再）生成する

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
import sys
from pathlib import Path

ENV_DIR = "ROUNDTABLE_DIR"
DEFAULT_DIR = "."
TEMPLATE = Path(__file__).with_name("roundtable_template.html")
INVALID = re.compile(r'[\\/:*?"<>|\s]+')


def session_root(parent) -> Path:
    root = parent or os.environ.get(ENV_DIR) or DEFAULT_DIR
    return Path(root).expanduser().resolve()


def cmd_init(args) -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    theme = INVALID.sub("-", args.theme).strip("-") or "untitled"
    d = session_root(args.parent) / f"{stamp}_roundtable_{theme}"
    d.mkdir(parents=True, exist_ok=True)
    print(d)
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


def numbered(d: Path, prefix: str) -> list:
    # <prefix>-N.html / <prefix>-N.answers.md の N を昇順で返す
    pat = re.compile(rf"{prefix}-(\d+)\.(?:html|answers\.md)$")
    return sorted({int(m.group(1)) for p in d.iterdir() if (m := pat.match(p.name))})


def links(d: Path, stem: str, html_label: str) -> str:
    parts = [f"[{label}]({name})" for label, name in ((html_label, f"{stem}.html"), ("回答", f"{stem}.answers.md"))
             if (d / name).exists()]
    return f"- {stem}: " + " / ".join(parts)


def cmd_index(args) -> int:
    d = Path(args.session_dir)
    rounds = numbered(d, "round")
    finals = numbered(d, "final")
    lines = [
        "---",
        "type: doc",
        f"status: {'approved' if (d / 'spec.md').exists() else 'draft'}",
        f"created: {datetime.date.today().isoformat()}",
        "---",
        f"# {d.name}",
        "",
        "## ラウンド",
    ]
    lines += [links(d, f"round-{n}", "質問") for n in rounds] or ["- （まだありません）"]
    lines += ["", "## 最終確認"]
    if (d / "spec.md").exists():
        lines.append("- [spec](spec.md)（承認済みの SPEC）")
    lines += [links(d, f"final-{n}", "SPEC 案") for n in finals]
    if (d / "final-summary.md").exists():
        lines.append("- [final-summary](final-summary.md)")
    (d / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(d / "index.md")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--theme", required=True)
    p.add_argument("--parent", help=f"セッションフォルダを作る親フォルダ（既定: 環境変数 {ENV_DIR}、なければカレントフォルダ）")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("render")
    p.add_argument("--session-dir", required=True)
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--final", action="store_true")
    p.add_argument("--input", required=True)
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("index")
    p.add_argument("--session-dir", required=True)
    p.set_defaults(fn=cmd_index)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
