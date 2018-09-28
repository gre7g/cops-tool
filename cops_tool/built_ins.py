"""Some minor hackery so that PyCharm doesn't highlight all SNAPpy built-ins"""

# (c)2016 Synapse Wireless,  Inc.

# pylint: disable=invalid-name

if True == False:  # pylint: disable=using-constant-test
    HOOK_STARTUP = HOOK_GPIN = HOOK_1MS = HOOK_10MS = HOOK_100MS = HOOK_1S = HOOK_STDIN = HOOK_STDOUT = \
        HOOK_RPC_SENT = 0


    def setHook(hook):
        """Decorate a hook"""
        pass


    def peek(addr, addrLo=0, word=0):
        """Read a memory location"""
        return 0


    def poke(*args):
        """Write a memory location"""
        pass


    def rpc(dstAddr, remoteFnObj, *args):
        """Remote Procedure Call (unicast)"""
        return True


    def mcastRpc(dstGroups, ttl, remoteFnObj, *args):
        """Remote Procedure Call (multicast)"""
        pass


    def getMs():
        """Elapsed milliseconds since startup (16bit)"""
        return 0


    def setPinDir(pin, isOutput):
        """Set direction for parallel I/O pin"""
        pass


    def setPinPullup(pin, isEnabled):
        """Enable pullup resistor (~25k) for Input pin"""
        pass


    def readPin(pin):
        """Read current level of pin"""
        return True


    def setPinSlew(pin, isRateControl):
        """Enable slew rate-control (~30ns) for Output pin"""


    def writePin(pin, isHigh):
        """Set Output pin level"""
        pass


    def monitorPin(pin, isMonitored):
        """Enable GPIN events on Input pin"""
        pass


    def pulsePin(pin, msWidth, isPositive):
        """Apply pulse to Output pin"""
        pass


    def readAdc(channel):
        """Sample ADC on specified input channel"""
        return 0


    def localAddr():
        """Local network address"""
        return ""


    def initUart(uartNum, baudRate, dataBits=0, parity="", stopBits=0):
        """Enable UART at specified rate (zero to disable)"""
        pass


    def flowControl(uartNum, isEnabled, isTxEnable=False):
        """Enable RTS/CTS flow control"""
        pass


    def crossConnect(dataSrc1, dataSrc2):
        """Cross-connect SNAP data-sources"""
        pass


    def uniConnect(dst, src):
        """Connect src->dst SNAP data-sources"""
        pass


    def ucastSerial(dstAddr):
        """Set Serial transparent mode to unicast"""
        pass


    def mcastSerial(dstGroups, ttl):
        """Set Serial transparent mode to multicast"""
        pass


    def getLq():
        """Link Quality in (-) dBm"""
        return 0


    def loadNvParam(id):
        """Load indexed parameter from NV storage"""
        pass


    def saveNvParam(id, obj, bits=0):
        """
        Save object to indexed NV storage location
        SNAP 2.6 or newer: saveNvParam(id, integer_obj, optional_bitmask)
        SNAP 2.6 or newer: saveNvParam(-id, obj) can in some cases trigger
        immediate actions
        """
        return 0


    def setChannel(channel, netid=0):
        """
        Set radio channel (0-15).
        SNAP 2.6 or newer: setChannel(channel, optional_network_id)
        """
        pass


    def getChannel():
        """Get radio channel (0-15)"""
        return 0


    def reboot(delay=0):
        """
        Reboot the device.
        SNAP 2.6 or newer: reboot(optional_milliseconds_until_reboot)
        """
        pass


    def resetVm():
        """Reset the embedded virtual machine (prep for upload)"""
        pass


    def eraseImage():
        """Erase user-application FLASH memory"""
        pass


    def writeChunk(ofs, str):
        """Write string to user-application FLASH memory"""
        pass


    def initVm():
        """Initialize embedded virtual machine"""
        pass


    def setSegments(segments):
        """Set eval-board LED segments (clockwise bitmask)"""
        pass


    def rpcSourceAddr():
        """Originating address of current RPC context (None if called outside RPC)"""
        return ""


    def sleep(mode,ticks):
        """Enter sleep mode for specified number of ticks\n(See SNAP Reference Manual for platform details)"""
        pass


    def rx(isEnabled):
        """Enable radio receiver"""
        pass


    def setNetId(netId):
        """Set Network ID (1-65535)"""
        pass


    def getNetId():
        """Current Network ID"""
        return 0


    def bist():
        """Built-in self test"""
        pass


    def imageName():
        """Name of current Snappy image"""
        return ""


    def errno():
        """Read and reset last error code"""
        return 0


    def call(rawOpcodes, *args):
        """Call embedded C code"""
        pass


    def vmStat(statusCode, *args):
        """Solicit a tellVmStat for system parameters"""
        pass


    def random():
        """Returns a pseudo-random number (0-4095)"""
        return 0


    def stdinMode(mode, echo):
        """Setup STDIN for Line or Character based input"""
        pass


    def setRate(rateNum):
        """Adjusts the sampling rate used by monitorPin() (0-3 = Off, 100ms, 10ms, 1ms)"""
        pass


    def cbusRd(numToRead):
        """Reads a string of bytes from the CBUS interface"""
        return ""


    def cbusWr(byteStr):
        """Writes a string of bytes to the CBUS interface"""
        pass


    def getEnergy():
        """Energy Detected on current channel (integer) in (-) dBm"""
        return 0


    def scanEnergy():
        """Energy Detected on all channels (string) in (-) dBm"""
        return ""


    def txPwr(power):
        """Set TX power level (0-17)"""
        pass


    def i2cInit(pullups, SCL_pin=0, SDA_pin=0):
        """Setup for I2C, with internal (True) or external (False) pullup resistors"""
        pass


    def i2cWrite(byteStr,retries,ignoreFirstAck,endWithRestart):
        """
        Send data out I2C - returns bytes actually sent
        endWithRestart parameter is optional, defaulting to False
        """
        pass


    def i2cRead(byteStr,numToRead,retries,ignoreFirstAck):
        """Send data out I2C then read response - returns response string"""
        return ""


    def getI2cResult():
        """Returns status code from most recent I2C operation"""
        return 0


    def spiInit(cpol,cpha,isMsbFirst,isFourWire):
        """Setup for SPI, with specified Clock Polarity, Clock Phase, Bit Order, and Physical Interface"""
        pass


    def spiWrite(byteStr,bitsInLastByte=8):
        """Send data out SPI - bitsInLastByte defaults to 8, can be less"""
        pass


    def spiRead(byteCount,bitsInLastByte=8):
        """Receive data in from SPI - returns response string (3 wire only)"""
        return ""


    def spiXfer(byteStr,bitsInLastByte=8):
        """Bidirectional SPI transfer - returns response string (4 wire only)"""
        return ""


    def getInfo(whichInfo):
        """
        Get details about the platform and operating environment

        whichInfo:
        0 = Vendor
        1 = Radio
        2 = CPU
        3 = Platform/Broad Firmware Category
        4 = Build
        5 = Version (Major)
        6 = Version (Minor)
        7 = Version (Build)
        8 = Encryption
        // From here onward requires SNAP 2.4 or newer
        9 = RPC Packet Buffer Reference
        10 = Is Multicast (Multicast or Directed Multicast only)
        11 = Remaining TTL (Multicast or Directed Multicast only)
        12 = Remaining Small Strings
        13 = Remaining Medium Strings
        14 = Route Table Size
        15 = Routes in Route Table
        16 = Bank free space
        // From here onward requires SNAP 2.5 or newer
        17 = Reserved
        18 = HOOK_STDIN status code
        // From here onward requires SNAP 2.6 or newer
        19 = Remaining Tiny Strings
        20 = Remaining Large Strings
        21 = Is Script's First Run
        22 = Base Address of the SNAPpy Script
        23 = Base Bank of the SNAPpy Script
        24 = Is Directed Multicast
        25 = Read and reset Delay Factor (Directed Multicast only)
        26 = Address Index (Directed Multicast only)
        27 = Multicast Groups (Multicast or Directed Multicast only)
        28 = Original TTL (Directed Multicast only)
        """
        pass


    def callback(callback, remoteFnObj, *args):
        """Like rpc() but also invokes specified callback routine with the result of the remoteFnObj routine"""
        pass


    def getStat(whichStat):
        """
        Get details about how busy the node has been with processing packets

        whichStat:
        0 = Null Transmit Buffers
        1 = UART0 Receive Buffers
        2 = UART0 Transmit Buffers
        3 = UART1 Receive Buffers
        4 = UART1 Transmit Buffers
        5 = Transparent Receive Buffers
        6 = Transparent Transmit Buffers
        7 = Packet Serial Receive Buffers
        8 = Packet Serial Transmit Buffers
        9 = Radio Receive Buffers
        10 = Radio Transmit Buffers
        11 = Radio Forwarded Unicasts
        12 = Packet Serial Forwarded Unicasts
        13 = Radio Forwarded Multicasts
        14 = Packet Serial Forwarded Multicasts
        """
        return 0


    def lcdPlot(*args):
        """Interface to eval board LCD panel"""
        pass


    def callout(dstAddr, callout, remoteFnObj, *args):
        """Like callback() but final result is reported to the specified dstAddr"""
        pass


    def dmCallout(nodeAddress, group, ttl, delayFactor, callback, remoteFunction, *remoteFunctionArgs):
        """Like callout() but for dmcastRpc"""
        pass


    def peekRadio(addr):
        """Returns the specified internal radio address"""
        return 0


    def pokeRadio(addr, byteValue):
        """Writes the specified value to the specified radio address"""
        pass


    def setRadioRate(dataRateEnum):
        """Set data rate of radio"""
        pass


    def updateDmxBuf(*args):
        """SNAP DMX only: Update the DMX buffer"""
        pass


    def getDmxBuf(*args):
        """SNAP DMX only: Update the DMX buffer"""
        pass


    def dmcastRpc(dstAddrs, dstGroups, ttl, delayFactor, remoteFnObj, *args):
        """
        SNAP 2.6 or newer:
        Remote Procedure Call (directed multicast)
        """
        return True
