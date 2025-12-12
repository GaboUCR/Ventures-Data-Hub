#!/usr/bin/env python3
"""
Collect all React frontend code in a project into a single file.

- Walks the directory tree starting at the directory containing this script.
- Ignores common junk dirs (node_modules, build, dist, .git, etc.).
- Skips .env and similar environment files.
- Includes typical React-related code files (see ALLOWED_EXTENSIONS).

Edit OUTPUT_FILENAME below to change the output name.
"""

import os
from pathlib import Path

# --- CONFIG ---
OUTPUT_FILENAME = "frontend_code_dump.txt"  # <-- change to any name you want

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
    # NOTE: ".env.example" is NOT an extension; handle via IGNORE/allowlist by filename if desired.
}


def is_ignored_file(file_path: Path) -> bool:
    """Return True if this file should be ignored."""
    name = file_path.name

    # Skip locks/envs and this script itself
    if name in IGNORE_FILE_NAMES or name == Path(__file__).name:
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

    # Allow files with no extension? (usually none in React projects; keep them out by default)
    if not file_path.suffix:
        return True

    # Only include allowed extensions
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
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
                if d not in IGNORE_DIRS and not d.startswith(".")  # skip hidden dirs
            ]

            for filename in sorted(filenames):
                file_path = Path(dirpath) / filename

                # Skip the output file itself if it's under root_dir
                if file_path.resolve() == output_file:
                    continue

                if is_ignored_file(file_path):
                    continue

                rel_path = file_path.resolve().relative_to(root_dir)

                out.write(f"\n\n// ===== FILE: {rel_path} =====\n\n")

                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                out.write(content)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    output_file = root_dir / OUTPUT_FILENAME

    print(f"Collecting frontend code from: {root_dir}")
    print(f"Writing combined code to: {output_file}")

    collect_code(root_dir, output_file)

    print("Done.")


if __name__ == "__main__":
    main()
