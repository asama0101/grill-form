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


# 廃止した仕様の語。SKILL.md・README.md・grill_form.py のどれにも残さない。
REMOVED_TERMS = [
    "grill-specs",
    "request.md",
    "inputs/",
    "GRILL_FORM_DIR",
    "soffice",
    "pdftoppm",
    "ファイル選択",
]


def test_SKILLにspec_pathの手順がある(text):
    assert "spec-path" in text


def test_SKILLが存在しないパスの再入力を求める(text):
    assert "再入力" in text


@pytest.mark.parametrize("term", REMOVED_TERMS)
def test_SKILLに廃止した語が残っていない(text, term):
    assert term not in text


@pytest.mark.parametrize("term", REMOVED_TERMS)
def test_READMEとスクリプトに廃止した語が残っていない(term):
    for name in ("README.md", "grill_form.py"):
        body = (ROOT / name).read_text(encoding="utf-8")
        assert term not in body, name


def test_stageサブコマンドの記述がどこにも残っていない(text):
    for name in ("README.md", "grill_form.py"):
        body = (ROOT / name).read_text(encoding="utf-8")
        assert re.search(r"\bstage\b", body) is None, name
    assert re.search(r"\bstage\b", text) is None


def test_SKILLは保存先を入力フォームで受け取りRound0は3点のまま(text):
    assert "`## 保存先`" in text
    assert "次の3点を" in text
    assert "次の4点を" not in text


def test_SKILLにダイアログで選ぶ手順がある(text):
    assert "pick-dir" in text
    assert "ダイアログで選ぶ" in text


def test_SKILLにファイルをダイアログで選ぶ手順がある(text):
    assert "pick-file" in text


def test_SKILLは保存先のフォルダの存在を確認する(text):
    assert "存在するフォルダか確認" in text


def test_SKILLは保存先の確認を承認より前の入力フォームの手順で行う(text):
    assert text.index("存在するフォルダか確認") < text.index("\n10. ")


UPSTREAM_COMMIT = "95249b0b49782349740fd9b8c6ce32b4e59e497a"
MAX_LINE = 400


def body_lines(text: str) -> list:
    # frontmatter（先頭の --- から次の --- まで）を除いた本文の行
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, flags=re.DOTALL).splitlines()


def test_SKILLの本文は1行が長すぎない(text):
    too_long = [
        (i, len(line))
        for i, line in enumerate(body_lines(text), 1)
        if len(line) > MAX_LINE
    ]
    assert too_long == []


@pytest.mark.parametrize(
    "rule",
    [
        "黙って仮定したまま残さない",
        "同じラウンドで未決の質問に依存する質問は、そのラウンドに出さず、次のラウンドに回す",
        "「はい」で推奨案を受け入れられる文言",
    ],
)
def test_SKILLのルールに元のgrillingの要点がある(text, rule):
    assert rule in text


def test_出典の固定する版が元の最新の版である():
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert UPSTREAM_COMMIT in notices
