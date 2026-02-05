#!/usr/bin/env python3
"""
SnapText - macOS 菜单栏 OCR 服务
基于 RapidOCR 的高精度本地 OCR 解决方案
"""
import os
import sys
import time
import tempfile
import threading
import base64
import subprocess
import traceback
import logging

# GUI Frameworks
import AppKit
import Cocoa
import rumps

# Local imports
# 确保模块路径正确 (PyInstaller 支持)
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
    os.chdir(app_path)
    sys.path.insert(0, app_path)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from ocr_server import run_server_threaded, set_status_callback
from ocr_engine import ocr_from_base64
from status_overlay import status_overlay
from hotkey_manager import init_hotkey_manager

# App Constants
APP_NAME = "SnapText"
APP_VERSION = "1.0.0"

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.snaptext/app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(APP_NAME)


def run_in_main_thread(func):
    """在主线程执行函数 (Helper)"""
    if threading.current_thread() is threading.main_thread():
        func()
    else:
        Cocoa.NSOperationQueue.mainQueue().addOperationWithBlock_(func)


def get_resource_path(filename):
    """获取资源文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包后 (MacOS/SnapText)
        base_path = os.path.dirname(sys.executable)
        
        # 1. Check Contents/Resources/resources/filename (PyInstaller standard with --add-data)
        nested_res = os.path.join(os.path.dirname(base_path), 'Resources', 'resources', filename)
        if os.path.exists(nested_res):
            return nested_res
            
        # 2. Check Contents/Resources/filename (Direct copy)
        root_res = os.path.join(os.path.dirname(base_path), 'Resources', filename)
        if os.path.exists(root_res):
            return root_res
            
        # 3. Check internal folder (PyInstaller 6+)
        if hasattr(sys, '_MEIPASS'):
            internal_res = os.path.join(sys._MEIPASS, 'resources', filename)
            if os.path.exists(internal_res):
                return internal_res
            
        return os.path.join(base_path, filename)
    else:
        # 开发时
        return os.path.join(os.path.dirname(__file__), 'resources', filename)


class SnapTextApp(rumps.App):
    """SnapText 菜单栏应用"""
    
    def __init__(self):
        # 确定资源路径
        icon_path = get_resource_path('menubar_icon.png')
        
        # 初始化 App
        super().__init__(
            name=APP_NAME,
            title="" if os.path.exists(icon_path) else "⊙",
            icon=icon_path if os.path.exists(icon_path) else None,
            template=True, # 适配深色/浅色模式
            quit_button=None
        )
        
        self.server_thread = None
        self.is_running = False
        self.is_processing = False
        self.hm = None
        self.settings_window = None
        
        # 初始化流程
        try:
            self.init_app()
        except Exception as e:
            self.handle_startup_error(e)
            
    def init_app(self):
        """应用初始化逻辑"""
        # 设置服务器状态回调
        set_status_callback(self.on_processing_status_change)
        
        # 构建菜单
        self.build_menu()
        
        # 启动 OCR 服务
        self.start_server()

        # Prevent App Nap (Critical for background hotkeys)
        try:
            from Foundation import NSProcessInfo, NSActivityUserInitiatedAllowingIdleSystemSleep
            process_info = NSProcessInfo.processInfo()
            self.activity = process_info.beginActivityWithOptions_reason_(
                NSActivityUserInitiatedAllowingIdleSystemSleep,
                "Background Hotkey Listener"
            )
            logger.info("App Nap disabled.")
        except Exception as e:
            logger.warning(f"Failed to disable App Nap: {e}")
        
        # 延迟初始化 (权限检查 & 热键)
        rumps.Timer(self._late_init, 1).start()

    def _late_init(self, timer):
        """延迟初始化步骤"""
        timer.stop()
        self.check_accessibility_permission()
        self.init_hotkey()

    def handle_startup_error(self, e):
        """处理启动错误"""
        logger.error(f"Startup Error: {e}\n{traceback.format_exc()}")
        rumps.alert("Startup Error", str(e))

    def check_accessibility_permission(self):
        """检查辅助功能权限"""
        try:
            # 使用 ApplicationServices 检查是否受信任
            import ApplicationServices
            
            # AXIsProcessTrustedWithOptions 接受一个字典来控制提示行为
            # kAXTrustedCheckOptionPrompt: True 表示如果未授权，系统会弹出提示框
            options = {k: True for k in [ApplicationServices.kAXTrustedCheckOptionPrompt]}
            is_trusted = ApplicationServices.AXIsProcessTrustedWithOptions(options)
            
            if not is_trusted:
                logger.warning("Accessibility permission missing. System prompt should appear.")
                rumps.alert(
                    "需要辅助功能权限",
                    "SnapText 需要“辅助功能”权限才能拦截全局快捷键。\n\n"
                    "请在弹出的系统窗口中点击“打开系统设置”，然后勾选 SnapText。\n\n"
                    "如果不授权，快捷键将无法使用。\n\n(授权后应用将自动重启)"
                )
                # 启动轮询等待权限
                rumps.Timer(self.wait_for_permission, 1).start()
            else:
                logger.info("Accessibility permission granted.")
                
        except ImportError:
            logger.error("Failed to import ApplicationServices. Permission check skipped.")
        except Exception as e:
            logger.warning(f"Permission check failed: {e}")

    def wait_for_permission(self, timer):
        """轮询等待权限授权，一旦授权则重启"""
        try:
            import ApplicationServices
            # 此时不再弹窗，只检查状态
            is_trusted = ApplicationServices.AXIsProcessTrustedWithOptions(None)
            
            if is_trusted:
                logger.info("Permission granted! Restarting...")
                timer.stop()
                
                # 给用户一个正反馈
                rumps.notification(APP_NAME, "授权成功", "正在重启应用以生效...")
                
                # 稍等一下让通知显示出来，然后重启
                time.sleep(1)
                self.restart_server(None)
        except Exception as e:
            logger.error(f"Error checking permission: {e}")

    def init_hotkey(self):
        """初始化全局热键"""
        try:
            self.hm = init_hotkey_manager(self._trigger_screenshot_ocr)
            success = self.hm.set_hotkey(config.hotkey)
            if success:
                logger.info("Hotkey manager initialized")
            else:
                logger.warning("Hotkey init failed (Permission denied?)")
        except Exception as e:
            logger.error(f"Failed to init hotkey: {e}")

    def build_menu(self):
        """构建菜单栏菜单"""
        # 状态项
        self.status_item = rumps.MenuItem("⏳ 启动中...")
        self.status_item.set_callback(None)
        
        # 端口项
        self.port_item = rumps.MenuItem(f"端口: {config.port}")
        self.port_item.set_callback(None)
        
        # 统计项
        stats = config.get_stats()
        self.stats_item = rumps.MenuItem(f"今日: {stats['today_count']} | 总计: {stats['total_count']}")
        self.stats_item.set_callback(None)
        
        # 截图按钮 (尝试解析并显示快捷键)
        shortcut_key, shortcut_mods = self._parse_hotkey_for_menu(config.hotkey)
        self.screenshot_item = rumps.MenuItem("截图识别", callback=self._trigger_screenshot_from_menu, key=shortcut_key)
        self._apply_menu_modifiers(self.screenshot_item, shortcut_mods)

        # 其他菜单项
        self.settings_item = rumps.MenuItem("偏好设置...", callback=self.open_settings)
        self.check_update_item = rumps.MenuItem("检查更新...", callback=self.check_for_updates)
        self.restart_item = rumps.MenuItem("重启服务", callback=self.restart_server)
        self.about_item = rumps.MenuItem("关于", callback=self.show_about)
        self.quit_item = rumps.MenuItem(f"退出 {APP_NAME}", callback=self.quit_app)
        
        self.menu = [
            self.status_item,
            self.port_item,
            rumps.separator,
            self.screenshot_item,
            rumps.separator,
            self.settings_item,
            self.check_update_item,
            self.restart_item,
            rumps.separator,
            self.about_item,
            self.quit_item
        ]
        
        # 定时刷新配置
        rumps.Timer(self.refresh_config, 2).start()

    def _parse_hotkey_for_menu(self, hotkey_str):
        """解析热键字符串用于菜单显示"""
        key = None
        mods = []
        if hotkey_str:
            # 兼容 pynput 格式 (<cmd>+<shift>+o)
            clean_str = hotkey_str.lower().replace(" ", "").replace("<", "").replace(">", "")
            parts = clean_str.split('+')
            if len(parts) > 0:
                key = parts[-1].upper()
                mapping = {
                    'cmd': 'cmd', 'command': 'cmd',
                    'ctrl': 'ctrl', 'control': 'ctrl',
                    'opt': 'opt', 'option': 'opt', 'alt': 'opt',
                    'shift': 'shift'
                }
                for p in parts[:-1]:
                    if p in mapping:
                        mods.append(mapping[p])
        return key, mods

    def _apply_menu_modifiers(self, menu_item, mods):
        """应用菜单修饰键"""
        if not mods:
            return
        
        try:
             # PyObjC constants
            from AppKit import NSCommandKeyMask, NSShiftKeyMask, NSAlternateKeyMask, NSControlKeyMask
            mask_map = {
                'cmd': NSCommandKeyMask,
                'ctrl': NSControlKeyMask,
                'opt': NSAlternateKeyMask,
                'shift': NSShiftKeyMask
            }
            mask = 0
            for mod in mods:
                if mod in mask_map:
                    mask |= mask_map[mod]
            
            menu_item._menuitem.setKeyEquivalentModifierMask_(mask)
        except Exception as e:
            logger.warning(f"Failed to set menu modifiers: {e}")

    def refresh_config(self, _):
        """刷新配置与 UI 状态"""
        old_hotkey = config.hotkey
        
        config.reload()
        
        # 更新文本
        self.port_item.title = f"端口: {config.port}"
        self.update_stats_display()
        
        # 检查热键变更
        if config.hotkey != old_hotkey:
            if self.hm:
                self.hm.set_hotkey(config.hotkey)
                logger.info(f"Hotkey updated to {config.hotkey}")
            
            # 更新菜单快捷键显示
            key, mods = self._parse_hotkey_for_menu(config.hotkey)
            if key:
                self.screenshot_item._menuitem.setKeyEquivalent_(key.lower())
                self._apply_menu_modifiers(self.screenshot_item, mods)

    def start_server(self):
        """启动 OCR 服务线程"""
        try:
            self.server_thread = run_server_threaded(config.port)
            # 等待一小会儿确保启动
            time.sleep(0.5)
            self.is_running = True
            self.update_status()
        except Exception as e:
            rumps.alert("启动失败", f"服务启动异常: {e}")
            self.is_running = False
            self.update_status()

    def restart_server(self, _):
        """重启整个应用"""
        rumps.notification(APP_NAME, "正在重启...", "")
        os.execv(sys.executable, ['python'] + sys.argv)

    def update_status(self):
        """更新状态栏文字"""
        run_in_main_thread(self._update_status_ui)

    def _update_status_ui(self):
        if self.is_processing:
            self.status_item.title = "正在识别..."
        elif self.is_running:
            self.status_item.title = "服务运行中"
        else:
            self.status_item.title = "服务已停止"

    def on_processing_status_change(self, is_processing: bool):
        """服务端状态回调"""
        self.is_processing = is_processing
        self.update_status()
        if not is_processing:
            self.update_stats_display()

    def update_stats_display(self):
        """更新统计数据UI"""
        run_in_main_thread(self._update_stats_ui)
        
    def _update_stats_ui(self):
        try:
            stats = config.get_stats()
            self.stats_item.title = f"今日: {stats['today_count']} | 总计: {stats['total_count']}"
        except Exception:
            self.stats_item.title = "统计数据不可用"

    # --- Actions ---

    def _trigger_screenshot_from_menu(self, _):
        self._trigger_screenshot_ocr()

    def _trigger_screenshot_ocr(self):
        """触发截图流程 (后台线程)"""
        threading.Thread(target=self.capture_and_ocr, daemon=True).start()

    def capture_and_ocr(self):
        """执行截图 -> OCR"""
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
            
            # 调用 screencapture
            # -i: 交互式, -x: 无声
            result = subprocess.run(['screencapture', '-i', '-x', temp_path], capture_output=True)
            
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                # 用户取消
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                return

            # 显示 Loading
            run_in_main_thread(status_overlay.show_loading_at_mouse)
            
            # 读取并编码
            with open(temp_path, 'rb') as f:
                img_data = f.read()
            
            # 清理
            os.remove(temp_path)
            temp_path = None
            
            base64_img = base64.b64encode(img_data).decode('utf-8')
            
            # 执行 OCR (复用逻辑)
            self._perform_ocr(base64_img)
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            run_in_main_thread(lambda: self.handle_ocr_error(str(e)))

    def _perform_ocr(self, base64_image):
        """执行 OCR (后台线程)"""
        try:
            run_in_main_thread(lambda: setattr(self.status_item, "title", "正在识别..."))
            
            texts, language = ocr_from_base64(base64_image)
            
            run_in_main_thread(lambda: self.handle_ocr_result(texts))
        except Exception as e:
            run_in_main_thread(lambda: self.handle_ocr_error(str(e)))

    def handle_ocr_result(self, texts):
        """处理 OCR 结果 (主线程)"""
        self.update_status()
        
        if not texts:
            status_overlay.update_to_error()
            return

        result_text = '\n'.join(texts)
        self.copy_to_clipboard(result_text)
        
        config.increment_count()
        self.update_stats_display()
        
        status_overlay.update_to_success()
        self.show_result_notification(result_text)

    def handle_ocr_error(self, msg):
        """处理错误 (主线程)"""
        self.update_status()
        status_overlay.update_to_error()
        rumps.alert("错误", f"识别失败: {msg}")

    def copy_to_clipboard(self, text):
        pb = Cocoa.NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, Cocoa.NSPasteboardTypeString)

    def show_result_notification(self, text):
        """显示结果通知/弹窗"""
        # 强制重新读取配置确保 silent_mode 是最新的
        config.reload()
        
        if config.silent_mode:
            # 仅通知
            pass
        else:
            # 弹窗
            display = text if len(text) < 500 else text[:500] + "...\n(更多内容已复制)"
            rumps.alert("识别结果", display)

    def check_for_updates(self, _):
        """检查更新"""
        threading.Thread(target=self._check_update_thread, daemon=True).start()

    def _check_update_thread(self):
        try:
            import urllib.request
            import ssl
            import json
            
            rumps.notification(APP_NAME, "正在检查更新...", "")
            
            url = "https://raw.githubusercontent.com/thirteenkai/snaptext/main/appcast.json"
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SnapText-Updater')
            
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            latest_ver = "0.0.0"
            download_url = ""
            
            if "version" in data:
                latest_ver = data["version"]
                download_url = data.get("url", "")
            elif "versions" in data:
                v = data["versions"][0]
                latest_ver = v.get("version", "0.0.0")
                download_url = v.get("url", "")
            
            # Simple compare
            if latest_ver != APP_VERSION:
                run_in_main_thread(lambda: self._prompt_update(latest_ver, download_url))
            else:
                rumps.notification(APP_NAME, "已是最新版本", f"当前版本 v{APP_VERSION}")
                
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            rumps.alert("更新检查失败", str(e))

    def _prompt_update(self, version, url):
        resp = rumps.alert(
            title="发现新版本",
            message=f"最新版本: v{version}\n当前版本: v{APP_VERSION}\n\n是否前往下载？",
            ok="下载",
            cancel="取消"
        )
        if resp == 1:
            import webbrowser
            webbrowser.open(url)

    def open_settings(self, _, tab='general'):
        """打开设置窗口 (独立进程)"""
        try:
            # 检查是否已存在设置进程
            if hasattr(self, 'settings_process') and self.settings_process and self.settings_process.poll() is None:
                # 尝试激活 app could be done via AppleScript but subprocess is separate.
                # Ideally we kill and restart to switch tab, or just return.
                # For simplicity, if asking for specific tab, maybe restart it?
                # Let's just restart it if it's already running to ensure tab switch, or just focus.
                # Restarting is easier to guarantee tab switch.
                self.settings_process.terminate()
                time.sleep(0.5)

            # 启动新进程
            import subprocess
            
            # Prepare args: exe, --settings, --tab=xxx
            cmd = []
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--settings"]
            else:
                cmd = [sys.executable, __file__, "--settings"]
            
            cmd.append(f"--tab={tab}")
            
            self.settings_process = subprocess.Popen(cmd)
            
        except Exception as e:
            rumps.alert("错误", f"无法打开设置: {e}")

    def show_about(self, _):
        """跳转到设置-关于"""
        self.open_settings(None, tab='about')

    def quit_app(self, _):
        """退出应用"""
        # 关闭设置窗口
        if hasattr(self, 'settings_process') and self.settings_process:
            try:
                self.settings_process.terminate()
            except:
                pass
        rumps.quit_application()


def main():
    try:
        debug_log = os.path.expanduser("~/.snaptext/startup.log")
        with open(debug_log, "a") as f:
            f.write(f"[{time.ctime()}] Startup args: {sys.argv}\n")
    except:
        pass

    # Check for settings mode
    if len(sys.argv) > 1 and "--settings" in sys.argv:
        try:
            with open(debug_log, "a") as f:
                f.write(f"[{time.ctime()}] Entering settings mode\n")
            
            # Parse tab
            initial_tab = 'general'
            for arg in sys.argv:
                if arg.startswith("--tab="):
                    initial_tab = arg.split("=", 1)[1]

            from settings_window import create_settings_window
            create_settings_window(initial_tab)
            return
        except Exception as e:
             with open(debug_log, "a") as f:
                f.write(f"[{time.ctime()}] Settings mode failed: {e}\n{traceback.format_exc()}\n")
             return

    SnapTextApp().run()


if __name__ == "__main__":
    main()
