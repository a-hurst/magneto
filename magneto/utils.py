import serial

from .constants import *


class CRCError(RuntimeError):
    pass


def byteify(x, enc='ascii'):
    if type(x) == str:
        return x.encode(enc)
    else:
        return bytes(x)

def int_to_ascii(num, width=1):
    num = int(num) # Ensure number is valid int
    return str(num).zfill(width).encode("ascii")

def calculate_crc(cmd):
    bytesum = sum([int(b) for b in byteify(cmd)])
    return byteify(chr(~bytesum & 0xFF))

def get_mode_byte(setting):
    return chr((1 << MODE_BASE) + (1 << setting))

def build_command(cmd, data=None):
    cmd = byteify(chr(cmd))
    if not data:
        data = chr(PAD_BYTE)
    base_cmd = cmd + byteify(data)
    return base_cmd + calculate_crc(base_cmd)

def _check_error(resp):
    err = None
    # Check for invalid command flags
    if resp[0] == INVALID_CMD:
        err = INVALID_CMD
    elif resp[1] == INVALID_DATA:
        err = INVALID_DATA
    elif resp[1] == SETTINGS_CONFLICT:
        err = SETTINGS_CONFLICT
    else:
        # Check for CRC mismatch
        crc = resp[-1]
        expected = ord(calculate_crc(resp[:-1]))
        if crc != expected:
            err = CRC_ERROR            
    return err

def _validate_response(resp):
    if resp.err == INVALID_CMD:
        e = "Magstim received an unrecognized command."
        raise RuntimeError(e)
    elif resp.err == INVALID_DATA:
        e = "Magstim received a command with invalid data."
        raise ValueError(e)
    elif resp.err == SETTINGS_CONFLICT:
        e = "Magstim received a command in conflict with its current settings."
        raise ValueError(e)
    elif resp.err == CRC_ERROR:
        e = "Magstim response failed CRC integrity check ({0})."
        raise CRCError(e.format(resp._raw))
