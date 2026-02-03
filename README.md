# SnapText

<p align="center">
  <img src="LocalOCR/resources/icon.png" width="128" alt="SnapText Logo">
</p>

<p align="center">
  <b>高精度本地 OCR 服务 · 完全离线 · 无需 API</b>
</p>

---

## ✨ 特性

- 🔤 **高精度识别** - 基于 PaddleOCR 模型
- 🌐 **多语言支持** - 中文、英文、日文、韩文等
- 🔒 **完全离线** - 无需网络，数据不外传
- 🚀 **开箱即用** - 菜单栏应用，双击即可运行
- 🧠 **智能排版** - 自动识别行列，保持原始格式

## 📦 安装

### 1. 安装 SnapText

1. 下载 [SnapText.app](https://github.com/thirteenkai/snaptext/releases)
2. 拖入「应用程序」文件夹
3. 双击运行

> 首次运行可能需要在「系统设置 → 隐私与安全性」中允许打开

### 2. 安装 Bob 插件

1. 下载 [snaptext.bobplugin](https://github.com/thirteenkai/snaptext/releases)
2. 双击安装到 Bob
3. 在 Bob **偏好设置 → 服务 → 文本识别** 中添加「SnapText」

## 🎯 使用

1. 确保菜单栏显示 SnapText 图标
2. 使用 Bob 的截图翻译功能
3. SnapText 会自动识别图片中的文字

## ⚙️ 设置

点击菜单栏图标可以：

- 查看服务状态和识别统计
- 开启/关闭开机启动
- 修改服务端口（默认 9999）

## � 系统要求

- macOS 11.0 (Big Sur) 或更高版本
- Bob 1.0.0 或更高版本
- 约 200MB 磁盘空间

## ❓ 常见问题

**Q: 服务无法启动？**

检查端口 9999 是否被占用，可以在设置中修改端口。

**Q: 识别不准确？**

SnapText 对清晰的截图效果最好。模糊或低分辨率图片可能影响识别。

**Q: 如何更新？**

在 Bob 插件设置中刷新可检查更新，或访问 [Releases](https://github.com/thirteenkai/snaptext/releases) 下载最新版。

## 📄 许可证

MIT License

## 🙏 致谢

- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Bob](https://bobtranslate.com/)
