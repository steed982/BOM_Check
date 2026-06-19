#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="BOM Check"
APP_DIR="$ROOT_DIR/dist/${APP_NAME}.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
MODULE_CACHE_DIR="$ROOT_DIR/.build/module-cache"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR" "$MODULE_CACHE_DIR"
cp "$ROOT_DIR/mac_app/Info.plist" "$CONTENTS_DIR/Info.plist"

xcrun swiftc \
  -target arm64-apple-macosx13.0 \
  -module-cache-path "$MODULE_CACHE_DIR" \
  -parse-as-library \
  "$ROOT_DIR/mac_app/BOMCheckApp.swift" \
  -o "$MACOS_DIR/BOMCheck"

chmod +x "$MACOS_DIR/BOMCheck"
codesign --force --deep --sign - "$APP_DIR" >/dev/null

echo "$APP_DIR"
