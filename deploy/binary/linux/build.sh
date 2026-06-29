#!/bin/bash
# Librarian Linux Build Script
#
# Builds standalone Linux executable using PyInstaller.
# Produces LibrarianAPI executable.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Librarian Linux Build ==="

cd "$REPO_ROOT"

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
mkdir -p dist/linux build/linux

# Build API executable
echo "Building LibrarianAPI..."
pyinstaller \
    --name LibrarianAPI \
    --onefile \
    --console \
    --additional-hooks-dir api/hooks \
    --distpath dist/linux \
    --workpath build/linux/api \
    --specpath build/linux \
    api/app.py

echo ""
echo "=== Build Complete ==="
echo "Output: dist/linux/"
ls -la dist/linux/

echo ""
echo "Run with: ./dist/linux/LibrarianAPI"
