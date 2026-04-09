#!/usr/bin/env python3
"""
Unzip all .zip files in a folder and delete the originals.
Usage: python unzip_and_delete.py [folder_path]
       If no folder path is given, the current directory is used.
"""

import zipfile
import os
import sys


def unzip_and_delete(folder_path):
    folder = os.path.abspath(folder_path)

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    zip_files = [f for f in os.listdir(folder) if f.lower().endswith(".zip")]

    if not zip_files:
        print("No .zip files found in the folder.")
        return

    print(f"Found {len(zip_files)} zip file(s) in '{folder}'.\n")

    success, failed = [], []

    for zip_name in zip_files:
        zip_path = os.path.join(folder, zip_name)
        print(f"Processing: {zip_name}")

        try:
            extract_dir = os.path.join(folder, os.path.splitext(zip_name)[0])
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            os.remove(zip_path)
            print(f"  ✓ Extracted to '{os.path.basename(extract_dir)}/' and deleted.\n")
            success.append(zip_name)
        except zipfile.BadZipFile:
            print(f"  ✗ Skipped — not a valid zip file.\n")
            failed.append(zip_name)
        except Exception as e:
            print(f"  ✗ Failed — {e}\n")
            failed.append(zip_name)

    print("─" * 40)
    print(f"Done. {len(success)} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed files:", ", ".join(failed))


if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    unzip_and_delete(folder_path)