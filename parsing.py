from utils import *

def parse_message(line: str) -> Optional[Event]:
    # parse into: (time, type, fish type?, weight?)
    def parse_fish_type() -> Optional[Event]:
        # [HH:MM:SS] You've caught a <number> lb <fish name>. Use /throwback to release the fish
        try:
            time = None# line.split(" ")[0]
            assert "has" not in line
            assert "breaking" not in line
            s = line.split("caught a ")[1]
            weight = float(s.split(" ")[0].replace(",",""))
            fish = " ".join(s.split(" ")[2:]).split(".")[0].split(",")[0] # remove weight, lb/Ib from beginning, then get fish name
            return Event(time, "caught", fish, weight)
        except:
            return None
    def parse_throwback() -> Optional[Event]:
        # [HH:MM:SS] You've caught a <number> lb <fish name>. Use /throwback to release the fish
        try:
            time = None# line.split(" ")[0]
            assert " thrown " in line
            assert " back " in line
            s = line.split("thrown ")[1]
            weight = float(s.split(" ")[0])
            fish = (" ".join(s.split(" of ")[1:]).split(" back ")[0])
            return Event(time, "thrown", fish, weight)
        except:
            return None
    def parse_fishing() -> Optional[Event]:
        # [HH:MM:SS] Fishing... Please Wait.
        try:
            time = line.split(" ")[0]
            assert ("fishing..." in line) or ("please wait" in line)
            return Event(time, "fishing")
        except:
            return None
    def parse_inv_full() -> Optional[Event]:
        # [HH:MM:SS] Your inventory is full.
        try:
            time = line.split(" ")[0]
            assert "inventory is full" in line
            return Event(time, "inv_full")
        except:
            return None
    def parse_sea_monster() -> Optional[Event]:
        try:
            time = None# line.split(" ")[0]
            assert "launched by a sea" in line
            return Event(time, "sea_monster")
        except:
            return None
    def parse_already_fishing() -> Optional[Event]:
        # [HH:MM:SS] You're already fishing.
        try:
            #time = line.split(" ")[0]
            assert "already fishing" in line
            return Event(None, "already_fishing")
        except:
            return None
    def parse_infected() -> Optional[Event]:
        # [HH:MM:SS] A fish has infected you...
        try:
            ts = line.split(" ")[0]
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
            assert "quit fishing" in line
            return Event(None, "quit")
        except:
            return None
    return (
        parse_fish_type() or
        parse_inv_full() or
        parse_already_fishing() or
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

def extract_mask(which=None, image: Optional[Union[Image.Image,np.ndarray]] = None) -> np.ndarray:
    if image is None:
        image = take_screenshot()
    if type(image) == np.ndarray:
        chat_box = image
    else:
        chat_box = np.array(image.crop((17,145,495,210)))
    dist_from_black = calc_dist_from_color(chat_box, [0,0,0], "l2")
    final_mask = None
    if which == "red":
        red_mask = (chat_box[:,:,1] < 50) & (chat_box[:,:,2] < 50) & (chat_box[:,:,0] > 100) | (dist_from_black < 2)
        red_mask = np.stack([red_mask, red_mask, red_mask], axis=2)
        final_mask = red_mask
    elif which == "blue":
        dist_from_blue = calc_dist_from_color(chat_box, COLOR_TURQUOISE)
        blue_mask = np.uint8(((dist_from_blue <= 0.03) | (dist_from_black < 2)) * 255)
        blue_mask = np.stack([blue_mask, blue_mask, blue_mask], axis=2)
        final_mask = blue_mask
    else:
        red_mask = (chat_box[:,:,1] < 50) & (chat_box[:,:,2] < 50) & (chat_box[:,:,0] > 100) | (dist_from_black < 2)
        red_mask = np.stack([red_mask, red_mask, red_mask], axis=2)
        dist_from_blue = calc_dist_from_color(chat_box, COLOR_TURQUOISE)
        blue_mask = np.uint8(((dist_from_blue <= 0.03) | (dist_from_black < 2)) * 255)
        blue_mask = np.stack([blue_mask, blue_mask, blue_mask], axis=2)
        final_mask = blue_mask | red_mask
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
        mask = extract_mask(which, image)
    chat_box = np.where(mask, np.array(chat_box), 0)
    text = pytesseract.image_to_string(chat_box, lang="eng")
    valid = list(parse_raw_text(text))
    # red_text = pytesseract.image_to_string(red_chat_box, lang="eng")
    # blue_text = pytesseract.image_to_string(blue_chat_box, lang="eng")
    # #Image.fromarray(np.uint8(red_chat_box)).convert('RGB').show()
    # valid = list(parse_raw_text(blue_text) | parse_raw_text(red_text))
    return valid
