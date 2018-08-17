from built_ins import *
from pcb import OLED_RESET, OLED_CS, OLED_CLK, OLED_MOSI, OLED_DC
from ssd1306.ssd1306 import init_display, USE_SPI
from ssd1306.font_8x8 import print_8x8, set_xy


@setHook(HOOK_STARTUP)
def on_startup():
    writePin(OLED_RESET, False)
    setPinDir(OLED_RESET, True)
    writePin(OLED_RESET, True)

    init_display(USE_SPI)

    print_8x8("abcdefghijklm")
    set_xy(0, 1)
    print_8x8("nopqrstuvwxyz")
    set_xy(0, 2)
    print_8x8("\x00\x01\x02\x01\x03\x01\x04\x01\x05\x01\x06\x01\x07\x01")
    set_xy(0, 3)
    print_8x8("\x07\x08\x07\x09\x07\x0a\x07\x0b\x07\x0c")
    # print_8x8("Best neighbors:")
#     set_xy(1, 1)
#     print_8x8("09a39f -27dB")
#     set_xy(1, 2)
#     print_8x8("0ba154 -45dB")
#     set_xy(1, 3)
#     print_8x8("05ef18 -87dB")
#
#
# @setHook(HOOK_1S)
# def on_1s(t):
#     x = random() % 4
#     set_xy(0, 1)
#     print_8x8("*" if x == 0 else " ")
#     set_xy(0, 2)
#     print_8x8("*" if x == 1 else " ")
#     set_xy(0, 3)
#     print_8x8("*" if x == 2 else " ")
