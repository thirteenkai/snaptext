# SnapText Bob Plugin

这是 [SnapText](https://github.com/thirteenkai/snaptext) 的官方 Bob 插件。

它允许 **Bob** 调用 SnapText 的本地离线 OCR 服务，实现免费、无限量、高精度的截图文本识别。

## 📋 前置条件

1. **必须安装并运行 SnapText 主程序**：[下载地址](https://github.com/thirteenkai/snaptext/releases)
2. 安装 [Bob](https://bobtranslate.com/) 翻译软件。

## 📦 安装插件

1. 下载最新的 `snaptext.bobplugin` 文件（可在 [Releases](https://github.com/thirteenkai/snaptext-bob-plugin/releases) 页面找到）。
2. 双击文件，Bob 会提示安装。
3. 安装后，在 Bob 的 **偏好设置** -> **翻译** -> **服务** -> **添加插件** 中，选择 **SnapText** 服务。

## ⚙️ 配置

通常无需配置，默认端口为 `9999`。

如果 SnapText 主程序修改了监听端口，请在 Bob 插件配置中同步修改。

## 🚀 使用

当 SnapText 主程序在后台运行时，您可以使用 Bob 的截图 OCR 功能，选择 SnapText 作为服务源即可。
