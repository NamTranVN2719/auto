import sys
sys.path.insert(0, "./library")
import pyscreeze
import pyautogui
import cv2
import numpy as np
import time
import os
import ctypes
import colorama
from colorama import Fore, Style, init
# Windows API Constants
MOUSEEVENTF_MOVE = 0x0001
SCAN_SIDE_RANGE = 200 
SCAN_STEP = 5 
LOOP_INTERVAL = 0.01 # Constant fast speed

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

def move_mouse_hard(x, y):
    extra = ctypes.c_ulong(0)
    ii_ = MOUSEINPUT(int(x), int(y), 0, MOUSEEVENTF_MOVE, 0, ctypes.pointer(extra))
    command = INPUT(0, ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

def get_current_diff(template_gray, region):
    screenshot = pyautogui.screenshot(region=region)
    frame = np.array(screenshot)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return np.mean(cv2.absdiff(template_gray, frame_gray))

def get_dynamic_step(diff):
    """
    Adjusts the pixel jump distance based on markers.
    The lower the diff, the smaller the jump.
    """
    if diff >= 120: return 70  # Large jumps
    if diff >= 100:  return 48
    if diff >= 90:  return 38
    if diff >= 80:  return 20
    if diff >= 70:  return 15
    if diff >= 50:  return 15   # Tiny crawling steps
    return 1

def find_lowest_diff(template_gray, region, current_diff):
    best_diff = current_diff
    best_offset_from_start = 0
    move_mouse_hard(-SCAN_SIDE_RANGE, 0)
    current_relative_pos = -SCAN_SIDE_RANGE
    total_sweep_dist = SCAN_SIDE_RANGE * 2
    
    for _ in range(0, total_sweep_dist, SCAN_STEP):
        move_mouse_hard(SCAN_STEP, 0)
        current_relative_pos += SCAN_STEP
        time.sleep(0.005)
        d = get_current_diff(template_gray, region)
        color = ansi_color_for_diff(best_diff)

        print(f"\r{Fore.YELLOW}Scanning: Best Diff {color}{best_diff:.4f}{Style.RESET_ALL} at offset {Fore.GREEN}{best_offset_from_start}px. {Style.RESET_ALL}",end="", flush=True)
        if d < best_diff:
            best_diff = d
            best_offset_from_start = current_relative_pos
            
    backtrack = -(current_relative_pos - best_offset_from_start)
    move_mouse_hard(backtrack, 0)
    print(f"\r{Fore.GREEN}Locked: Best Diff {color}{best_diff:.4f}{Style.RESET_ALL} at offset {Fore.GREEN}{best_offset_from_start}px. {Style.RESET_ALL}",end="\n", flush=True)
    return best_diff, best_offset_from_start

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Initialize colorama to enable ANSI sequences on Windows
init()


def ansi_color_for_diff(diff: float) -> str:
    """
    Return an ANSI 24-bit color escape sequence that maps `diff` on the
    range 50 (green) -> 80 (red). Values >=80 are solid red; <=50 are solid green.
    """
    low, red_point = 20, 80.0
    # Solid red if at or above red_point
    if diff >= red_point:
        return "\x1b[38;2;255;0;0m"
    # Solid green if at or below low
    if diff <= low:
        return "\x1b[38;2;0;255;0m"
    # Interpolate between green (50) and red (80)
    clamped = max(min(diff, red_point), low)
    ratio = (clamped - low) / (red_point - low)
    r = int(255 * ratio)
    g = int(255 * (1.0 - ratio))
    return f"\x1b[38;2;{r};{g};0m"

def main():
    CAPTURE_REGION = (717, 0, 518, 284)
    template = cv2.imread("a.png")
    if template is None:
        print("Error: a.png not found")
        return

    template = cv2.resize(template, (CAPTURE_REGION[2], CAPTURE_REGION[3]))
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    try:
        print("Starting to find direction...")
        while True:
            diff_value = get_current_diff(template_gray, CAPTURE_REGION)
            color = ansi_color_for_diff(diff_value)
            print(f"\rDiff: {color}{diff_value:.2f}{Style.RESET_ALL}", end="", flush=True)

            if diff_value > 50:
                # Get the pixel step based on markers
                step = get_dynamic_step(diff_value)
                move_mouse_hard(step, 0)
            else:
                # Marker 50 or below reached
                print(f"\n{Fore.BLUE}Status: PRECISION RANGE (<50).{Style.RESET_ALL}")
                best_d, offset = find_lowest_diff(template_gray, CAPTURE_REGION, diff_value)
                return

            time.sleep(LOOP_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()