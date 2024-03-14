

s = None
with open("fishlog.txt", "r") as f:
    s = f.readlines()
s = [eval(line.strip()) for line in s if line]
lines = []
for line in s:
    if len(line) == 5:
        lines.append(line)
    elif len(line) == 4:
        lines.append((None, *line))
    else:
        raise Exception()

all_fish = dict()
for line in lines:
    ts, _, event_name, fish_name, fish_weight = line
    all_fish[fish_name] = all_fish.get(fish_name, 0) + 1


# upper_dict.py
corrections = {
    "dolphin": {"dolp!", "dolphii", "dolphit"},
    "blue marlin": {"blue mar!", "blue marl"},
    "haddock": {"haddoa"},
    "ray": {"ib ray"},
    "sailfish": {"ib sailfish"},
    "lionfish": {"lionti"},
    "moray eel": {"moray fel"},
    "red snapper": {"red snapp:"},
    "sailfish": {"saitfish"},
}

new_corrections = dict()
for correct, aliases in corrections.items():
    for alias in aliases:
        assert alias not in new_corrections
        new_corrections[alias] = correct
corrections = new_corrections

class TypoDict(dict):
    def __init__(self, mapping=None, /, **kwargs):
        super().__init__(mapping, **kwargs)

    def __setitem__(self, key, value):
        #key = key.upper()
        super().__setitem__(key, value)
    
    def __getitem__(self, key):
        key = corrections.get(key, key)
        return super().__getitem__(key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
