#!/usr/bin/env python3
"""
Collect all Python code in a project into a single file.

Usage:
    python collect_code.py /path/to/project output.txt

- Walks the directory tree starting at the given root.
- Ignores common junk directories (venv, .git, __pycache__, etc.).
- Skips .env and similar environment files.
- By default only includes .py files (adjust ALLOWED_EXTENSIONS if needed).
"""

import os
import argparse
from pathlib import Path

# Directories we don't want to descend into
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".vscode",
    ".idea",
    "venv",
    ".venv",
    "env",
    ".env",       # often a dir in some setups, just in case
    "node_modules",
    "dist",
    "build",
    ".tox",
}

# File names we want to skip entirely
IGNORE_FILE_NAMES = {
    ".env",        # main env file
    ".env.local",
    ".env.development",
    ".env.production",
    ".DS_Store",
    "get_code.py"
}

# File extensions we consider "code" by default
ALLOWED_EXTENSIONS = {
    ".py",
    # If you later want more, you can add things like:
    # ".txt", ".md", ".json", ".yaml", ".yml", ".ini",
    # ".sh", ".cfg", ".toml",
}


def is_ignored_file(file_path: Path) -> bool:
    """Return True if this file should be ignored."""
    name = file_path.name

    # Skip exact env filenames
    if name in IGNORE_FILE_NAMES:
        return True

    # Skip obvious binary and non-code types (extend if needed)
    binary_like_exts = {
        ".pyc", ".pyo", ".pyd",
        ".so", ".dll", ".dylib",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".pdf", ".zip", ".tar", ".gz", ".xz", ".bz2",
        ".exe",
    }
    if file_path.suffix.lower() in binary_like_exts:
        return True

    # Only allow certain extensions
    if file_path.suffix and file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return True

    return False


def collect_code(root_dir: Path, output_file: Path) -> None:
    root_dir = root_dir.resolve()
    output_file = output_file.resolve()

    with output_file.open("w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Modify dirnames in-place to prevent walking into ignored dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in IGNORE_DIRS and not d.startswith(".")  # skip hidden dirs
            ]

            for filename in sorted(filenames):
                file_path = Path(dirpath) / filename

                # Skip output file itself if it's inside the tree
                if file_path == output_file:
                    continue

                if is_ignored_file(file_path):
                    continue

                rel_path = file_path.relative_to(root_dir)

                # Write a nice header for each file
                header = f"\n\n# ===== FILE: {rel_path} =====\n\n"
                out.write(header)

                # Read file content, being tolerant of encoding weirdness
                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Fallback: best-effort read ignoring errors
                    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                out.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect all Python code in a codebase into a single file."
    )
    parser.add_argument(
        "root",
        help="Root directory of the codebase (e.g., . for current directory)",
    )
    parser.add_argument(
        "output",
        help="Output file path (e.g., ./code_dump.txt)",
    )
    args = parser.parse_args()

    root_dir = Path(args.root)
    output_file = Path(args.output)

    if not root_dir.is_dir():
        raise SystemExit(f"Root directory does not exist or is not a directory: {root_dir}")

    print(f"Collecting code from: {root_dir}")
    print(f"Writing combined code to: {output_file}")

    collect_code(root_dir, output_file)

    print("Done.")


if __name__ == "__main__":
    main()
