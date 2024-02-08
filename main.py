from utils import *
from parsing import *
shell.AppActivate("FiveM")


def should_throwback(fish_type, fish_weight):
    DONT_WANT = 999999999
    DEFAULT_MIN = 150
    fish_type = fish_type.lower()
    throwback = {
        # throw back any fish weighing less than this
        # if unspecified, keep
        "sunfish": DONT_WANT,
        "catfish": DONT_WANT,
        "swordfish": DONT_WANT,
        "tuna": DONT_WANT,
        "mackerel": DONT_WANT,
        "sturgeon": DONT_WANT, # maybe 2000?
        "cod": DONT_WANT,
        "halibut": 100,
        "shark": 2000, # maybe dont want?
        "squid": 1000,
        "sailfish": 1000,
        "amberjack": 1000,
        "blue marlin": 2000,
        "moray eel": 100,
        "ray": 100,
    }
    return fish_weight < throwback.get(fish_type, DEFAULT_MIN)


class FishingBot:
    def __init__(self):
        self.reset_state()
        self.messages = []
    
    def reset_state(self):
        self.last_click = time.time()
        self.last_click_button = dict()
        self.state = State.INIT
    
    def step(self):
        prev_state = self.state
        self.click(VK_LOTTO, min_time_between_clicks=60*12)
        if prev_state == State.INIT:
            self.click(VK_BACKSPACE)
            self.state = State.FISHING
        if prev_state == State.FISHING:
            self.state = self.step_fishing()
        elif prev_state == State.LOOKING_AT_INVENTORY:
            self.state = self.step_inventory()
        elif prev_state == State.INVENTORY_FULL_FINAL:
            # nothing to do
            pass
        elif prev_state == State.UNDEFINED:
            self.click(VK_SHIFT, min_time_between_clicks=7.5) # in case we are dead
            pass

    def step_fishing(self):
        assert self.state == State.FISHING
        ss = take_screenshot()
        messages = extract_chat_messages(ss)
        messages_to_react_to = []
        next_state = State.FISHING
        for message in messages:
            if message in self.messages:
                continue
            messages_to_react_to.append(message)
        self.messages += messages_to_react_to
        self.messages = self.messages[-100:]
        printd(f"messages to react to: {messages_to_react_to}")
        for message in messages_to_react_to:
            ts, msg_type, fish_type, weight = message
            if msg_type == "inv_full":
                #self.click(VK_INV)
                #next_state = State.LOOKING_AT_INVENTORY
                next_state = State.INVENTORY_FULL_FINAL
                self.click(VK_FINFO, min_time_between_clicks=5)
                beep()
                break
            elif msg_type == "caught":
                with open("fishlog.txt", "a") as f:
                    f.write(str((time.time(), *message)) + "\n")
                if should_throwback(fish_type, weight):
                    self.click(VK_TB, min_time_between_clicks=5)
                next_state = State.FISHING
                self.click(VK_FINFO, min_time_between_clicks=5)
                break
            elif msg_type == "sea_monster":
                beep()
                self.click([VK_SHIFT, VK_S], click_length=10)
                next_state = State.UNDEFINED
                break
            elif msg_type == "infected":
                beep()
                self.click(VK_ADRENALINE, min_time_between_clicks=10)
                #next_state = State.UNDEFINED
                pass #break
            else:
                # ignore other messages
                pass
        if next_state == State.FISHING:
            self.click(VK_FISH, min_time_between_clicks=2.5)
            self.click(VK_SHIFT, min_time_between_clicks=10)
            self.click(VK_FINFO, min_time_between_clicks=5)
        return next_state

    def step_inventory(self):
        assert self.state == State.LOOKING_AT_INVENTORY
        print("iterating over fish")
        for i in range(20): # there are max 20 fish
            ss = take_screenshot()
            result = extract_finv_fish(ss)
            print(f"entry {i}: {result}")
            if result is None:
                # probably emptied everything?
                beep()
                self.click(VK_BACKSPACE)
                return State.UNDEFINED
            else:
                _, _, fish_type, weight = result
                if should_throwback(fish_type, weight):
                    print(f"throwing back {fish_type} weighing {weight}")
                    self.click(VK_ENTER)
                    self.click(VK_BACKSPACE)
                    return State.FISHING
                else:
                    # keep fish
                    print(f"keeping {fish_type}")
                    self.click(VK_DOWN)
        beep()
        self.click(VK_BACKSPACE) # gone over all fish, nothing to throw back
        return State.INVENTORY_FULL_FINAL
    
    def click(self, key, *, blocking=False, click_length:float=0.08, min_time_between_clicks:float=1):
        if isinstance(key, (list, tuple,)):
            key = tuple(key)
        last_click = self.last_click_button.get(key, 0)
        next_allowed_click = last_click + min_time_between_clicks
        time_until_click = next_allowed_click - time.time()
        if time_until_click > 0:
            if blocking:
                time.sleep(time_until_click)
            else:
                return
        click_keyboard(key, click_length)
        click_time = time.time()
        self.last_click = click_time
        self.last_click_button[key] = click_time


def main():
    #time.sleep(5)
    global DEBUG_COUNTER
    bot = FishingBot()
    is_enabled_next = None
    is_enabled = False
    while True:
        is_enabled_next = is_enabled ^ win32api.GetAsyncKeyState(win32con.VK_DELETE)
        if is_enabled_next != is_enabled:
            if is_enabled_next:
                printd(f"enabled. running, state is {bot.state}")
                beep(freq=3500)
            else:
                printd("disabled. waiting")
                beep(freq=2000)
        is_enabled = is_enabled_next
        if is_enabled:
            printd(f"enabled. running, state is {bot.state}")
            bot.step()
        else:
            bot.reset_state()
        time.sleep(0.1)
        DEBUG_COUNTER += 1


if __name__ == "__main__":
    main()