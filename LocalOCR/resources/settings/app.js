// 全局变量
let KEY_MAP = {
    ' ': 'Space',
    'ArrowUp': 'Up',
    'ArrowDown': 'Down',
    'ArrowLeft': 'Left',
    'ArrowRight': 'Right',
    'Enter': 'Enter',
    'Backspace': 'Backspace',
    'Escape': 'Esc',
    'Tab': 'Tab',
    'Delete': 'Delete',
    'CapsLock': 'CapsLock',
    '/': '/',
    '\\': '\\',
    '[': '[',
    ']': ']',
    '-': '-',
    '=': '=',
    '.': '.',
    ',': ',',
    '`': '`',
    ';': ';',
    "'": "'",
};

// 页面加载完成后
window.addEventListener('DOMContentLoaded', async () => {
    // 侧边栏切换
    setupNavigation();

    // 等待 pywebview API 准备就绪
    if (window.pywebview) {
        initApp();
    } else {
        window.addEventListener('pywebviewready', initApp);
    }
});

function setupNavigation() {
    const items = document.querySelectorAll('.sidebar-item');
    const pages = document.querySelectorAll('.page');

    items.forEach(item => {
        item.addEventListener('click', () => {
            // 移除所有 active
            items.forEach(i => i.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));

            // 激活当前
            item.classList.add('active');
            const targetId = item.dataset.target; // "general", "shortcuts", "about"
            const targetPage = document.getElementById(targetId);
            if (targetPage) {
                targetPage.classList.add('active');
            } else {
                console.error("Target page not found:", targetId);
            }
        });
    });
}

async function initApp() {
    // 获取当前配置
    try {
        const config = await window.pywebview.api.get_config();
        applyConfig(config);

        // 绑定事件
        bindEvents();

        // 切换到指定Tab
        if (window.pywebview.api.get_initial_tab) {
            const tab = await window.pywebview.api.get_initial_tab();
            if (tab) {
                switchTab(tab);
            }
        }

        // 初始化快捷键录制
        initHotkeys();
    } catch (e) {
        console.error("Failed to load config:", e);
    }
}

function switchTab(targetId) {
    const items = document.querySelectorAll('.sidebar-item');
    const pages = document.querySelectorAll('.page');

    items.forEach(i => i.classList.remove('active'));
    pages.forEach(p => p.classList.remove('active'));

    const item = document.querySelector(`.sidebar-item[data-target="${targetId}"]`);
    if (item) item.classList.add('active');

    const targetPage = document.getElementById(targetId);
    if (targetPage) targetPage.classList.add('active');
}

function applyConfig(config) {
    // 通用设置
    const launchCheck = document.getElementById('launch_at_login');
    if (launchCheck) launchCheck.checked = config.launch_at_login;

    // 端口 (span)
    const portSpan = document.getElementById('port');
    if (portSpan) portSpan.textContent = config.port;

    // 快捷键
    updateHotkeyDisplay(config.hotkey, true);
}

// Helper for About page links
function openUrl(url) {
    if (window.pywebview && window.pywebview.api.open_url) {
        window.pywebview.api.open_url(url);
    } else {
        console.log("Opening URL:", url);
    }
}

// Check Update
async function checkUpdate() {
    const btn = document.getElementById('btn-check-update');
    const originalText = btn.innerHTML;
    btn.innerHTML = 'Checking...';
    btn.disabled = true;

    try {
        const res = await window.pywebview.api.check_for_updates();

        if (res.error) {
            alert("检查失败: " + res.error);
        } else {
            const currentVer = "1.0.0";
            const latestVer = res.latest; // e.g. "1.5.6"

            if (compareVersions(latestVer, currentVer) > 0) {
                if (confirm(`发现新版本 v${latestVer}！\n当前版本 v${currentVer}\n\n是否前往下载？`)) {
                    openUrl(res.url);
                }
            } else {
                alert(`当前已是最新版本 (v${currentVer})`);
            }
        }
    } catch (e) {
        alert("Error: " + e);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function compareVersions(a, b) {
    // 简单的版本比较
    const pa = a.split('.');
    const pb = b.split('.');
    for (let i = 0; i < 3; i++) {
        const na = parseInt(pa[i] || 0);
        const nb = parseInt(pb[i] || 0);
        if (na > nb) return 1;
        if (na < nb) return -1;
    }
    return 0;
}

// Start Recording
function startRecording(e) {
    // Must prevent propagation to avoid immediate handling
    e.stopPropagation();

    const recorder = document.getElementById('hotkey_recorder');
    if (!recorder || recorder.classList.contains('recording')) return;

    recorder.classList.add('recording');
    // REMOVED: recorder.innerHTML = '<span class="placeholder">按下快捷键...</span>';
    // Visual cue that we are recording is the border color change via CSS (.recording)

    // Hide clear button while recording
    const clearBtn = document.getElementById('clear_hotkey');
    if (clearBtn) clearBtn.style.display = 'none';

    // 暂停热键监听 (Create lock file)
    if (window.pywebview && window.pywebview.api.set_hotkey_paused) {
        window.pywebview.api.set_hotkey_paused(true);
    }

    // 开始监听键盘
    activeModifiers.clear();
    document.addEventListener('keydown', onRecordingKeydown);
    document.addEventListener('keyup', onRecordingKeyup);

    // Global click to cancel recording if clicked outside
    document.addEventListener('click', onGlobalClickChange);
}

function onGlobalClickChange(e) {
    const recorder = document.getElementById('hotkey_recorder');
    if (recorder && !recorder.contains(e.target)) {
        cancelRecording();
    }
}

// Bind events
function bindEvents() {
    // 1. Hotkey Recorder
    const rec = document.getElementById('hotkey_recorder');
    if (rec) {
        rec.addEventListener('click', startRecording);
    }

    // 2. Update Button
    const updateBtn = document.getElementById('btn-check-update');
    if (updateBtn) {
        updateBtn.addEventListener('click', checkUpdate);
    }

    // 3. General Settings
    const launchCheck = document.getElementById('launch_at_login');
    if (launchCheck) {
        launchCheck.addEventListener('change', (e) => {
            window.pywebview.api.set_config('launch_at_login', e.target.checked);
        });
    }

    // 4. Silent Mode (Legacy/Removed, but keeping logic structure if needed)
    /*
    const silentCheck = document.getElementById('silent_mode');
    if (silentCheck) {
        silentCheck.addEventListener('change', (e) => {
            window.pywebview.api.set_config('silent_mode', e.target.checked);
        });
    }
    */
}

function initHotkeys() {
    // 权限跳转 (不再需要，隐藏)
    const warning = document.getElementById('permission_warning');
    if (warning) warning.style.display = 'none';
}

// 实时录制逻辑
let activeModifiers = new Set();

function onRecordingKeydown(e) {
    e.preventDefault();
    e.stopPropagation();

    const code = e.code;
    const key = e.key;
    const location = e.location; // 1=Left, 2=Right

    // 如果按下的是纯修饰键，更新实时显示但不结束录制
    if (key === 'Meta' || key === 'OS') { activeModifiers.add('command'); updateRealtimeDisplay(); return; }
    if (key === 'Control') { activeModifiers.add('control'); updateRealtimeDisplay(); return; }
    if (key === 'Alt') { activeModifiers.add('option'); updateRealtimeDisplay(); return; }
    if (key === 'Shift') { activeModifiers.add('shift'); updateRealtimeDisplay(); return; }

    // Build parts
    // 最终保存时以事件修饰键为准，避免误判（例如未按shift却显示）
    const parts = [];
    if (e.metaKey) parts.push('command');
    if (e.ctrlKey) parts.push('control');
    if (e.altKey) parts.push('option');
    if (e.shiftKey) parts.push('shift');
    const order = ['command', 'control', 'option', 'shift'];
    parts.sort((a, b) => order.indexOf(a) - order.indexOf(b));

    // Handle main key using code for better mapping if possible, or key
    if (code.startsWith('Key')) {
        char = code.slice(3).toLowerCase();
    } else if (code.startsWith('Digit')) {
        char = code.slice(5);
    } else {
        // Special case mapping
        if (key === ' ') char = 'space';
        else char = key.toLowerCase();
    }

    // Safety Check: Require Modifiers for non-function keys
    const isFunctionKey = /^f(1[0-2]|[1-9])$/i.test(char);
    if (activeModifiers.size === 0 && !isFunctionKey) {
        // Unsafe hotkey (single letter like 'o'), ignore or warn
        console.warn("Single key hotkeys are unsafe/ignored:", char);
        // Visual feedback could be shaking or showing text "Need Modifier"
        const recorder = document.getElementById('hotkey_recorder');
        recorder.innerHTML = '<span class="placeholder" style="color:red">需包含修饰键 (⌘/⌃/⌥)</span>';

        // Reset after short delay
        setTimeout(() => {
            if (recorder.classList.contains('recording')) {
                recorder.innerHTML = '<span class="placeholder">按下快捷键...</span>';
            }
        }, 1500);
        return; // Continue recording
    }

    parts.push(char);
    const raw = parts.join('+');

    // 停止录制 (Remove BOTH listeners to prevent KeyUp from clearing display)
    document.removeEventListener('keydown', onRecordingKeydown);
    document.removeEventListener('keyup', onRecordingKeyup);
    document.removeEventListener('click', onGlobalClickChange);

    // 恢复 UI
    const recorder = document.getElementById('hotkey_recorder');
    if (recorder) recorder.classList.remove('recording');

    // 恢复热键监听
    if (window.pywebview && window.pywebview.api.set_hotkey_paused) {
        window.pywebview.api.set_hotkey_paused(false);
    }

    // 更新显示
    updateHotkeyDisplay(parts, true);

    // 保存
    console.log("Saving hotkey:", raw);
    window.pywebview.api.set_config('hotkey', raw);

    // Clear modifiers set so it doesn't interfere if we start again
    activeModifiers.clear();
}

function onRecordingKeyup(e) {
    const key = e.key;
    let mod = null;
    if (key === 'Meta' || key === 'OS') mod = 'command';
    else if (key === 'Control') mod = 'control';
    else if (key === 'Alt') mod = 'option';
    else if (key === 'Shift') mod = 'shift';

    if (mod && activeModifiers.has(mod)) {
        activeModifiers.delete(mod);
        updateRealtimeDisplay();
    }
}

function updateRealtimeDisplay() {
    const parts = [...activeModifiers];
    const order = ['command', 'control', 'option', 'shift'];
    parts.sort((a, b) => order.indexOf(a) - order.indexOf(b));
    updateHotkeyDisplay(parts, false);
}

function updateHotkeyDisplay(input, showClear = false) {
    const container = document.getElementById('hotkey_recorder');
    const oldClear = document.getElementById('clear_hotkey');
    if (oldClear) oldClear.remove();

    if (!container) return;

    container.innerHTML = '';

    // Check empty
    if (!input || (Array.isArray(input) && input.length === 0)) {
        container.innerHTML = '<span class="placeholder">点击录制...</span>';
        return;
    }

    // Normalize input to parts array
    let parts = [];
    if (Array.isArray(input)) {
        parts = input;
    } else if (typeof input === 'string') {
        const raw = input.toLowerCase().replace(/\s/g, '');
        if (raw) parts = raw.split('+');
    }

    // Render Keys
    parts.forEach(p => {
        const k = document.createElement('kbd');
        k.className = 'hotkey-key';
        k.textContent = getSymbol(p);
        container.appendChild(k);
    });

    // Add Clear Button
    if (showClear) {
        const xBtn = document.createElement('div');
        xBtn.id = 'clear_hotkey';
        xBtn.className = 'clear-btn';
        xBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;

        xBtn.onclick = (e) => {
            e.stopPropagation();
            updateHotkeyDisplay([]);
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.set_config('hotkey', '');
            }
        };
        container.appendChild(xBtn);
    }
}

function getSymbol(key) {
    if (!key) return '';
    switch (key.toLowerCase()) {
        case 'command': case 'cmd': return '⌘';
        case 'control': case 'ctrl': return '⌃';
        case 'option': case 'opt': case 'alt': return '⌥';
        case 'shift': return '⇧';
        case 'enter': return '↵';
        case 'space': return '␣';
        case 'backspace': return '⌫';
        case 'delete': return '⌦';
        case 'escape': case 'esc': return '⎋';
        case 'up': return '↑';
        case 'down': return '↓';
        case 'left': return '←';
        case 'right': return '→';
        default: return key.toUpperCase();
    }
}

function cancelRecording() {
    activeModifiers.clear();
    document.removeEventListener('keydown', onRecordingKeydown);
    document.removeEventListener('keyup', onRecordingKeyup);

    const recorder = document.getElementById('hotkey_recorder');
    // Just reload page to restore state, easiest way
    window.location.reload();
}

// 供后端调用的回调
window.onHotkeyRecorded = function (friendly, raw) {
    // Legacy support, mostly unused now as front-end handles recording
    // But if backend sends hotkey string (like "cmd+shift+s")
    updateHotkeyDisplay(raw, true);
};

window.onPermissionCheck = function (authorized) {
    // No-op
};
