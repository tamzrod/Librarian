#!/bin/bash
# Librarian macOS Build Script
#
# Builds macOS application bundle or standalone executable.
# Produces LibrarianAPI executable or .app bundle.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Librarian macOS Build ==="

cd "$REPO_ROOT"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    PLATFORM="macosx-11.0-arm64"
else
    PLATFORM="macosx-11.0-x86_64"
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller

# Create build directory
mkdir -p dist/macos build/macos

# Build API executable
echo "Building LibrarianAPI for $PLATFORM..."
pyinstaller \
    --name LibrarianAPI \
    --onefile \
    --console \
    --additional-hooks-dir api/hooks \
    --distpath dist/macos \
    --workpath build/macos/api \
    --specpath build/macos \
    api/app.py

echo ""
echo "=== Build Complete ==="
echo "Output: dist/macos/"
ls -la dist/macos/

echo ""
echo "Run with: ./dist/macos/LibrarianAPI"
