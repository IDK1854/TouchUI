"""
Always-on-top 'Home' overlay — bottom-right of 7-inch display.
Uses tkinter with aggressive keep-alive.
"""
import tkinter as tk
import ctypes
import ctypes.wintypes
import threading
import urllib.request

ctypes.windll.shcore.SetProcessDpiAwareness(2)

TARGET_X = 3840
TARGET_W = 1024
TARGET_H = 600
BTN_SIZE = 68
BTN_X = TARGET_X + TARGET_W - BTN_SIZE - 10
BTN_Y = TARGET_H - BTN_SIZE - 10

API = "http://127.0.0.1:8000/api/minimize-active"
user32 = ctypes.windll.user32


def call_minimize():
    try:
        req = urllib.request.Request(API, method="POST")
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"[overlay] {e}")


def main():
    root = tk.Tk()
    root.title("TouchUI Home")
    root.geometry(f"{BTN_SIZE}x{BTN_SIZE}+{BTN_X}+{BTN_Y}")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.4)
    root.configure(bg="#1e1e22")

    canvas = tk.Canvas(root, width=BTN_SIZE, height=BTN_SIZE, bg="#1e1e22",
                       highlightthickness=0, bd=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    def draw(bg="#1e1e22", fg="white"):
        canvas.delete("all")
        # Background rounded rect (approximate with filled rect)
        canvas.create_rectangle(0, 0, BTN_SIZE, BTN_SIZE, fill=bg, outline="")

        cx, cy = BTN_SIZE // 2, BTN_SIZE // 2
        # House roof
        canvas.create_polygon(
            cx, cy - 18,
            cx - 22, cy + 2,
            cx + 22, cy + 2,
            fill=fg, outline=""
        )
        # House body
        canvas.create_rectangle(cx - 14, cy + 2, cx + 14, cy + 22, fill=fg, outline="")
        # Door
        canvas.create_rectangle(cx - 5, cy + 10, cx + 5, cy + 22, fill=bg, outline="")

    draw()

    def on_enter(e):
        root.attributes("-alpha", 0.95)
        draw(bg="#0A84FF", fg="white")

    def on_leave(e):
        root.attributes("-alpha", 0.4)
        draw()

    def on_click(e):
        draw(bg="#0060cc", fg="white")
        root.update_idletasks()
        threading.Thread(target=call_minimize, daemon=True).start()
        root.after(200, lambda: draw(bg="#0A84FF", fg="white"))

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_click)

    # Aggressively keep on top and in position
    def keep_alive():
        try:
            # Apply NOACTIVATE to Overlay to prevent game minimize
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            if not hwnd: hwnd = root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if not (ex_style & WS_EX_NOACTIVATE):
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE)

            # Apply NOACTIVATE to Edge browser TouchUI window
            def enum_cb(h, _):
                if user32.IsWindowVisible(h):
                    length = user32.GetWindowTextLengthW(h)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(h, buf, length + 1)
                        if "TouchUI" in buf.value and "TouchUI Home" not in buf.value:
                            style = user32.GetWindowLongW(h, GWL_EXSTYLE)
                            if not (style & WS_EX_NOACTIVATE):
                                user32.SetWindowLongW(h, GWL_EXSTYLE, style | WS_EX_NOACTIVATE)
                return True
            
            CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(CMPFUNC(enum_cb), 0)

            fg = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(fg)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg, buf, length + 1)
            
            is_home = ("TouchUI" in buf.value) and ("TouchUI Home" not in buf.value)
            
            if is_home:
                root.withdraw()
            else:
                if root.state() == 'withdrawn':
                    root.deiconify()
                root.attributes("-topmost", True)
                root.lift()
                try:
                    user32.SetWindowPos(hwnd, -1, BTN_X, BTN_Y, BTN_SIZE, BTN_SIZE, 0x0040 | 0x0010) # NOACTIVATE
                except Exception:
                    pass
        except tk.TclError:
            return  # window destroyed
        root.after(1000, keep_alive)

    root.after(1000, keep_alive)
    root.mainloop()


if __name__ == "__main__":
    main()
