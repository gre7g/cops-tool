from synapse.nvparams import NV_FEATURE_BITS_ID, NV_AES128_ENABLE_ID
from synapse.switchboard import DS_NULL, DS_STDIO, DS_PACKET_SERIAL

from built_ins import *
from pcb import *
from display import display, display_on_1s, num_to_hex
from display_cache import cache_8x8
from ssd1306.font_8x8 import set_xy, BATTERY_CHARS, UP_ARROW, DOWN_ARROW, RIGHT_ARROW
from ssd1306.ssd1306 import init_display, USE_SPI, low_power

# Constants:
ADC_THRESHOLDS = (879, 893, 908, 922, 937, 951, 965, 980, 994, 1009, 1023)
LOW_LEVEL = 2
PASSIVE_TIMESLOTS = 300
PROBE_TIMESLOTS = 10
MAX_TTL = 5
INITIAL_TIMEOUT = 10
CONTROLLER_TIMEOUT = 180

# Reasons for entering FSM code:
REASON_START = 0
REASON_1S_HOOK = 1
REASON_UP = 2
REASON_DOWN = 3
REASON_LEFT = 4
REASON_RIGHT = 5
REASON_PRESS = 6
REASON_GOTO = 7

# States:
STATE_WAKE_MESSAGE = 0
STATE_CONTROLLER = 1
STATE_MENU1 = 2
STATE_MENU2 = 3
STATE_MENU3 = 4
STATE_MENU4 = 5
STATE_MENU5 = 6
STATE_MENU6 = 7
STATE_MENU7 = 8
STATE_MENU8 = 9
STATE_PROBE = 10
STATE_PASSIVE = 11
STATE_INTERROGATE = 12
STATE_SET_NV = 13

# Globals:
G_TIMESLOT_COUNTDOWN = 0
G_FSM_STATE = 0
G_GENERAL_COUNTDOWN = 0
G_BEST_LQ = None


@setHook(HOOK_STARTUP)
def on_startup():
    global G_MY_TIMESLOT

    writePin(OLED_RESET, False)
    setPinDir(OLED_RESET, True)
    writePin(OLED_RESET, True)

    setPinDir(BUTTON_LEFT, False)
    setPinPullup(BUTTON_LEFT, True)
    monitorPin(BUTTON_LEFT, True)
    setPinDir(BUTTON_RIGHT, False)
    setPinPullup(BUTTON_RIGHT, True)
    monitorPin(BUTTON_RIGHT, True)
    setPinDir(BUTTON_UP, False)
    setPinPullup(BUTTON_UP, True)
    monitorPin(BUTTON_UP, True)
    setPinDir(BUTTON_DOWN, False)
    setPinPullup(BUTTON_DOWN, True)
    monitorPin(BUTTON_DOWN, True)
    setPinDir(BUTTON_PRESS, False)
    setPinPullup(BUTTON_PRESS, True)
    monitorPin(BUTTON_PRESS, True)

    uniConnect(DS_NULL, DS_STDIO)
    uniConnect(DS_NULL, DS_PACKET_SERIAL)

    fsm_go(REASON_START)


def clear_screen():
    for y in xrange(4):
        set_xy(0, y)
        cache_8x8("                ")


@setHook(HOOK_GPIN)
def on_gpin(pin_num, is_set):
    if is_set:
        pass
    elif pin_num == BUTTON_LEFT:
        fsm_go(REASON_LEFT)
    elif pin_num == BUTTON_RIGHT:
        fsm_go(REASON_RIGHT)
    elif pin_num == BUTTON_UP:
        fsm_go(REASON_UP)
    elif pin_num == BUTTON_DOWN:
        fsm_go(REASON_DOWN)
    elif pin_num == BUTTON_PRESS:
        fsm_go(REASON_PRESS)


@setHook(HOOK_STDOUT)
def on_printed():
    """Handle STDOUT hook"""
    # See sleep_fsm.sleep1.advance_to_state() for an explanation
    fsm_go(REASON_GOTO)


def get_battery():
    global G_BATTERY_LOW

    adc = readAdc(BATTERY_ADC)

    # Battery may require calibration. For now, we'll presume linearity between 3.8 and 2.75 to give us full to empty
    # thresholds. These may be tweaked later.
    # Empty = 2.75V = 1.38 @ ADC = 879
    # Full = 3.8V = 1.9V @ ADC =  1022
    for level in xrange(len(ADC_THRESHOLDS)):
        if adc < ADC_THRESHOLDS[level]:
            break
    else:
        level = len(ADC_THRESHOLDS)

    G_BATTERY_LOW = level <= LOW_LEVEL

    return level


def cops_report_in(slots):
    global G_TIMESLOT_COUNTDOWN, G_BEST_LQ

    # Choose a timeslot
    addr = localAddr()
    G_TIMESLOT_COUNTDOWN = (((ord(addr[1]) & 0x7f) << 8) | ord(addr[2])) % slots

    lq = getLq()
    if (G_BEST_LQ is None) or (lq < G_BEST_LQ):
        G_BEST_LQ = lq


def set_battery(string):
    global G_BATTERY_LOW

    G_BATTERY_LOW = string


@setHook(HOOK_1S)
def on_1s(t):
    fsm_go(REASON_1S_HOOK)


@setHook(HOOK_100MS)
def on_100ms(t):
    global G_TIMESLOT_COUNTDOWN, G_BEST_LQ

    if G_TIMESLOT_COUNTDOWN:
        G_TIMESLOT_COUNTDOWN -= 1
        if G_TIMESLOT_COUNTDOWN == 0:
            mcastRpc(1, MAX_TTL, "report_in", G_BEST_LQ, get_battery())
            G_BEST_LQ = None


def report_in(lq, battery):
    pass


def fsm_goto(state):
    global G_FSM_STATE

    ##################################################### WARNING! #####################################################
    #                                                                                                                  #
    # Okay, I really hate putting "clever" hacks into my code, but this one REALLY cleans up the state machine, so let #
    # me explain! There's a bunch of places in the FSM where I've needed to do the same thing over and over. I tried   #
    # moving that repeated code to functions, but found that doing so really hurt the code's legibility. So I added    #
    # this fsm_goto(state) function to move to a new state WITHOUT recursively calling the FSM. Within the machine, it #
    # acts like a go-to-this-state-immediately-without-waiting-for-an-event (a zero second timeout).                   #
    #                                                                                                                  #
    # Under the covers, this works by printing a blank line to the STDIO (which is mapped to NULL) and then trapping   #
    # the "finished printing" handler. That allows us to unwind the stack, return to SNAPpy for a moment, and then     #
    # continue execution. Simple, elegant, but also kind'a clever and tricky. Sorry.                                   #
    #                                                                                                                  #
    ####################################################################################################################

    G_FSM_STATE = state
    print


def general_countdown():
    global G_GENERAL_COUNTDOWN

    G_GENERAL_COUNTDOWN -= 1
    return G_GENERAL_COUNTDOWN == 0


def fsm_go(reason):
    global G_FSM_STATE, G_GENERAL_COUNTDOWN

    if reason == REASON_START:
        fsm_goto(STATE_WAKE_MESSAGE)

    elif G_FSM_STATE == STATE_WAKE_MESSAGE:
        if reason == REASON_GOTO:
            # Boot-up
            init_display(USE_SPI)
            set_xy(0, 0)
            cache_8x8(" COPS Eval Tool ")
            set_xy(0, 1)
            cache_8x8("PUSH/" + RIGHT_ARROW + " for menu ")
            set_xy(0, 2)
            cache_8x8("Else controller ")
            G_GENERAL_COUNTDOWN = INITIAL_TIMEOUT

        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_go(STATE_MENU1)

        set_xy(0, 3)
        cache_8x8("mode in " + str(G_GENERAL_COUNTDOWN) + " sec  ")

    elif G_FSM_STATE == STATE_CONTROLLER:
        if reason == REASON_GOTO:
            low_power()
        elif reason == REASON_UP:
            fsm_goto(STATE_WAKE_MESSAGE)

    elif G_FSM_STATE == STATE_MENU1:
        # PASSIVE OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8("== MAIN MENU == ")
            set_xy(0, 1)
            cache_8x8(RIGHT_ARROW + " Passive mode  ")
            set_xy(0, 2)
            cache_8x8("  Probe mode    ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Controller    ")
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU2)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_PASSIVE)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU2:
        # PROBE OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8("== MAIN MENU == ")
            set_xy(0, 1)
            cache_8x8("  Passive mode  ")
            set_xy(0, 2)
            cache_8x8(RIGHT_ARROW + " Probe mode    ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Controller    ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU1)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU3)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_PROBE)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU3:
        # CONTROLLER OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Passive mode  ")
            set_xy(0, 1)
            cache_8x8("  Probe mode    ")
            set_xy(0, 2)
            cache_8x8(RIGHT_ARROW + " Controller    ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Interrogate   ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU7)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU4)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU4:
        # INTERROGATE OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Probe mode    ")
            set_xy(0, 1)
            cache_8x8("  Controller    ")
            set_xy(0, 2)
            cache_8x8(RIGHT_ARROW + " Interrogate   ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Set NV params ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU6)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU5)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_INTERROGATE)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU5:
        # SET NV PARAMS OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Probe mode    ")
            set_xy(0, 1)
            cache_8x8("  Controller    ")
            set_xy(0, 2)
            cache_8x8("  Interrogate   ")
            set_xy(0, 3)
            cache_8x8(RIGHT_ARROW + " Set NV params ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU4)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_SET_NV)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU6:
        # CONTROLLER OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Probe mode    ")
            set_xy(0, 1)
            cache_8x8(RIGHT_ARROW + "  Controller    ")
            set_xy(0, 2)
            cache_8x8("  Interrogate   ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Set NV params ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU3)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU4)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU7:
        # PROBE OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Passive mode  ")
            set_xy(0, 1)
            cache_8x8(RIGHT_ARROW + " Probe mode    ")
            set_xy(0, 2)
            cache_8x8("  Controller    ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Interrogate   ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU2)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU3)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_PROBE)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_PROBE:
        if (reason == REASON_GOTO) or (reason == REASON_PRESS):
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_1S_HOOK:
            display_on_1s()
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_MENU1)

    elif G_FSM_STATE == STATE_PASSIVE:
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_1S_HOOK:
            display_on_1s()
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            elif (G_GENERAL_COUNTDOWN % PASSIVE_TIMESLOTS) == 0:
                mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_MENU1)

    elif G_FSM_STATE == STATE_INTERROGATE:
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            clear_screen()
            set_xy(0, 0)
            cache_8x8("TODO:INTERROGATE")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_MENU1)

    elif G_FSM_STATE == STATE_SET_NV:
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8("Channel: " + str(getChannel()) + "     ")
            set_xy(0, 1)
            cache_8x8("Network ID: " + num_to_hex(getNetId()))
            set_xy(0, 2)
            cache_8x8("FeatureBts: " + num_to_hex(loadNvParam(NV_FEATURE_BITS_ID)))
            set_xy(0, 3)
            cache_8x8("Encryption: " + str(loadNvParam(NV_AES128_ENABLE_ID)) + "   ")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_MENU1)
