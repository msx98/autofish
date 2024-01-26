from utils import *

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
            time = line.split(" ")[0]
            assert "inventory is full" in line
            return (time, "inv_full", None, None)
        except:
            return None
    def parse_sea_monster() -> Optional[Tuple[str, str, str, float]]:
        try:
            time = None# line.split(" ")[0]
            assert "launched by a sea" in line
            return (time, "sea_monster", None, None)
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
    def parse_infected() -> Optional[Tuple[None, str, None, None]]:
        # [HH:MM:SS] A fish has infected you...
        try:
            ts = line.split(" ")[0]
            assert "infected" in line
            return (ts, "infected", None, None)
        except:
            return None
    return (
        parse_fish_type() or
        parse_inv_full() or
        parse_already_fishing() or
        parse_sea_monster() or
        parse_infected() or
        #parse_finv_fish() or
        None
    )

def parse_finv_fish(line) -> Optional[Tuple[None, str, None, None]]:
    # <FISH>, <WEIGHT> lb
    try:
        fish_name = " ".join(line[:-2])
        fish_weight = float(line[-2])
        return (None, "finv", fish_name, fish_weight)
    except:
        return None


def extract_finv_fish(image) -> Tuple[Optional[str], str, Optional[str], Optional[float]]:
    finv_info = np.array(image.crop((1500,760,1920,900)))
    dist_from_purple = calc_dist_from_color(finv_info, COLOR_PURPLE)
    dist_from_green = calc_dist_from_color(finv_info, COLOR_GREEN)
    dist_from_black = calc_dist_from_color(finv_info, [0,0,0], "l2")
    mask = ((dist_from_purple <= 0.2) | (dist_from_green <= 0.2) | (dist_from_black < 10))
    mask = np.stack([mask, mask, mask], axis=2)
    new_finv_info = np.where(mask, np.array(finv_info), 0)
    #Image.romarray(np.uint8(new_finv_info)).convert('RGB').show()
    fish_text = pytesseract.image_to_string(new_finv_info, lang="eng").split("\n")[0].split(" ")
    return parse_finv_fish(fish_text)


def extract_chat_messages(image) -> List[Tuple[Optional[str], str, Optional[str], Optional[float]]]:
    def parse_raw_text(raw_text):
        lines = [x for x in raw_text.split("\n") if x]
        parsed = [parse_message(x) for x in lines]
        valid = [x for x in parsed if x]
        return set(valid)
    chat_box = np.array(image.crop((0, 50, 800, 300)))
    dist_from_blue = calc_dist_from_color(chat_box, COLOR_TURQUOISE)
    dist_from_black = calc_dist_from_color(chat_box, [0,0,0], "l2")
    red_mask = (chat_box[:,:,1] < 50) & (chat_box[:,:,2] < 50) & (chat_box[:,:,0] > 100) | (dist_from_black < 2)
    red_mask = np.stack([red_mask, red_mask, red_mask], axis=2)
    blue_mask = np.uint8(((dist_from_blue <= 0.03) | (dist_from_black < 2)) * 255)
    blue_mask = np.stack([blue_mask, blue_mask, blue_mask], axis=2)
    red_chat_box = np.where(red_mask, np.array(chat_box), 0)
    blue_chat_box = np.where(blue_mask, np.array(chat_box), 0)
    red_text = pytesseract.image_to_string(red_chat_box, lang="eng")
    blue_text = pytesseract.image_to_string(blue_chat_box, lang="eng")
    #Image.fromarray(np.uint8(red_chat_box)).convert('RGB').show()
    valid = list(parse_raw_text(blue_text) | parse_raw_text(red_text))
    return valid
