from built_ins import *
from display import G_SAVED_DISPLAY, G_BATTERY_LOW, display

# Constants:
HIGH_WATER_LEN = 240

# Globals:
G_LRU_LIST = ""


# G_SAVED_DISPLAY format:
# Offset | Width | Meaning
#      0 |     1 | Selected item
#      1 |     1 | Battery level (0-11)
#   5n+2 |     1 | Signal strength (-dBm)
#   5n+3 |     1 | Recent message (1=yes, 0=no)
#   5n+4 |     3 | MAC address

def display_neighbors(battery):
    global G_SAVED_DISPLAY

    G_SAVED_DISPLAY = G_SAVED_DISPLAY[0] + chr(battery) + G_SAVED_DISPLAY[2:]
    display()

    # Mark all neighbors no bars and not recently contacted
    for index in xrange(2, len(G_SAVED_DISPLAY), 5):
        G_SAVED_DISPLAY = G_SAVED_DISPLAY[:index] + "\xff\x00" + G_SAVED_DISPLAY[index + 2:]


def update_lru(addr):
    global G_LRU_LIST

    for index in xrange(0, len(G_LRU_LIST), 3):
        if addr == G_LRU_LIST[index:index + 3]:
            G_LRU_LIST = addr + G_LRU_LIST[:index] + G_LRU_LIST[index + 3:]
            break
    else:
        G_LRU_LIST = addr + G_LRU_LIST


def known_addr(addr):
    for index in xrange(2, len(G_SAVED_DISPLAY), 5):
        if addr == G_SAVED_DISPLAY[index + 2:index + 5]:
            return index
    else:
        return 0


def update_neighbor(index, lq):
    global G_SAVED_DISPLAY

    G_SAVED_DISPLAY = G_SAVED_DISPLAY[:index] + chr(lq) + "\x01" + G_SAVED_DISPLAY[index + 2:]


def delete_oldest():
    global G_LRU_LIST, G_SAVED_DISPLAY

    oldest = G_LRU_LIST[-3:]
    G_LRU_LIST = G_LRU_LIST[:-3]
    index = known_addr(oldest)
    if index:
        G_SAVED_DISPLAY = G_SAVED_DISPLAY[:index] + G_SAVED_DISPLAY[index + 5:]


def sort_in_new(lq, addr):
    global G_SAVED_DISPLAY

    for index in xrange(2, len(G_SAVED_DISPLAY), 5):
        if sorts_before(addr, G_SAVED_DISPLAY[index + 2:index + 5]) < 0:
            break
    else:
        index = len(G_SAVED_DISPLAY)

    G_SAVED_DISPLAY = G_SAVED_DISPLAY[:index] + chr(lq) + "\x01" + addr + G_SAVED_DISPLAY[index:]


def sorts_before(new_one, old_one):
    for index in xrange(3):
        new_char = ord(new_one[index])
        old_char = ord(old_one[index])
        if new_char < old_char:
            return -1
        if new_char > old_char:
            return 1
    else:
        return 0


def manage_battery(addr, low):
    global G_BATTERY_LOW

    # Is addr in list?
    for index in xrange(1, len(G_BATTERY_LOW), 3):
        if addr == G_BATTERY_LOW[index:index + 3]:
            # Yes, but should it be?
            if not low:
                # No, remove it
                G_BATTERY_LOW = G_BATTERY_LOW[:index] + G_BATTERY_LOW[index + 3:]
            return
        # No, should it be?
        elif low:
            # Yes, sort it in
            break
    else:
        return

    # Sort in
    for index in xrange(1, len(G_BATTERY_LOW), 3):
        if sorts_before(addr, G_BATTERY_LOW[index:index + 3]) < 0:
            break
    else:
        index = len(G_BATTERY_LOW)

    G_BATTERY_LOW = G_BATTERY_LOW[:index] + addr + G_SAVED_DISPLAY[index:]


def update_from_neighbor(addr, lq_level, battery_low):
    # Update the LRU list
    update_lru(addr)

    # Have we received from this address previously?
    index = known_addr(addr)
    if index:
        # Yes, update the record
        update_neighbor(index, lq_level)
    else:
        # No, is there room for another?
        if len(G_SAVED_DISPLAY) > HIGH_WATER_LEN:
            # No, delete the oldest from the LRU
            delete_oldest()

        # Sort in new record
        sort_in_new(lq_level, addr)

    # Update battery status
    manage_battery(addr, battery_low)
