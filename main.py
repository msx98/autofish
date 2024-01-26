from utils import *
from parsing import *
shell.AppActivate("FiveM")


def should_throwback(fish_type, fish_weight):
    DONT_WANT = 999999999
    DEFAULT_MIN = 100
    throwback = {
        # throw back any fish weighing less than this
        # if unspecified, keep
        "sunfish": DONT_WANT,
        "catfish": DONT_WANT,
        "sturgeon": 2000,
        "swordfish": 1000,
        "sailfish": 500,
        "moray eel": 150,
        "shark": 1750,
        "amberjack": 200,
        "tuna": 2000,
        "mackerel": 200,
        "blue marlin": 2000,
    }
    return fish_weight < throwback.get(fish_type, DEFAULT_MIN)


class State(Enum):
    INIT = 0
    FISHING = 1
    LOOKING_AT_INVENTORY = 3
    INVENTORY_FULL_FINAL = 4
    UNDEFINED = 5


class FishingBot:
    def __init__(self):
        self.reset_state()
        self.messages = []
    
    def reset_state(self):
        self.last_click = time.time()
        self.state = State.INIT
    
    def step(self):
        prev_state = self.state
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
            # also nothing to do
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
                self.click(VK_INV)
                next_state = State.LOOKING_AT_INVENTORY
                break
            elif msg_type == "caught":
                if should_throwback(fish_type, weight):
                    self.click(VK_TB)
                next_state = State.FISHING
                break
            elif msg_type == "sea_monster":
                self.click(VK_S, click_length=20)
                next_state = State.UNDEFINED
                break
            elif msg_type == "infected":
                self.click(VK_ADRENALINE,min_time_between_clicks=10)
                #next_state = State.UNDEFINED
                pass #break
            else:
                # ignore other messages
                pass
        if next_state == State.FISHING:
            self.click(VK_FISH)
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
        self.click(VK_BACKSPACE) # gone over all fish, nothing to throw back
        return State.INVENTORY_FULL_FINAL
    
    def click(self, key, *, click_length:float=0.08, min_time_between_clicks:float=1):
        next_allowed_click = self.last_click + min_time_between_clicks
        time_until_click = next_allowed_click - time.time()
        if time_until_click > 0:
            time.sleep(time_until_click)
        click_keyboard(key, click_length)
        self.last_click = time.time()


def main():
    #time.sleep(5)
    global DEBUG_COUNTER
    bot = FishingBot()
    is_enabled = False
    while True:
        is_enabled = is_enabled ^ win32api.GetAsyncKeyState(win32con.VK_CAPITAL)
        if is_enabled:
            printd(f"enabled. running, state is {bot.state}")
            bot.step()
        else:
            printd("disabled. waiting")
            bot.reset_state()
        time.sleep(1)
        DEBUG_COUNTER += 1


if __name__ == "__main__":
    main()