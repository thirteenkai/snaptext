"""
状态浮窗模块 - 显示 OCR 识别状态
在截图区域中心显示 loading/成功/失败 状态
"""
import os
import sys
import threading
import time

import AppKit
import Cocoa
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode


def get_resource_path(filename):
    """获取资源文件路径"""
    if getattr(sys, 'frozen', False):
        # 打包后 (MacOS/SnapText)
        base_path = os.path.dirname(sys.executable)
        
        # 1. Check Contents/Resources/resources/filename (PyInstaller standard)
        nested_res = os.path.join(os.path.dirname(base_path), 'Resources', 'resources', filename)
        if os.path.exists(nested_res):
            return nested_res
            
        # 2. Check Contents/Resources/filename (Manual copy)
        root_res = os.path.join(os.path.dirname(base_path), 'Resources', filename)
        if os.path.exists(root_res):
            return root_res
            
        # 3. Check Contents/MacOS/filename (Fallback)
        return os.path.join(base_path, filename)
    else:
        # 开发时
        return os.path.join(os.path.dirname(__file__), 'resources', filename)


class StatusOverlay:
    """状态浮窗管理器"""
    
    def __init__(self):
        self.window = None
        self.spinner = None
        self.image_view = None
        self._timer = None
    
    def show_loading(self, x: float, y: float):
        """显示加载状态（系统菊花）"""
        self._ensure_main_thread(lambda: self._create_window(x, y, 'loading'))

    def show_loading_at_mouse(self):
        """在鼠标当前位置显示加载状态"""
        # 获取鼠标位置
        try:
            # Need to get location carefully from main thread if possible, 
            # but NSEvent.mouseLocation() is generally thread-safe or we wrap it.
            # However, since we need to pass x,y to show_loading which does ensure_main_thread,
            # we can just get it here.
            loc = Cocoa.NSEvent.mouseLocation()
            self.show_loading(loc.x, loc.y)
        except Exception as e:
            print(f"Failed to get mouse location: {e}")
    
    def show_success(self, x: float, y: float):
        """显示成功状态"""
        self._ensure_main_thread(lambda: self._create_window(x, y, 'success'))
    
    def show_error(self, x: float, y: float):
        """显示错误状态"""
        self._ensure_main_thread(lambda: self._create_window(x, y, 'error'))
    
    def update_to_success(self):
        """从 loading 更新为成功，1秒后消失"""
        self._ensure_main_thread(lambda: self._update_status('success'))
    
    def update_to_error(self):
        """从 loading 更新为错误，1秒后消失"""
        self._ensure_main_thread(lambda: self._update_status('error'))
    
    def hide(self):
        """隐藏浮窗"""
        self._ensure_main_thread(self._hide_window)
    
    def _ensure_main_thread(self, func):
        """确保在主线程执行"""
        if threading.current_thread() is threading.main_thread():
            func()
        else:
            # 在主线程执行
            Cocoa.NSOperationQueue.mainQueue().addOperationWithBlock_(func)
    
    def _create_window(self, x: float, y: float, status: str):
        """创建浮窗"""
        # 关闭之前的窗口
        self._hide_window()
        
        # 窗口大小 (只比图标稍大)
        size = 32
        
        # 计算窗口位置（居中于给定坐标）
        frame = Cocoa.NSMakeRect(x - size/2, y - size/2, size, size)
        
        # 创建无边框窗口
        self.window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            Cocoa.NSWindowStyleMaskBorderless,
            Cocoa.NSBackingStoreBuffered,
            False
        )
        
        # 设置窗口属性
        self.window.setLevel_(Cocoa.NSStatusWindowLevel + 1)  # 最顶层
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(Cocoa.NSColor.clearColor())
        self.window.setIgnoresMouseEvents_(True)
        self.window.setCollectionBehavior_(
            Cocoa.NSWindowCollectionBehaviorCanJoinAllSpaces |
            Cocoa.NSWindowCollectionBehaviorStationary
        )
        
        # 创建内容视图
        content_view = Cocoa.NSView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(0, 0, size, size)
        )
        content_view.setWantsLayer_(True)
        # 背景全透明，不设置 content_view.layer().setBackgroundColor_
        content_view.layer().setBackgroundColor_(Cocoa.NSColor.clearColor().CGColor())
        
        self.window.setContentView_(content_view)
        
        if status == 'loading':
            self._add_spinner(content_view, size)
        else:
            self._add_image(content_view, size, status)
        
        self.window.makeKeyAndOrderFront_(None)
        
        # 如果不是 loading，1秒后自动消失
        if status != 'loading':
            self._schedule_hide(1.0)
    
    def _add_spinner(self, parent_view, size):
        """添加系统菊花"""
        spinner_size = 24
        x = (size - spinner_size) / 2
        y = (size - spinner_size) / 2
        
        self.spinner = Cocoa.NSProgressIndicator.alloc().initWithFrame_(
            Cocoa.NSMakeRect(x, y, spinner_size, spinner_size)
        )
        self.spinner.setStyle_(Cocoa.NSProgressIndicatorStyleSpinning)
        self.spinner.setControlSize_(Cocoa.NSControlSizeSmall)  # 小号
        self.spinner.setIndeterminate_(True)
        self.spinner.startAnimation_(None)
        
        # 设置白色
        if hasattr(self.spinner, 'setAppearance_'):
            self.spinner.setAppearance_(
                Cocoa.NSAppearance.appearanceNamed_(Cocoa.NSAppearanceNameVibrantDark)
            )
        
        parent_view.addSubview_(self.spinner)
    
    def _add_image(self, parent_view, size, status: str):
        """添加图片"""
        # 获取图片路径
        if status == 'success':
            image_path = get_resource_path('success.png')
        else:
            image_path = get_resource_path('error.png')
        
        if not os.path.exists(image_path):
            print(f"图标文件不存在: {image_path}")
            return
        
        image = Cocoa.NSImage.alloc().initWithContentsOfFile_(image_path)
        if not image:
            print(f"无法加载图标: {image_path}")
            return
        
        img_size = 24
        x = (size - img_size) / 2
        y = (size - img_size) / 2
        
        self.image_view = Cocoa.NSImageView.alloc().initWithFrame_(
            Cocoa.NSMakeRect(x, y, img_size, img_size)
        )
        self.image_view.setImage_(image)
        self.image_view.setImageScaling_(Cocoa.NSImageScaleProportionallyUpOrDown)
        
        parent_view.addSubview_(self.image_view)
    
    def _update_status(self, status: str):
        """更新状态（从 loading 切换）"""
        if not self.window:
            return
        
        content_view = self.window.contentView()
        size = content_view.frame().size.width
        
        # 移除 spinner
        if self.spinner:
            self.spinner.stopAnimation_(None)
            self.spinner.removeFromSuperview()
            self.spinner = None
        
        # 添加新图片
        self._add_image(content_view, size, status)
        
        # 1秒后消失
        self._schedule_hide(1.0)
    
    def _schedule_hide(self, delay: float):
        """延迟隐藏"""
        def hide_after_delay():
            time.sleep(delay)
            self._ensure_main_thread(self._hide_window)
        
        threading.Thread(target=hide_after_delay, daemon=True).start()
    
    def _hide_window(self):
        """隐藏窗口"""
        if self.spinner:
            self.spinner.stopAnimation_(None)
            self.spinner = None
        
        if self.window:
            self.window.orderOut_(None)
            self.window = None
        
        self.image_view = None


# 全局实例
status_overlay = StatusOverlay()
