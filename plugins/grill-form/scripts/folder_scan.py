"""入力フォーム用に、作業フォルダのフォルダとファイルを調べる。"""

from __future__ import annotations

import stat
from pathlib import Path

MAX_DEPTH = 3  # 作業フォルダを 0、直下を 1 とした、含めるフォルダの深さの上限
MAX_ENTRIES = 200  # 1 フォルダで拾うフォルダとファイルの合計
MAX_TOTAL = 5000  # 全体の合計（巨大な作業フォルダで固まらないための上限）
EXTS = frozenset({".docx", ".pdf", ".pptx", ".xlsx", ".md", ".txt"})
SKIP_DIRS = frozenset({".git", "node_modules", "__pycache__"})

_LINK_TAGS = {
    getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", -1),
    getattr(stat, "IO_REPARSE_TAG_SYMLINK", -1),
}
_HIDDEN = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0) | getattr(
    stat, "FILE_ATTRIBUTE_SYSTEM", 0
)


def _skip(p: Path) -> bool:
    # 隠し・Office のロックファイル・リンク（ジャンクション含む）は出さない。
    # OneDrive のクラウドのファイルも再解析ポイントなので、タグでリンクだけを除く
    if p.name.startswith((".", "~$")) or p.name in SKIP_DIRS:
        return True
    try:
        st = p.lstat()
    except OSError:
        return True
    if stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) in _LINK_TAGS:
        return True
    return bool(getattr(st, "st_file_attributes", 0) & _HIDDEN)


def _node(path: Path, depth: int, budget: list[int]) -> dict:
    node = {
        "name": path.name,
        "path": str(path),
        "dirs": [],
        "files": [],
        "truncated": False,
    }
    try:
        entries = sorted(path.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return node  # 読めないフォルダは中身なしで出す
    kept = 0
    for p in entries:
        if _skip(p):
            continue
        is_dir = p.is_dir()
        if not is_dir and p.suffix.lower() not in EXTS:
            continue
        if is_dir and depth + 1 > MAX_DEPTH:
            continue
        if kept >= MAX_ENTRIES or budget[0] <= 0:
            node["truncated"] = True
            break
        kept += 1
        budget[0] -= 1
        if is_dir:
            node["dirs"].append(_node(p, depth + 1, budget))
        else:
            node["files"].append(p.name)
    return node


def scan(root: Path) -> dict:
    return _node(root, 0, [MAX_TOTAL])
