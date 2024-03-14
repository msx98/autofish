from utils import *

def extract_time(
        line: str, *,
        time_estimate_real: datetime.datetime = None,
        is_forgiving: bool = False,
) -> Optional[datetime.datetime]:
    if time_estimate_real is None:
        time_estimate_real = datetime.datetime.now()
    prev_day = time_estimate_real - datetime.timedelta(days=1)
    first_of_month = prev_day.month < time_estimate_real.month
    first_of_year = prev_day.year < time_estimate_real.year
    try:
        time_str = line.split(" ")[0]
        assert len(time_str) == len("[00:00:00]")
        time_h, time_m, time_s = int(time_str[1:3]), int(time_str[4:6]), int(time_str[7:9])
        if is_forgiving:
            if int(time_h / 10) == 4:
                time_h = 10 + (time_h % 10)
        assert (0 <= time_h <= 23) and (0 <= time_m <= 59) and (0 <= time_s <= 59)
        is_prev_day = time_estimate_real.hour < time_h
        is_prev_month = is_prev_day and first_of_month
        is_prev_year = is_prev_day and first_of_year
        ts = datetime.datetime(
            year=time_estimate_real.year - (1*is_prev_year),
            month=time_estimate_real.month - (1*is_prev_month),
            day=time_estimate_real.day - (1*is_prev_day),
            hour=time_h,
            minute=time_m,
            second=time_s,
        )
        if is_forgiving:
            pass
        else:
            if abs(ts - time_estimate_real).total_seconds() >= 10:
                return None
        return ts
    except:
        return None

def parse_message(line: str) -> Optional[Event]:
    #print(f"Parsing: {line}")
    # parse into: (time, type, fish type?, weight?)
    def parse_fish_type() -> Optional[Event]:
        # [HH:MM:SS] You've caught a <number> lb <fish name>. Use /throwback to release the fish
        try:
            ts = None #extract_time(line)
            assert "has" not in line
            assert "breaking" not in line
            s = line.split("caught a ")[1]
            weight = float(s.split(" ")[0].replace(",",""))
            fish = " ".join(s.split(" ")[2:]).split(".")[0].split(",")[0] # remove weight, lb/Ib from beginning, then get fish name
            return Event(ts, "caught", fish, weight)
        except:
            return None
    def parse_throwback() -> Optional[Event]:
        # [HH:MM:SS] You've caught a <number> lb <fish name>. Use /throwback to release the fish
        try:
            ts = extract_time(line)
            assert " thrown " in line
            assert " back " in line
            s = line.split("thrown ")[1]
            weight = float(s.split(" ")[0])
            fish = (" ".join(s.split(" of ")[1:]).split(" back ")[0])
            return Event(ts, "thrown", fish, weight)
        except:
            return None
    def parse_failed_to_catch() -> Optional[Event]:
        try:
            ts = extract_time(line)
            assert "failed to catch" in line
            return Event(ts, "failed_to_catch", None, None)
        except:
            return None
    def parse_wait_before_fishing() -> Optional[Event]:
        try:
            ts = extract_time(line)
            assert "wait before fishing" in line
            return Event(ts, "wait_before_fishing", None, None)
        except:
            return None
    def parse_fishing() -> Optional[Event]:
        # [HH:MM:SS] Fishing... Please Wait.
        try:
            ts = extract_time(line)
            assert ("fishing..." in line) or ("please wait" in line)
            return Event(ts, "fishing")
        except:
            return None
    def parse_inv_full() -> Optional[Event]:
        # [HH:MM:SS] Your inventory is full.
        try:
            ts = extract_time(line, is_forgiving=True)
            assert "inventory is full" in line
            return Event(ts, "inv_full")
        except:
            return None
    def parse_sea_monster() -> Optional[Event]:
        try:
            ts = extract_time(line)
            assert "launched by a sea" in line
            return Event(ts, "sea_monster")
        except:
            return None
    def parse_already_fishing() -> Optional[Event]:
        # [HH:MM:SS] You're already fishing.
        try:
            ts = extract_time(line)
            assert "already fishing" in line
            return Event(ts, "already_fishing")
        except:
            return None
    def parse_infected() -> Optional[Event]:
        # [HH:MM:SS] A fish has infected you...
        try:
            ts = extract_time(line)
            assert "infected" in line
            return Event(ts, "infected")
        except:
            return None
    def parse_exploded() -> Optional[Event]:
        try:
            ts = line.split(" ")[0]
            assert ("undetonated" in line) or ("you're dead" in line)
            return Event(ts, "exploded")
        except:
            return None
    def parse_quit_fishing() -> Optional[Event]:
        try:
            ts = line.split(" ")[0]
            assert ("on the coast" in line) or ("boat or right" in line)
            return Event(ts, "quit")
        except:
            return None
    return (
        parse_fish_type() or
        parse_inv_full() or
        parse_already_fishing() or
        parse_failed_to_catch() or
        parse_throwback() or
        parse_sea_monster() or
        parse_infected() or
        parse_fishing() or
        parse_quit_fishing() or
        parse_exploded() or
        #parse_finv_fish() or
        None
    )


def extract_finv_fish(image) -> Tuple[Event]:
    finv_info = np.array(image.crop(convert_res(1500,760,1920,900)))
    dist_from_purple = calc_dist_from_color(finv_info, COLOR_PURPLE)
    dist_from_green = calc_dist_from_color(finv_info, COLOR_GREEN)
    dist_from_black = calc_dist_from_color(finv_info, [0,0,0], "l2")
    mask = ((dist_from_purple <= 0.2) | (dist_from_green <= 0.2) | (dist_from_black < 10))
    mask = np.stack([mask, mask, mask], axis=2)
    new_finv_info = np.where(mask, np.array(finv_info), 0)
    #Image.romarray(np.uint8(new_finv_info)).convert('RGB').show()
    fish_text = pytesseract.image_to_string(new_finv_info, lang="eng").split("\n")[0].split(" ")
    try:
        fish_name = " ".join(fish_text[:-2])
        fish_weight = float(fish_text[-2])
        return Event(None, "finv", fish_name, fish_weight)
    except:
        return None

def extract_mask(which=None, image: Optional[np.ndarray] = None) -> np.ndarray:
    chat_box = np.array(image)
    chat_box_hsv = rgb_to_hsv(chat_box)
    dist_from_black = calc_dist_from_color(chat_box_hsv, 0, "intensity")
    dist_from_blue = calc_dist_from_color(chat_box_hsv, COLOR_TURQUOISE)
    shadow_mask = dist_from_black<np.min(dist_from_black)+20
    red_mask = ((chat_box[:,:,1] < 50) & (chat_box[:,:,2] < 50) & (chat_box[:,:,0] > 100)) | shadow_mask
    blue_mask = (dist_from_blue <= 0.1) | shadow_mask
    final_mask = blue_mask | red_mask
    final_mask = np.stack([final_mask, final_mask, final_mask], axis=2)
    return final_mask

def extract_chat_events(which=None, image: Optional[Union[Image.Image,np.ndarray]] = None, mask=None) -> List[Event]:
    def parse_raw_text(raw_text):
        lines = [x for x in raw_text.split("\n") if x]
        parsed = [parse_message(x) for x in lines]
        valid = [x for x in parsed if x]
        return set(valid)
    if image is None:
        image = take_screenshot()
    #chat_box = np.array(image.crop((0, 25, 533, 230)))
    if type(image) == np.ndarray:
        chat_box = image
    else:
        chat_box = np.array(select_chat_box(image))
    if mask is None:
        mask = extract_mask(which, chat_box)
    chat_box = np.where(mask, np.array(chat_box), 0)
    text = pytesseract.image_to_string(chat_box, lang="eng", config="--psm 6").replace("{","[").replace("}","]")
    valid = list(parse_raw_text(text))
    # red_text = pytesseract.image_to_string(red_chat_box, lang="eng")
    # blue_text = pytesseract.image_to_string(blue_chat_box, lang="eng")
    # #Image.fromarray(np.uint8(red_chat_box)).convert('RGB').show()
    # valid = list(parse_raw_text(blue_text) | parse_raw_text(red_text))
    #if any([e.name == "quit" for e in valid]):
    #    print("break here")
    return valid
