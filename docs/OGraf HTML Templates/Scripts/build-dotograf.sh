#!/bin/bash
# Build individual dotOgraf (.ograf) files from example templates.
#
# A .ograf file is a ZIP archive containing a single self-contained template.
# MIME type: application/zip+ograf
#
# Usage:
#   ./build-dotograf.sh [source_dir] [output_dir]
#
# Defaults:
#   source_dir = ../Examples
#   output_dir = ../dist
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${1:-$SCRIPT_DIR/../Examples}"
OUTPUT_DIR="${2:-$SCRIPT_DIR/../Prebuilt}"

echo "Building dotOgraf (.ograf) files..."
echo "  Source: $SOURCE_DIR"
echo "  Output: $OUTPUT_DIR"

mkdir -p "$OUTPUT_DIR"

# Process each subdirectory containing an .ograf.json manifest
for manifest in "$SOURCE_DIR"/*/*.ograf.json; do
    [ -f "$manifest" ] || continue

    graphic_dir="$(dirname "$manifest")"
    graphic_name="$(basename "$graphic_dir")"

    echo "  Packaging: $graphic_name"

    # Create .ograf (ZIP archive) containing all files in the graphic directory
    cd "$graphic_dir"
    zip -r "$OUTPUT_DIR/${graphic_name}.ograf" . \
        -x '*.DS_Store' -x '__MACOSX/*'
    cd - > /dev/null

    echo "    Created: $OUTPUT_DIR/${graphic_name}.ograf"
done

echo ""
echo "Done! Output in: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/*.ograf 2>/dev/null || echo "  (no .ograf files created)"
