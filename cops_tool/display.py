from ssd1306.ssd1306 import clear_ram
from ssd1306.font_8x8 import print_8x8, set_xy, BATTERY_CHARS, SIGNAL_CHAR, UP_ARROW, DOWN_ARROW, RIGHT_ARROW

# Constants:
DMODE_NONE = -1
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
G_SAVED_DISPLAY = "\x00\x00"
G_DISPLAY_MODE = DMODE_NONE
G_REDUCE_COUNTDOWN = -1
G_SCROLL_POS = 0


def display_on_1s(t):
    """Handle 1s timer event.

    :param int t: Ignored
    """
    global G_REDUCE_COUNTDOWN

    if G_REDUCE_COUNTDOWN >= 0:
        G_REDUCE_COUNTDOWN -= 1

        if G_REDUCE_COUNTDOWN == 0:
            display(G_SAVED_DISPLAY)


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


def display(display_string):
    """Update the display.

    :param str display_string: See format, below
    """
    global G_DISPLAY_MODE, G_REDUCE_COUNTDOWN, G_SAVED_DISPLAY

    # display_string format:
    # Offset | Width | Meaning
    #      0 |     1 | Selected item
    #      1 |     1 | Battery level (0-11)
    #   5n+2 |     1 | Signal strength (-dBm)
    #   5n+3 |     1 | Recent message (1=yes, 0=no)
    #   5n+4 |     3 | MAC address
    G_SAVED_DISPLAY = display_string
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5
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
        G_DISPLAY_MODE = redraw_3(display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_4:
        G_DISPLAY_MODE = redraw_4(display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_6:
        G_DISPLAY_MODE = redraw_6(display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_LIST_8:
        G_DISPLAY_MODE = redraw_8(display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_SCROLL_LIST:
        G_DISPLAY_MODE = redraw_scroll(display_mode != G_DISPLAY_MODE)
    elif display_mode == DMODE_TRACEROUTE:
        pass  # TODO


def expand_node_entry(node_entry):
    """Expand a 5-byte node entry into a printable string.

    :param str node_entry: 5-byte node entry string
    :return: Printable string (see format, below)
    :rtype: str
    """
    # Return format:
    # Offset | Width | Meaning
    #      0 |     1 | "*" if a recent message, " " otherwise
    #      1 |     1 | Space
    #      2 |     6 | MAC address
    #      8 |     1 | Space
    #      9 |     7 | Signal strength (ex: "-100dBm")
    #     16 |     1 | Signal strength bars
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


def redraw_3(force_redraw):
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    battery_string = BATTERY_CHARS[ord(G_SAVED_DISPLAY[1])]
    if force_redraw:
        clear_ram()
        print_8x8("Neighbors:    " + battery_string)
    else:
        set_xy(14, 0)
        print_8x8(battery_string)

    set_xy(0, 1)
    print_8x8(expand_node_entry(G_SAVED_DISPLAY[2:7])[:-1] if num_nodes > 0 else "                ")
    set_xy(0, 2)
    if num_nodes > 0:
        print_8x8(expand_node_entry(G_SAVED_DISPLAY[7:12])[:-1] if num_nodes > 1 else "                ")
    else:
        print_8x8("  (none yet)    ")
    set_xy(0, 3)
    print_8x8(expand_node_entry(G_SAVED_DISPLAY[12:17])[:-1] if num_nodes > 2 else "                ")

    return DMODE_LIST_3


def redraw_4(force_redraw):
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3(True)

    if force_redraw:
        clear_ram()

    for y in xrange(4):
        set_xy(0, y)
        line = expand_node_entry(G_SAVED_DISPLAY[(y * 5) + 2:(y * 5) + 7])[:-1] if num_nodes > y else "                "
        print_8x8(line)

    return DMODE_LIST_4


def redraw_6(force_redraw):
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3(True)

    if force_redraw:
        clear_ram()
        print_8x8("Neighbors:    " + BATTERY_CHARS[ord(G_SAVED_DISPLAY[1])])
    else:
        set_xy(14, 0)
        print_8x8(BATTERY_CHARS[ord(G_SAVED_DISPLAY[1])])

    for index in xrange(6):
        set_xy(0 if index < 3 else 9, (index % 3) + 1)
        if index < num_nodes:
            text = expand_node_entry(G_SAVED_DISPLAY[(index * 5) + 2:(index * 5) + 7])
            print_8x8(text[2:8] + text[-1])
        else:
            print_8x8("       ")

    return DMODE_LIST_6


def redraw_8(force_redraw):
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3(True)

    if force_redraw:
        clear_ram()

    for index in xrange(8):
        set_xy(0 if index < 4 else 9, index % 4)
        if index < num_nodes:
            text = expand_node_entry(G_SAVED_DISPLAY[(index * 5) + 2:(index * 5) + 7])
            print_8x8(text[2:8] + text[-1])
        else:
            print_8x8("       ")

    return DMODE_LIST_8


def redraw_scroll(force_redraw):
    global G_SCROLL_POS, G_DISPLAY_MODE

    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3(True)

    if force_redraw:
        clear_ram()

    selected = ord(G_SAVED_DISPLAY[0])
    # Beyond the last item?
    if selected > (num_nodes - 1):
        selected = num_nodes - 1
    # Before the first displayed item?
    if selected <= G_SCROLL_POS:
        G_SCROLL_POS = (selected - 1) if selected > 0 else 0
    # Selected the fourth row (or beyond)
    if selected >= (G_SCROLL_POS + 3):
        # On the last item?
        if selected == (num_nodes - 1):
            G_SCROLL_POS = (selected - 3) if selected >= 3 else 0
        else:
            G_SCROLL_POS = (selected - 2) if selected >= 2 else 0

    set_xy(0, 0)

    print_8x8(UP_ARROW if selected > 0 else RIGHT_ARROW)
    line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 2:(G_SCROLL_POS * 5) + 7])
    print_8x8(line[1:-1])

    if (G_SCROLL_POS + 1) >= (num_nodes - 1):
        print_8x8("                ")
    else:
        if selected == (G_SCROLL_POS + 1):
            print_8x8(RIGHT_ARROW)
        else:
            print_8x8(DOWN_ARROW if selected == (num_nodes - 1) else " ")
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 7:(G_SCROLL_POS * 5) + 12])
        print_8x8(line[1:-1])

    if (G_SCROLL_POS + 2) >= (num_nodes - 1):
        print_8x8("                ")
    else:
        if selected == (G_SCROLL_POS + 1):
            print_8x8(RIGHT_ARROW)
        else:
            print_8x8(DOWN_ARROW if selected == (num_nodes - 1) else " ")
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 12:(G_SCROLL_POS * 5) + 17])
        print_8x8(line[1:-1])

    if (G_SCROLL_POS + 3) >= (num_nodes - 1):
        print_8x8("                ")
    else:
        print_8x8(RIGHT_ARROW if selected == (G_SCROLL_POS + 1) else DOWN_ARROW)
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 12:(G_SCROLL_POS * 5) + 17])
        print_8x8(line[1:-1])

    return DMODE_SCROLL_LIST
