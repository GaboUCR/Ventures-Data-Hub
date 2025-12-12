#!/usr/bin/env python3
"""
Collect all React frontend code in a project into a single file.

Usage:
    python collect_frontend_code.py /path/to/frontend output_frontend.txt

- Walks the directory tree starting at the given root.
- Ignores common junk dirs (node_modules, build, dist, .git, etc.).
- Skips .env and similar environment files.
- Includes typical React-related code files:
  .js, .jsx, .ts, .tsx, .json, .css, .scss, .sass, .html, .md, .tsx, .cjs, .mjs

Adjust ALLOWED_EXTENSIONS if needed.
"""

import os
import argparse
from pathlib import Path

# Directories we don't want to descend into
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".vscode",
    ".idea",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".next",
    ".turbo",
    ".parcel-cache",
    ".cache",
    ".env",      # in case somebody has it as a dir
}

# File names we want to skip entirely
IGNORE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "yarn.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
}

# File extensions we consider "frontend code" by default
ALLOWED_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".json",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
    ".md",
    ".mdx",
    ".toml",
    ".yaml",
    ".yml",
    ".env.example",
}


def is_ignored_file(file_path: Path) -> bool:
    """Return True if this file should be ignored."""
    name = file_path.name

    if name in IGNORE_FILE_NAMES:
        return True

    # Obvious binary / assets to skip
    binary_like_exts = {
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
        ".webp", ".avif",
        ".mp4", ".mp3", ".ogg", ".wav",
        ".woff", ".woff2", ".ttf", ".eot",
        ".pdf", ".zip", ".tar", ".gz", ".rar",
    }
    if file_path.suffix.lower() in binary_like_exts:
        return True

    # Only include allowed extensions; if it has an extension and it's not in the list, skip
    if file_path.suffix and file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return True

    return False


def collect_code(root_dir: Path, output_file: Path) -> None:
    root_dir = root_dir.resolve()
    output_file = output_file.resolve()

    with output_file.open("w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # prevent walking into ignored dirs
            dirnames[:] = [
                d for d in dirnames
                if d not in IGNORE_DIRS and not d.startswith(".")  # also skip hidden dirs
            ]

            for filename in sorted(filenames):
                file_path = Path(dirpath) / filename

                # Skip the output file itself if it's under root_dir
                if file_path == output_file:
                    continue

                if is_ignored_file(file_path):
                    continue

                rel_path = file_path.relative_to(root_dir)

                header = f"\n\n// ===== FILE: {rel_path} =====\n\n"
                out.write(header)

                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                out.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect all React frontend code in a codebase into a single file."
    )
    parser.add_argument(
        "root",
        help="Root directory of the frontend (e.g., . for current directory)",
    )
    parser.add_argument(
        "output",
        help="Output file path (e.g., ./frontend_code_dump.txt)",
    )
    args = parser.parse_args()

    root_dir = Path(args.root)
    output_file = Path(args.output)

    if not root_dir.is_dir():
        raise SystemExit(f"Root directory does not exist or is not a directory: {root_dir}")

    print(f"Collecting frontend code from: {root_dir}")
    print(f"Writing combined code to: {output_file}")

    collect_code(root_dir, output_file)

    print("Done.")


if __name__ == "__main__":
    main()
