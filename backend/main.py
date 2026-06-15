"""
TouchUI Backend — System controller for the 7-inch dashboard.
"""
import os
import subprocess
import time
import threading
import ctypes
import ctypes.wintypes
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import pythoncom
from pycaw.pycaw import AudioUtilities
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

# DPI Awareness — MUST be first
ctypes.windll.shcore.SetProcessDpiAwareness(2)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TARGET_X = 3840
TARGET_Y = 0
TARGET_W = 1024
TARGET_H = 600

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ── Cursor tracker ──
_last_main_cursor = [960, 540]
_cursor_lock = threading.Lock()


def _cursor_tracker():
    while True:
        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        if pt.x < TARGET_X:
            with _cursor_lock:
                _last_main_cursor[0] = pt.x
                _last_main_cursor[1] = pt.y
        time.sleep(0.1)


def _restore_cursor():
    with _cursor_lock:
        x, y = _last_main_cursor
    user32.SetCursorPos(x, y)


# ── Volume ──
def _get_volume():
    try:
        pythoncom.CoInitialize()
        return AudioUtilities.GetSpeakers().EndpointVolume.GetMasterVolumeLevelScalar()
    except Exception as e:
        print(f"[vol-get] {e}")
        return 0.5
    finally:
        try: pythoncom.CoUninitialize()
        except: pass


def _set_volume(scalar: float):
    try:
        pythoncom.CoInitialize()
        AudioUtilities.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(scalar, None)
    except Exception as e:
        print(f"[vol-set] {e}")
    finally:
        try: pythoncom.CoUninitialize()
        except: pass


# ── Window management ──
SW_RESTORE = 9
SW_MINIMIZE = 6
SWP_SHOWWINDOW = 0x0040
SWP_FRAMECHANGED = 0x0020
GWL_STYLE = -16
WS_THICKFRAME = 0x00040000

EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM
)

def _force_foreground(hwnd):
    fg_hwnd = user32.GetForegroundWindow()
    if fg_hwnd == hwnd:
        return
    if fg_hwnd:
        fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
        my_tid = kernel32.GetCurrentThreadId()
        if fg_tid != my_tid:
            user32.AttachThreadInput(my_tid, fg_tid, True)
            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.AttachThreadInput(my_tid, fg_tid, False)
            return
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)

def _find_windows_by_title(title_substr: str):
    results = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                if title_substr.lower() in buf.value.lower():
                    results.append(hwnd)
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return results


def _find_windows_by_process(proc_name: str):
    """Find visible top-level windows owned by a given process name, sorting by area to skip splash screens."""
    target_pids = set()
    for p in psutil.process_iter(['name', 'pid']):
        if proc_name.lower() in p.info['name'].lower():
            target_pids.add(p.info['pid'])

    if not target_pids:
        return []

    results = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in target_pids:
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                area = (rect.right - rect.left) * (rect.bottom - rect.top)
                
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                length = user32.GetWindowTextLengthW(hwnd)
                
                is_minimized = user32.IsIconic(hwnd)
                
                # Exclude obvious tooltips or tiny splash screens, but ALLOW minimized windows
                if (area > 10000 or is_minimized) and (length > 0 or 'Chrome_WidgetWin' in cls_buf.value):
                    sort_val = 9999999 if is_minimized else area
                    results.append((sort_val, hwnd))
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    
    # Sort by area descending, return the largest window (main window)
    results.sort(key=lambda x: x[0], reverse=True)
    return [hwnd for _, hwnd in results]


def _move_resize(hwnd, x, y, w, h):
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.4)
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_THICKFRAME)
    user32.SetWindowPos(hwnd, 0, x, y, w, h, SWP_SHOWWINDOW | SWP_FRAMECHANGED)
    user32.MoveWindow(hwnd, x, y, w, h, True)
    _force_foreground(hwnd)


# ── App configs ──
LOCAL = os.environ.get("LOCALAPPDATA", "")

apps = {
    "tradingview": {
        "name": "TradingView",
        "launch": r"explorer.exe shell:appsFolder\TradingView.Desktop_n534cwy3pjxzj!TradingView.Desktop",
        "find_by": "process",
        "find_value": "TradingView.exe",
    },
    "discord": {
        "name": "Discord",
        "launch": f"{LOCAL}\\Discord\\Update.exe --processStart Discord.exe",
        "find_by": "title",
        "find_value": "Discord",
    },
    "youtube": {
        "name": "YouTube",
        "launch": f'"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --app=https://www.youtube.com',
        "find_by": "process",
        "find_value": "msedge.exe",
    },
    "spotify": {
        "name": "Spotify",
        "launch": r"explorer.exe shell:appsFolder\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
        "find_by": "process",
        "find_value": "Spotify.exe",
    }
}


# ── API ──
@app.get("/api/volume")
def api_get_volume():
    return {"volume": round(_get_volume() * 100)}


@app.post("/api/volume/{level}")
def api_set_volume(level: int):
    level = max(0, min(100, level))
    _set_volume(level / 100.0)
    _restore_cursor()
    return {"volume": level}


@app.get("/api/system")
def api_system():
    return {"cpu": psutil.cpu_percent(interval=None), "ram": psutil.virtual_memory().percent}


@app.get("/api/media")
async def api_get_media():
    try:
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        session = manager.get_current_session()
        if not session:
            return {"playing": False, "title": "", "artist": ""}
        info = await session.try_get_media_properties_async()
        playback = session.get_playback_info()
        is_playing = playback.playback_status.value == 4 # 4=Playing, 5=Paused
        return {
            "playing": is_playing,
            "title": info.title,
            "artist": info.artist
        }
    except Exception as e:
        return {"playing": False, "title": "", "artist": "", "error": str(e)}


@app.post("/api/media/switch")
async def api_media_switch():
    try:
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        sessions = manager.get_sessions()
        current = manager.get_current_session()
        if not sessions:
            return {"status": "no sessions"}
        
        idx = -1
        for i, s in enumerate(sessions):
            if current and s.source_app_user_model_id == current.source_app_user_model_id:
                idx = i
                break
                
        next_idx = (idx + 1) % len(sessions)
        if current:
            await current.try_pause_async()
        await sessions[next_idx].try_play_async()
        return {"status": "switched"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/media/{action}")
async def api_media_action(action: str):
    try:
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        session = manager.get_current_session()
        if session:
            if action == "playpause":
                await session.try_toggle_play_pause_async()
            elif action == "next":
                await session.try_skip_next_async()
            elif action == "prev":
                await session.try_skip_previous_async()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/mixer")
def api_get_mixer():
    sessions_data = []
    try:
        pythoncom.CoInitialize()
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process:
                name = session.Process.name()
                pid = session.Process.pid
                vol = session.SimpleAudioVolume
                volume = round(vol.GetMasterVolume() * 100)
                muted = vol.GetMute()
                name = name.replace(".exe", "")
                
                # Exclude background/system apps
                excluded = {"ledkeeper2", "wallpaper32", "wallpaper64", "rtkuwp", "system sounds", "nvcontainer", "steamwebhelper"}
                if name.lower() in excluded:
                    continue
                
                sessions_data.append({
                    "pid": pid,
                    "name": name,
                    "volume": volume,
                    "muted": muted
                })
    except Exception as e:
        print(f"[mixer-get] {e}")
    finally:
        try: pythoncom.CoUninitialize()
        except: pass
        
    grouped = {}
    for s in sessions_data:
        name = s["name"]
        if name.lower() == "msedge": name = "Edge"
        elif name.lower() == "chrome": name = "Chrome"
        elif name.lower() == "spotify": name = "Spotify"
        
        # Capitalize first letter
        name = name[0].upper() + name[1:] if name else "Unknown"
        if name not in grouped:
            grouped[name] = {"pid": s["pid"], "name": name, "volume": s["volume"], "muted": s["muted"]}
            
    return {"sessions": list(grouped.values())}


@app.post("/api/mixer/{pid}/{level}")
def api_set_mixer(pid: int, level: int):
    level = max(0, min(100, level))
    try:
        pythoncom.CoInitialize()
        sessions = AudioUtilities.GetAllSessions()
        
        target_name = None
        for session in sessions:
            if session.Process and session.Process.pid == pid:
                target_name = session.Process.name()
                break
                
        if target_name:
            for session in sessions:
                if session.Process and session.Process.name() == target_name:
                    session.SimpleAudioVolume.SetMasterVolume(level / 100.0, None)
    except Exception as e:
        print(f"[mixer-set] {e}")
    finally:
        try: pythoncom.CoUninitialize()
        except: pass
        
        _restore_cursor()
    return {"status": "ok"}

@app.post("/api/mixer/{pid}/mute/{state}")
def api_set_mixer_mute(pid: int, state: int):
    try:
        pythoncom.CoInitialize()
        sessions = AudioUtilities.GetAllSessions()
        
        target_name = None
        for session in sessions:
            if session.Process and session.Process.pid == pid:
                target_name = session.Process.name()
                break
                
        if target_name:
            for session in sessions:
                if session.Process and session.Process.name() == target_name:
                    session.SimpleAudioVolume.SetMute(state, None)
    except Exception as e:
        print(f"[mixer-mute] {e}")
    finally:
        try: pythoncom.CoUninitialize()
        except: pass
        
    _restore_cursor()
    return {"status": "ok"}


@app.post("/api/launch/{app_id}")
def api_launch(app_id: str):
    if app_id not in apps:
        return {"error": "Unknown app"}

    info = apps[app_id]
    find_fn = _find_windows_by_process if info["find_by"] == "process" else _find_windows_by_title

    # First check if it's already running
    existing_hwnds = find_fn(info["find_value"])
    if existing_hwnds:
        _move_resize(existing_hwnds[0], TARGET_X, TARGET_Y, TARGET_W, TARGET_H)
        _restore_cursor()
        return {"status": "success", "message": f'{info["name"]} restored'}

    subprocess.Popen(info["launch"], shell=True)

    find_fn = _find_windows_by_process if info["find_by"] == "process" else _find_windows_by_title

    # For TradingView, sometimes the splash screen comes up first, then the main window
    # Wait up to 30 iterations for the largest window to actually be big enough
    for _ in range(30):
        time.sleep(0.5)
        hwnds = find_fn(info["find_value"])
        if hwnds:
            _move_resize(hwnds[0], TARGET_X, TARGET_Y, TARGET_W, TARGET_H)
            _restore_cursor()
            return {"status": "success", "message": f'{info["name"]} launched and moved'}

    _restore_cursor()
    return {"status": "partial", "message": f'{info["name"]} launched but window not found'}


@app.post("/api/minimize-active")
def api_minimize():
    # Instead of just taking the foreground window (which could be the overlay itself),
    # let's find any window on the second screen that isn't the browser or overlay and minimize it.
    
    # First find the browser window on that screen
    browser_hwnd = None
    for title_hint in ["localhost", "TouchUI", "127.0.0.1"]:
        hwnds = _find_windows_by_title(title_hint)
        for h in hwnds:
            # Skip the overlay window explicitly!
            length = user32.GetWindowTextLengthW(h)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(h, buf, length + 1)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(h, cls_buf, 256)
            
            if "TouchUI Home" in buf.value or cls_buf.value == "TkTopLevel":
                continue

            r = ctypes.wintypes.RECT()
            user32.GetWindowRect(h, ctypes.byref(r))
            if r.left >= TARGET_X - 200:
                browser_hwnd = h
                break
        if browser_hwnd:
            break

    # Now find the active app on the second screen and minimize it
    def minimize_apps_cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            r = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            
            # Check if window is largely on the second screen
            if r.left >= TARGET_X - 100:
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(max(length + 1, 1))
                user32.GetWindowTextW(hwnd, buf, length + 1)
                
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                try:
                    pname = psutil.Process(pid.value).name().lower()
                except:
                    pname = ""
                
                # Don't minimize the dashboard, overlay, or system UI
                if hwnd != browser_hwnd and "TouchUI" not in buf.value and cls_buf.value not in ("Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow", "TkTopLevel"):
                    # Exclude overlay by class name if we used WNDCLASS, or by title
                    if "python" not in pname and "TouchUI Home" not in buf.value:
                        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True

    user32.EnumWindows(EnumWindowsProc(minimize_apps_cb), 0)
    time.sleep(0.2)

    # Refocus the browser dashboard
    if browser_hwnd:
        _move_resize(browser_hwnd, TARGET_X, TARGET_Y, TARGET_W, TARGET_H)
        _restore_cursor()
        return {"status": "focused"}

    _restore_cursor()
    return {"status": "minimized"}


if __name__ == "__main__":
    psutil.cpu_percent(interval=None)
    threading.Thread(target=_cursor_tracker, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
