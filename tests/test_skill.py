"""SKILL.md の形式を検査する（plugin-rules F1 の単体スキル分: 1・2・3・4）。"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"
# 単体スキルの SKILL.md は、このリポジトリの直下にある。
# そのため親ディレクトリ名ではなく、期待するスキル名と照合する。
EXPECTED_NAME = "grill-form"


@pytest.fixture(scope="module")
def text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    assert m, "SKILL.md の先頭に frontmatter がない"
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def test_frontmatterのnameがスキル名と一致する(text):
    assert parse_frontmatter(text)["name"] == EXPECTED_NAME


def test_ハードコードした絶対パスがない(text):
    # ドライブ文字付きのパス、または /Users/<名前>・/home/<名前>。
    # 「C:/.../」のような省略記法の例は対象外にする。
    pattern = r"(?<![A-Za-z])[A-Za-z]:[\/]+\w|/(?:Users|home)/\w"
    assert re.findall(pattern, text) == []


def test_CLAUDE_SKILL_DIR_が指すファイルが実在する(text):
    refs = re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([^\s\"'`)]+)", text)
    assert refs, "参照が 1 件もない（検査が空振りしている）"
    missing = [r for r in refs if not (ROOT / r).is_file()]
    assert missing == []


def test_相対リンクと地の文の相対パスがない(text):
    # Markdown リンクのうち、URL・アンカー以外のもの
    links = re.findall(r"\]\((?!https?://|mailto:|#)[^)]*\)", text)
    # ./ や ../ で始まるパス
    prose = re.findall(r"(?:^|[\s`(\"'])\.{1,2}/", text, re.MULTILINE)
    assert links == []
    assert prose == []
