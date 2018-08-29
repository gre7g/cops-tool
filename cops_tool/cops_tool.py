from built_ins import *
from pcb import *
from display import display, display_on_1s
from ssd1306.font_8x8 import print_8x8, set_xy, BATTERY_CHARS
from ssd1306.ssd1306 import init_display, USE_SPI, clear_ram


@setHook(HOOK_STARTUP)
def on_startup():
    writePin(OLED_RESET, False)
    setPinDir(OLED_RESET, True)
    writePin(OLED_RESET, True)

    init_display(USE_SPI)

    # print_8x8("abcdefghijklm")
    # set_xy(0, 1)
    # print_8x8("nopqrstuvwxyz")
    # set_xy(0, 2)
    # print_8x8("\x00\x01\x02\x01\x03\x01\x04\x01\x05\x01\x06\x01\x07\x01")
    # set_xy(0, 3)
    # print_8x8("\x07\x08\x07\x09\x07\x0a\x07\x0b\x07\x0c")
    # print_8x8("Best neighbors:")
#     set_xy(1, 1)
#     print_8x8("09a39f -27dB")
#     set_xy(1, 2)
#     print_8x8("0ba154 -45dB")
#     set_xy(1, 3)
#     print_8x8("05ef18 -87dB")
#
#
@setHook(HOOK_1S)
def on_1s(t):
    display_on_1s(t)
#     x = random() % 4
#     set_xy(0, 1)
#     print_8x8("*" if x == 0 else " ")
#     set_xy(0, 2)
#     print_8x8("*" if x == 1 else " ")
#     set_xy(0, 3)
#     print_8x8("*" if x == 2 else " ")
#
# def go(x):
#     clear_ram()
#     if x == 0:
#         print_8x8("Neighbors:    " + BATTERY_CHARS[random() % 12])
#         set_xy(2, 2)
#         print_8x8("(none yet)")
#     elif x == 1:
#         print_8x8("Neighbors:    " + BATTERY_CHARS[random() % 12])
#         set_xy(0, 1)
#         print_8x8("* abcdef -100dBm")
#         set_xy(0, 2)
#         print_8x8("  abcdef -100dBm")
#         set_xy(0, 3)
#         print_8x8("  abcdef -100dBm")
#     elif x == 2:
#         print_8x8("  abcdef -100dBm")
#         set_xy(0, 1)
#         print_8x8("* abcdef -100dBm")
#         set_xy(0, 2)
#         print_8x8("  abcdef -100dBm")
#         set_xy(0, 3)
#         print_8x8("  abcdef -100dBm")
#     elif x == 3:
#         print_8x8("Neighbors:    " + BATTERY_CHARS[random() % 12])
#         set_xy(0, 1)
#         print_8x8("abcdef\x10  abcdef\x10")
#         set_xy(0, 2)
#         print_8x8("abcdef\x0f  abcdef\x0e")
#         set_xy(0, 3)
#         print_8x8("abcdef\x0d  abcdef\x20")
#     elif x == 4:
#         print_8x8("abcdef\x10  abcdef\x10")
#         set_xy(0, 1)
#         print_8x8("abcdef\x10  abcdef\x10")
#         set_xy(0, 2)
#         print_8x8("abcdef\x0f  abcdef\x0e")
#         set_xy(0, 3)
#         print_8x8("abcdef\x0d  abcdef\x20")
#     elif x == 5:
#         print_8x8("\x11 abcdef -100dBm")
#         set_xy(0, 1)
#         print_8x8("\x13 abcdef -100dBm")
#         set_xy(0, 2)
#         print_8x8("\x20 abcdef -100dBm")
#         set_xy(0, 3)
#         print_8x8("\x12 abcdef -100dBm")
#     elif x == 6:
#         print_8x8("\x11 \x20abcdef -100")
#         set_xy(0, 1)
#         print_8x8("\x20 \x14abcdef -100")
#         set_xy(0, 2)
#         print_8x8("\x20 \x14abcdef -100")
#         set_xy(0, 3)
#         print_8x8("\x12 \x14abcdef -100")
#   0........10...15
# 0 Strong neighbors
# 1
# 2   (none yet)
# 3
#
# 0 Strong neighbors
# 1 * abcdef -100dB
# 2   abcdef -100dB
# 3   abcdef -100dB
#
# 0   abcdef -100dB
# 1 * abcdef -100dB
# 2   abcdef -100dB
# 3   abcdef -100dB
#
# 0 Strong neighbors
# 1 abcdef*  abcdef*
# 2 abcdef*  abcdef*
# 3 abcdef*  abcdef*
#
# 0 abcdef*  abcdef*
# 1 abcdef*  abcdef*
# 2 abcdef*  abcdef*
# 3 abcdef*  abcdef*
#
# 0 Strong neighbors
# 1 * abcdef -100dB
# 2   abcdef -100dB
# 3   abcdef -100dB
#
# 0 ^ abcdef -100dB
# 1 > abcdef -100dB
# 2   abcdef -100dB
# 3 v abcdef -100dB
#
