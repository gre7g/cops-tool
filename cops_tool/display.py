from display_cache import cache_8x8
from ssd1306.font_8x8 import set_xy, BATTERY_CHARS, SIGNAL_CHAR, UP_ARROW, DOWN_ARROW, RIGHT_ARROW

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
SPACES_2 = " " * 2
SPACES_7 = " " * 7
SPACES_16 = " " * 16
NONE_YET = "   (none yet)   "
LOW_US = "* LOW BATTERY! *"
LOW_NEIGHBOR = "LOW BATT: "

SIGNAL_LEVELS = (80, 60, 40, 20)

# Globals:
G_SAVED_DISPLAY = "\x00\x00"
G_DISPLAY_MODE = DMODE_NONE
G_REDUCE_COUNTDOWN = -1
G_SCROLL_POS = 0
G_BATTERY_MSG_STATE = 0  # 0=normal, 1=1st message, 2=2nd message...
G_BATTERY_LOW = "\x00"

# G_BATTERY_LOW format:
# Offset | Width | Notes
#      0 |     1 | We're low (0=no, 1=yes)
#   3n+1 |     3 | MAC address of a low neighbor


def display_on_1s():
    """Handle 1s timer event"""
    global G_REDUCE_COUNTDOWN

    if G_REDUCE_COUNTDOWN >= 0:
        G_REDUCE_COUNTDOWN -= 1

        if G_REDUCE_COUNTDOWN == 0:
            display(G_SAVED_DISPLAY)

    # Cycle through any battery messages
    cycle_batt_msg()


def cycle_batt_msg():
    """Cycle through a battery message."""
    global G_BATTERY_MSG_STATE

    # How many messages to cycle around?
    num_msgs = ord(G_BATTERY_LOW[0]) + (len(G_BATTERY_LOW) / 3) + 1
    state = G_BATTERY_MSG_STATE / 2  # Two seconds per state

    # Wrap around?
    if state >= num_msgs:
        G_BATTERY_MSG_STATE = state = 0

    # Display the full screen to start
    if state == 0:
        display(G_SAVED_DISPLAY)
    else:
        set_xy(0, 3)
        mac_to_show = state - 1 - ord(G_BATTERY_LOW[0])

        # Is this node low?
        if mac_to_show < 0:
            # Yes, show that
            cache_8x8(LOW_US)
        else:
            # Must be some other node, show them
            cache_8x8(LOW_NEIGHBOR + mac_to_str(G_BATTERY_LOW[(mac_to_show * 3) + 1:(mac_to_show * 3) + 4]))

    # Next state
    G_BATTERY_MSG_STATE += 1


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


def display():
    """Update the display"""
    global G_DISPLAY_MODE, G_REDUCE_COUNTDOWN, G_SAVED_DISPLAY

    # G_SAVED_DISPLAY format:
    # Offset | Width | Meaning
    #      0 |     1 | Selected item
    #      1 |     1 | Battery level (0-11)
    #   5n+2 |     1 | Signal strength (-dBm)
    #   5n+3 |     1 | Recent message (1=yes, 0=no)
    #   5n+4 |     3 | MAC address
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
        G_DISPLAY_MODE = redraw_3()
    elif display_mode == DMODE_LIST_4:
        G_DISPLAY_MODE = redraw_4()
    elif display_mode == DMODE_LIST_6:
        G_DISPLAY_MODE = redraw_6()
    elif display_mode == DMODE_LIST_8:
        G_DISPLAY_MODE = redraw_8()
    elif display_mode == DMODE_SCROLL_LIST:
        G_DISPLAY_MODE = redraw_scroll()
    elif display_mode == DMODE_TRACEROUTE:
        pass  # TODO


def mac_to_str(mac):
    """Convert a three byte MAC address into a hex string.

    :param str mac: Three byte MAC address
    :return: Hex string
    :rtype: str
    """
    string = ""
    for i in xrange(3):
        byte = ord(mac[i])
        string += HEX[byte >> 4]
        string += HEX[byte & 0x0f]
    return string


def num_to_hex(number):
    string = ""
    for shift in xrange(12, -1, -4):
        string += HEX[(number >> shift) & 0x000f]
    return string


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
    expanded = ("* " if ord(node_entry[1]) else "  ") + mac_to_str(node_entry[2:5]) + " "

    # Right-justified level
    level = ord(node_entry[0])
    power = "   " + str(-level) + "dBm"
    expanded += power[-7:]

    # Bars
    for index in xrange(4):
        if level > SIGNAL_LEVELS[index]:
            return expanded + SIGNAL_CHAR[index]
    else:
        return expanded + SIGNAL_CHAR[4]


def print_neighbors():
    """Print the neighbors line at top of screen."""
    set_xy(0, 0)
    cache_8x8("Neighbors:    " + BATTERY_CHARS[ord(G_SAVED_DISPLAY[1])])


def redraw_3():
    """Redraw the screen with up to three nodes.

    :return: Mode to enter
    :rtype: int
    """
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    print_neighbors()

    set_xy(0, 1)
    cache_8x8(expand_node_entry(G_SAVED_DISPLAY[2:7])[:-1] if num_nodes > 0 else SPACES_16)
    set_xy(0, 2)
    if num_nodes > 0:
        cache_8x8(expand_node_entry(G_SAVED_DISPLAY[7:12])[:-1] if num_nodes > 1 else SPACES_16)
    else:
        cache_8x8(NONE_YET)
    set_xy(0, 3)
    cache_8x8(expand_node_entry(G_SAVED_DISPLAY[12:17])[:-1] if num_nodes > 2 else SPACES_16)

    return DMODE_LIST_3


def redraw_4():
    """Redraw the screen with up to four nodes.

    :return: Mode to enter
    :rtype: int
    """
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3()

    for y in xrange(4):
        set_xy(0, y)
        line = expand_node_entry(G_SAVED_DISPLAY[(y * 5) + 2:(y * 5) + 7])[:-1] if num_nodes > y else SPACES_16
        cache_8x8(line)

    return DMODE_LIST_4


def redraw_6():
    """Redraw the screen with up to six nodes.

    :return: Mode to enter
    :rtype: int
    """
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3()

    print_neighbors()

    for index in xrange(6):
        set_xy(0 if index < 3 else 9, (index % 3) + 1)
        if index < num_nodes:
            text = expand_node_entry(G_SAVED_DISPLAY[(index * 5) + 2:(index * 5) + 7])
            cache_8x8(text[2:8] + text[-1])
        else:
            cache_8x8(SPACES_7)
        if index < 3:
            cache_8x8(SPACES_2)

    return DMODE_LIST_6


def redraw_8():
    """Redraw the screen with up to eight nodes.

    :return: Mode to enter
    :rtype: int
    """
    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3()

    for index in xrange(8):
        set_xy(0 if index < 4 else 9, index % 4)
        if index < num_nodes:
            text = expand_node_entry(G_SAVED_DISPLAY[(index * 5) + 2:(index * 5) + 7])
            cache_8x8(text[2:8] + text[-1])
        else:
            cache_8x8(SPACES_7)
        if index < 4:
            cache_8x8(SPACES_2)

    return DMODE_LIST_8


def redraw_scroll():
    """Redraw the screen with a scrolling display.

    :return: Mode to enter
    :rtype: int
    """
    global G_SCROLL_POS, G_DISPLAY_MODE

    num_nodes = (len(G_SAVED_DISPLAY) - 2) / 5

    # No items?
    if num_nodes == 0:
        return redraw_3()

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
    # Would scrolling up show more items?
    while (G_SCROLL_POS > 0) and ((G_SCROLL_POS + 3) > (num_nodes - 1)):
        G_SCROLL_POS -= 1

    set_xy(0, 0)

    cache_8x8(UP_ARROW if selected > 0 else RIGHT_ARROW)
    line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 2:(G_SCROLL_POS * 5) + 7])
    cache_8x8(line[1:-1])

    set_xy(0, 1)

    if (G_SCROLL_POS + 1) > (num_nodes - 1):
        cache_8x8(SPACES_16)
    else:
        if selected == (G_SCROLL_POS + 1):
            cache_8x8(RIGHT_ARROW)
        else:
            cache_8x8(DOWN_ARROW if (G_SCROLL_POS + 1) == (num_nodes - 1) else " ")
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 7:(G_SCROLL_POS * 5) + 12])
        cache_8x8(line[1:-1])

    set_xy(0, 2)

    if (G_SCROLL_POS + 2) > (num_nodes - 1):
        cache_8x8(SPACES_16)
    else:
        if selected == (G_SCROLL_POS + 2):
            cache_8x8(RIGHT_ARROW)
        else:
            cache_8x8(DOWN_ARROW if (G_SCROLL_POS + 2) == (num_nodes - 1) else " ")
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 12:(G_SCROLL_POS * 5) + 17])
        cache_8x8(line[1:-1])

    set_xy(0, 3)

    if (G_SCROLL_POS + 3) > (num_nodes - 1):
        cache_8x8(SPACES_16)
    else:
        cache_8x8(RIGHT_ARROW if selected == (G_SCROLL_POS + 3) else DOWN_ARROW)
        line = expand_node_entry(G_SAVED_DISPLAY[(G_SCROLL_POS * 5) + 17:(G_SCROLL_POS * 5) + 22])
        cache_8x8(line[1:-1])

    return DMODE_SCROLL_LIST
