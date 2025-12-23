import subprocess
import sys,os
import time
sys.path.insert(0, "./library")
from pynput import keyboard
import psutil
import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SC_W = 0x11
SC_F = 0x21
SC_SHIFT = 0x2A
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", INPUT_UNION),
    ]
TARGET_TITLE = "OverField"
def focus_own_cmd():
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return hwnd
    return None

def key_up(scan):
    inp = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(
            ki=KEYBDINPUT(0, scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, None)
        )
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
process = None
p_pressed = False
def exit_gracefully():
    focus_own_cmd()
def on_press(key):
    global process, p_pressed
    try:
        # Check if it's the P key using the vk (virtual key) attribute
        # This detects the physical P key regardless of modifiers (Shift, Ctrl, Alt, etc.)
        if hasattr(key, 'vk') and key.vk == 112:  # Virtual key 112 is P
            p_pressed = True
            if process:
                # Kill all child processes first
                try:
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.kill()
                    parent.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process.terminate()
                key_up(SC_W)
                key_up(SC_SHIFT)
                key_up(SC_F)
                exit_gracefully()
                print("Exitting...")
                sys.exit(0)
        # Also check char for compatibility if vk is not available
        elif hasattr(key, 'char') and key.char and key.char.lower() == 'p':
            p_pressed = True
            if process:
                # Kill all child processes first
                try:
                    parent = psutil.Process(process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.kill()
                    parent.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process.terminate()
                key_up(SC_W)
                key_up(SC_SHIFT)
                key_up(SC_F)
                exit_gracefully()
                print("Exitting...")
                sys.exit(0)
    except AttributeError:
        pass

def on_release(key):
    global process, p_pressed
    try:
        # Check if it's the P key being released
        if hasattr(key, 'vk') and key.vk == 112:  # Virtual key 112 is P
            p_pressed = False
        elif hasattr(key, 'char') and key.char and key.char.lower() == 'p':
            p_pressed = False
    except AttributeError:
        pass

# Start main.py
print("Script bắt đầu chạy nhấn P để dừng bất cứ lúc nào.")
i = 5
while i>=0:
    print("Script chạy sau ",i," giây...", end="\r", flush=True)
    time.sleep(1)
    i -= 1
print("\n")
process = subprocess.Popen(
    ["./python/python.exe", "main.py"],
    cwd=os.path.dirname(__file__)
)


# Listen for Shift + S
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()