# SnapText

<p align="center">
  <img src="LocalOCR/resources/icon.png" width="128" alt="SnapText Logo">
</p>

**SnapText** 是一款专为 macOS 设计的高性能本地 OCR 工具。

它常驻于菜单栏，基于 RapidOCR (ONNX Runtime) 引擎，能够瞬间捕捉并识别屏幕上的文字。所有处理过程均在本地设备完成，无需联网，充分保护您的隐私。

---

## 核心特性

* **隐私至上**：无需互联网连接，无需 API 密钥。所有 OCR 操作均在您的 Mac 上离线完成。
* **极致性能**：优化的模型加载策略，确保毫秒级的响应速度。
* **流畅工作流**：
  * 菜单栏常驻，随时待命。
  * 全局快捷键支持，一键截图。
  * 识别结果自动复制到剪贴板。
  * 提供可视化结果预览窗口（可配置）。
* **Bob 集成**：内置插件支持，可作为 [Bob](https://bobtranslate.com/) 翻译软件的离线 OCR 引擎。

## 系统要求

* **架构**：仅支持 Apple Silicon 芯片 (M1 / M2 / M3)。
  * *注意：暂不支持 Intel 芯片的 Mac。*
* **操作系统**：macOS 11.0 (Big Sur) 或更高版本。
* **磁盘空间**：约 200MB。

## 安装指南

1. 访问 [Releases 页面](https://github.com/thirteenkai/snaptext/releases) 下载最新版本的安装包 (`.dmg`)。
2. 打开 DMG 文件，将 **SnapText.app** 拖入您的 **应用程序 (Applications)** 文件夹。
3. 从启动台或应用程序文件夹中启动 SnapText。

### 常见问题排查

**提示“SnapText 已损坏，无法打开”**

此错误通常由 macOS Gatekeeper 安全机制引起（因为应用未签名）。请在终端 (Terminal) 中运行以下命令以修复：

```bash
sudo xattr -cr /Applications/SnapText.app
```

**权限说明**

首次使用时，macOS 会请求 **屏幕录制** 和 **辅助功能** 权限。这是实现截图和全局快捷键功能的必要条件，请务必授权以确保软件正常运行。

## 使用方法

1. **启动**：打开 SnapText，菜单栏会出现一个相机图标。
2. **截图**：按下默认快捷键 `Cmd + Opt + S`（可在设置中自定义）。
3. **结果**：识别到的文字将自动复制到您的剪贴板。如果启用了预览，结果窗口也会同时弹出。

## Bob 插件集成

SnapText 可以作为 Bob 的本地 OCR 服务端运行。

1. 确保 SnapText 主程序正在后台运行。
2. 从 Releases 页面下载 `snaptext.bobplugin` 插件文件。
3. 双击插件文件将其安装到 Bob 中。
4. 在 Bob 的 **偏好设置 > 服务 > 文本识别** 中，选择 **SnapText**。

## 开发构建

如果您希望从源码构建：

1. 克隆仓库：

    ```bash
    git clone https://github.com/thirteenkai/snaptext.git
    cd snaptext
    ```

2. 安装依赖：

    ```bash
    pip install -r LocalOCR/requirements.txt
    ```

3. 运行应用：

    ```bash
    python3 LocalOCR/main.py
    ```

## 许可证

MIT License
