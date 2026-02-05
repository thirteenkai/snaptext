# SnapText

<p align="center">
  <img src="LocalOCR/resources/icon.png" width="128" alt="SnapText Logo">
</p>

**SnapText** is a high-performance, offline OCR tool designed for macOS.

It resides in your menu bar, ready to capture and recognize text from your screen instantly using the RapidOCR engine (ONNX Runtime). All processing is done locally on your device, ensuring your data remains private.

---

## Key Features

* **Privacy First**: No internet connection required. No API keys needed. All OCR operations are performed offline on your Mac.
* **High Performance**: Optimized model loading ensures millisecond-level response times.
* **Seamless Workflow**:
  * Menu bar resident for quick access.
  * Global hotkeys for instant screen capture.
  * Automatic copying of recognized text to clipboard.
  * Optional preview window for results.
* **Bob Integration**: Includes a plugin to serve as a local, offline OCR engine for [Bob](https://bobtranslate.com/).

## System Requirements

* **Architecture**: Apple Silicon (M1 / M2 / M3) Only.
  * *Note: Intel Macs are not currently supported.*
* **OS**: macOS 11.0 (Big Sur) or later.
* **Storage**: Approximately 200MB.

## Installation

1. Download the latest release (`.dmg`) from the [Releases Page](https://github.com/thirteenkai/snaptext/releases).
2. Open the DMG file and drag **SnapText.app** into your **Applications** folder.
3. Launch SnapText from your Applications folder or Launchpad.

### Troubleshooting

**"SnapText is damaged and can't be opened."**

This error occurs due to macOS Gatekeeper restrictions on unsigned applications. To resolve this, run the following command in Terminal:

```bash
sudo xattr -cr /Applications/SnapText.app
```

**Permissions**

Upon first use, macOS will request permissions for **Screen Recording** and **Accessibility**. These are required for taking screenshots and handling global shortcuts. Please grant these permissions to ensure full functionality.

## Usage

1. **Launch**: Open SnapText. A camera icon will appear in your menu bar.
2. **Capture**: Press the default hotkey `Cmd + Opt + S` (customizable in Settings).
3. **Result**: The recognized text is automatically copied to your clipboard. A preview window may appear if enabled.

## Bob Plugin Integration

SnapText can function as a local OCR service for Bob.

1. Ensure SnapText Main App is running in the background.
2. Download the `snaptext.bobplugin` from the Releases page.
3. Double-click to install it into Bob.
4. In Bob Preferences > Services > Text Recognition, select **SnapText**.

## Development

To build from source:

1. Clone the repository:

    ```bash
    git clone https://github.com/thirteenkai/snaptext.git
    cd snaptext
    ```

2. Install dependencies:

    ```bash
    pip install -r LocalOCR/requirements.txt
    ```

3. Run the application:

    ```bash
    python3 LocalOCR/main.py
    ```

## License

MIT License
