# 开发者指南

## 项目结构

```
snaptext/
├── LocalOCR/              # Python 菜单栏应用
│   ├── main.py            # 主程序入口
│   ├── config.py          # 配置管理
│   ├── ocr_engine.py      # OCR 引擎封装
│   ├── ocr_server.py      # HTTP API 服务
│   ├── requirements.txt   # Python 依赖
│   └── resources/         # 图标资源
├── snaptext.bobplugin/    # Bob 插件
│   ├── info.json          # 插件配置
│   ├── main.js            # 插件逻辑
│   └── icon.png           # 插件图标
├── build/                 # 构建脚本
└── dist/                  # 打包输出
```

## 从源码运行

```bash
cd LocalOCR
pip install -r requirements.txt
python main.py
```

## 打包应用

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
cd LocalOCR
pyinstaller --name "SnapText" --windowed --onedir \
  --icon resources/icon.icns \
  --add-data "resources/menubar_icon.png:." \
  --hidden-import rapidocr_onnxruntime \
  --hidden-import onnxruntime \
  --hidden-import PIL \
  --hidden-import flask \
  --hidden-import werkzeug \
  --hidden-import rumps \
  --hidden-import AppKit \
  --collect-data rapidocr_onnxruntime \
  main.py

# 添加 LSUIElement 隐藏 Dock 图标
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/SnapText.app/Contents/Info.plist

# 复制菜单栏图标
cp resources/menubar_icon.png dist/SnapText.app/Contents/Resources/
```

## API 接口

### OCR 识别

```bash
POST http://localhost:9999/ocr
Content-Type: application/json

{
  "image": "<base64编码的图片>"
}
```

响应：

```json
{
  "texts": ["第一行", "第二行"],
  "from": "zh-Hans"
}
```

### 健康检查

```bash
GET http://localhost:9999/health
```

### 统计信息

```bash
GET http://localhost:9999/stats
```

## 配置文件

配置保存在 `~/.snaptext/config.json`：

```json
{
  "port": 9999,
  "launch_at_login": false,
  "stats": {
    "today_count": 0,
    "total_count": 100,
    "last_date": "2024-01-01"
  }
}
```
