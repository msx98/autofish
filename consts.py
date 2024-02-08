import colorsys

VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F9 = 0x78

VK_TB = VK_F2
VK_FISH = VK_F3
VK_INV = VK_F4
VK_ADRENALINE = VK_F5
VK_FINFO = VK_F6
VK_LOTTO = VK_F7
VK_DOWN = 0x26
VK_BACKSPACE = 0x08
VK_ENTER = 0x0D
VK_S = 0x53
VK_SHIFT = 0x10


from enum import Enum
class State(Enum):
    INIT = 0
    FISHING = 1
    LOOKING_AT_INVENTORY = 3
    INVENTORY_FULL_FINAL = 4
    UNDEFINED = 5


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