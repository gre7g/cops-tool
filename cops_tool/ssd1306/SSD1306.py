"""Framework for displaying graphics on a 128x64 OLED screen powered by the SSD1306 chip."""

from built_ins import *

try:
    # Fake import to appease PyCharm
    from top_level import OLED_CS
except ImportError:
    pass

SSD1306_ADDRESS = 0x78
SSD1306_ROWS = 64
SSD1306_COLS = 128

SELECT_CONTROL_BYTE = 0x80
SELECT_DATA_BYTE = 0x40

USE_INVALID = 0x00
USE_I2C = 0x01
USE_SPI = 0x02

MODE_HORIZONTAL = 0
MODE_VERTICAL = 1
MODE_PAGE = 2

INITIAL_CONTRAST = 0xCF

G_CONNECTION_TYPE = USE_INVALID


# Fundamental commands:
def set_contrast(level):
    """Sets the contrast  of the display.

    The display has 256 contrast steps from 0x00 to 0xFF. The segment output current increases
    as the contrast step value increases.
    """
    send_command(0x81)
    send_command(level)


def clear_entire_display(pixels_on):
    """Sets the entire display to ON or resets back to GDDRAM values.

    :param bool pixels_on: True for pixels on, False for off
    """
    send_command(0xA5 if pixels_on else 0xA4)


def set_invert_display(enable):
    """Inverts or resets the display.

    :param bool enable: True for inverted, False for normal
    """
    send_command(0xA7 if enable else 0xA6)


def turn_display_on(turn_on):
    """Turns the entire display on or off.

    :param bool turn_on: True for on, False for off
    """
    send_command(0xAF if turn_on else 0xAE)


def clear_ram():
    """Clears the graphics RAM."""
    set_page_address(0, 7)
    set_column_address(0, 127)
    for i in xrange(SSD1306_COLS * SSD1306_ROWS / 128):
        send_data("\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    set_page_address(0, 7)
    set_column_address(0, 127)


# Scrolling commands:
def start_horizontal_scroll(scroll_right, start_page, end_page, speed, top_fixed_rows, scroll_rows):
    """Scrolls the display horizontally.

    If scroll_right is True, the display will scroll to the right.
    If scroll_right is False, the display will scroll to the left.

    The start and end pages values may range from 0-7.

    The rate at which the display scrolls is determined by speed, where a
    lower value results in a slower speed. Value may range from 0-7.

    The vertical area that actually scrolls is defined as the scroll_row rows
    after the top_fixed_rows rows. For example:
           Scroll whole screen: top_fixed_rows=0, scroll_rows=64
                 Static header: top_fixed_rows=8, scroll_rows=48
      Static header and footer: top_fixed_rows=8, scroll_rows=40
                 Static footer: top_fixed_rows=0, scroll_rows=48
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
    send_command(map_scroll_speed(speed))
    # Set end page address:
    send_command(end_page)
    # Dummy byte 0x00:
    send_command(0x00)
    # Dummy byte 0xFF:
    send_command(0xFF)
    # Set the vertical scroll area:
    set_scroll_area(top_fixed_rows, scroll_rows)
    # Start scrolling:
    start_scroll()


def start_dual_scroll(scroll_right, start_page, end_page, speed, vertical_offset, top_fixed_rows, scroll_rows):
    """Scrolls the display vertically and horizontally.

    If scroll_right is True, the display will scroll vertically and to the right.
    If scroll_right is False, the display will scroll vertically and to the left.

    The start and end pages values may range from 0-7.

    The rate at which the display scrolls is determined by speed, where a
    lower value results in a slower speed. Value may range from 0-7.

    The number of rows that are scrolled vertically per scroll step is defined by
    vertical_offset. Value may range from 0-63 rows.

    The vertical area that actually scrolls is defined as the scroll_row rows
    after the top_fixed_rows rows. For example:
           Scroll whole screen: top_fixed_rows=0, scroll_rows=64
                 Static header: top_fixed_rows=8, scroll_rows=48
      Static header and footer: top_fixed_rows=8, scroll_rows=40
                 Static footer: top_fixed_rows=0, scroll_rows=48
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
    send_command(map_scroll_speed(speed))
    # Set end page address:
    send_command(end_page)
    # Set vertical offset:
    send_command(vertical_offset)
    # Set the vertical scroll area:
    set_scroll_area(top_fixed_rows, scroll_rows)
    # Start scrolling:
    start_scroll()


def stop_scroll():
    """Stops the display from scrolling."""
    send_command(0x2E)


def start_scroll():
    """Starts scrolling the display based on scrolling setup parameters"""
    send_command(0x2F)


def map_scroll_speed(speed):
    """Maps a reasonable speed value between 0 and 7 to the weird SSD1306 value."""
    speed_map = (0b011, 0b010, 0b001, 0b110, 0b000, 0b101, 0b100, 0b111)
    return speed_map[speed]


def set_scroll_area(top_fixed_rows, scroll_rows):
    send_command(0xA3)
    send_command(top_fixed_rows)
    send_command(scroll_rows)


# Addressing-setting commands:
def set_start_col_addr(address):
    """Sets the column starts address register for Page Addressing Mode.

    :param int address: 0x00-0xff
    """
    send_command(address & 0x0F)
    send_command((address >> 4) | 0x10)


def set_addressing_mode(mode):
    """Sets the memory addressing mode for the display RAM.

    :param int mode: MODE_HORIZONTAL, MODE_VERTICAL, or MODE_PAGE
    """
    send_command(0x20)
    send_command(mode)


def set_column_address(start_addr, end_addr):
    """Sets the start and end column pointers, resetting the current column to the start column.

    :param int start_addr: Start address
    :param int end_addr: End address
    """
    send_command(0x21)
    send_command(start_addr)
    send_command(end_addr)


def set_page_address(start_page, end_page):
    """Sets the start and end page pointers, resetting the current page to the start page.

    :param int start_page: Start page
    :param int end_page: End page
    """
    send_command(0x22)
    send_command(start_page)
    send_command(end_page)


# Hardware-configuration commands:
def set_display_start_line(line):
    """Sets the display RAMs start line register.

     :param int line: Line 0-64
     """
    send_command(0x40 | line)


def set_multiplex_ratio(ratio):
    """Sets the multiplex ratio.

     :param int ratio: Ratio from 16-63
     """
    send_command(0xA8)
    send_command(ratio)


def set_display_offset(offset):
    """Sets the vertical display offset.

    :param int offset: Offset from 0-63
    """
    send_command(0xD3)
    send_command(offset)


def enable_charge_pump(enable):
    """Enables the internally-regulated charge pump supply voltage.

    :param bool enable: True for on, False for off"""
    send_command(0x8D)
    send_command(0x14 if enable else 0x10)


def set_segment_remap(remap):
    """Sets the segment remapping.

    :param bool remap: True remaps column 127 to SEG0, False maps column 0 to SEG0
    """
    send_command(0xA1 if remap else 0xA0)


def set_com_scan_direction(invert):
    """Inverts the COM output scan direction.

    :param invert: True to invert mode scan from COM[N-1] COM0, False for normal (COM0 to COM[N-1])
    """
    send_command(0xC8 if invert else 0xC0)


def set_com_pins_config(set_sequential, enable_remap):
    """Sets the COM pin sequencing and remapping configurations.

    :param bool set_sequential: True for sequential sequencing, False for alternating sequencing
    :param bool enable_remap: True for left/right remapping, False for no remapped
    """
    a4_bit = 0x00 if set_sequential else 0x10
    a5_bit = 0x20 if enable_remap else 0x00

    send_command(0xDA)
    send_command(0x02 | a4_bit | a5_bit)


# Timing and driving scheme setting commands:
def set_clock_divide_ratio_frequency(ratio, frequency):
    """Sets the display clock's divide ratio and oscillator frequency."""
    send_command(0xD5)
    send_command(frequency << 4 | ratio)


def set_precharge_period(phase1_period, phase2_period):
    """Sets the duration of the pre-charge period of phase 1 and 2.

    :param int phase1_period: 1-15
    :param int phase2_period: 1-15
    """
    send_command(0xD9)
    send_command(phase1_period | (phase2_period << 4))


def set_vcom_deselect_level(level):
    """Set the V_COMH regulator output voltage.

    :param int level: 0-7 -> output voltage to 0.65 - 1.07 times VCC, in increments of 0.06 times VCC
    """
    send_command(0xDB)
    send_command(level << 4)


def send_noop():
    """Sends a no-op to the display controller."""
    send_command(0xE3)


def init_display(connection_type):
    """Initialize connection

    :param int connection_type: USE_I2C or USE_SPI
    """
    connection_init(connection_type)
    turn_display_on(False)
    set_clock_divide_ratio_frequency(0, 4)
    set_multiplex_ratio(63)
    set_display_offset(0)
    set_display_start_line(0)
    enable_charge_pump(True)
    set_addressing_mode(MODE_HORIZONTAL)
    set_segment_remap(True)
    set_com_scan_direction(True)
    set_com_pins_config(False, False)
    # Set initial contrast:
    set_contrast(INITIAL_CONTRAST)
    set_precharge_period(1, 15)
    set_vcom_deselect_level(4)
    clear_ram()
    turn_display_on(True)
    set_invert_display(False)


def connection_init(connection_type):
    """Initialize connection

    :param int connection_type: USE_I2C or USE_SPI
    """
    global G_CONNECTION_TYPE

    G_CONNECTION_TYPE = connection_type

    if connection_type == USE_I2C:
        i2cInit(False)
    elif connection_type == USE_SPI:
        setPinDir(OLED_CS, True)
        writePin(OLED_CS, True)
        spiInit(0, 0, True, False)
    else:
        print "Invalid connection type."


def send_command(command):
    """Sends a command byte to the display controller.

    :param int command: Command byte 0x00-0xff
    """
    if G_CONNECTION_TYPE == USE_I2C:
        i2cWrite(chr(SSD1306_ADDRESS) + chr(SELECT_CONTROL_BYTE) + chr(command), 10, False)
    else:
        # spiWrite is actually appropriate, but broken!
        spiXfer(chr(SELECT_CONTROL_BYTE | (command >> 1)) + chr((command << 7) & 0x80), 1)


def send_data(data_string):
    """Sends a data string to the display's GDDRAM.

    :param str data_string: Data string
    """
    if G_CONNECTION_TYPE == USE_I2C:
        i2cWrite(chr(SSD1306_ADDRESS) + chr(SELECT_DATA_BYTE) + data_string, 10, False)
    else:
        for character in data_string:
            byte_value = ord(character)
            spiXfer(chr(byte_value >> 1) + chr((byte_value << 7) & 0x80), 1)
