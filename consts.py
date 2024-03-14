import colorsys

VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F9 = 0x78

# del / R4+L5 to toggle
VK_TB = VK_F2 # L3
VK_FISH = VK_F3 # L4
VK_INV = VK_F4 # R4
VK_ADRENALINE = VK_F5 # R5
VK_FINFO = VK_F6
VK_LOTTO = VK_F7
VK_DOWN = 0x26
VK_BACKSPACE = 0x08
VK_ENTER = 0x0D
VK_S = 0x53
VK_SHIFT = 0x10
VK_POST_TEST_MSG = VK_F9


from enum import Enum, auto
class State(Enum):
    DISABLED = auto()
    INIT = auto()
    WAIT_FOR_FISHING = auto()
    FISHING = auto()
    DEAD = auto()
    INVENTORY_FULL_FINAL = auto()
    UNDEFINED = auto()


BEEP_SEQS = {
    State.INIT: [
        (500, 1000),
    ],
    State.FISHING: [
        (500, 2000),
    ],
    State.INVENTORY_FULL_FINAL: [
        (300, 1000),
        (300, 1500),
        (300, 2000),
    ],
    State.UNDEFINED: [
        (500, 4000),
        (500, 3000),
        (500, 4000),
        (500, 3000),
        (500, 4000),
        (500, 3000),
    ]
}

COLOR_PURPLE = (116,90,198)#(0.70679, 0.545454, 198)
COLOR_GREEN = (98,175,98)#(0.333333, 0.43956, 182)
COLOR_TURQUOISE = (51,204,255) #(0.53897, 0.788235, 255)
COLOR_RED = (255,0,0) # colorsys.rgb_to_hex(190,12,14)
COLOR_RED_2 = (189,9,10)

from dataclasses import dataclass
import datetime

@dataclass
class Event:
    ts: datetime.datetime
    name: str
    fish_type: str = None
    fish_weight: float = None
    def __str__(self) -> str:
        return str((self.ts, self.name, self.fish_type, self.fish_weight))
    def __repr__(self) -> str:
        return self.__str__()
    def __hash__(self):
        return hash(str(self))