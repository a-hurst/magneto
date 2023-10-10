
# Magstim command codes

SET_POWER_A = 0x40

SET_BASE_MODE = 0x45
ENABLE_REMOTE_CTRL = 0x51
DISABLE_REMOTE_CTRL = 0x52

GET_PARAMS = 0x4A
GET_VERSION = 0x4E
GET_ERR_CODE = 0x49


# Undocumented commands

GET_SYSTEM_TYPE = 0x4B
GET_SYSTEM_MODE = 0x58


# BiStim-specific commands

SET_POWER_B = 0x41
SET_PULSE_INTERVAL = 0x43

ENABLE_HIRES_TIME = 0x59
DISABLE_HIRES_TIME = 0x5A


# Rapid-specific commands

SET_PULSE_FREQ = 0x42
SET_PULSE_COUNT = 0x44

IGNORE_COIL_INTERLOCK = 0x62
SET_RAPID_DURATION = 0x5B
ENABLE_ENHANCED_POWER = 0x5E
DISABLE_ENHANCED_POWER = 0x5F

GET_RAPID_PARAMS = 0x5C
GET_RAPID_STATUS = 0x78


# Instrument status bits

STATUS_STANDBY = 0
STATUS_ARMED = 1
STATUS_READY = 2
STATUS_COIL_PRESENT = 3
STATUS_REPLACE_COIL = 4
STATUS_ERR = 5
STATUS_ERR_TYPE = 6
STATUS_REMOTE_CTRL = 7


# Rapid status bits

RAPID_ENHANCED_POWER = 0
RAPID_TRAIN_STATUS = 1
RAPID_WAIT_STATUS = 2
RAPID_SINGLE_PULSE = 3
RAPID_HV_PSU = 4
RAPID_COIL_READY = 5
RAPID_THETA_PSU_CONFIG = 6
RAPID_COIL_ALGORITHM_MOD = 7


# Extended instrument status bits (Rapid-only)

STATUS_EXT_PLUS1_MODULE = 0
STATUS_EXT_SPECIAL_TRIGGER = 1


# Mode settings bits

MODE_STOPPED = 0
MODE_ARMED = 1
MODE_TRIGGER = 3
MODE_BASE = 6


# Additional command constants

PAD_BYTE = 0x40

INVALID_CMD = ord('?')
INVALID_DATA = ord('?')
SETTINGS_CONFLICT = ord('S')


# Undocumented command constants

SYSTEM_TYPE_RAPID = b'3012' # 3010 for Magstim 200/BiStim, but Signal 6 only checks if Rapid


# Magneto constants not from Magstim docs

CRC_ERROR = -1

SYSTEM_MODE_200 = 1
SYSTEM_MODE_BISTIM = 2
SYSTEM_MODE_BISTIM_IBT = 3
SYSTEM_MODE_BISTIM_WRONG_PORT = 4
SYSTEM_MODE_UNKNOWN = -1

# Based on decompiled switch statement from Signal 6.06 Magstim DLL
SYSTEM_MODE_MAP = {
    0x30: SYSTEM_MODE_200,
    0x31: SYSTEM_MODE_BISTIM,
    0x32: SYSTEM_MODE_BISTIM,
    0x33: SYSTEM_MODE_BISTIM_IBT,
    0x34: SYSTEM_MODE_BISTIM,
    0x51: SYSTEM_MODE_BISTIM_WRONG_PORT,
    0x52: SYSTEM_MODE_BISTIM_WRONG_PORT,
    0x53: SYSTEM_MODE_BISTIM_WRONG_PORT,
    0x54: SYSTEM_MODE_BISTIM_WRONG_PORT,
}

# Commands that don't have a 'status' byte
CMD_NO_STATUS = (GET_VERSION, GET_SYSTEM_TYPE)
