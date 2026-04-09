#!/usr/bin/env python3
"""
Recursively rename all files and folders in a directory,
removing spaces, hyphens, and single quotes.
Usage: python unspacer.py [folder_path]
       If no folder path is given, the current directory is used.
"""

import os
import sys


def rename_spaces(folder_path):
    folder = os.path.abspath(folder_path)

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    renamed, failed = [], []

    # Walk bottom-up so folders are renamed after their contents
    for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
        entries = filenames + dirnames

        for name in entries:
            if " " not in name and "-" not in name and "'" not in name:
                continue

            old_path = os.path.join(dirpath, name)
            new_name = name.replace(" ", "").replace("-", "").replace("'", "")
            new_path = os.path.join(dirpath, new_name)

            try:
                os.rename(old_path, new_path)
                rel = os.path.relpath(new_path, folder)
                print(f"  ✓ '{name}'  →  '{new_name}'")
                renamed.append(rel)
            except Exception as e:
                print(f"  ✗ Failed to rename '{name}': {e}")
                failed.append(name)

    print("\n" + "─" * 40)
    print(f"Done. {len(renamed)} renamed, {len(failed)} failed.")
    if failed:
        print("Failed:", ", ".join(failed))


if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    rename_spaces(folder_path)