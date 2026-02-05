import os
import sys
import json
import webview
import threading
from config import config
from hotkey_manager import HotkeyManager
import subprocess

# 资源路径处理
def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SettingsAPI:
    def __init__(self, window, app_instance=None):
        self.window = window
        self.app_instance = app_instance
        self.hotkey_manager = HotkeyManager(None) # Helper for formatting

    def get_config(self):
        """获取当前配置"""
        # 重新加载配置（防止 Main App 修改了）
        config.reload()
        
        # 将内部数据转换为前端需要的格式
        data = {
            "launch_at_login": config.launch_at_login,
            "silent_mode": config.silent_mode,
            "port": config.port,
            "hotkey": self.hotkey_manager.friendly_format(config.hotkey) # 友好显示
        }
        return data

    def set_config(self, key, value):
        """更新配置"""
        print(f"Setting config: {key} = {value}")
        
        # Reload first to ensure we don't overwrite other recent changes
        config.reload()
        
        if key == 'launch_at_login':
            config.launch_at_login = value
        elif key == 'silent_mode':
            config.silent_mode = value
        elif key == 'port':
            config.port = value
        elif key == 'hotkey':
            config.hotkey = value
            # Since we are in a separate process, we don't update the main app's hotkey manager directly.
            # The main app has a timer (refresh_config) that will pick up the change from file.
        
        config.save()
        
    def start_hotkey_recording(self):
        """开始录制快捷键"""
        # Tell UI it is safe to record
        self.window.evaluate_js("window.onPermissionCheck(true)")
        return True

    def open_privacy_settings(self):
        pass 

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def set_hotkey_paused(self, paused):
        """控制热键监听暂停/恢复 (通过文件锁)"""
        lock_file = os.path.expanduser("~/.snaptext/recording_hotkey.lock")
        try:
            if paused:
                # Create lock file
                with open(lock_file, "w") as f:
                    f.write("locked")
            else:
                # Remove lock file
                if os.path.exists(lock_file):
                    os.remove(lock_file)
        except Exception as e:
            print(f"Failed to set paused state {paused}: {e}")

    def check_for_updates(self):
        """检查更新"""
        try:
            import urllib.request
            import ssl
            
            # 使用 GitHub Raw 获取最新版本信息
            # 替换为实际的仓库地址
            url = "https://raw.githubusercontent.com/thirteenkai/snaptext/main/appcast.json"
            
            print(f"Checking update from: {url}")
            
            # 忽略 SSL 错误 (可选，取决于环境)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            # Add User-Agent to avoid 403
            req.add_header('User-Agent', 'SnapText-Updater')
            
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            # Parse standalone appcast
            # Standard format: { "version": "1.0.0", "url": "...", "notes": "..." }
            # Or Bob format: { "versions": [...] }
            
            latest_ver = "0.0.0"
            download_url = ""
            
            if "version" in data:
                # Standalone format
                latest_ver = data["version"]
                download_url = data.get("url", "")
            elif "versions" in data:
                # List format (take first)
                v = data["versions"][0]
                latest_ver = v.get("version", "0.0.0")
                download_url = v.get("url", "")
                
            return {
                "latest": latest_ver,
                "url": download_url,
                "error": None
            }
            
        except Exception as e:
            return {"error": str(e)}

    def get_initial_tab(self):
        """获取初始 Tab"""
        return getattr(self, 'initial_tab', None)


class SettingsWindow:
    def __init__(self, app_instance=None):
        self.window = None
        self.api = None
        self.app_instance = app_instance
        
    def show(self):
        if self.window:
            self.window.show()
            self.window.restore()
            return
            
        self.api = SettingsAPI(None, self.app_instance)
        
        html_path = get_resource_path('resources/settings/index.html')
        html_url = f'file://{html_path}'
        
        self.window = webview.create_window(
            "SnapText 设置", 
            html_url,
            width=600,
            height=500,
            resizable=False,
            js_api=self.api,
            background_color='#1e1e1e'
        )
        self.api.window = self.window
        self.window.events.closed += self.on_closed

    def on_closed(self):
        self.window = None





def create_settings_window(initial_tab='general'):
    # 隐藏 Dock 图标 (作为子进程启动时)
    try:
        import AppKit
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except Exception:
        pass
    
    api = SettingsAPI(None)
    api.initial_tab = initial_tab
    
    html_path = get_resource_path('resources/settings/index.html')
    html_url = f'file://{html_path}'
    
    window = webview.create_window(
        'SnapText 设置', 
        html_url,
        js_api=api,
        width=600,
        height=400,
        resizable=False,
        background_color='#1e1e1e' # Dark mode default to avoid flash
    )
    api.window = window
    webview.start(debug=False)

if __name__ == '__main__':
    # Parse explicit args if run directly for testing
    tab = 'general'
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg.startswith("--tab="):
                tab = arg.split("=")[1]
    create_settings_window(tab)
