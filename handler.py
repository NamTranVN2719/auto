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
        if hasattr(key, 'char') and key.char == 'p':
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
        if hasattr(key, 'char') and key.char == 'p':
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