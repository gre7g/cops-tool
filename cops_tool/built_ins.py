"""Some minor hackery so that PyCharm doesn't highlight all SNAPpy built-ins"""

# (c)2016 Synapse Wireless,  Inc.

# pylint: disable=invalid-name

if False:  # pylint: disable=using-constant-test
    call = callback = callout = crossConnect = dmCallout = dmcastRpc = eraseImage = errno = flowControl = getChannel = \
        getEnergy = getI2cResult = getInfo = getLq = getMs = getNetId = getStat = i2cInit = i2cRead = i2cWrite = \
        imageName = initUart = later = loadNvParam = localAddr = mcastRpc = mcastSerial = monitorPin = nodeConfig = \
        peek = peekRadio = poke = pokeRadio = pulsePin = random = readAdc = readPin = reboot = resetVm = rpc = \
        rpcSourceAddr = rx = saveNvParam = scanEnergy = setChannel = setNetId = setPinDir = setPinPullup = \
        setPinSlew = setRadioRate = setRate = sleep = spiInit = spiRead = spiWrite = spiXfer = stdinMode = txPwr = \
        ucastSerial = uniConnect = vmStat = writeChunk = writePin = setHook = HOOK_STARTUP = HOOK_GPIN = HOOK_1MS = \
        HOOK_10MS = HOOK_100MS = HOOK_1S = HOOK_STDIN = HOOK_STDOUT = HOOK_RPC_SENT = str
