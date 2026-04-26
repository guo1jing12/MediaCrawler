#!/usr/bin/env python3
"""Install MediaCrawler agent integrations for local AI coding tools."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = REPO_ROOT / "agent-skills" / "mediacrawler"
CLAUDE_COMMAND_SOURCE = REPO_ROOT / ".claude" / "commands" / "mediacrawler-crawl.md"
CURSOR_RULE_SOURCE = REPO_ROOT / ".cursor" / "rules" / "mediacrawler.mdc"


def copy_file(src: Path, dst: Path, dry_run: bool) -> None:
    if src.resolve() == dst.resolve():
        print(f"already installed {dst}")
        return
    if dry_run:
        print(f"[dry-run] copy {src} -> {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"installed {dst}")


def copy_dir(src: Path, dst: Path, dry_run: bool) -> None:
    if src.resolve() == dst.resolve():
        print(f"already installed {dst}")
        return
    if dry_run:
        print(f"[dry-run] copytree {src} -> {dst}")
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    print(f"installed {dst}")


def install_project_files(dry_run: bool) -> None:
    copy_file(
        CLAUDE_COMMAND_SOURCE,
        REPO_ROOT / ".claude" / "commands" / "mediacrawler-crawl.md",
        dry_run,
    )
    copy_file(
        CURSOR_RULE_SOURCE,
        REPO_ROOT / ".cursor" / "rules" / "mediacrawler.mdc",
        dry_run,
    )


def install_openclaw(home: Path, dry_run: bool) -> None:
    # OpenClaw installations may use either global or workspace skill roots.
    copy_dir(SKILL_SOURCE, home / ".openclaw" / "skills" / "mediacrawler", dry_run)
    copy_dir(SKILL_SOURCE, home / ".openclaw" / "workspace" / "skills" / "mediacrawler", dry_run)


def install_claude_global(home: Path, dry_run: bool) -> None:
    copy_file(
        CLAUDE_COMMAND_SOURCE,
        home / ".claude" / "commands" / "mediacrawler-crawl.md",
        dry_run,
    )


def install_cursor_global(home: Path, dry_run: bool) -> None:
    copy_file(
        CURSOR_RULE_SOURCE,
        home / ".cursor" / "rules" / "mediacrawler.mdc",
        dry_run,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Install MediaCrawler agent integrations.")
    parser.add_argument(
        "--target",
        choices=["project", "openclaw", "claude", "cursor", "all"],
        default="project",
        help="Integration target to install.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Home directory used for global tool installations.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    args = parser.parse_args()

    if not SKILL_SOURCE.exists():
        raise SystemExit(f"Missing skill source: {SKILL_SOURCE}")

    if args.target in ("project", "all"):
        install_project_files(args.dry_run)
    if args.target in ("openclaw", "all"):
        install_openclaw(args.home, args.dry_run)
    if args.target in ("claude", "all"):
        install_claude_global(args.home, args.dry_run)
    if args.target in ("cursor", "all"):
        install_cursor_global(args.home, args.dry_run)


if __name__ == "__main__":
    main()
