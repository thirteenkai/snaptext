#!/bin/bash
# create_custom_dmg.sh
# Usage: ./create_custom_dmg.sh <app_path> <output_dmg_path>

APP_PATH="$1"
DMG_PATH="$2"
VOL_NAME="SnapText"
TEMP_DMG="temp.dmg"
STAGING_DIR="build/dmg_staging"

# 1. Clean up
rm -rf "$DMG_PATH" "$TEMP_DMG" "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
mkdir -p "$(dirname "$DMG_PATH")"

# 2. Prepare staging area
echo "Copying app to staging area..."
# Use ditto to preserve symlinks and metadata (crucial for App Bundles)
ditto "$APP_PATH" "$STAGING_DIR/$(basename "$APP_PATH")"
ln -s /Applications "$STAGING_DIR/Applications"

# 3. Create writable image
echo "Creating writable disk image..."
hdiutil create -srcfolder "$STAGING_DIR" -volname "$VOL_NAME" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW "$TEMP_DMG"

# 4. Mount image
echo "Mounting disk image..."
ATTACH_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG")
DEVICE=$(echo "$ATTACH_OUTPUT" | egrep '^/dev/' | sed 1q | awk '{print $1}')
MOUNT_POINT=$(echo "$ATTACH_OUTPUT" | grep "/Volumes/" | awk -F'\t+' '{print $3}' | grep "/Volumes/")

# Fallback if parsing fails (sometimes spaces format differs)
if [ -z "$MOUNT_POINT" ]; then
    MOUNT_POINT=$(echo "$ATTACH_OUTPUT" | grep "/Volumes/" | awk '{print $3,$4,$5,$6}' | sed 's/ *$//')
    # This is risky. Let's rely on standard hdiutil output which is tab separated.
    # actually, hdiutil output varies.
    # The most reliable way for simple script is:
    MOUNT_POINT="/Volumes/$VOL_NAME"
    # But if collision, it effectively adds numbers.
    # Let's try to find it via find /Volumes -maxdepth 1
fi
# Best effort clean
MOUNT_POINT=$(echo "$MOUNT_POINT" | xargs)

echo "Device: $DEVICE"
echo "Mount Point: $MOUNT_POINT"

VOL_NAME_MOUNTED=$(basename "$MOUNT_POINT")

# Wait for mount
sleep 3

# 5. Setup View Options
echo "Setting up view options..."

# Hide system files
# Note: We need to hide them in the mounted volume
# MOUNT_POINT override removed, use detected mount point
if [ -d "$MOUNT_POINT" ]; then
    # Create background folder if interested later, but for now just cleanup
    # Hide common artifacts
    SetFile -a V "$MOUNT_POINT/.fseventsd" || true
    SetFile -a V "$MOUNT_POINT/.Trashes" || true
fi



osascript <<EOF
tell application "Finder"
    tell disk "$VOL_NAME_MOUNTED"
        open
        
        -- Wait for window to open
        delay 1

        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        
        -- Window Size (x, y, width, height) - Make it spacious
        set the bounds of container window to {400, 100, 1100, 600}
        
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 144
        set text size of theViewOptions to 14
        
        -- Force positions (Left to Right)
        -- SnapText (App) on LEFT at {180, 240}
        set position of item "SnapText.app" of container window to {180, 240}
        
        -- Applications (Link) on RIGHT at {480, 240}
        set position of item "Applications" of container window to {480, 240}
        
        -- Clean up just in case
        update without registering applications
        delay 2
        
        -- Close to save .DS_Store
        close
    end tell
end tell
EOF

# 6. Unmount and Convert
echo "Finalizing DMG..."
chmod -Rf go-w /Volumes/"$VOL_NAME"
sync
hdiutil detach "$DEVICE"
sleep 2

echo "Converting to compressed DMG..."
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"
rm "$TEMP_DMG"
rm -rf "$STAGING_DIR"

echo "Done! DMG created at $DMG_PATH"
