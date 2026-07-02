#!/usr/bin/env bash
set -euo pipefail

echo "=== Screencast Recorder: Prerequisite Check ==="

# Check for shot-scraper
if command -v shot-scraper &>/dev/null; then
    echo "[OK] shot-scraper found: $(shot-scraper --version 2>/dev/null || echo 'version unknown')"
else
    echo "[..] shot-scraper not found. Installing via uv..."
    if command -v uv &>/dev/null; then
        uv tool install shot-scraper
    elif command -v pip3 &>/dev/null; then
        pip3 install shot-scraper
    else
        echo "[FAIL] Neither uv nor pip3 found. Install Python first."
        exit 1
    fi
    echo "[OK] shot-scraper installed"
fi

# Check for Playwright browsers
if shot-scraper install --dry-run &>/dev/null 2>&1; then
    echo "[OK] Playwright browsers available"
else
    echo "[..] Installing Playwright browsers (chromium)..."
    shot-scraper install chromium 2>/dev/null || python3 -m playwright install chromium
    echo "[OK] Playwright browsers installed"
fi

# Check for ffmpeg (needed for --mp4 conversion)
if command -v ffmpeg &>/dev/null; then
    echo "[OK] ffmpeg found for MP4 conversion"
else
    echo "[WARN] ffmpeg not found. Recordings will be WebM only."
    echo "       Install via: brew install ffmpeg"
fi

# Verify output directory
OUTPUT_DIR="/Users/kidehen/Movies/screencasts"
if [ -d "$OUTPUT_DIR" ]; then
    echo "[OK] Output directory: $OUTPUT_DIR"
else
    echo "[..] Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

echo "=== Prerequisites: ready ==="
