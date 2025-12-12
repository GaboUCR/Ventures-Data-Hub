#!/usr/bin/env python3
"""
Collect all Python code in a project into a single file.

- Walks the directory tree starting at the directory containing this script.
- Ignores common junk directories (venv, .git, __pycache__, etc.).
- Skips .env and similar environment files.
- By default only includes .py files (adjust ALLOWED_EXTENSIONS if needed).

Edit OUTPUT_FILENAME below to change the output name.
"""

import os
from pathlib import Path

# --- CONFIG ---
OUTPUT_FILENAME = "code_dump.txt"  # <-- change to any name you want

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
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".DS_Store",
}

# File extensions we consider "code" by default
ALLOWED_EXTENSIONS = {
    ".py",
}

# --- LOGIC ---
def is_ignored_file(file_path: Path) -> bool:
    """Return True if this file should be ignored."""
    name = file_path.name

    # Skip exact env filenames and this script itself
    if name in IGNORE_FILE_NAMES or name == Path(__file__).name:
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
            # Prevent walking into ignored dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in IGNORE_DIRS and not d.startswith(".")
            ]

            for filename in sorted(filenames):
                file_path = Path(dirpath) / filename

                # Skip output file itself if it's inside the tree
                if file_path.resolve() == output_file:
                    continue

                if is_ignored_file(file_path):
                    continue

                rel_path = file_path.resolve().relative_to(root_dir)

                out.write(f"\n\n# ===== FILE: {rel_path} =====\n\n")

                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                out.write(content)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    output_file = root_dir / OUTPUT_FILENAME

    print(f"Collecting code from: {root_dir}")
    print(f"Writing combined code to: {output_file}")

    collect_code(root_dir, output_file)

    print("Done.")


if __name__ == "__main__":
    main()
