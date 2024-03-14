from typing import *
from consts import *
from enum import Enum
from PIL import ImageGrab, Image
import win32api, win32con
import win32com.client
import time
import datetime
import sys
import pytesseract
import numpy as np
import colorsys
from matplotlib.colors import rgb_to_hsv
from threading import Thread
import threading
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
shell = win32com.client.Dispatch("WScript.Shell")


def sleep(seconds: float, interrupt_event: Optional[threading.Event] = None) -> bool:
    """
    sleeps until seconds pass OR interrupt_event is triggered
    returns True <-> interrupted
    """
    if interrupt_event is None:
        #print(f"No event is set")
        time.sleep(seconds)
        return False
    else:
        # wait_start = time.time()
        is_interrupted = interrupt_event.wait(timeout=seconds)
        # wait_end = time.time()
        # wait_elapsed = round(wait_end - wait_start, 2)
        # if not is_interrupted:
        #     print(f"Managed to wait for {wait_elapsed} seconds")
        # else:
        #     print(f"Interrupt event is set; waited for {wait_elapsed}")
        return is_interrupted


def convert_res(x0, y0, x1, y1):
    return (int(x0*(1280/1920)), int(y0*(720/1080)),
            int(x1*(1280/1920)), int(y1*(720/1080)))


DEBUG_COUNTER = 0
def printd(s):
    global DEBUG_COUNTER
    nice_date = time.strftime("%H:%M:%S", time.localtime())
    print(f"{DEBUG_COUNTER}, {nice_date}: {s}")


def beep(*, freq=2000, duration=500):
    win32api.Beep(freq, duration)


def calc_dist_from_color(image, color, metric="hsv"):
    if metric == "l2":
        dist = np.sqrt(np.sum((image - color) ** 2, axis=2))
    elif metric == "hsv":
        image_hsv = image[:,:,0:2]
        color_hsv = colorsys.rgb_to_hsv(*color)[0:2]
        dist = np.sqrt(np.sum((image_hsv - color_hsv) ** 2, axis=2))
    elif metric == "intensity":
        image_hsv = image[:,:,2]
        dist = image_hsv - color
    return dist


def calc_hsv_dist_from_color(image_hsv, color_hsv):
    # drop dimension 3:
    image_hsv_flat = image_hsv[:,:,:2]
    color_hsv = color_hsv[:2]
    # now calculate distance
    dist = np.sqrt(np.sum((image_hsv_flat - color_hsv) ** 2, axis=2))
    return dist


def calc_l2_dist_from_color(image, color):
    dist = np.sqrt(np.sum((image - color) ** 2, axis=2))
    return dist


def take_screenshot() -> Image.Image:
    return ImageGrab.grab()


def select_chat_box(ss):
    # select the chat box
    #chat_box = ss.crop((17,100,495,210))
    chat_box = ss.crop((17,45,495,210))
    return chat_box


def click_keyboard(keys, click_length=0.08, *, new_thread: bool = True):
    if isinstance(keys, int):
        keys = [keys]
    def do_click():
        for key in keys:
            win32api.keybd_event(key, win32api.MapVirtualKey(key, 0), 0, 0)
        time.sleep(click_length)
        for key in keys:
            win32api.keybd_event(key, win32api.MapVirtualKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)
    if new_thread:
        Thread(target=do_click).start()
    else:
        do_click()


def click_fish():
    printd("fishing")
    click_keyboard(VK_FISH)


def click_inv():
    printd("opening inventory")
    click_keyboard(VK_INV)


def click_inv_exit():
    printd("exiting inventory")
    click_keyboard(VK_BACKSPACE)


def click_tb():
    printd("throwing back")
    click_keyboard(VK_TB)


def click_down():
    printd("moving down")
    click_keyboard(VK_DOWN)


def click_mouse(x,y):
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
