from typing import *
from consts import *
from enum import Enum
from PIL import ImageGrab, Image
import win32api, win32con
import win32com.client
import time
import sys
import pytesseract
import numpy as np
import colorsys
from matplotlib.colors import rgb_to_hsv
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
shell = win32com.client.Dispatch("WScript.Shell")


DEBUG_COUNTER = 0
def printd(s):
    global DEBUG_COUNTER
    nice_date = time.strftime("%H:%M:%S", time.localtime())
    print(f"{DEBUG_COUNTER}, {nice_date}: {s}")


def calc_dist_from_color(image, color, metric="hsv"):
    if metric == "l2":
        dist = np.sqrt(np.sum((image - color) ** 2, axis=2))
    elif metric == "hsv":
        image_hsv = rgb_to_hsv(image)[:,:,0:2]
        color_hsv = colorsys.rgb_to_hsv(*color)[0:2]
        dist = np.sqrt(np.sum((image_hsv - color_hsv) ** 2, axis=2))
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


def take_screenshot():
    return ImageGrab.grab()


def select_chat_box(ss):
    # select the chat box
    chat_box = ss.crop((0, 50, 800, 300))
    return chat_box


def click_keyboard(key, click_length=0.08):
    win32api.keybd_event(key, win32api.MapVirtualKey(key, 0), 0, 0)
    time.sleep(click_length)
    win32api.keybd_event(key, win32api.MapVirtualKey(key, 0), win32con.KEYEVENTF_KEYUP, 0)


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