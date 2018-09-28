"""Test cache functions"""

# (c) Copyright 2018, Synapse Wireless Inc.

from mock import call, patch
import os
from unittest import TestCase

from snap_simulator.virtual_machine import SnappyVM

# Constants:
SOURCE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "cops_tool", "display_cache.py")

# Globals:
G_VM = None


def set_xy(x, y):
    global G_VM

    G_VM.globals.G_DRAW_X = x
    G_VM.globals.G_DRAW_Y = y


class TestCache(TestCase):
    """Test cache functions"""
    def setUp(self):
        global G_VM
        G_VM = SnappyVM(SOURCE_PATH)

    @patch("snap_simulator.patch.print_8x8")
    @patch("snap_simulator.patch.set_xy", side_effect=set_xy)
    def test_timer_cache(self, set_xy, print_8x8):
        """Should refresh the display when the timer runs out"""
        # All new text
        G_VM.functions.set_xy(2, 1)
        G_VM.functions.cache_8x8("abcdef")
        G_VM.mocks.assert_has_calls([
            call.set_xy(2, 1),
            call.set_xy(2, 1),

            call.cache_8x8('abcdef'),
            call.print_8x8('abcdef')
        ])
        G_VM.mocks.reset_mock()

        # Change nothing
        G_VM.functions.set_xy(2, 1)
        G_VM.functions.cache_8x8("abcdef")
        G_VM.mocks.assert_has_calls([
            call.set_xy(2, 1),
            call.set_xy(2, 1),

            call.cache_8x8('abcdef'),
            call.set_xy(8, 1)
        ])
        G_VM.mocks.reset_mock()

        # Change beginning
        G_VM.functions.set_xy(2, 1)
        G_VM.functions.cache_8x8("ABcd")
        G_VM.mocks.assert_has_calls([
            call.set_xy(2, 1),
            call.set_xy(2, 1),

            call.cache_8x8('ABcd'),
            call.print_8x8('AB'),
            call.set_xy(6, 1)
        ])
        G_VM.mocks.reset_mock()

        # Change end
        G_VM.functions.set_xy(4, 1)
        G_VM.functions.cache_8x8("cdEF")
        G_VM.mocks.assert_has_calls([
            call.set_xy(4, 1),
            call.set_xy(4, 1),

            call.cache_8x8('cdEF'),
            call.set_xy(6, 1),
            call.print_8x8('EF')
        ])
        G_VM.mocks.reset_mock()

        # Starts and stops
        G_VM.functions.set_xy(2, 1)
        G_VM.functions.cache_8x8("AbCdeF")  # Was ABcdEF
        G_VM.mocks.assert_has_calls([
            call.set_xy(2, 1),
            call.set_xy(2, 1),

            call.cache_8x8('AbCdeF'),
            call.set_xy(3, 1), call.print_8x8('bC'),
            call.set_xy(6, 1), call.print_8x8('e'),
            call.set_xy(8, 1)
        ])
