# Librarian Windows Build Script
#
# Builds standalone Windows executables using PyInstaller.
# Produces LibrarianAPI.exe and LibrarianGUI.exe

param(
    [switch]$Clean,
    [switch]$SkipGUI
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== Librarian Windows Build ===" -ForegroundColor Cyan

# Change to repository root
Set-Location $RepoRoot

# Install build dependencies if needed
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller

# Build API executable
Write-Host "Building LibrarianAPI.exe..." -ForegroundColor Yellow
pyinstaller `
    --name LibrarianAPI `
    --onefile `
    --console `
    --additional-hooks-dir api/hooks `
    --distpath dist/windows `
    --workpath build/windows/api `
    --specpath build/windows `
    api/app.py

# Build GUI executable (if not skipped)
if (-not $SkipGUI) {
    Write-Host "Building LibrarianGUI.exe..." -ForegroundColor Yellow
    
    # Create GUI entry point
    $GuiEntry = @"
import sys
sys.path.insert(0, '.')
from gui.main import main
main()
"@
    $GuiEntry | Out-File -FilePath "gui_entry.py" -Encoding UTF8
    
    pyinstaller `
        --name LibrarianGUI `
        --onefile `
        --windowed `
        --additional-hooks-dir gui/hooks `
        --distpath dist/windows `
        --workpath build/windows/gui `
        --specpath build/windows `
        gui_entry.py
    
    Remove-Item "gui_entry.py" -ErrorAction SilentlyContinue
}

# Clean up build artifacts
if ($Clean) {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output: dist/windows/"
Get-ChildItem dist/windows -Filter "*.exe" | ForEach-Object {
    Write-Host "  - $($_.Name)"
}
