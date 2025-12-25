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
import mss
def capture_screen_region(x, y, w, h):
    with mss.mss() as sct:
        img = np.array(sct.grab({
            "top": y,
            "left": x,
            "width": w,
            "height": h
        }))
    return img
# =======================
# FPS DETECTION & ADJUSTMENT
# =======================
def detect_fps():
    """
    Detect current game FPS using OpenCV's high-precision timing.
    Minimal overhead, very fast.
    """
    tick_frequency = cv2.getTickFrequency()
    frame_count = 0
    start_tick = cv2.getTickCount()
    
    # Sample for 0.3 seconds with OpenCV timing
    while True:
        frame_count += 1
        current_tick = cv2.getTickCount()
        elapsed_seconds = (current_tick - start_tick) / tick_frequency
        
        if elapsed_seconds >= 0.3:
            break
        time.sleep(0.001)  # Minimal sleep
    
    estimated_fps = frame_count / elapsed_seconds if elapsed_seconds > 0 else 60
    
    # Clamp to reasonable values
    estimated_fps = max(15, min(estimated_fps, 240))
    print(f"{Fore.CYAN}Detected FPS: {estimated_fps:.1f}{Style.RESET_ALL}")
    return estimated_fps

# Get FPS and calculate speed multiplier for dynamic steps
TARGET_FPS = 60

speed_multiplier = 1


# Windows API Constants
MOUSEEVENTF_MOVE = 0x0001
SCAN_SIDE_RANGE = 300 
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
    screenshot = capture_screen_region(*region)
    frame = np.array(screenshot)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    return np.mean(cv2.absdiff(template_gray, frame_gray))

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

FPS_SCALE = 1
def get_dynamic_step(diff):
    """
    Adjusts the pixel jump distance based on markers.
    The lower the diff, the smaller the jump.
    Scales with FPS for consistent movement across different framerates.
    """
    if diff >= 120: return 70 *FPS_SCALE  # Large jumps
    if diff >= 100:  return 60 *FPS_SCALE
    if diff >= 90:  return 50 *FPS_SCALE
    if diff >= 80:  return 40 *FPS_SCALE
    if diff >= 70:  return 30 *FPS_SCALE
    if diff >= 50:  return 20 *FPS_SCALE   # Tiny crawling steps
    return 1 *FPS_SCALE
ROTATE_STEP = 5
ROTATE_DELAY = 0.033
def rotate_to_offset(offset):
    step = ROTATE_STEP if offset > 0 else -ROTATE_STEP

    moved = 0
    while abs(moved) < abs(offset):
        move_mouse_hard(step, 0)
        moved += step
        time.sleep(ROTATE_DELAY)

def find_lowest_diff(template_gray, region, current_diff):
    time.sleep(0.2)
    best_diff = current_diff
    best_offset_from_start = 0
    
    # 1. Rotate 400 pixels to the left to start the scan
    START_OFFSET = -500
    SWEEP_DISTANCE = 600
    move_mouse_hard(START_OFFSET, 0)
    
    time.sleep(0.2)
    
    # Track position relative to where we started BEFORE the 400px jump
    current_relative_pos = START_OFFSET 
    
    # 2. Sweep 600 pixels to the right
    for _ in range(0, SWEEP_DISTANCE, SCAN_STEP):
        move_mouse_hard(SCAN_STEP, 0)
        current_relative_pos += SCAN_STEP
        time.sleep(0.033)
        
        d = get_current_diff(template_gray, region)
        
        if d < best_diff:
            best_diff = d
            best_offset_from_start = current_relative_pos

    # 3. Calculate how much we need to move to get back to the best match
    # 'backtrack' is the distance from our current end position to the best offset
    backtrack = best_offset_from_start - current_relative_pos
    
    color = ansi_color_for_diff(best_diff)
    print(f"\r{Fore.GREEN}Locked: Best Diff {color}{best_diff:.4f}{Style.RESET_ALL} at offset {Fore.GREEN}{best_offset_from_start}px. {Style.RESET_ALL}")

    if best_diff < 40:
        print(f"{Fore.GREEN}Target found, rotating back to target...{Style.RESET_ALL}")
        # Use your slow rotation function to return to the best match
        rotate_to_offset(backtrack)
        return best_diff
    else:
        print(f"{Fore.RED}Scan failed, returning to center...{Style.RESET_ALL}")
        rotate_to_offset(-current_relative_pos) # Return to the original starting point
        return best_diff

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
    template = cv2.imread("a3.png")
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
            # print(f"\rDiff: {color}{diff_value:.2f}{Style.RESET_ALL}", end="", flush=True)

            if diff_value >60:
                # Get the pixel step based on markers
                step = get_dynamic_step(diff_value)
                print(step,end="\r", flush=True)
                move_mouse_hard(step, 0)
                time.sleep(0.02)
            else:
                # Marker 50 or below reached
                print(f"\n{Fore.BLUE}Status: PRECISION RANGE (<50).{Style.RESET_ALL}")
                best_d = find_lowest_diff(template_gray, CAPTURE_REGION, diff_value)
                if best_d > 40:
                    print(f"{Fore.RED}Could find a better position. Retrying...{Style.RESET_ALL}")
                    continue
                return

            time.sleep(LOOP_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()