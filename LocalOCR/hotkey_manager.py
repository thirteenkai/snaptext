"""
Hotkey Manager - 使用 Quartz Event Tap 实现全局快捷键拦截
解决输入法"Í"泄漏问题，且比 ctypes 更稳定
"""
import Quartz
import Cocoa
from AppKit import NSEvent
import threading

# Key code mapping for Quartz/Carbon (ANSI)
KEY_MAP = {
    'A': 0, 'S': 1, 'D': 2, 'F': 3, 'H': 4, 'G': 5, 'Z': 6, 'X': 7, 'C': 8, 'V': 9,
    'B': 11, 'Q': 12, 'W': 13, 'E': 14, 'R': 15, 'Y': 16, 'T': 17, '1': 18, '2': 19,
    '3': 20, '4': 21, '6': 22, '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28,
    '0': 29, ']': 30, 'O': 31, 'U': 32, '[': 33, 'I': 34, 'P': 35, 'RETURN': 36, 'ENTER': 36,
    'L': 37, 'J': 38, "'": 39, 'K': 40, ';': 41, '\\': 42, ',': 43, '/': 44, 'N': 45,
    'M': 46, '.': 47, 'TAB': 48, 'SPACE': 49, '`': 50, 'DELETE': 51, 'ESC': 53,
    'F1': 122, 'F2': 120, 'F3': 99, 'F4': 118, 'F5': 96, 'F6': 97, 'F7': 98, 'F8': 100,
    'F9': 101, 'F10': 109, 'F11': 103, 'F12': 111
}

# Modifiers
kCGEventFlagMaskCommand = Quartz.kCGEventFlagMaskCommand
kCGEventFlagMaskShift = Quartz.kCGEventFlagMaskShift
kCGEventFlagMaskAlternate = Quartz.kCGEventFlagMaskAlternate # Option
kCGEventFlagMaskControl = Quartz.kCGEventFlagMaskControl
kCGEventFlagMaskSecondaryFn = Quartz.kCGEventFlagMaskSecondaryFn

# Debug Logger
# import os
# import datetime

import os
import datetime

def log(msg):
    try:
        log_path = os.path.expanduser("~/.snaptext/hotkey.log")
        with open(log_path, "a") as f:
            f.write(f"[{datetime.datetime.now()}] {msg}\n")
    except:
        pass

class HotkeyManager:
    def __init__(self, callback):
        self.callback = callback
        self.tap = None
        self.runLoopSource = None
        self.target_key_code = None
        self.target_modifiers = 0
        self.lock = threading.Lock()
        self.paused = False
        log("HotkeyManager init")
        
    def pause(self):
        """暂停热键监听"""
        with self.lock:
            self.paused = True
            log("HotkeyManager PAUSED")

    def resume(self):
        """恢复热键监听"""
        with self.lock:
            self.paused = False
            log("HotkeyManager RESUMED")
        
    def set_hotkey(self, hotkey_str):
        log(f"set_hotkey called: {hotkey_str}")
        if not hotkey_str:
            # 清空快捷键：禁用并移除现有事件 Tap
            with self.lock:
                self.target_key_code = None
                self.target_modifiers = 0
                if self.tap:
                    try:
                        Quartz.CGEventTapEnable(self.tap, False)
                    except Exception:
                        pass
                    if self.runLoopSource:
                        try:
                            Quartz.CFRunLoopRemoveSource(Quartz.CFRunLoopGetCurrent(), self.runLoopSource, Quartz.kCFRunLoopCommonModes)
                        except Exception:
                            pass
                        self.runLoopSource = None
                    self.tap = None
                log("Hotkey cleared and event tap removed")
            return True
            
        mods, code = self._parse_hotkey(hotkey_str)
        if code is None:
            log(f"Invalid hotkey parse: {hotkey_str}")
            return
            
        # Safety Check: Reject single key hotkeys (mods=0) unless F-keys (codes 96-122 roughly)
        # Standard letters are 0-50 range.
        # Let's simple reject mods=0. Global single keys are aggressive.
        if mods == 0:
             # Exception for F-keys?
             # F1=122, F2=120... F12=111.
             # If user REALLY wants F1, allow it?
             # User issue is "O". "O" is code 31.
             is_f_key = code in [122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111]
             if not is_f_key:
                 log(f"Rejected unsafe single-key hotkey: {hotkey_str} (code={code})")
                 print(f"Refusing to set unsafe single-key global hotkey: {hotkey_str}")
                 return False

        with self.lock:
            self.target_key_code = code
            self.target_modifiers = mods
            
            # Clean up existing tap
            if self.tap:
                log("Disabling existing tap")
                Quartz.CGEventTapEnable(self.tap, False)
                if self.runLoopSource:
                    Quartz.CFRunLoopRemoveSource(Quartz.CFRunLoopGetCurrent(), self.runLoopSource, Quartz.kCFRunLoopCommonModes)
                    self.runLoopSource = None
                self.tap = None

            # Create new tap
            mask = Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
            
            self.tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap, 
                Quartz.kCGHeadInsertEventTap, 
                0, 
                mask, 
                self._event_callback, 
                None
            )
            
            if self.tap is None:
                log("FAILED to create event tap. Check Accessibility permissions!")
                print("Failed to create event tap. Check Accessibility permissions!")
                return False
            
            self.runLoopSource = Quartz.CFMachPortCreateRunLoopSource(None, self.tap, 0)
            # Ensure we attach to the MAIN run loop, not just the current one (though likely the same)
            Quartz.CFRunLoopAddSource(
                Quartz.CFRunLoopGetMain(), 
                self.runLoopSource, 
                Quartz.kCFRunLoopCommonModes
            )
            Quartz.CGEventTapEnable(self.tap, True)
            log(f"Quartz Hotkey set: {hotkey_str} (code={code}, flag={mods})")
            return True

    def _event_callback(self, proxy, type_, event, refcon):
        """Event Tap Callback"""
        try:
            if type_ == Quartz.kCGEventTapDisabledByTimeout:
                log("Tap disabled by timeout! Re-enabling...")
                Quartz.CGEventTapEnable(self.tap, True)
                return event
            
            if type_ == Quartz.kCGEventKeyDown:
                code = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
                flags = Quartz.CGEventGetFlags(event)
                
                if self.paused:
                    # Log only if debugging, otherwise too noisy
                    # log("Paused, ignoring event")
                    return event

                # Check for external recording lock (prevent greedy consumption when setting hotkey)
                lock_file = os.path.expanduser("~/.snaptext/recording_hotkey.lock")
                if os.path.exists(lock_file):
                    # log("Recorder Active - Passing event")
                    return event

                # Filter current flags to only interesting ones
                relevant_mask = (kCGEventFlagMaskCommand | 
                               kCGEventFlagMaskShift | 
                               kCGEventFlagMaskAlternate | 
                               kCGEventFlagMaskControl)
                current_relevant = flags & relevant_mask
                
                log(f"Key: {code}, Flags: {current_relevant} (Target: {self.target_key_code}, {self.target_modifiers})")
                
                if code == self.target_key_code:
                    if current_relevant == self.target_modifiers:
                        log("MATCH! Triggering & Suppressing")
                        if self.callback:
                             Cocoa.NSOperationQueue.mainQueue().addOperationWithBlock_(self.callback)
                        return None # Suppress
        except Exception as e:
            log(f"Callback Error: {e}")
            
        # Pass through
        return event

    def _parse_hotkey(self, hotkey_str):
        parts = hotkey_str.lower().replace(" ", "").split('+')
        if not parts:
            return 0, None
            
        key_part = parts[-1].upper()
        modifiers = 0
        
        for p in parts[:-1]:
            if p in ['cmd', 'command']: modifiers |= kCGEventFlagMaskCommand
            if p in ['ctrl', 'control']: modifiers |= kCGEventFlagMaskControl
            if p in ['opt', 'option', 'alt']: modifiers |= kCGEventFlagMaskAlternate
            if p in ['shift']: modifiers |= kCGEventFlagMaskShift
            
        key_code = KEY_MAP.get(key_part)
        return modifiers, key_code
        
    def friendly_format(self, hotkey_str):
        if not hotkey_str: return ""
        s = hotkey_str.lower()
        s = s.replace('command', '⌘').replace('cmd', '⌘')
        s = s.replace('control', '⌃').replace('ctrl', '⌃')
        s = s.replace('option', '⌥').replace('alt', '⌥')
        s = s.replace('shift', '⇧')
        return s.upper().replace('+', '')

# Singleton
hotkey_manager = None

def init_hotkey_manager(callback):
    global hotkey_manager
    hotkey_manager = HotkeyManager(callback)
    return hotkey_manager
