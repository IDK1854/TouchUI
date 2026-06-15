import pygetwindow as gw

def print_screens():
    # Note: pygetwindow currently relies on active windows to find monitors
    # For a robust way to get all Windows monitors in Python without extra heavy libraries:
    import ctypes
    user32 = ctypes.windll.user32
    
    monitors = []
    
    # Callback type
    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.wintypes.RECT), ctypes.c_double
    )
    
    def monitor_enum_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rect = lprcMonitor.contents
        monitors.append({
            "left": rect.left,
            "top": rect.top,
            "right": rect.right,
            "bottom": rect.bottom,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top
        })
        return 1
    
    # Needs wintypes.RECT
    import ctypes.wintypes
    user32.EnumDisplayMonitors(None, None, MonitorEnumProc(monitor_enum_callback), 0)
    
    print("\n=== Detected Monitors ===")
    for i, m in enumerate(monitors):
        print(f"Monitor {i+1}:")
        print(f"  Resolution: {m['width']}x{m['height']}")
        print(f"  X Offset (Left): {m['left']}")
        print(f"  Y Offset (Top):  {m['top']}\n")
    print("Use the 'X Offset' and 'Y Offset' of your 7-inch display to update TARGET_X and TARGET_Y in backend/main.py!")

if __name__ == "__main__":
    print_screens()
