"""檢查 production code 中可客觀判定的註解違規。"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = (
    "backend/api",
    "backend/core",
    "backend/models",
    "backend/services",
    "web/app",
    "web/components",
    "web/hooks",
    "web/lib",
)
SUFFIXES = {".py", ".ts", ".tsx"}
TEMPORAL_RE = re.compile(r"\b(?:Phase|roadmap)\s+\d|\b20\d{2}-\d{2}-\d{2}\b", re.I)
SECTION_RE = re.compile(
    r"^[#/\s*=\-]*(?:response\s+)?(?:schemas?|endpoints?|main|prompt)[#/\s*=\-]*$",
    re.I,
)
TODO_RE = re.compile(r"\b(?:TODO|FIXME)\b")
TRACKED_TODO_RE = re.compile(r"\b(?:TODO|FIXME)\(#\d+\):")
PY_SUPPRESSION_RE = re.compile(r"#\s*(?:type:\s*ignore(?:\[[^]]+\])?|noqa(?::\s*[A-Z0-9, ]+)?)")
TS_SUPPRESSION_RE = re.compile(r"eslint-disable(?:-next-line|-line)?\b")
REASON_RE = re.compile(r"\s(?:--|—)\s*\S")


@dataclass(frozen=True)
class Comment:
    line: int
    text: str


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    message: str


def _python_comments(source: str) -> list[Comment]:
    """用 tokenizer 取 Python comments，避免掃到字串與教材內容。"""
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return [
        Comment(token.start[0], token.string)
        for token in tokens
        if token.type == tokenize.COMMENT
    ]


def _typescript_comments(source: str) -> list[Comment]:
    """取 JS/TS comments；跳過一般字串與 template literal。"""
    comments: list[Comment] = []
    i = 0
    line = 1
    quote: str | None = None
    while i < len(source):
        char = source[i]
        next_char = source[i + 1] if i + 1 < len(source) else ""
        if quote:
            if char == "\\":
                i += 2
                continue
            if char == quote:
                quote = None
            if char == "\n":
                line += 1
            i += 1
            continue
        if char in "'\"`":
            quote = char
            i += 1
            continue
        if char == "/" and next_char == "/":
            end = source.find("\n", i)
            end = len(source) if end == -1 else end
            comments.append(Comment(line, source[i:end]))
            i = end
            continue
        if char == "/" and next_char == "*":
            end = source.find("*/", i + 2)
            end = len(source) - 2 if end == -1 else end
            text = source[i : end + 2]
            for offset, part in enumerate(text.splitlines()):
                comments.append(Comment(line + offset, part))
            line += text.count("\n")
            i = end + 2
            continue
        if char == "\n":
            line += 1
        i += 1
    return comments


def comments_for(path: Path) -> list[Comment]:
    """依副檔名擷取註解。"""
    source = path.read_text(encoding="utf-8")
    return _python_comments(source) if path.suffix == ".py" else _typescript_comments(source)


def check_file(path: Path) -> list[Violation]:
    """檢查單一檔案並回傳所有違規。"""
    violations: list[Violation] = []
    for comment in comments_for(path):
        text = comment.text.strip()
        if TEMPORAL_RE.search(text):
            violations.append(Violation(path, comment.line, "CP001", "禁止 Phase／roadmap／日期快照"))
        if SECTION_RE.fullmatch(text):
            violations.append(Violation(path, comment.line, "CP002", "區段標題只重述程式結構"))
        if TODO_RE.search(text) and not TRACKED_TODO_RE.search(text):
            violations.append(Violation(path, comment.line, "CP003", "TODO/FIXME 必須使用 TODO(#issue): 說明"))
        suppression = PY_SUPPRESSION_RE.search(text) or TS_SUPPRESSION_RE.search(text)
        if suppression and not REASON_RE.search(text):
            violations.append(Violation(path, comment.line, "CP004", "suppression 必須以 -- 或 — 補充理由"))
    return violations


def production_files(root: Path = ROOT) -> list[Path]:
    """列出受政策約束的 production source。"""
    return sorted(
        path
        for directory in SCAN_DIRS
        for path in (root / directory).rglob("*")
        if path.is_file() and path.suffix in SUFFIXES
    )


def main() -> int:
    """執行全庫檢查。"""
    violations = [item for path in production_files() for item in check_file(path)]
    for item in violations:
        print(f"{item.path.relative_to(ROOT)}:{item.line}: {item.code} {item.message}")
    if violations:
        print(f"Comment policy failed: {len(violations)} violation(s)")
        return 1
    print("Comment policy passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
