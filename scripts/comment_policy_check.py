"""檢查 production code 中可客觀判定的註解違規。"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("backend", "web", "runner", "scripts")
SUFFIXES = {".py", ".ts", ".tsx"}
IGNORED_PARTS = {".next", ".venv", "__pycache__", "node_modules"}
TEMPORAL_RE = re.compile(r"\b(?:Phase|roadmap)\s+\d", re.I)
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
    is_docstring: bool = False


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    message: str


def _python_comments(source: str) -> list[Comment]:
    """取 Python comments 與 docstrings，避開一般字串內教材內容。"""
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    comments = [
        Comment(token.start[0], token.string)
        for token in tokens
        if token.type == tokenize.COMMENT
    ]
    for node in ast.walk(ast.parse(source)):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            comments.extend(
                Comment(value.lineno + offset, line, is_docstring=True)
                for offset, line in enumerate(value.value.splitlines())
            )
    return comments


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
    migration_history = "alembic" in path.parts and "versions" in path.parts
    for comment in comments_for(path):
        text = comment.text.strip()
        if not migration_history and TEMPORAL_RE.search(text):
            violations.append(Violation(path, comment.line, "CP001", "禁止 Phase／Roadmap 快照"))
        if SECTION_RE.fullmatch(text):
            violations.append(Violation(path, comment.line, "CP002", "區段標題只重述程式結構"))
        if not comment.is_docstring and TODO_RE.search(text) and not TRACKED_TODO_RE.search(text):
            violations.append(Violation(path, comment.line, "CP003", "TODO/FIXME 必須使用 TODO(#issue): 說明"))
        suppression = not comment.is_docstring and (
            PY_SUPPRESSION_RE.search(text) or TS_SUPPRESSION_RE.search(text)
        )
        if suppression and not REASON_RE.search(text):
            violations.append(Violation(path, comment.line, "CP004", "suppression 必須以 -- 或 — 補充理由"))
    return violations


def production_files(root: Path = ROOT) -> list[Path]:
    """列出受政策約束的 production source。"""
    return sorted(
        path
        for directory in SCAN_DIRS
        for path in (root / directory).rglob("*")
        if path.is_file()
        and path.suffix in SUFFIXES
        and not IGNORED_PARTS.intersection(path.parts)
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
