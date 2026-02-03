#!/usr/bin/env python3
"""
SnapText - macOS 菜单栏 OCR 服务
基于 RapidOCR 的高精度本地 OCR 解决方案
"""
import os
import sys
import subprocess
import time
import AppKit

import rumps

# 确保模块路径正确
if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
    os.chdir(app_path)
    sys.path.insert(0, app_path)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from ocr_server import run_server_threaded, set_status_callback

# App 名称
APP_NAME = "SnapText"
APP_VERSION = "1.0.0"


class SnapTextApp(rumps.App):
    """SnapText 菜单栏应用"""
    
    def __init__(self):
        # 获取图标路径
        if getattr(sys, 'frozen', False):
            # 打包后
            icon_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'menubar_icon.png')
        else:
            # 开发时
            icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'menubar_icon.png')
        
        # 如果图标文件存在则使用图标，否则使用文字
        if os.path.exists(icon_path):
            super().__init__(
                name=APP_NAME,
                title="",  # 空字符串，不显示文字
                icon=icon_path,
                template=True,  # 使用模板模式，自动适应深色/浅色模式
                quit_button=None
            )
        else:
            super().__init__(
                name=APP_NAME,
                title="⊙",
                quit_button=None
            )
        
        self.server_thread = None
        self.is_running = False
        self.is_processing = False
        
        # 隐藏 Dock 图标
        self._hide_dock_icon()
        
        # 设置状态回调
        set_status_callback(self.on_processing_status_change)
        
        # 构建菜单
        self.build_menu()
        
        # 启动服务器
        self.start_server()
    
    def _hide_dock_icon(self):
        """隐藏 Dock 图标"""
        try:
            AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        except Exception:
            pass
    
    def build_menu(self):
        """构建菜单"""
        # 状态显示
        self.status_item = rumps.MenuItem("⏳ 启动中...")
        self.status_item.set_callback(None)
        
        # 端口信息
        self.port_item = rumps.MenuItem(f"端口: {config.port}")
        self.port_item.set_callback(None)
        
        # 统计信息
        stats = config.get_stats()
        self.stats_item = rumps.MenuItem(
            f"今日: {stats['today_count']} 次 | 总计: {stats['total_count']} 次"
        )
        self.stats_item.set_callback(None)
        
        # 设置子菜单
        self.settings_menu = rumps.MenuItem("设置")
        
        # 开机启动
        self.launch_item = rumps.MenuItem(
            "开机启动",
            callback=self.toggle_launch_at_login
        )
        self.launch_item.state = config.launch_at_login
        
        # 修改端口
        self.port_setting = rumps.MenuItem("修改端口...", callback=self.change_port)
        
        self.settings_menu.add(self.launch_item)
        self.settings_menu.add(self.port_setting)
        
        # 操作
        self.restart_item = rumps.MenuItem("重启服务", callback=self.restart_server)
        
        # 关于和退出
        self.about_item = rumps.MenuItem("关于", callback=self.show_about)
        self.quit_item = rumps.MenuItem("退出", callback=self.quit_app)
        
        # 构建菜单结构（简化版，移除历史记录和模式选择）
        self.menu = [
            self.status_item,
            self.port_item,
            None,
            self.stats_item,
            None,
            self.settings_menu,
            self.restart_item,
            None,
            self.about_item,
            self.quit_item
        ]
    
    def update_stats_display(self):
        """更新统计显示"""
        stats = config.get_stats()
        self.stats_item.title = f"今日: {stats['today_count']} 次 | 总计: {stats['total_count']} 次"
    
    def start_server(self):
        """启动 OCR 服务器"""
        try:
            self.server_thread = run_server_threaded(config.port)
            time.sleep(0.5)
            self.is_running = True
            self.update_status()
        except Exception as e:
            rumps.alert("启动失败", f"OCR 服务启动失败: {e}")
            self.is_running = False
            self.update_status()
    
    def update_status(self):
        """更新状态显示"""
        # 只更新菜单项文字，不修改菜单栏图标/标题
        if self.is_processing:
            self.status_item.title = "⏳ 正在识别..."
        elif self.is_running:
            self.status_item.title = "✓ 服务运行中"
        else:
            self.status_item.title = "✗ 服务已停止"
    
    def on_processing_status_change(self, is_processing: bool):
        """处理状态变化回调"""
        self.is_processing = is_processing
        try:
            self.update_status()
            if not is_processing:
                # OCR 完成后更新统计
                self.update_stats_display()
        except Exception:
            pass
    
    def restart_server(self, _):
        """重启服务器"""
        rumps.notification(
            title=APP_NAME,
            subtitle="正在重启服务...",
            message=""
        )
        os.execv(sys.executable, ['python'] + sys.argv)
    
    def toggle_launch_at_login(self, sender):
        """切换开机启动"""
        config.launch_at_login = not config.launch_at_login
        sender.state = config.launch_at_login
        
        status = "已启用" if config.launch_at_login else "已禁用"
        rumps.notification(APP_NAME, f"开机启动{status}", "")
    
    def change_port(self, _):
        """修改端口"""
        response = rumps.Window(
            message="请输入新的端口号 (1024-65535):",
            title="修改端口",
            default_text=str(config.port),
            ok="确定",
            cancel="取消"
        ).run()
        
        if response.clicked:
            try:
                new_port = int(response.text)
                if 1024 <= new_port <= 65535:
                    config.port = new_port
                    self.port_item.title = f"端口: {new_port}"
                    rumps.notification(
                        APP_NAME,
                        "端口已修改",
                        f"新端口: {new_port}，重启后生效"
                    )
                else:
                    rumps.alert("错误", "端口必须在 1024-65535 之间")
            except ValueError:
                rumps.alert("错误", "请输入有效的端口号")
    
    def show_about(self, _):
        """显示关于信息"""
        rumps.alert(
            title=f"关于 {APP_NAME}",
            message=(
                f"{APP_NAME} v{APP_VERSION}\n\n"
                "基于 RapidOCR 的高精度本地 OCR 服务\n"
                "用于 Bob 翻译软件\n\n"
                f"API: http://localhost:{config.port}/ocr\n\n"
                "完全离线运行，无需 API Key"
            )
        )
    
    def quit_app(self, _):
        """退出应用"""
        rumps.quit_application()


def main():
    """主函数"""
    app = SnapTextApp()
    app.run()


if __name__ == "__main__":
    main()
