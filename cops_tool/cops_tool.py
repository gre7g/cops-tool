from synapse.nvparams import NV_FEATURE_BITS_ID, NV_AES128_ENABLE_ID, NV_CHANNEL_ID, NV_NETWORK_ID, NV_AES128_KEY_ID
from synapse.switchboard import DS_NULL, DS_STDIO, DS_PACKET_SERIAL

from built_ins import *
from pcb import *
from display import display_on_1s, num_to_hex
from display_cache import cache_8x8, low_power
from neighbor_mgmt import update_from_neighbor, display_neighbors, clear_not_heard_from
from ssd1306.font_8x8 import set_xy, UP_ARROW, DOWN_ARROW, RIGHT_ARROW, INVERTED_HEX, LEFT_ARROW
from ssd1306.ssd1306 import init_display, USE_SPI

# Constants:
ADC_THRESHOLDS = (879, 893, 908, 922, 937, 951, 965, 980, 994, 1009, 1023)
BATTERY_LOW_LEVEL = 2
PASSIVE_TIMESLOTS = 300
PROBE_TIMESLOTS = 10
MAX_TTL = 5
INITIAL_TIMEOUT = 10
CONTROLLER_TIMEOUT = 180
CRYPTO_KEY = "\x7c\x8d\x48\x3c\xd0\x63\xfd\x94\xb1\xb6\x8d\x8f\x83\x1e\x17\xb1"

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
STATE_MENU9 = 10
STATE_PROBE = 11
STATE_PASSIVE = 12
STATE_INTERROGATE = 13
STATE_SET_NV1 = 14
STATE_SET_NV2 = 15
STATE_SET_NV3 = 16
STATE_SET_NV4 = 17
STATE_SET_NV5 = 18
STATE_SET_NV6 = 19
STATE_SET_NV7 = 20
STATE_SET_NV8 = 21
STATE_SET_NV9 = 22
STATE_SET_NV10 = 23
STATE_SET_NV11 = 24
STATE_SET_NV12 = 25
STATE_SET_NV13 = 26
STATE_SET_NV14 = 27
STATE_SET_NV15 = 28
STATE_SIMON1 = 29
STATE_SIMON2 = 30
STATE_SIMON3 = 31
STATE_SIMON4 = 32
STATE_SIMON5 = 33
STATE_SIMON6 = 34
STATE_SIMON7 = 35
STATE_SIMON8 = 36
STATE_SIMON9 = 37
STATE_SIMON10 = 38
STATE_SIMON11 = 39
STATE_SIMON12 = 40
STATE_SIMON13 = 41
STATE_SIMON14 = 42

# Globals:
G_TIMESLOT_COUNTDOWN = 0
G_FSM_STATE = 0
G_GENERAL_COUNTDOWN = 0
G_BEST_LQ = None
G_HEARD_FROM = ""
G_NEED_REBOOT = False
G_SEQUENCE = ""
G_POSITION = 0


@setHook(HOOK_STARTUP)
def on_startup():
    global G_MY_TIMESLOT

    writePin(OLED_RESET, False)
    setPinDir(OLED_RESET, True)
    writePin(OLED_RESET, True)

    setPinDir(BUTTON_LEFT, False)
    monitorPin(BUTTON_LEFT, True)
    setPinDir(BUTTON_RIGHT, False)
    monitorPin(BUTTON_RIGHT, True)
    setPinDir(BUTTON_UP, False)
    monitorPin(BUTTON_UP, True)
    setPinDir(BUTTON_DOWN, False)
    monitorPin(BUTTON_DOWN, True)
    setPinDir(BUTTON_PRESS, False)
    monitorPin(BUTTON_PRESS, True)

    uniConnect(DS_NULL, DS_STDIO)
    # uniConnect(DS_NULL, DS_PACKET_SERIAL)

    fsm_go(REASON_START)

    # Make sure the encryption key is set
    if loadNvParam(NV_AES128_KEY_ID) != CRYPTO_KEY:
        saveNvParam(NV_AES128_KEY_ID, CRYPTO_KEY)
        reboot()


def clear_screen():
    for y in xrange(4):
        set_xy(0, y)
        cache_8x8("                ")


@setHook(HOOK_GPIN)
def on_gpin(pin_num, is_set):
    if is_set:
        if pin_num == BUTTON_LEFT:
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

    G_BATTERY_LOW = ("\x01" if level <= BATTERY_LOW_LEVEL else "\x00") + G_BATTERY_LOW[1:]

    return level


def cops_report_in(slots):
    global G_TIMESLOT_COUNTDOWN, G_BEST_LQ

    # Choose a timeslot
    addr = localAddr()
    G_TIMESLOT_COUNTDOWN = (((ord(addr[1]) & 0x7f) << 8) | ord(addr[2])) % slots

    lq = getLq()
    if (G_BEST_LQ is None) or (lq < G_BEST_LQ):
        G_BEST_LQ = lq


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
    global G_HEARD_FROM

    addr = rpcSourceAddr()
    G_HEARD_FROM += addr
    update_from_neighbor(addr, lq, battery <= BATTERY_LOW_LEVEL)


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
    global G_FSM_STATE, G_GENERAL_COUNTDOWN, G_HEARD_FROM, G_NEED_REBOOT, G_SEQUENCE, G_POSITION

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
            fsm_goto(STATE_MENU1)

        set_xy(0, 3)
        cache_8x8("mode in " + str(G_GENERAL_COUNTDOWN) + " sec  ")

    elif G_FSM_STATE == STATE_CONTROLLER:
        if reason == REASON_GOTO:
            low_power()
        elif reason == REASON_LEFT:
            init_display(USE_SPI)
            fsm_goto(STATE_MENU3)

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
            cache_8x8(UP_ARROW + " Passive mode  ")
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
            cache_8x8(UP_ARROW + " Controller    ")
            set_xy(0, 1)
            cache_8x8("  Interrogate   ")
            set_xy(0, 2)
            cache_8x8(RIGHT_ARROW + " Set NV params ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Simon         ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU9)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU8)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_SET_NV1)
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
            cache_8x8(RIGHT_ARROW + " Controller    ")
            set_xy(0, 2)
            cache_8x8("  Interrogate   ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Set NV params ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU2)
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

    elif G_FSM_STATE == STATE_MENU8:
        # SIMON OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Controller    ")
            set_xy(0, 1)
            cache_8x8("  Interrogate   ")
            set_xy(0, 2)
            cache_8x8("  Set NV params ")
            set_xy(0, 3)
            cache_8x8(RIGHT_ARROW + " Simon         ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU5)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_SIMON1)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_MENU9:
        # INTERROGATE OPTION
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(0, 0)
            cache_8x8(UP_ARROW + " Controller    ")
            set_xy(0, 1)
            cache_8x8(RIGHT_ARROW + " Interrogate   ")
            set_xy(0, 2)
            cache_8x8("  Set NV params ")
            set_xy(0, 3)
            cache_8x8(DOWN_ARROW + " Simon         ")
        elif reason == REASON_UP:
            fsm_goto(STATE_MENU6)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_MENU5)
        elif (reason == REASON_RIGHT) or (reason == REASON_PRESS):
            fsm_goto(STATE_INTERROGATE)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)

    elif G_FSM_STATE == STATE_PROBE:
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            display_neighbors(get_battery())
            G_HEARD_FROM = ""
            mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_PRESS:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            display_neighbors(get_battery())
            G_HEARD_FROM = ""
            mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_1S_HOOK:
            display_on_1s()
            if G_GENERAL_COUNTDOWN == (CONTROLLER_TIMEOUT - (PROBE_TIMESLOTS / 10)):
                clear_not_heard_from(G_HEARD_FROM)
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_MENU2)

    elif G_FSM_STATE == STATE_PASSIVE:
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            display_neighbors(get_battery())
            G_HEARD_FROM = ""
            mcastRpc(1, MAX_TTL, "cops_report_in", PROBE_TIMESLOTS)
        elif reason == REASON_1S_HOOK:
            display_on_1s()
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            elif (G_GENERAL_COUNTDOWN % (PASSIVE_TIMESLOTS / 10)) == 0:
                clear_not_heard_from(G_HEARD_FROM)
                G_HEARD_FROM = ""
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
            fsm_goto(STATE_MENU4)

    elif G_FSM_STATE == STATE_SET_NV1:
        set_xy(0, 0)
        cache_8x8("Channel: " + str(getChannel()) + "     ")
        set_xy(0, 1)
        cache_8x8("Network ID: " + num_to_hex(getNetId()))
        set_xy(0, 2)
        cache_8x8("FeatureBts: " + num_to_hex(loadNvParam(NV_FEATURE_BITS_ID)))
        set_xy(0, 3)
        cache_8x8("Encryption: " + ("On  " if loadNvParam(NV_AES128_ENABLE_ID) else "Off "))
        G_NEED_REBOOT = False
        fsm_goto(STATE_SET_NV2)

    elif G_FSM_STATE == STATE_SET_NV2:
        channel = getChannel()
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(9, 0)
            cache_8x8(str(channel) + " ")
            set_xy(9, 0)
            print_invert(1 if channel > 9 else channel)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(9, 0)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(1 if channel > 9 else channel)
                else:
                    cache_8x8(str(channel))
        elif reason == REASON_UP:
            setChannel((channel + 1) % 16)
            fsm_goto(STATE_SET_NV2)
        elif reason == REASON_DOWN:
            setChannel((channel + 15) % 16)
            fsm_goto(STATE_SET_NV2)
        elif reason == REASON_PRESS:
            set_xy(9, 0)
            cache_8x8(str(channel) + " ")
            saveNvParam(NV_CHANNEL_ID, channel)
            fsm_goto(STATE_SET_NV3)

    elif G_FSM_STATE == STATE_SET_NV3:
        net_id = getNetId()
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            set_xy(12, 1)
            print_invert(net_id >> 12)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 1)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(net_id >> 12)
                else:
                    cache_8x8(num_to_hex(net_id))
        elif reason == REASON_UP:
            setNetId(net_id + 0x1000)
            fsm_goto(STATE_SET_NV3)
        elif reason == REASON_DOWN:
            setNetId(net_id + 0xf000)
            fsm_goto(STATE_SET_NV3)
        elif reason == REASON_RIGHT:
            fsm_goto(STATE_SET_NV4)
        elif reason == REASON_PRESS:
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            saveNvParam(NV_NETWORK_ID, net_id)
            fsm_goto(STATE_SET_NV7)

    elif G_FSM_STATE == STATE_SET_NV4:
        net_id = getNetId()
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            set_xy(13, 1)
            print_invert(net_id >> 8)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                if G_GENERAL_COUNTDOWN % 2:
                    set_xy(13, 1)
                    print_invert(net_id >> 8)
                else:
                    set_xy(12, 1)
                    cache_8x8(num_to_hex(net_id))
        elif reason == REASON_UP:
            setNetId(((net_id + 0x0100) & 0x0f00) | (net_id & 0xf0ff))
            fsm_goto(STATE_SET_NV4)
        elif reason == REASON_DOWN:
            setNetId(((net_id + 0x0f00) & 0x0f00) | (net_id & 0xf0ff))
            fsm_goto(STATE_SET_NV4)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_SET_NV3)
        elif reason == REASON_RIGHT:
            fsm_goto(STATE_SET_NV5)
        elif reason == REASON_PRESS:
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            saveNvParam(NV_NETWORK_ID, net_id)
            fsm_goto(STATE_SET_NV7)

    elif G_FSM_STATE == STATE_SET_NV5:
        net_id = getNetId()
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            set_xy(14, 1)
            print_invert(net_id >> 4)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                if G_GENERAL_COUNTDOWN % 2:
                    set_xy(14, 1)
                    print_invert(net_id >> 4)
                else:
                    set_xy(12, 1)
                    cache_8x8(num_to_hex(net_id))
        elif reason == REASON_UP:
            setNetId(((net_id + 0x0010) & 0x00f0) | (net_id & 0xff0f))
            fsm_goto(STATE_SET_NV5)
        elif reason == REASON_DOWN:
            setNetId(((net_id + 0x00f0) & 0x00f0) | (net_id & 0xff0f))
            fsm_goto(STATE_SET_NV5)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_SET_NV4)
        elif reason == REASON_RIGHT:
            fsm_goto(STATE_SET_NV6)
        elif reason == REASON_PRESS:
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            saveNvParam(NV_NETWORK_ID, net_id)
            fsm_goto(STATE_SET_NV7)

    elif G_FSM_STATE == STATE_SET_NV6:
        net_id = getNetId()
        if reason == REASON_GOTO:
            G_GENERAL_COUNTDOWN = CONTROLLER_TIMEOUT
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            set_xy(15, 1)
            print_invert(net_id)
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                if G_GENERAL_COUNTDOWN % 2:
                    set_xy(15, 1)
                    print_invert(net_id)
                else:
                    set_xy(12, 1)
                    cache_8x8(num_to_hex(net_id))
        elif reason == REASON_UP:
            setNetId(((net_id + 0x0001) & 0x000f) | (net_id & 0xfff0))
            fsm_goto(STATE_SET_NV6)
        elif reason == REASON_DOWN:
            setNetId(((net_id + 0x000f) & 0x000f) | (net_id & 0xfff0))
            fsm_goto(STATE_SET_NV6)
        elif reason == REASON_LEFT:
            fsm_goto(STATE_SET_NV5)
        elif reason == REASON_PRESS:
            set_xy(12, 1)
            cache_8x8(num_to_hex(net_id))
            saveNvParam(NV_NETWORK_ID, net_id)
            fsm_goto(STATE_SET_NV7)

    elif G_FSM_STATE == STATE_SET_NV7:
        feature_bits = loadNvParam(NV_FEATURE_BITS_ID)
        if feature_bits == 0x011f:
            fsm_goto(STATE_SET_NV8)
        elif feature_bits == 0x051f:
            fsm_goto(STATE_SET_NV9)
        elif feature_bits == 0x091f:
            fsm_goto(STATE_SET_NV10)
        else:
            fsm_goto(STATE_SET_NV11)

    elif G_FSM_STATE == STATE_SET_NV8:
        if reason == REASON_GOTO:
            set_xy(12, 2)
            print_invert(0)
            cache_8x8("1")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 2)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("0")
        elif reason == REASON_UP:
            fsm_goto(STATE_SET_NV9)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_SET_NV11)
        elif reason == REASON_PRESS:
            set_xy(12, 2)
            cache_8x8("0")
            if loadNvParam(NV_FEATURE_BITS_ID) != 0x011f:
                saveNvParam(NV_FEATURE_BITS_ID, 0x011f)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV12)

    elif G_FSM_STATE == STATE_SET_NV9:
        if reason == REASON_GOTO:
            set_xy(12, 2)
            print_invert(0)
            cache_8x8("5")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 2)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("0")
        elif reason == REASON_UP:
            fsm_goto(STATE_SET_NV10)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_SET_NV8)
        elif reason == REASON_PRESS:
            set_xy(12, 2)
            cache_8x8("0")
            if loadNvParam(NV_FEATURE_BITS_ID) != 0x051f:
                saveNvParam(NV_FEATURE_BITS_ID, 0x051f)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV12)

    elif G_FSM_STATE == STATE_SET_NV10:
        if reason == REASON_GOTO:
            set_xy(12, 2)
            print_invert(0)
            cache_8x8("9")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 2)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("0")
        elif reason == REASON_UP:
            fsm_goto(STATE_SET_NV11)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_SET_NV9)
        elif reason == REASON_PRESS:
            set_xy(12, 2)
            cache_8x8("0")
            if loadNvParam(NV_FEATURE_BITS_ID) != 0x091f:
                saveNvParam(NV_FEATURE_BITS_ID, 0x091f)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV12)

    elif G_FSM_STATE == STATE_SET_NV11:
        if reason == REASON_GOTO:
            set_xy(12, 2)
            print_invert(0)
            cache_8x8("d")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 2)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("0")
        elif reason == REASON_UP:
            fsm_goto(STATE_SET_NV8)
        elif reason == REASON_DOWN:
            fsm_goto(STATE_SET_NV10)
        elif reason == REASON_PRESS:
            set_xy(12, 2)
            cache_8x8("0")
            if loadNvParam(NV_FEATURE_BITS_ID) != 0x0d1f:
                saveNvParam(NV_FEATURE_BITS_ID, 0x0d1f)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV12)

    elif G_FSM_STATE == STATE_SET_NV12:
        if loadNvParam(NV_AES128_ENABLE_ID):
            fsm_goto(STATE_SET_NV13)
        else:
            fsm_goto(STATE_SET_NV14)

    elif G_FSM_STATE == STATE_SET_NV13:
        if reason == REASON_GOTO:
            set_xy(12, 3)
            print_invert(0)
            cache_8x8("n ")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 3)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("O")
        elif (reason == REASON_UP) or (reason == REASON_DOWN):
            fsm_goto(STATE_SET_NV14)
        elif reason == REASON_PRESS:
            set_xy(12, 3)
            cache_8x8("O")
            if loadNvParam(NV_AES128_ENABLE_ID) != 1:
                saveNvParam(NV_AES128_ENABLE_ID, 1)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV15)

    elif G_FSM_STATE == STATE_SET_NV14:
        if reason == REASON_GOTO:
            set_xy(12, 3)
            print_invert(0)
            cache_8x8("ff")
        elif reason == REASON_1S_HOOK:
            if general_countdown():
                fsm_goto(STATE_CONTROLLER)
            else:
                set_xy(12, 3)
                if G_GENERAL_COUNTDOWN % 2:
                    print_invert(0)
                else:
                    cache_8x8("O")
        elif (reason == REASON_UP) or (reason == REASON_DOWN):
            fsm_goto(STATE_SET_NV13)
        elif reason == REASON_PRESS:
            set_xy(12, 3)
            cache_8x8("O")
            if loadNvParam(NV_AES128_ENABLE_ID) != 0:
                saveNvParam(NV_AES128_ENABLE_ID, 0)
                G_NEED_REBOOT = True
            fsm_goto(STATE_SET_NV15)

    if G_FSM_STATE == STATE_SET_NV15:
        if G_NEED_REBOOT:
            reboot()
        else:
            fsm_goto(STATE_MENU5)

    elif G_FSM_STATE == STATE_SIMON1:
        if reason == REASON_GOTO:
            set_xy(0, 0)
            cache_8x8("Watch!  3 2 1   ")
            set_xy(0, 1)
            cache_8x8("                ")
            set_xy(0, 2)
            cache_8x8("                ")
            set_xy(0, 3)
            cache_8x8("                ")
            G_SEQUENCE = ""
        elif reason == REASON_1S_HOOK:
            fsm_goto(STATE_SIMON2)

    elif G_FSM_STATE == STATE_SIMON2:
        if reason == REASON_GOTO:
            set_xy(8, 0)
            cache_8x8(" ")
        elif reason == REASON_1S_HOOK:
            fsm_goto(STATE_SIMON3)

    elif G_FSM_STATE == STATE_SIMON3:
        if reason == REASON_GOTO:
            set_xy(10, 0)
            cache_8x8(" ")
        elif reason == REASON_1S_HOOK:
            fsm_goto(STATE_SIMON4)

    elif G_FSM_STATE == STATE_SIMON4:
        if reason == REASON_GOTO:
            set_xy(0, 0)
            cache_8x8("Watch!       ")
        elif reason == REASON_1S_HOOK:
            fsm_goto(STATE_SIMON5)

    elif G_FSM_STATE == STATE_SIMON5:
        G_SEQUENCE += chr(random() % 4)
        G_POSITION = 0
        fsm_goto(STATE_SIMON6)

    elif G_FSM_STATE == STATE_SIMON6:
        if reason == REASON_GOTO:
            arrow = ord(G_SEQUENCE[G_POSITION])
            if arrow == 0:
                set_xy(7, 1)
                cache_8x8(UP_ARROW)
            elif arrow == 1:
                set_xy(4, 2)
                cache_8x8(LEFT_ARROW)
            elif arrow == 2:
                set_xy(10, 2)
                cache_8x8(RIGHT_ARROW)
            else:
                set_xy(7, 3)
                cache_8x8(DOWN_ARROW)
        elif reason == REASON_1S_HOOK:
            set_xy(7, 1)
            cache_8x8(" ")
            set_xy(4, 2)
            cache_8x8("       ")
            set_xy(7, 3)
            cache_8x8(" ")
            fsm_goto(STATE_SIMON7)

    elif G_FSM_STATE == STATE_SIMON7:
        if reason == REASON_1S_HOOK:
            G_POSITION += 1
            fsm_goto(STATE_SIMON6 if G_POSITION < len(G_SEQUENCE) else STATE_SIMON8)

    elif G_FSM_STATE == STATE_SIMON8:
        # if reason == REASON_1S_HOOK:
            set_xy(0, 0)
            cache_8x8("      ")
            G_POSITION = 0
            fsm_goto(STATE_SIMON9)

    elif G_FSM_STATE == STATE_SIMON9:
        if reason == REASON_1S_HOOK:
            set_xy(0, 0)
            cache_8x8("Repeat!")
            G_GENERAL_COUNTDOWN = 2
            fsm_goto(STATE_SIMON10)

    elif G_FSM_STATE == STATE_SIMON10:
        arrow = None
        if reason == REASON_UP:
            arrow = 0
        elif reason == REASON_LEFT:
            arrow = 1
        elif reason == REASON_RIGHT:
            arrow = 2
        elif reason == REASON_DOWN:
            arrow = 3
        elif reason == REASON_1S_HOOK:
            G_GENERAL_COUNTDOWN -= 1
            if G_GENERAL_COUNTDOWN == 0:
                fsm_goto(STATE_SIMON11)

        if arrow is not None:
            if arrow == ord(G_SEQUENCE[G_POSITION]):
                if arrow == 0:
                    set_xy(7, 1)
                    cache_8x8(UP_ARROW)
                elif arrow == 1:
                    set_xy(4, 2)
                    cache_8x8(LEFT_ARROW)
                elif arrow == 2:
                    set_xy(10, 2)
                    cache_8x8(RIGHT_ARROW)
                else:
                    set_xy(7, 3)
                    cache_8x8(DOWN_ARROW)
                G_POSITION += 1
                fsm_goto(STATE_SIMON12 if G_POSITION < len(G_SEQUENCE) else STATE_SIMON13)
            else:
                fsm_goto(STATE_SIMON11)

    elif G_FSM_STATE == STATE_SIMON11:
        if reason == REASON_GOTO:
            set_xy(7, 2)
            cache_8x8("X")
            G_GENERAL_COUNTDOWN = 2
        elif reason == REASON_1S_HOOK:
            G_GENERAL_COUNTDOWN -= 1
            if G_GENERAL_COUNTDOWN == 0:
                fsm_goto(STATE_MENU8)

    elif G_FSM_STATE == STATE_SIMON12:
        if reason == REASON_1S_HOOK:
            set_xy(7, 1)
            cache_8x8(" ")
            set_xy(4, 2)
            cache_8x8("       ")
            set_xy(7, 3)
            cache_8x8(" ")
            fsm_goto(STATE_SIMON10)

    elif G_FSM_STATE == STATE_SIMON13:
        if reason == REASON_1S_HOOK:
            set_xy(0, 0)
            cache_8x8("       ")
            set_xy(7, 1)
            cache_8x8(" ")
            set_xy(4, 2)
            cache_8x8("       ")
            set_xy(7, 3)
            cache_8x8("Good job!")
            G_GENERAL_COUNTDOWN = 2
            fsm_goto(STATE_SIMON14)

    elif G_FSM_STATE == STATE_SIMON14:
        if reason == REASON_1S_HOOK:
            G_GENERAL_COUNTDOWN -= 1
            if G_GENERAL_COUNTDOWN == 0:
                set_xy(7, 3)
                cache_8x8("         ")
                fsm_goto(STATE_SIMON4)


def print_invert(digit):
    cache_8x8(INVERTED_HEX[digit & 0x000f])
