"""Framework for displaying graphics on a 128x64 OLED screen powered by the SSD1306 chip."""

SSD1306_ADDRESS     = 0x78

SELECT_CONTROL_BYTE = 0x80
SELECT_DATA_BYTE    = 0x40

# Fundamental commands:
def set_contrast(level):
    """Sets the contrast  of the display.

    The display has 256 contrast steps from 0x00 to 0xFF. The segment output current increases 
    as the contrast step value increases.
    """
    send_command(0x81)
    send_command(level)

def set_entire_display_on(enable):
    """Sets the entire display to ON or resets back to GDDRAM values.

    If enable is True, every pixel will be lit.
    If enable is False, each pixel will be lit according to GDDRAM.
    """
    if enable:
        send_command(0xA5)
    else:
        send_command(0xA4)

def set_invert_display(enable):
    """Inverts or resets the display.

    If enable is True, the display will be inverted.
    If enable is False, the display will be restored to normal.
    """
    if enable:
        send_command(0xA7)
    else:
        send_command(0xA6)

def turn_display_off(turn_off):
    """Turns the entire display off or turns it back on to normal operation.

    If turn_off is True, the entire display will be turned off.
    If turn_off is False, the display will be turned back on.
    """
    if turn_off:
        send_command(0xAE)
    else:
        send_command(0xAF)

# Scrolling commands:
def start_horizontal_scroll(scroll_right, start_page, end_page, speed):
    """Scrolls the display horizontally.

    If scroll_right is True, the display will scroll to the right.
    If scroll_right is False, the display will scroll to the left.

    TODO: Figure out what the start and end pages actually do. Values may
    range from 0-7.

    The rate at which the display scrolls is determined by speed, where a
    lower value results in a slower speed. Value may range from 0-7.
    """
    # First stop the display if it's already scrolling:
    stop_scroll()
    # Set the scroll direction:
    if scroll_right:
        send_command(0x26)
    else:
        send_command(0x27)
    # Dummy byte 0x00:
    send_command(0x00)
    # Set start page address:
    send_command(start_page)
    # Set scroll speed:
    send_command(_map_scroll_speed(speed))
    # Set end page address:
    send_command(end_page)
    # Dummy byte 0x00:
    send_command(0x00)
    # Dummy byte 0xFF:
    send_command(0xFF)
    # Start scrolling:
    _start_scroll()

def start_dual_scroll(scroll_right, start_page, end_page, speed, vertical_offset):
    """Scrolls the display vertically and horizontally.

    If scroll_right is True, the display will scroll vertically and to the right.
    If scroll_right is False, the display will scroll vertically and to the left.

    TODO: Figure out what the start and end pages actually do. Values may
    range from 0-7.

    The rate at which the display scrolls is determined by speed, where a
    lower value results in a slower speed. Value may range from 0-7.

    The number of rows that are scrolled vertically per scroll step is defined by
    vertical_offset. Value may range from 0-63 rows.
    """
    # First stop the display if it's already scrolling:
    stop_scroll()
    # Set the scroll direction:
    if scroll_right:
        send_command(0x29)
    else:
        send_command(0x2A)
    # Dummy byte 0x00:
    send_command(0x00)
    # Set start page address:
    send_command(start_page)
    # Set scroll speed:
    send_command(_map_scroll_speed(speed))
    # Set end page address:
    send_command(end_page)
    # Set vertical offset:
    send_command(vertical_offset)
    # Start scrolling:
    _start_scroll()

def stop_scroll():
    """Stops the display from scrolling."""
    send_command(0x2E)

def _start_scroll():
    """Starts scrolling the display based on scrolling setup parameters"""
    send_command(0x2F)

def _map_scroll_speed(speed):
    """Maps a reasonable speed value between 0 and 7 to the weird SSD1306 value."""
    speed_map = (0b011, 0b010, 0b001, 0b110, 0b000, 0b101, 0b100, 0b111)
    return speed_map[speed]

# Addressing-setting commands:

# Hardware-configuration commands:

# Timing and driving scheme setting commands:


def init_display():
    # Init i2c with no pullups (they're external):
    i2cInit(False)

def send_command(command):
    """Sends a command byte to the display controller."""
    cmd = ""
    cmd += chr( SSD1306_ADDRESS )
    cmd += chr( SELECT_CONTROL_BYTE )
    cmd += chr( command )
    i2cWrite(cmd, 10, False)

def send_data(data_string):
    """Sends a data string to the display's GDDRAM"""
    cmd = ""
    cmd += chr( SSD1306_ADDRESS )
    cmd += chr( SELECT_DATA_BYTE )
    cmd += data_string
    i2cWrite(cmd, 10, False)
    