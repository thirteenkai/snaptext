## 问题与根因
- 快捷键录制显示“shift”异常：未在主键事件使用 e.metaKey/e.ctrlKey/e.altKey/e.shiftKey 读取实际修饰键，导致误判。
- 清空后重新录入同快捷键会触发截图：设置窗口以子进程方式启动，无法暂停主进程热键；且 set_hotkey('') 未清理旧的事件 tap。
- DMG 打开后没有“访达路径/拖拽目标”：普通版 DMG未包含“Applications”别名和窗口布局，无法直观拖拽到应用程序。

## 修改方案
1. 前端录制修正（resources/settings/app.js）
- 在 onRecordingKeydown 记录主键的当下，用 e.metaKey/e.ctrlKey/e.altKey/e.shiftKey 采集修饰键，避免误显示 shift。
- activeModifiers 仅用于 UI 实时展示，不参与最终保存。

2. 设置窗口改回主进程内（main.py + settings_window.py）
- open_settings 由子进程改为 self.settings_window.show()，SettingsAPI 拿到主进程 app_instance。
- 录制开始 SettingsAPI.set_hotkey_paused(true) 暂停主进程热键；录制结束恢复。

3. HotkeyManager 行为增强（hotkey_manager.py）
- set_hotkey('') 清理现有 CGEventTap（Disable + RemoveSource + 置空 tap/runLoopSource/target_key_code），确保清空后不再触发。
- 维持 pause/resume 逻辑以配合录制。

4. 打包资源完整（PyInstaller）
- 打包时加入 --add-data "resources:resources"，确保 settings 的 HTML/CSS/JS 全部在 .app 内，避免空白窗口。

5. DMG 可拖拽安装（不美化）
- 使用 dmgbuild 生成“功能型”DMG：仅包含 SnapText.app 和 Applications → /Applications 别名；默认 icon-view，设置 icon 位置，保留 Finder 简洁视图。
- 不加背景图/美化，仅保证打开 DMG 即可拖拽到 Applications。

## 验证步骤
- 启动打包版 App，打开偏好设置：内容显示正常。
- 录制：不按 shift 时不再显示；清空后重新录 cmd+shift+s 时不触发截图（录制期热键暂停 + 空热键清理 tap）。
- 保存后热键立即生效。
- 打开新版 DMG：看到 SnapText.app 与 Applications 链接，可直接拖拽安装。

## 交付
- 生成普通功能型 DMG（含 Applications 链接，无背景美化）。

请确认是否按此方案开始修改与重新打包。