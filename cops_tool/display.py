from ssd1306.ssd1306 import clear_ram
from ssd1306.font_8x8 import print_8x8, set_xy, BATTERY_CHARS, SIGNAL_CHAR, UP_ARROW, DOWN_ARROW, RIGHT_ARROW

# Constants:
DMODE_LIST_3 = 0
DMODE_LIST_4 = 1
DMODE_LIST_6 = 2
DMODE_LIST_8 = 3
DMODE_SCROLL_LIST = 4
DMODE_TRACEROUTE = 5

REDUCE_TIMEOUT = 3

HEX = "0123456789abcdef"

SIGNAL_LEVELS = (80, 60, 40, 20)

# Globals:
G_LAST_DISPLAY = "\x00"
G_DISPLAY_MODE = DMODE_LIST_3
G_REDUCE_COUNTDOWN = 0
G_SCROLL_POS = 0


def display_on_1s(t):
    """Handle 1s timer event.

    :param int t: Ignored
    """
    global G_REDUCE_COUNTDOWN

    if G_REDUCE_COUNTDOWN >= 0:
        G_REDUCE_COUNTDOWN -= 1

        if G_REDUCE_COUNTDOWN == 0:
            display(G_LAST_DISPLAY, None)


def find_ideal_mode(num_nodes):
    """Return the ideal mode for the given number of nodes.

    :param int num_nodes: Number of nodes
    :return: Ideal mode
    :rtype: int
    """
    if num_nodes <= 3:
        return DMODE_LIST_3
    elif num_nodes <= 4:
        return DMODE_LIST_4
    elif num_nodes <= 6:
        return DMODE_LIST_6
    elif num_nodes <= 8:
        return DMODE_LIST_8
    else:
        return DMODE_SCROLL_LIST


def display(display_string, battery_level):
    """Update the display.

    :param str display_string: See format, below
    :param int|None battery_level: Battery level 0-11
    """
    global G_DISPLAY_MODE, G_REDUCE_COUNTDOWN

    # display_string format:
    # Offset | Width | Meaning
    #      0 |     1 | Selected item
    #     5n |     1 | Signal strength (-dBm)
    #   5n+1 |     1 | Recent message (1=yes, 0=no)
    #   5n+2 |     3 | MAC address
    num_nodes = (len(display_string) - 1) / 4
    display_mode = G_DISPLAY_MODE
    ideal_mode = find_ideal_mode(num_nodes)

    # Adjust mode up immediately, but if the mode is being reduced, use the timer to decide when. That way the display
    # won't alternate badly when crossing back and forth over a boundary.
    if ideal_mode > display_mode:
        display_mode = ideal_mode
        G_REDUCE_COUNTDOWN = -1
    elif ideal_mode < display_mode:
        if G_REDUCE_COUNTDOWN < 0:
            G_REDUCE_COUNTDOWN = REDUCE_TIMEOUT
        elif G_REDUCE_COUNTDOWN == 0:
            display_mode = ideal_mode
    else:
        G_REDUCE_COUNTDOWN = -1

    if display_mode == DMODE_LIST_3:
        redraw_3(display_string, battery_level, display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_4:
        redraw_4(display_string, display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_6:
        redraw_6(display_string, battery_level, display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_8:
        redraw_8(display_string, display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_SCROLL_LIST:
        redraw_scroll(display_string, display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_TRACEROUTE:
        pass  # TODO

    G_DISPLAY_MODE = display_mode


def expand_node_entry(node_entry):
    expanded = "* " if ord(node_entry[1]) else "  "

    # Hex address
    for i in xrange(2, 5):
        byte = ord(node_entry[i])
        expanded += HEX[byte >> 4]
        expanded += HEX[byte & 0x0f]

    expanded += " "

    # Right-justified level
    level = ord(node_entry[0])
    if level >= 100:
        expanded += str(-level)
    elif level >= 10:
        expanded += " " + str(-level)
    else:
        expanded += "  " + str(-level)

    expanded += "dBm"

    # Bars
    for index in xrange(4):
        if level > SIGNAL_LEVELS[index]:
            return expanded + SIGNAL_CHAR[index]
    else:
        return expanded + SIGNAL_CHAR[4]


def redraw_3(display_string, battery_level, force_redraw):
    battery_string = ("" if battery_level is None else BATTERY_CHARS[battery_level])
    if force_redraw:
        clear_ram()
        print_8x8("Neighbors:    " + battery_string)
    else:
        set_xy(14, 0)
        print_8x8(battery_string)

    num_nodes = (len(display_string) - 1) / 4

    set_xy(14, 1)
    print_8x8(expand_node_entry(display_string[1:6])[:-1] if num_nodes > 0 else "                ")
    set_xy(14, 2)
    if num_nodes > 0:
        print_8x8(expand_node_entry(display_string[6:11])[:-1] if num_nodes > 1 else "                ")
    else:
        print_8x8("  (none yet)    ")
    set_xy(14, 1)
    print_8x8(expand_node_entry(display_string[11:16])[:-1] if num_nodes > 2 else "                ")


def redraw_4(display_string, force_redraw):
    if force_redraw:
        clear_ram()

    num_nodes = (len(display_string) - 1) / 4

    for y in xrange(4):
        set_xy(14, y)
        line = expand_node_entry(display_string[(y * 5) + 1:(y * 5) + 6])[:-1] if num_nodes > y else "                "
        print_8x8(line)


def redraw_6(display_string, battery_level, force_redraw):
    if force_redraw:
        clear_ram()
        print_8x8("Neighbors:    " + BATTERY_CHARS[battery_level])
    else:
        set_xy(14, 0)
        print_8x8(BATTERY_CHARS[battery_level])

    num_nodes = (len(display_string) - 1) / 4

    for index in xrange(6):
        set_xy(0 if index < 3 else 9, (index % 3) + 1)
        if index < num_nodes:
            text = expand_node_entry(display_string[(index * 5) + 1:(index * 5) + 6])
            print_8x8(text[2:8] + text[-1])
        else:
            print_8x8("       ")


def redraw_8(display_string, force_redraw):
    if force_redraw:
        clear_ram()

    num_nodes = (len(display_string) - 1) / 4

    for index in xrange(8):
        set_xy(0 if index < 4 else 9, index % 4)
        if index < num_nodes:
            text = expand_node_entry(display_string[(index * 5) + 1:(index * 5) + 6])
            print_8x8(text[2:8] + text[-1])
        else:
            print_8x8("       ")


def redraw_scroll(display_string, force_redraw):
    global G_SCROLL_POS

    if force_redraw:
        clear_ram()

    num_nodes = (len(display_string) - 1) / 4

    selected = ord(G_LAST_DISPLAY[0])
    if selected <= G_SCROLL_POS:
        G_SCROLL_POS = (selected - 1) if selected > 0 else 0
    if selected >= (G_SCROLL_POS + 3):
        if selected == (num_nodes - 1):
            G_SCROLL_POS = (selected - 3) if selected >= 3 else 0
        else:
            G_SCROLL_POS = (selected - 2) if selected >= 2 else 0

    set_xy(0, 0)

    print_8x8(UP_ARROW if selected > 0 else RIGHT_ARROW)

