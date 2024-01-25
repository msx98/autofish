from enum import Enum
from typing import *
from PIL import ImageGrab, Image
import win32api, win32con
import win32com.client
import time
import sys
import pytesseract
import numpy as np
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
shell = win32com.client.Dispatch("WScript.Shell")
shell.AppActivate("FiveM")
VK_TB = 0x74
VK_FISH = 0x75

DEBUG_COUNTER = 0
def printd(s):
    global DEBUG_COUNTER
    nice_date = time.strftime("%H:%M:%S", time.localtime())
    print(f"{DEBUG_COUNTER}, {nice_date}: {s}")


def take_screenshot():
    ss = ImageGrab.grab()
    # fetch the screen shot
    return ss


def select_chat_box(ss):
    # select the chat box
    chat_box = ss.crop((0, 50, 800, 300))
    return chat_box


def show_image_in_window(image):
    # show the image in a window
    image.show()


def click(x,y):
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)

def click_fish():
    printd("fishing")
    win32api.keybd_event(VK_FISH, win32api.MapVirtualKey(VK_FISH, 0), 0, 0)
    time.sleep(0.08)
    win32api.keybd_event(VK_FISH, win32api.MapVirtualKey(VK_FISH, 0), win32con.KEYEVENTF_KEYUP, 0)

def click_tb():
    printd("throwing back")
    win32api.keybd_event(VK_TB, win32api.MapVirtualKey(VK_TB, 0), 0, 0)
    time.sleep(0.08)
    win32api.keybd_event(VK_TB, win32api.MapVirtualKey(VK_TB, 0), win32con.KEYEVENTF_KEYUP, 0)


def parse_message(line: str) -> Tuple[str, str, Optional[str], Optional[float]]:
    # parse into: (time, type, fish type?, weight?)
    def parse_fish_type() -> Optional[Tuple[str, str, str, float]]:
        # [HH:MM:SS] You've caught a <number> lb <fish name>. Use /throwback to release the fish
        try:
            time = None# line.split(" ")[0]
            s = line.split("caught a ")[1]
            weight = float(s.split(" ")[0].replace(",",""))
            fish = " ".join(s.split(" ")[2:]).split(".")[0].split(",")[0] # remove weight, lb/Ib from beginning, then get fish name
            return (time, "caught", fish, weight)
        except:
            return None
    def parse_inv_full() -> Optional[Tuple[None, str, None, None]]:
        # [HH:MM:SS] Your inventory is full.
        try:
            #time = line.split(" ")[0]
            assert "inventory is full" in line
            return (None, "inv_full", None, None)
        except:
            return None
    def parse_already_fishing() -> Optional[Tuple[None, str, None, None]]:
        # [HH:MM:SS] You're already fishing.
        try:
            #time = line.split(" ")[0]
            assert "already fishing" in line
            return (None, "already_fishing", None, None)
        except:
            return None
    return (
        parse_fish_type() or
        parse_inv_full() or
        parse_already_fishing() or
        None
    )


def extract_messages(image) -> List[Tuple[Optional[str], str, Optional[str], Optional[float]]]:
    def parse_raw_text(raw_text):
        lines = [x for x in raw_text.split("\n") if x]
        parsed = [parse_message(x) for x in lines]
        valid = [x for x in parsed if x]
        return set(valid)
    chat_box = np.array(image.crop((0, 50, 800, 300)))
    #dist_from_red = 255 - chat_box[:,:,0]
    dist_from_red = np.sqrt(np.sum((chat_box - [190,12,14]) ** 2, axis=2))
    dist_from_blue = np.sqrt(np.sum((chat_box - [54,208,255]) ** 2, axis=2))
    dist_from_black = np.sqrt(np.sum((chat_box - [0,0,0]) ** 2, axis=2))
    blue_mask = np.uint8(((dist_from_blue <= 60) | (dist_from_black < 2)) * 255)
    red_mask = np.uint8(((dist_from_red <= 70) | (dist_from_black < 2)) * 255)
    #Image.fromarray(np.uint8(mask)).convert('RGB').show()
    blue_text = pytesseract.image_to_string(blue_mask, lang="eng")
    red_text = pytesseract.image_to_string(red_mask, lang="eng")
    valid = list(parse_raw_text(blue_text) | parse_raw_text(red_text))
    return valid


class FishingBot:
    def __init__(self):
        self.last_click = time.time()
        self.messages = []
    
    def react(self, message: Tuple[Optional[str], str, Optional[str], Optional[float]]):
        ts, msg_type, fish_type, weight = message
        if msg_type == "caught":
            DONT_WANT = 999999999
            DEFAULT_MIN = 100
            throwback = {
                # throw back any fish weighing less than this
                # if unspecified, keep
                "sunfish": DONT_WANT,
                "catfish": DONT_WANT,
            }
            should_throwback = weight < throwback.get(fish_type, DEFAULT_MIN)
            if should_throwback:
                click_tb()
                return True
            else:
                pass
        elif msg_type == "inv_full":
            # maybe send a message on telegram at some point
            pass
        else:
            pass
        return False

    def update(self, messages):
        messages_to_react_to = []
        for message in messages:
            if message not in self.messages:
                messages_to_react_to.append(message)
        reacted = False
        for message in reversed(messages_to_react_to):
            if self.react(message):
                reacted = True
        # now truncate to last 100 messages
        self.messages += messages_to_react_to
        self.messages = self.messages[-100:]
        printd(f"messages to react to: {messages_to_react_to}, did i react? {reacted}")
        if not messages_to_react_to:
            click_fish()


def main():
    #time.sleep(5)
    global DEBUG_COUNTER
    bot = FishingBot()
    is_enabled = False
    while True:
        is_enabled = is_enabled ^ win32api.GetAsyncKeyState(win32con.VK_CAPITAL)
        if is_enabled:
            printd("enabled. running")
            ss = take_screenshot()
            valid_messages = extract_messages(ss)
            printd(f"messages: {valid_messages}")
            bot.update(valid_messages)
        else:
            printd("disabled. waiting")
        time.sleep(2)
        DEBUG_COUNTER += 1


if __name__ == "__main__":
    main()