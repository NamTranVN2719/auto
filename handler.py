import subprocess
import sys,os
import time
sys.path.insert(0, "./library")
from pynput import keyboard
import psutil

process = None
p_pressed = False

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
time.sleep(5)  # Give user time to read the message
process = subprocess.Popen(
    ["./python/python.exe", "main.py"],
    cwd=os.path.dirname(__file__)
)


# Listen for Shift + S
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()