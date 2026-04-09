#!/usr/bin/env python3
"""
Rename asset files to match the pattern:
{botanicalName}_{assetID}_{assetDescriptor}_lod{N}

for FBX files, and:
{botanicalName}_{assetID}_{assetDescriptor}

for USDC files (without lod suffix).

Folder structure: {commonName}_{botanicalName}_{assetID}_FBX/
"""

import os
import sys
import re
from pathlib import Path


# Known spelling corrections for botanical names
SPELLING_CORRECTIONS = {
    "Sylverstris": "Sylvestris",  # CowParsley, etc.
    "Perrenne": "Perenne",         # PerennialRyegrass spelling variant
}


def extract_asset_info(folder_name):
    """
    Extract botanical name and asset ID from folder name.
    Expected format: {commonName}_{botanicalName}_{assetID}_FBX
    """
    if not folder_name.endswith("_FBX"):
        return None, None
    
    folder_name = folder_name[:-4]  # Remove _FBX
    parts = folder_name.rsplit("_", 1)  # Split from right to get assetID
    
    if len(parts) != 2:
        return None, None
    
    name_part, asset_id = parts
    
    # Find the botanical name - it's the last CamelCase word in the name_part
    # Split by underscore and find where CamelCase starts
    words = name_part.split("_")
    
    # The botanical name is typically the last word or last few words
    # It starts with an uppercase letter and contains no spaces
    botanical_name = None
    for i in range(len(words) - 1, -1, -1):
        if words[i] and words[i][0].isupper() and " " not in words[i]:
            botanical_name = "_".join(words[i:])
            break
    
    if botanical_name is None:
        botanical_name = words[-1] if words else None
    
    return botanical_name, asset_id


def apply_spelling_corrections(text):
    """Apply known spelling corrections to text."""
    for incorrect, correct in SPELLING_CORRECTIONS.items():
        text = text.replace(incorrect, correct)
    return text


def should_rename_file(file_name, botanical_name, asset_id):
    """
    Check if a file should be renamed.
    Returns (should_rename, new_name) tuple.
    """
    base_name, ext = os.path.splitext(file_name)
    
    if ext not in [".fbx", ".usdc", ".FBX", ".USDC"]:
        return False, file_name
    
    # Correct extension case
    ext = ext.lower()
    
    # Apply spelling corrections to the base name
    corrected_base = apply_spelling_corrections(base_name)
    
    # Files should match pattern: {botanicalName}_{assetID}_{descriptor}[_lod{N}]
    pattern = rf"^{re.escape(botanical_name)}_{re.escape(asset_id)}_"
    
    # Check if already correct
    if re.match(pattern, corrected_base) and base_name == corrected_base:
        return False, file_name
    
    # If there's a spelling correction needed
    if base_name != corrected_base:
        return True, corrected_base + ext
    
    # Check if file needs renaming due to wrong prefix
    if not re.match(pattern, base_name):
        # Extract descriptor parts after the first few components
        # Try to match and rename files that don't have the botanical name prefix
        parts = base_name.split("_")
        
        # Find descriptor part (usually after asset ID)
        descriptor_parts = []
        lod_part = None
        
        for part in parts:
            if part.startswith("lod") or re.match(r"lod\d+", part):
                lod_part = part
                break
            descriptor_parts.append(part)
        
        if descriptor_parts:
            descriptor = "_".join(descriptor_parts)
            if lod_part:
                new_name = f"{botanical_name}_{asset_id}_{descriptor}_{lod_part}{ext}"
            else:
                new_name = f"{botanical_name}_{asset_id}_{descriptor}{ext}"
            
            if new_name != file_name:
                return True, new_name
    
    return False, file_name


def process_assets(assets_folder, dry_run=True):
    """
    Process all asset folders and rename files as needed.
    
    Args:
        assets_folder: Path to the Graswald_Assets folder
        dry_run: If True, only report what would be changed (don't rename)
    """
    assets_path = Path(assets_folder)
    
    if not assets_path.is_dir():
        print(f"Error: '{assets_folder}' is not a valid directory.")
        sys.exit(1)
    
    # Find all _FBX folders
    fbx_folders = sorted([d for d in assets_path.iterdir() if d.is_dir() and d.name.endswith("_FBX")])
    
    if not fbx_folders:
        print(f"No _FBX folders found in {assets_folder}")
        sys.exit(1)
    
    total_renamed = 0
    total_corrections = 0
    renamed_files = []
    correction_files = []
    errors = []
    
    for fbx_folder in fbx_folders:
        botanical_name, asset_id = extract_asset_info(fbx_folder.name)
        
        if not botanical_name or not asset_id:
            print(f"⚠ Skipped {fbx_folder.name}: Could not extract asset info")
            continue
        
        # Apply spelling corrections to botanical name
        corrected_botanical = apply_spelling_corrections(botanical_name)
        
        print(f"\n📁 {fbx_folder.name}")
        print(f"   botanicalName: {botanical_name} → {corrected_botanical}")
        print(f"   assetID: {asset_id}")
        
        folder_renamed = 0
        folder_corrections = 0
        
        # Process all files in the folder
        for file_path in fbx_folder.iterdir():
            if file_path.is_file():
                should_rename, new_name = should_rename_file(
                    file_path.name, 
                    corrected_botanical, 
                    asset_id
                )
                
                if should_rename:
                    new_path = file_path.parent / new_name
                    
                    # Check if it's a spelling correction
                    is_correction = apply_spelling_corrections(file_path.name) == new_name
                    
                    status = "🔤" if is_correction else "📝"
                    print(f"   {status} {file_path.name} → {new_name}")
                    
                    if not dry_run:
                        try:
                            file_path.rename(new_path)
                        except Exception as e:
                            error_msg = f"Failed to rename {file_path.name}: {e}"
                            print(f"      ✗ {error_msg}")
                            errors.append(error_msg)
                            continue
                    
                    renamed_files.append((fbx_folder.name, file_path.name, new_name))
                    
                    if is_correction:
                        folder_corrections += 1
                        total_corrections += 1
                    else:
                        folder_renamed += 1
                        total_renamed += 1
        
        if folder_renamed == 0 and folder_corrections == 0:
            print(f"   ✓ All files correct")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files to be renamed (pattern): {total_renamed}")
    print(f"Files to be corrected (spelling): {total_corrections}")
    print(f"Total changes: {total_renamed + total_corrections}")
    
    if errors:
        print(f"\nErrors: {len(errors)}")
        for error in errors:
            print(f"  ✗ {error}")
    
    if dry_run:
        print("\n💾 DRY RUN - No files were changed.")
        print("Run with --execute to apply changes.")
    else:
        print("\n✓ Changes applied!")
    
    return total_renamed + total_corrections


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rename asset files to match the correct pattern"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Path to Graswald_Assets folder (default: current directory)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply changes (default is dry-run to preview changes)"
    )
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    process_assets(args.folder, dry_run=dry_run)
