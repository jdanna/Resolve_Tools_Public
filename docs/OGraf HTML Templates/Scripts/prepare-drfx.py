#!/usr/bin/env python3
"""Create a .drfx template bundle from OGraf example templates.

A .drfx file is a ZIP archive with Resolve's template directory structure:
  Edit/Titles/<CategoryName>/<template files>

Usage:
  python3 prepare-drfx.py [--source DIR] [--output FILE] [--category NAME]

Defaults:
  --source    ../Examples
  --output    ../dist/ograf-templates.drfx
  --category  OGraf
"""

import argparse
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Create a .drfx template bundle from OGraf templates."
    )
    script_dir = Path(__file__).parent
    parser.add_argument(
        "--source",
        type=Path,
        default=script_dir / ".." / "Examples",
        help="Source directory containing template subdirectories",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=script_dir / ".." / "Prebuilt" / "ograf-templates.drfx",
        help="Output .drfx file path",
    )
    parser.add_argument(
        "--category",
        default="OGraf",
        help="Category name (subdirectory under Edit/Titles/)",
    )
    args = parser.parse_args()

    source_dir = args.source.resolve()
    output_path = args.output.resolve()
    category = args.category

    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    staging_root = Path(tempfile.mkdtemp())
    try:
        staging_dir = staging_root / "Edit" / "Titles" / category
        staging_dir.mkdir(parents=True, exist_ok=True)

        template_count = 0
        for template_dir in sorted(source_dir.iterdir()):
            if not template_dir.is_dir() or template_dir.name.startswith("."):
                continue

            # Check for at least one .ograf.json manifest
            manifests = list(template_dir.glob("*.ograf.json"))
            if not manifests:
                print(f"  Skipping {template_dir.name} (no .ograf.json found)")
                continue

            # Copy all template files to staging
            for src_file in sorted(template_dir.iterdir()):
                if src_file.name.startswith("."):
                    continue
                dest = staging_dir / src_file.name
                shutil.copy2(src_file, dest)
                print(f"  {template_dir.name}/{src_file.name} -> {category}/{src_file.name}")

            template_count += 1

        if template_count == 0:
            print("No templates found. Nothing to package.")
            return

        # Create .drfx (ZIP archive)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(staging_root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for file in sorted(files):
                    if file.startswith("."):
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(staging_root)
                    zf.write(file_path, arcname)

        print(f"\nCreated: {output_path}")
        print(f"Templates: {template_count}")
        print(f"Category: Edit/Titles/{category}/")

    finally:
        shutil.rmtree(staging_root)


if __name__ == "__main__":
    main()
