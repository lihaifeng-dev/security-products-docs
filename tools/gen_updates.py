#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate lists based on file CREATION time in Git (first commit).
- "Latest Updates" on index.md (recent N by creation time)
- "Archives" page grouped by Year/Month (by creation time)

Usage examples:
  python tools/gen_updates.py --docs docs --index docs/index.md --limit 15
  python tools/gen_updates.py --docs docs --archives docs/archives.md

Run at repo root. Requires `git` in PATH.
"""

import argparse
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

IGNORE_DIRS = {
    ".git",
    "assets",
    "images",
    "img",
    "static",
    "styles",
    "javascripts",
    "javascript",
    "overrides",
}
IGNORE_FILES = {"index.md"}
MD_EXTS = {".md", ".markdown"}

# 首页/归档标记
UPDATES_BEGIN = "<!-- BEGIN AUTO UPDATES -->"
UPDATES_END = "<!-- END AUTO UPDATES -->"
ARCHIVES_BEGIN = "<!-- BEGIN AUTO ARCHIVES -->"
ARCHIVES_END = "<!-- END AUTO ARCHIVES -->"


def run_git(repo_root: Path, args: List[str]) -> str:
    return subprocess.check_output(
        ["git"] + args,
        cwd=repo_root,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()


def git_creation_date(repo_root: Path, file_path: Path) -> Optional[str]:
    """
    Return ISO date (YYYY-MM-DD) of the FIRST commit that introduced the file.
    Uses --diff-filter=A and --follow to track renames. Fallback: None.
    """
    rel = str(file_path.relative_to(repo_root))
    # %cI -> strict ISO 8601, we slice to date part
    cmd = ["log", "--diff-filter=A", "--follow", "--format=%cI", "-1", "--", rel]
    try:
        out = run_git(repo_root, cmd)
        if out:
            return out[:10]
    except subprocess.CalledProcessError:
        pass
    return None


def extract_title(md_file: Path) -> str:
    try:
        text = md_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return md_file.stem

    # YAML front matter title
    m = re.search(r"^---\s*$(.*?)^---\s*$", text, flags=re.M | re.S)
    if m:
        fm = m.group(1)
        m2 = re.search(r"^\s*title\s*:\s*(.+?)\s*$", fm, flags=re.M)
        if m2:
            return m2.group(1).strip().strip('"').strip("'")

    # first ATX heading
    m = re.search(r"^\s*#\s+(.+?)\s*$", text, flags=re.M)
    if m:
        return m.group(1).strip()

    return md_file.stem


def collect_docs(repo_root: Path, docs_dir: Path) -> List[Dict]:
    items = []
    for p in docs_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in MD_EXTS:
            continue

        rel = p.relative_to(docs_dir)

        # 跳过首页/归档自身和忽略目录/文件
        if rel.name in IGNORE_FILES:
            continue
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if rel.as_posix().lower() in {"index.md"}:
            continue

        # archives.md 本身可被计入或跳过；这里默认跳过
        if rel.as_posix().lower() in {"archives.md"}:
            continue

        created = git_creation_date(repo_root, p) or "1970-01-01"
        items.append(
            {
                "path": p,
                "rel": rel,  # path relative to docs/
                "date": created,  # creation date
                "title": extract_title(p),
            }
        )
    # 按创建时间降序（最近创建在前）
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def build_updates_markdown(items: List[Dict], limit: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    out = [f"_Generated on {today} • Ordered by creation time_", ""]
    for it in items[:limit]:
        url = it["rel"].with_suffix("").as_posix() + "/"
        out.append(f"- {it['date']} — [{it['title']}]({url})")
    out.append("")
    return "\n".join(out)


def build_archives_markdown(items: List[Dict]) -> str:
    """
    Group by Year -> Month using creation date (YYYY, YYYY-MM).
    """
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for it in items:
        ym = it["date"][:7]  # YYYY-MM
        groups[ym].append(it)

    # 按年月降序
    yms = sorted(groups.keys(), reverse=True)

    out = []
    for ym in yms:
        out.append(f"## {ym}")
        for it in groups[ym]:
            url = it["rel"].with_suffix("").as_posix() + "/"
            out.append(f"- {it['date']} — [{it['title']}]({url})")
        out.append("")  # 每组后空行
    return "\n".join(out).rstrip() + "\n"


def replace_block(file_path: Path, begin_marker: str, end_marker: str, new_block: str) -> None:
    text = file_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"({re.escape(begin_marker)})(.*)({re.escape(end_marker)})", flags=re.S)
    if not pattern.search(text):
        raise RuntimeError(f"Markers {begin_marker} / {end_marker} not found in {file_path}")
    new_text = pattern.sub(rf"\1\n{new_block}\3", text)
    file_path.write_text(new_text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs", help="Docs directory")
    ap.add_argument("--index", default=None, help="Path to index.md (to update Latest Updates)")
    ap.add_argument("--archives", default=None, help="Path to archives.md (to update Archives)")
    ap.add_argument("--limit", type=int, default=20, help="How many items in Latest Updates")
    args = ap.parse_args()

    repo_root = Path.cwd()
    docs_dir = Path(args.docs).resolve()

    items = collect_docs(repo_root, docs_dir)

    if args.index:
        index_path = Path(args.index).resolve()
        md_updates = build_updates_markdown(items, args.limit)
        replace_block(index_path, UPDATES_BEGIN, UPDATES_END, md_updates)
        print(f"Updated Latest Updates in {index_path}")

    if args.archives:
        archives_path = Path(args.archives).resolve()
        md_archives = build_archives_markdown(items)
        replace_block(archives_path, ARCHIVES_BEGIN, ARCHIVES_END, md_archives)
        print(f"Updated Archives in {archives_path}")


if __name__ == "__main__":
    main()
