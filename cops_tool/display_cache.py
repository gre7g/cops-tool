"""Cache the display to accelerate updates."""

# (c)2018 Synapse Wireless,  Inc.

from ssd1306.font_8x8 import print_8x8, set_xy, G_DRAW_X, G_DRAW_Y
from ssd1306.ssd1306 import turn_display_on, enable_charge_pump

G_DISPLAY_CACHE = "\xff" * 16 * 4


def low_power():
    """Turn display off"""
    global G_DISPLAY_CACHE

    turn_display_on(False)
    enable_charge_pump(False)
    G_DISPLAY_CACHE = "\xff" * 16 * 4


def flush_change(string):
    """Flush a change out to the display at the current XY.

    :param str string: String to write
    """
    global G_DISPLAY_CACHE

    # Update the cache
    offset = G_DRAW_X + (G_DRAW_Y * 16)
    G_DISPLAY_CACHE = G_DISPLAY_CACHE[:offset] + string + G_DISPLAY_CACHE[offset + len(string):]

    # Display it
    print_8x8(string)


def cache_8x8(string):
    """Write the changed portions of a string out to the display.

    :param str string: String to write
    """
    # Have any characters changed?
    offset = G_DRAW_X + (G_DRAW_Y * 16)
    length = len(string)
    if string == G_DISPLAY_CACHE[offset:offset + length]:
        # Nope, unchanged. Advance and return.
        set_xy(G_DRAW_X + length, G_DRAW_Y)
        return

    # At least one character has changed. Loop over all to find changes.
    x = G_DRAW_X
    change_starts = None
    for index in xrange(length):
        # Has this character changed?
        if string[index] == G_DISPLAY_CACHE[offset + index:offset + index + 1]:
            # No, this one was the same, but what about the ones before it?
            if change_starts is not None:
                # This is the end of a change, so flush that change out
                flush_change(string[change_starts:index])
                change_starts = None
        else:
            # Yes, this character changed, but is it the first?
            if change_starts is None:
                # Yes, this is the first character to change. Update write position.
                if index:
                    set_xy(x + index, G_DRAW_Y)
                change_starts = index

    # Loop is finished, but is there an unwritten change to flush?
    if change_starts is None:
        # Nothing has changed, so update the position
        set_xy(x + length, G_DRAW_Y)
    else:
        # Yes we have an unwritten change, flush it
        flush_change(string[change_starts:])
