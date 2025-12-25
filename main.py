from asyncio import subprocess
import sys, time
sys.path.insert(0, "./library")
import ctypes
import subprocess
from ctypes import wintypes
import pyscreeze
import pyautogui
import cv2
import numpy as np
import os
import colorama
from colorama import Fore, Style,init
# =======================
# WINDOW FOCUS (UNCHANGED)
# =======================
TARGET_TITLE = "OverField"
CAPTURE_REGION_loaded1 = (51, 1013, 13, 24)
CAPTURE_REGION_loaded2 = (0, 1020, 1920, 60)
def focus_window(title):
    user32 = ctypes.windll.user32
    SW_RESTORE = 9

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _get_window_text(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    found = {"hwnd": None}

    @EnumWindowsProc
    def _enum(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            text = _get_window_text(hwnd)
            if title.lower() in text.lower():
                user32.ShowWindow(hwnd, SW_RESTORE)
                time.sleep(0.1)
                user32.SetForegroundWindow(hwnd)
                found["hwnd"] = hwnd
                return False
        return True

    user32.EnumWindows(_enum, 0)
    return found["hwnd"]

focus_window(TARGET_TITLE)

# =======================
# HARD INPUT SETUP
# =======================
user32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
INPUT_MOUSE = 0

KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def detect_fps_from_screen(region, sample_time=0.5):
    last = None
    frames = 0
    start = time.perf_counter()

    while time.perf_counter() - start < sample_time:
        img = pyautogui.screenshot(region=region)
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

        if last is not None:
            if np.mean(cv2.absdiff(last, gray)) > 1:
                frames += 1

        last = gray
        time.sleep(0.001)

    fps = frames / sample_time if frames > 0 else 60
    fps = max(20, min(fps, 240))
    print(f"{Fore.CYAN}Detected FPS: {fps:.1f}{Style.RESET_ALL}")
    return fps

# Scan codes
SC_W = 0x11
SC_F = 0x21
SC_SHIFT = 0x2A
SC_ALT = 0x38
def get_current_diff(template_gray, region):
    screenshot = pyautogui.screenshot(region=region)
    frame = np.array(screenshot)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return np.mean(cv2.absdiff(template_gray, frame_gray))
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

def key_down(scan):
    inp = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(
            ki=KEYBDINPUT(0, scan, KEYEVENTF_SCANCODE, 0, None)
        )
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def key_up(scan):
    inp = INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(
            ki=KEYBDINPUT(0, scan, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, None)
        )
    )
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
loaded = cv2.imread("loaded.png")
loaded2 = cv2.imread("loaded2.png")
loaded2_gray = cv2.cvtColor(loaded2, cv2.COLOR_BGR2GRAY)
loaded_gray = cv2.cvtColor(loaded, cv2.COLOR_BGR2GRAY)
def click(x, y):
    user32.SetCursorPos(x, y)

    down = INPUT(
        type=INPUT_MOUSE,
        union=INPUT_UNION(
            mi=MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
        )
    )

    up = INPUT(
        type=INPUT_MOUSE,
        union=INPUT_UNION(
            mi=MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
        )
    )

    user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(down))
    user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(up))
def waitforloadingscreen():
    diff_value = get_current_diff(loaded_gray, CAPTURE_REGION_loaded1)
    diff_value2 = get_current_diff(loaded2_gray, CAPTURE_REGION_loaded2)
    if diff_value < 10:
        return 1
    if diff_value2 < 10:
        return 2
    return 0
def waitbeforeloading():
    diff_value1 = get_current_diff(loaded_gray, CAPTURE_REGION_loaded1)
    if diff_value1 < 10:
        return 1
    return 0
def waitaftercombat():
    diff_value2 = get_current_diff(loaded2_gray, CAPTURE_REGION_loaded2)
    if diff_value2 < 10:
        return 1
    return 0
# =======================
# MAIN LOOP (LOGIC SAME)
# =======================
a = 2
counter =0
GAME_REGION = (0, 0, 1920, 1080)
GAME_FPS = detect_fps_from_screen(GAME_REGION)
while True:
    start = time.perf_counter()
    counter+=1
    print(f"{Fore.CYAN}============== Starting automation loop #{counter} =============={Style.RESET_ALL}")
    timeoutt = time.perf_counter()
    restartloop= False
    while True:
        a = waitbeforeloading()
        if a==1:
            print(f"{Fore.GREEN}Menu loaded{Style.RESET_ALL}")
            break
    key_down(SC_W); time.sleep(2); key_up(SC_W)
    key_down(SC_F); time.sleep(0.2); key_up(SC_F)
    time.sleep(1)

    click(260, 800)
    time.sleep(1)

    key_down(SC_F); time.sleep(0.2); key_up(SC_F)

    time.sleep(1)
    key_down(SC_F); time.sleep(0.2); key_up(SC_F)
    time.sleep(2)
    #loading
    while True:
        a = waitforloadingscreen()
        if a==1:
            print(f"{Fore.YELLOW}Loading finished with anti-automation senario{Style.RESET_ALL}")
            process = subprocess.Popen(
                ["./python/python.exe", "automation.py",str(GAME_FPS)],
                cwd=os.path.dirname(__file__)
            )
            process.wait()
            break
        if a ==2:
            print(f"{Fore.GREEN}Loading finished with normal senario{Style.RESET_ALL}")
            time.sleep(2)
            click(960, 540)
            time.sleep(5)
            break
        time.sleep(1)
    time.sleep(0.5)
    key_down(SC_W)
    key_down(SC_SHIFT)
    while True:
        a = waitaftercombat()
        if a==1:
            print(f"\n{Fore.LIGHTGREEN_EX}Combat finished{Style.RESET_ALL}")
            break
        time.sleep(0.5)
    key_up(SC_W)
    key_up(SC_SHIFT)
    time.sleep(5)
    key_down(SC_W)
    time.sleep(3)
    key_up(SC_W)

    time.sleep(1)
    key_down(SC_F); time.sleep(1); key_up(SC_F)
    click(900, 200)

    key_down(SC_F); time.sleep(1); key_up(SC_F)
    click(900, 200)

    time.sleep(1)
    key_down(SC_ALT)
    time.sleep(0.3)
    click(1630, 84)
    time.sleep(1)
    click(1122, 666)
    time.sleep(1)
    key_up(SC_ALT)

    time.sleep(2)
    elapsed = time.perf_counter() - start
    print(f"{Fore.MAGENTA}>>>>>>>>>> Automation loop #{counter} completed in {elapsed:.2f} seconds <<<<<<<<<<{Style.RESET_ALL}")
