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
        "sailfish": 1000, "saitfish": 1000,
        "amberjack": 1000,
        "blue marlin": 2000,
        "moray eel": 100,
        "ray": 100,
    }
    return fish_weight < throwback.get(fish_type, DEFAULT_MIN)


import threading
class FishingBot:
    def __init__(self):
        self.state = State.DISABLED
        self.events: List[Event] = []
        self.events_lock: threading.Lock = threading.Lock()
        self.new_mask_lock: threading.Lock = threading.Lock()
        self.new_mask = False
        self.unread_events: int = 0
        self.tried_to_throw = None
        self.ignore_next_quit = False
        self.last_batch_reaction: datetime.datetime = datetime.datetime(1970, 1, 1, 1, 1, 1)
        self.extract_chat_events_loop()
    
    @property
    def state(self):
        return self._state

    @property
    def enabled(self):
        return self.state != State.DISABLED
    
    @state.setter
    def state(self, new_state: State):
        old_state = getattr(self, "_state", None)
        if new_state == old_state:
            return
        printd(f"old_state={old_state} --> new_state={new_state}")
        self._state = new_state
        if new_state in {State.INIT, State.DISABLED}:
            self.last_click = time.time()
            self.last_click_button = dict()
            if new_state == State.INIT: #enabled
                beep(freq=3500, duration=500)
            else: #disabled
                beep(freq=1500, duration=500)
    
    @enabled.setter
    def enabled(self, value: bool):
        self.state = State.INIT if value else State.DISABLED
        self.tried_to_throw = None
    
    def toggle(self):
        enabled = not self.enabled
        self.enabled = enabled

    def step(self):
        if self.state != State.DISABLED:
            self.click(VK_LOTTO, min_time_between_clicks=60*12)
        state = self.state
        next_state = state
        if state != State.DISABLED:
            next_state = self.perform_step(state)
            if self.state == State.DISABLED:
                pass
            else:
                self.state = next_state
        self.perform_post_step(self.state)
    
    def extract_chat_events_loop(self):
        self.ss = None
        def ss_thread():
            self.ss = np.array(select_chat_box(take_screenshot()))
            self.mask = extract_mask(None, self.ss)
            while True:
                if self.enabled:
                    new_ss = np.array(select_chat_box(take_screenshot()))
                    new_mask = extract_mask(None, new_ss)
                    diff = np.mean(np.uint8((self.mask ^ new_mask)*1))
                    self.new_mask_lock.acquire()
                    self.ss = new_ss
                    self.mask = new_mask
                    if diff > 0.1: # more than
                        self.new_mask = True
                    self.new_mask_lock.release()
        def loop(which):
            while True:
                if self.enabled:
                    t = time.time()
                    self.new_mask_lock.acquire()
                    new_mask = self.new_mask
                    if new_mask:
                        new_mask = False
                        ss = np.copy(self.ss)
                        mask = np.copy(self.mask)
                        self.new_mask_lock.release()
                        chat_events = extract_chat_events(which, ss, mask)
                    else:
                        self.new_mask_lock.release()
                        time.sleep(0.08)
                        continue
                    delay = time.time() - t
                    self.events_lock.acquire()
                    new_events: List[Event] = [e for e in chat_events if e not in self.events]
                    #printd(f"{which} extracting {len(chat_events)} chat events of which {len(new_events)} are new, took {round(delay,2)}: {new_events}")
                    self.unread_events += len(new_events)
                    self.events = (self.events + new_events)[-100:]
                    self.events_lock.release()
        threading.Thread(target=ss_thread).start()
        time.sleep(0.25)
        #threading.Thread(target=loop, args=("red",)).start()
        #threading.Thread(target=loop, args=("blue",)).start()
        threading.Thread(target=loop, args=(None,)).start()

    def perform_step(self, state: State) -> State:
        if state == State.DISABLED:
            return state
        elif state == State.INIT:
            return State.FISHING
        elif state == State.FISHING:
            self.events_lock.acquire()
            new_events = self.events[len(self.events)-self.unread_events:]
            self.unread_events = 0
            self.events_lock.release()
            for e in new_events:
                state = self.step_on_event(state, e)
            self.last_batch_reaction = datetime.datetime.now()
            return state
        raise RuntimeError(f"Undefined state: {state}")

    def step_on_event(self, prev_state: State, e: Event) -> State:
        printd(f"REACT: {e}")
        if e.name == "fishing":
            seconds_now = datetime.datetime.now().second
            try:
                seconds_then = int(e.ts.split(":")[-1].replace("]",""))
                assert 0 <= seconds_then < 60
            except:
                seconds_then = seconds_now - 1
            delay = seconds_now - seconds_then
            if delay < 0:
                delay += 60
            delay = min(delay, 5)
            next_time_allowed = (time.time() - delay) + 8.5 # doesnt account for next cycle, image proc interval, etc
            self.last_click_button[VK_FISH] = next_time_allowed
            return State.FISHING
        if e.name == "caught":
            with open("fishlog.txt", "a") as f:
                f.write(str((time.time(), None, e.name, e.fish_type, e.fish_weight)) + "\n")
            if should_throwback(e.fish_type, e.fish_weight):
                time.sleep(0.75)
                result = self.click(VK_TB, min_time_between_clicks=5)
                printd(f"Throwback result for {e.fish_type}: {result}")
            #self.click(VK_FISH, min_time_between_clicks=None)
            self.spam_test()
            self.click(VK_FINFO, min_time_between_clicks=5)
            return State.FISHING#prev_state
        if e.name == "inv_full":
            self.click(VK_FINFO, min_time_between_clicks=5)
            return State.DISABLED
        if e.name == "sea_monster":
            self.click(VK_SHIFT)
            time.sleep(0.3)
            self.click([VK_SHIFT, VK_S], click_length=7, min_time_between_clicks=0.1)
            return State.DISABLED
        if e.name == "exploded":
            time.sleep(1)
            self.click(VK_SHIFT, min_time_between_clicks=0.1)
            return State.DISABLED
        if e.name == "quit":
            return State.DISABLED
        if e.name == "infected":
            self.click(VK_ADRENALINE, min_time_between_clicks=10)
            time.sleep(5)
            self.click(VK_FISH, min_time_between_clicks=None)
            time.sleep(1)
            return State.FISHING#prev_state
        if e.name == "already_fishing":
            self.last_click_button[VK_FISH] = time.time() +2
            return State.FISHING
        if e.name == "wait_before_fishing":
            self.last_click_button[VK_FISH] = time.time() +0.5
            return State.FISHING
        if e.name == "thrown":
            self.tried_to_throw = None
            return State.FISHING
        if e.name == "failed_to_catch":
            self.last_click_button[VK_FISH] = time.time() + 0.5
            return State.FISHING
        raise RuntimeError(f"Did not return a state: {e}, {prev_state}")

    def perform_post_step(self, state: State):
        if state == State.INIT:
            self.click(VK_BACKSPACE)
        elif state == State.FISHING:
            self.click(VK_FISH, min_time_between_clicks=1)
            self.click(VK_SHIFT, min_time_between_clicks=10)
        elif state == State.UNDEFINED:
            self.click(VK_SHIFT, min_time_between_clicks=7.5) # in case we are dead

    def click(self, key, *, block_until_keydown=False, click_length:float=0.08, min_time_between_clicks:Optional[float]=1) -> Optional[bool]:
        if isinstance(key, (list, tuple,)):
            key = tuple(key)
        last_click = self.last_click_button.get(key, 0)
        if min_time_between_clicks is not None:
            next_allowed_click = last_click + min_time_between_clicks
            time_until_click = next_allowed_click - time.time()
            if time_until_click > 0:
                if block_until_keydown:
                    time.sleep(time_until_click)
                else:
                    return False
        click_keyboard(key, click_length)
        click_time = time.time()
        self.last_click = click_time
        self.last_click_button[key] = click_time
        return True
    
    def spam_test(self, *, do_thread: bool = True, n_clicks: int = 5, time_between_clicks: float = 0.08):
        assert n_clicks >= 1
        assert time_between_clicks > 0
        def f():
            self.click(VK_POST_TEST_MSG, min_time_between_clicks=time_between_clicks)
            for i in range(n_clicks - 1):
                time.sleep(time_between_clicks)
                self.click(VK_POST_TEST_MSG, min_time_between_clicks=time_between_clicks)
        t = threading.Thread(target=f)
        t.start()
        if not do_thread:
            t.join()


def main():
    #time.sleep(5)
    global DEBUG_COUNTER
    bot = FishingBot()
    def toggle_thread():
            while True:
                if win32api.GetAsyncKeyState(win32con.VK_DELETE):
                    bot.toggle()
                time.sleep(0.08)
    threading.Thread(target=toggle_thread).start()
    while True:
        bot.step()
        if bot.enabled:
            time.sleep(0.08)
            pass
        else:
            time.sleep(1/30)
        DEBUG_COUNTER += 1


if __name__ == "__main__":
    main()