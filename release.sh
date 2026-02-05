#!/bin/bash

# SnapText Release Automation Script
# Usage: ./release.sh <version>
# Example: ./release.sh 1.0.2

set -e

if [ -z "$1" ]; then
    echo "Please provide a version number."
    echo "Usage: ./release.sh <version>"
    exit 1
fi

VERSION=$1
echo "🚀 Preparing Release v$VERSION..."

# 1. Update Version in Files

# LocalOCR/main.py
sed -i '' "s/APP_VERSION = \".*\"/APP_VERSION = \"$VERSION\"/" LocalOCR/main.py

# SnapText.spec (CFBundleVersion & CFBundleShortVersionString)
sed -i '' "s/'CFBundleVersion': \".*\"/'CFBundleVersion': \"$VERSION\"/" SnapText.spec
sed -i '' "s/'CFBundleShortVersionString': \".*\"/'CFBundleShortVersionString': \"$VERSION\"/" SnapText.spec

# SnapText-Bob-Plugin/snaptext.bobplugin/info.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" SnapText-Bob-Plugin/snaptext.bobplugin/info.json

# appcast.json (Main App) - Just updating version, description needs manual edit usually but we set a placeholder
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" appcast.json

# SnapText-Bob-Plugin/appcast.json (Plugin)
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" SnapText-Bob-Plugin/appcast.json
sed -i '' "s/SnapText-Bob-Plugin_v.*.bobplugin.zip/SnapText-Bob-Plugin_v$VERSION.bobplugin.zip/" SnapText-Bob-Plugin/appcast.json

echo "✅ Updated version numbers to $VERSION"

# 2. Build App
echo "🔨 Building SnapText.app..."
python3 -m PyInstaller --clean --noconfirm SnapText.spec

# 3. Sign App
echo "✍️  Signing SnapText.app..."
codesign --force --deep -s - "dist/SnapText.app"

# 4. Package DMG
echo "📦 Creating DMG..."
./create_custom_dmg.sh "dist/SnapText.app" "release/SnapText_v$VERSION.dmg" "$VERSION"

# 5. Package Bob Plugin
echo "🧩 Zipping Bob Plugin..."
zip -r "release/SnapText-Bob-Plugin_v$VERSION.bobplugin.zip" SnapText-Bob-Plugin/snaptext.bobplugin

echo "🎉 Release v$VERSION Ready!"
echo "Files:"
echo "  - release/SnapText_v$VERSION.dmg"
echo "  - release/SnapText-Bob-Plugin_v$VERSION.bobplugin.zip"
