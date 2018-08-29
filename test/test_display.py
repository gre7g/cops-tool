"""Test display functions"""

# (c) Copyright 2018, Synapse Wireless Inc.

from mock import call, patch
import os
from unittest import TestCase

from snap_simulator.virtual_machine import SnappyVM

SOURCE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "cops_tool", "display.py")


class TestDisplay(TestCase):
    """Test display functions"""
    def setUp(self):
        self.vm = SnappyVM(SOURCE_PATH)

    @patch("snap_simulator.patch.display")
    def test_timer_hook(self, display):
        """Should refresh the display when the timer runs out"""
        self.vm.globals.G_REDUCE_COUNTDOWN = 3
        self.vm.globals.G_SAVED_DISPLAY = "display string"
        self.vm.functions.display_on_1s(1000)
        self.vm.functions.display_on_1s(2000)
        self.vm.functions.display_on_1s(3000)
        self.vm.functions.display_on_1s(4000)
        self.vm.functions.display_on_1s(5000)
        self.vm.mocks.assert_has_calls([
            call.display_on_1s(1000),
            call.display_on_1s(2000),
            call.display_on_1s(3000),
            call.display('display string'),
            call.display_on_1s(4000),
            call.display_on_1s(5000)
        ])
        self.assertEqual(self.vm.globals.G_REDUCE_COUNTDOWN, -1)

    def test_find_ideal_mode(self):
        """Should be able to find the ideal number of nodes."""
        for nodes, mode in [(0, 0), (1, 0), (2, 0), (3, 0), (4, 1), (5, 2), (6, 2), (7, 3), (8, 3), (9, 4)]:
            self.assertEqual(self.vm.functions.find_ideal_mode(nodes), mode)

    @patch("snap_simulator.patch.redraw_3", return_value=0)
    @patch("snap_simulator.patch.redraw_4", return_value=1)
    @patch("snap_simulator.patch.redraw_6", return_value=2)
    @patch("snap_simulator.patch.redraw_8", return_value=3)
    @patch("snap_simulator.patch.redraw_scroll", return_value=4)
    def test_display(self, redraw_scroll, redraw_8, redraw_6, redraw_4, redraw_3):
        """Should call the appropriate display method"""

        # Increasing display mode
        for i in xrange(10):
            self.vm.functions.display("HH" + "".join(str(j) * 5 for j in xrange(i + 1)))
        self.vm.mocks.assert_has_calls([
            call.display('HH00000'),
            call.redraw_3(True),

            call.display('HH0000011111'),
            call.redraw_3(False),

            call.display('HH000001111122222'),
            call.redraw_3(False),

            call.display('HH00000111112222233333'),
            call.redraw_4(True),

            call.display('HH0000011111222223333344444'),
            call.redraw_6(True),

            call.display('HH000001111122222333334444455555'),
            call.redraw_6(False),

            call.display('HH00000111112222233333444445555566666'),
            call.redraw_8(True),

            call.display('HH0000011111222223333344444555556666677777'),
            call.redraw_8(False),

            call.display('HH000001111122222333334444455555666667777788888'),
            call.redraw_scroll(True),

            call.display('HH00000111112222233333444445555566666777778888899999'),
            call.redraw_scroll(False)
        ])
        self.vm.mocks.reset_mock()

        # Decreasing display mode
        self.vm.functions.display("HH0000011111222223333344444555556666677777")
        self.vm.functions.display_on_1s(1000)
        self.vm.functions.display_on_1s(2000)
        self.vm.functions.display_on_1s(3000)
        self.vm.functions.display_on_1s(4000)
        self.vm.functions.display("HH00000111112222233333")
        self.vm.functions.display_on_1s(5000)
        self.vm.functions.display_on_1s(6000)
        self.vm.functions.display_on_1s(7000)
        self.vm.functions.display_on_1s(8000)
        self.vm.functions.display_on_1s(9000)
        self.vm.mocks.assert_has_calls([
            call.display('HH0000011111222223333344444555556666677777'),
            call.redraw_scroll(False),

            call.display_on_1s(1000),

            call.display_on_1s(2000),

            call.display_on_1s(3000),
            call.redraw_8(True),

            call.display_on_1s(4000),

            call.display('HH00000111112222233333'),
            call.redraw_8(False),

            call.display_on_1s(5000),

            call.display_on_1s(6000),

            call.display_on_1s(7000),
            call.redraw_4(True),

            call.display_on_1s(8000),

            call.display_on_1s(9000)
        ])

        # Can change mode
        redraw_scroll.return_value = 0
        self.vm.functions.display("HH00000111112222233333444445555566666777778888899999")
        self.assertEqual(self.vm.globals.G_DISPLAY_MODE, 0)

    def test_expand_node_entry(self):
        """Should expand a node entry to something human legible."""
        for signal_str, recent, mac, expected in [
            (0, False, "\x01\x23\x45", "  012345    0dBm\x10"),
            (1, True, "\x67\x89\xab", "* 6789ab   -1dBm\x10"),
            (9, False, "\xcd\xef\x01", "  cdef01   -9dBm\x10"),
            (10, False, "\x01\x23\x45", "  012345  -10dBm\x10"),
            (20, False, "\x01\x23\x45", "  012345  -20dBm\x10"),
            (21, False, "\x01\x23\x45", "  012345  -21dBm\x0f"),
            (40, False, "\x01\x23\x45", "  012345  -40dBm\x0f"),
            (41, False, "\x01\x23\x45", "  012345  -41dBm\x0e"),
            (60, False, "\x01\x23\x45", "  012345  -60dBm\x0e"),
            (61, False, "\x01\x23\x45", "  012345  -61dBm\r"),
            (80, False, "\x01\x23\x45", "  012345  -80dBm\r"),
            (81, False, "\x01\x23\x45", "  012345  -81dBm "),
            (99, False, "\x01\x23\x45", "  012345  -99dBm "),
            (100, False, "\x01\x23\x45", "  012345 -100dBm "),
        ]:
            node = chr(signal_str) + ("\x01" if recent else "\x00") + mac
            self.assertEqual(self.vm.functions.expand_node_entry(node), expected)

    @patch("snap_simulator.patch.expand_node_entry", return_value="* abcdef -100dBm#")
    @patch("snap_simulator.patch.clear_ram")
    @patch("snap_simulator.patch.set_xy")
    @patch("snap_simulator.patch.print_8x8")
    def test_redraw_3(self, print_8x8, set_xy, clear_ram, expand_node_entry):
        """Should be able to draw 0-3 nodes."""
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00"
        self.assertEqual(self.vm.functions.redraw_3(True), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_3(True),
            call.clear_ram(), call.print_8x8('Neighbors:    \x00\x01'),
            call.set_xy(0, 1), call.print_8x8('                '),
            call.set_xy(0, 2), call.print_8x8('  (none yet)    '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x01aaaaa"
        self.assertEqual(self.vm.functions.redraw_3(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_3(False),
            call.set_xy(14, 0), call.print_8x8('\x02\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('                '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x02aaaaabbbbb"
        self.assertEqual(self.vm.functions.redraw_3(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_3(False),
            call.set_xy(14, 0), call.print_8x8('\x03\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x03aaaaabbbbbccccc"
        self.assertEqual(self.vm.functions.redraw_3(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_3(False),
            call.set_xy(14, 0), call.print_8x8('\x04\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 3), call.expand_node_entry('ccccc'), call.print_8x8('* abcdef -100dBm')
        ])

    @patch("snap_simulator.patch.redraw_3", return_value=0)
    @patch("snap_simulator.patch.expand_node_entry", return_value="* abcdef -100dBm#")
    @patch("snap_simulator.patch.clear_ram")
    @patch("snap_simulator.patch.set_xy")
    @patch("snap_simulator.patch.print_8x8")
    def test_redraw_4(self, print_8x8, set_xy, clear_ram, expand_node_entry, redraw_3):
        """Should be able to draw 0-4 nodes."""
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00"
        self.assertEqual(self.vm.functions.redraw_4(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_4(False),
            call.redraw_3(True)
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaa"
        self.assertEqual(self.vm.functions.redraw_4(True), 1)
        self.vm.mocks.assert_has_calls([
            call.redraw_4(True),
            call.clear_ram(),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8('                '),
            call.set_xy(0, 2), call.print_8x8('                '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbb"
        self.assertEqual(self.vm.functions.redraw_4(False), 1)
        self.vm.mocks.assert_has_calls([
            call.redraw_4(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('                '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbccccc"
        self.assertEqual(self.vm.functions.redraw_4(False), 1)
        self.vm.mocks.assert_has_calls([
            call.redraw_4(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccddddd"
        self.assertEqual(self.vm.functions.redraw_4(False), 1)
        self.vm.mocks.assert_has_calls([
            call.redraw_4(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('* abcdef -100dBm'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('* abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

    @patch("snap_simulator.patch.redraw_3", return_value=0)
    @patch("snap_simulator.patch.expand_node_entry", return_value="* abcdef -100dBm#")
    @patch("snap_simulator.patch.clear_ram")
    @patch("snap_simulator.patch.set_xy")
    @patch("snap_simulator.patch.print_8x8")
    def test_redraw_6(self, print_8x8, set_xy, clear_ram, expand_node_entry, redraw_3):
        """Should be able to draw 0-6 nodes."""
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00"
        self.assertEqual(self.vm.functions.redraw_6(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.redraw_3(True)
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x04aaaaa"
        self.assertEqual(self.vm.functions.redraw_6(True), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(True),
            call.clear_ram(),
            call.print_8x8('Neighbors:    \x05\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.print_8x8('       '),
            call.set_xy(0, 3), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x05aaaaabbbbb"
        self.assertEqual(self.vm.functions.redraw_6(False), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.set_xy(14, 0), call.print_8x8('\x06\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x06aaaaabbbbbccccc"
        self.assertEqual(self.vm.functions.redraw_6(False), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.set_xy(14, 0), call.print_8x8('\x07\x01'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x07aaaaabbbbbcccccddddd"
        self.assertEqual(self.vm.functions.redraw_6(False), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.set_xy(14, 0), call.print_8x8('\x07\x08'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x08aaaaabbbbbcccccdddddeeeee"
        self.assertEqual(self.vm.functions.redraw_6(False), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.set_xy(14, 0), call.print_8x8('\x07\t'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x09aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_6(False), 2)
        self.vm.mocks.assert_has_calls([
            call.redraw_6(False),
            call.set_xy(14, 0), call.print_8x8('\x07\n'),
            call.set_xy(0, 1), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 3), call.expand_node_entry('fffff'), call.print_8x8('abcdef#')
        ])
        self.vm.mocks.reset_mock()

    @patch("snap_simulator.patch.redraw_3", return_value=0)
    @patch("snap_simulator.patch.expand_node_entry", return_value="* abcdef -100dBm#")
    @patch("snap_simulator.patch.clear_ram")
    @patch("snap_simulator.patch.set_xy")
    @patch("snap_simulator.patch.print_8x8")
    def test_redraw_8(self, print_8x8, set_xy, clear_ram, expand_node_entry, redraw_3):
        """Should be able to draw 0-8 nodes."""
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00"
        self.assertEqual(self.vm.functions.redraw_8(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.redraw_3(True)
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaa"
        self.assertEqual(self.vm.functions.redraw_8(True), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(True),
            call.clear_ram(),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.print_8x8('       '),
            call.set_xy(0, 2), call.print_8x8('       '),
            call.set_xy(0, 3), call.print_8x8('       '),
            call.set_xy(9, 0), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbb"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.print_8x8('       '),
            call.set_xy(0, 3), call.print_8x8('       '),
            call.set_xy(9, 0), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbccccc"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.print_8x8('       '),
            call.set_xy(9, 0), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccddddd"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 0), call.print_8x8('       '),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccdddddeeeee"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 0), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.print_8x8('       '),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 0), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('fffff'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.print_8x8('       '),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccdddddeeeeefffffggggg"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 0), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('fffff'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.expand_node_entry('ggggg'), call.print_8x8('abcdef#'),
            call.set_xy(9, 3), call.print_8x8('       ')
        ])
        self.vm.mocks.reset_mock()

        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccdddddeeeeefffffggggghhhhh"
        self.assertEqual(self.vm.functions.redraw_8(False), 3)
        self.vm.mocks.assert_has_calls([
            call.redraw_8(False),
            call.set_xy(0, 0), call.expand_node_entry('aaaaa'), call.print_8x8('abcdef#'),
            call.set_xy(0, 1), call.expand_node_entry('bbbbb'), call.print_8x8('abcdef#'),
            call.set_xy(0, 2), call.expand_node_entry('ccccc'), call.print_8x8('abcdef#'),
            call.set_xy(0, 3), call.expand_node_entry('ddddd'), call.print_8x8('abcdef#'),
            call.set_xy(9, 0), call.expand_node_entry('eeeee'), call.print_8x8('abcdef#'),
            call.set_xy(9, 1), call.expand_node_entry('fffff'), call.print_8x8('abcdef#'),
            call.set_xy(9, 2), call.expand_node_entry('ggggg'), call.print_8x8('abcdef#'),
            call.set_xy(9, 3), call.expand_node_entry('hhhhh'), call.print_8x8('abcdef#')
        ])
        self.vm.mocks.reset_mock()

    @patch("snap_simulator.patch.redraw_3", return_value=0)
    @patch("snap_simulator.patch.expand_node_entry", return_value="* abcdef -100dBm#")
    @patch("snap_simulator.patch.clear_ram")
    @patch("snap_simulator.patch.set_xy")
    @patch("snap_simulator.patch.print_8x8")
    def test_redraw_scroll(self, print_8x8, set_xy, clear_ram, expand_node_entry, redraw_3):
        """Should be able to draw a scrolling list of nodes."""
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 0)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.redraw_3(True)
        ])
        self.vm.mocks.reset_mock()

        # Six items, select the first
        self.vm.globals.G_SAVED_DISPLAY = "\x00\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(True), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(True),
            call.clear_ram(),
            call.set_xy(0, 0), call.print_8x8('\x13'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8(' '),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Down to second
        self.vm.globals.G_SAVED_DISPLAY = "\x01\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8('\x13'),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8(' '),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Down to third
        self.vm.globals.G_SAVED_DISPLAY = "\x02\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('\x13'),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Down to fourth
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('\x13'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('eeeee'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Down to last
        self.vm.globals.G_SAVED_DISPLAY = "\x05\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8(' '),
            call.expand_node_entry('eeeee'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x13'),
            call.expand_node_entry('fffff'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Up one
        self.vm.globals.G_SAVED_DISPLAY = "\x04\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('\x13'),
            call.expand_node_entry('eeeee'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('fffff'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Up one
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbbcccccdddddeeeeefffff"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8('\x13'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8(' '),
            call.expand_node_entry('eeeee'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('fffff'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Reduce list
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbbcccccdddddeeeee"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('\x13'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x12'),
            call.expand_node_entry('eeeee'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Reduce list
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbbcccccddddd"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8(' '),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('\x13'),
            call.expand_node_entry('ddddd'), call.print_8x8(' abcdef -100dBm')
        ])
        self.vm.mocks.reset_mock()

        # Reduce list
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbbccccc"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8(' '),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('\x13'),
            call.expand_node_entry('ccccc'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        # Reduce list
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaabbbbb"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x11'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8('\x13'),
            call.expand_node_entry('bbbbb'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 2), call.print_8x8('                '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()

        # Reduce list
        self.vm.globals.G_SAVED_DISPLAY = "\x03\x00aaaaa"
        self.assertEqual(self.vm.functions.redraw_scroll(False), 4)
        self.vm.mocks.assert_has_calls([
            call.redraw_scroll(False),
            call.set_xy(0, 0), call.print_8x8('\x13'),
            call.expand_node_entry('aaaaa'), call.print_8x8(' abcdef -100dBm'),
            call.set_xy(0, 1), call.print_8x8('                '),
            call.set_xy(0, 2), call.print_8x8('                '),
            call.set_xy(0, 3), call.print_8x8('                ')
        ])
        self.vm.mocks.reset_mock()
