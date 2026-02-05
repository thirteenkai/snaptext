"""
配置管理模块
"""
import json
import os
from pathlib import Path

class Config:
    """应用配置管理"""
    
    # 默认配置
    DEFAULTS = {
        "port": 9999,
        "language": "auto",  # auto, zh, en, ja, ko
        "mode": "accurate",  # fast, accurate
        "launch_at_login": False,
        "silent_mode": True,  # 静默模式（通知而非弹窗）
        "hotkey": "<cmd>+<shift>+o",  # 默认截图快捷键 (pynput格式)
        "history_limit": 20,
        "stats": {
            "today_count": 0,
            "total_count": 0,
            "last_date": ""
        }
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".snaptext"
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.json"
        self.log_file = self.config_dir / "service.log"
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self._load()
    
    def reload(self):
        """重新从磁盘加载配置"""
        self._load()
    
    def _load(self):
        """加载配置"""
        # 旧目录（用于迁移）
        self._old_config_dir = Path.home() / ".local_ocr"
        
        # 确保配置目录存在 (虽然__init__中已创建，但_migrate_old_config可能需要)
        self._ensure_config_dir()
        self._migrate_old_config()  # 迁移旧配置
        
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # 合并默认配置
                    config = self.DEFAULTS.copy()
                    config.update(saved)
                    self._config = config
                    return
            except Exception:
                pass
        self._config = self.DEFAULTS.copy()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _migrate_old_config(self):
        """从旧目录迁移配置（如果存在且新配置不存在）"""
        old_config_file = self._old_config_dir / "config.json"
        
        # 如果旧配置存在且新配置不存在，执行迁移
        if old_config_file.exists() and not self.config_file.exists():
            try:
                import shutil
                shutil.copy(old_config_file, self.config_file)
                print(f"已迁移旧配置: {old_config_file} -> {self.config_file}")
            except Exception as e:
                print(f"迁移配置失败: {e}")
    
    def _load_config(self) -> dict:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # 合并默认配置
                    config = self.DEFAULTS.copy()
                    config.update(saved)
                    return config
            except Exception:
                pass
        return self.DEFAULTS.copy()
    
    def save(self):
        """保存配置"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
    
    @property
    def port(self) -> int:
        return self._config.get("port", 9999)
    
    @port.setter
    def port(self, value: int):
        self._config["port"] = value
        self.save()
    
    @property
    def language(self) -> str:
        return self._config.get("language", "auto")
    
    @language.setter
    def language(self, value: str):
        self._config["language"] = value
        self.save()
    
    @property
    def mode(self) -> str:
        return self._config.get("mode", "accurate")
    
    @mode.setter
    def mode(self, value: str):
        self._config["mode"] = value
        self.save()
    
    @property
    def launch_at_login(self) -> bool:
        return self._config.get("launch_at_login", False)
    
    @launch_at_login.setter
    def launch_at_login(self, value: bool):
        self._config["launch_at_login"] = value
        self.save()
        # 实际设置开机启动
        self._set_launch_at_login(value)
    
    @property
    def silent_mode(self) -> bool:
        return self._config.get("silent_mode", True)
    
    @silent_mode.setter
    def silent_mode(self, value: bool):
        self._config["silent_mode"] = value
        self.save()
        
    @property
    def hotkey(self) -> str:
        return self._config.get("hotkey", self.DEFAULTS["hotkey"])
    
    @hotkey.setter
    def hotkey(self, value: str):
        self._config["hotkey"] = value
        self.save()

    
    def _set_launch_at_login(self, enable: bool):
        """实际设置开机启动（通过 LaunchAgent）"""
        import sys
        
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        plist_path = launch_agents_dir / "com.snaptext.ocr.plist"
        
        # 获取应用路径
        if getattr(sys, 'frozen', False):
            # 打包后的应用
            # sys.executable 指向 MacOS/SnapText (二进制)
            # 我们需要指向 SnapText.app (Bundle)
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            if app_path.endswith('.app'):
                # 使用 open -a 命令启动 App
                program_args = [
                    "/usr/bin/open",
                    "-a",
                    app_path
                ]
            else:
                # 可能是单纯的二进制文件
                program_args = [sys.executable]
        else:
            # 开发时
            program_args = [
                "/usr/bin/python3",
                os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
            ]
        
        if enable:
            # 创建 LaunchAgent 目录
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建 ProgramArguments xml
            args_xml = ""
            for arg in program_args:
                args_xml += f"        <string>{arg}</string>\n"
            
            # 创建 plist 文件
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.snaptext.ocr</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/snaptext.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/snaptext.err.log</string>
</dict>
</plist>
'''
            try:
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
            except Exception as e:
                print(f"创建开机启动失败: {e}")
        else:
            # 删除 plist 文件
            try:
                if plist_path.exists():
                    plist_path.unlink()
            except Exception as e:
                print(f"移除开机启动失败: {e}")
    
    @property
    def history_limit(self) -> int:
        return self._config.get("history_limit", 20)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        from datetime import date
        stats = self._config.get("stats", self.DEFAULTS["stats"].copy())
        today = date.today().isoformat()
        
        # 如果是新的一天，重置今日计数
        if stats.get("last_date") != today:
            stats["today_count"] = 0
            stats["last_date"] = today
            self._config["stats"] = stats
            self.save()
        
        return stats
    
    def increment_count(self):
        """增加识别计数"""
        from datetime import date
        stats = self.get_stats()
        stats["today_count"] += 1
        stats["total_count"] += 1
        stats["last_date"] = date.today().isoformat()
        self._config["stats"] = stats
        self.save()


# 全局配置实例
config = Config()
