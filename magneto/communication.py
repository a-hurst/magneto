import time
import threading
from queue import Queue

import serial

from .constants import *
from .utils import build_command, validate_response, int_to_ascii, _check_error


resp_lengths = {
    SET_POWER_A: 3,
    SET_POWER_B: 3,
    SET_PULSE_INTERVAL: 3,
    SET_BASE_MODE: 3,
    ENABLE_REMOTE_CTRL: 3,
    DISABLE_REMOTE_CTRL: 3,
    ENABLE_HIRES_TIME: 3,
    DISABLE_HIRES_TIME: 3,
    GET_PARAMS: 12,
}


class Response(object):

    def __init__(self, raw):
        self._err = _check_error(raw)
        self._raw = raw

    @property
    def cmd(self):
        return self._raw[0]

    @property
    def status(self):
        # NOTE: Missing for Rapid 'software version' responses
        return None if self._err else self._raw[1]

    @property
    def data(self):
        return self._raw[2:-1]

    @property
    def err(self):
        # The error type (if any) for the response packet
        return self._err


class MagstimStatus(object):
    
    def __init__(self, status):
        if isinstance(status, bytes):
            status = int.from_bytes(status, "little")
        self._status = status
        
    def _check_bit(self, bit):
        return bool(self._status & (1 << bit))

    def __repr__(self):
        bits = ""
        for bit in range(8):
            bitstr = "1" if self._check_bit(bit) else "0"
            bits = bitstr + bits
        return "MagstimStatus({})".format(bits)
        
    @property
    def standby(self):
        return self._check_bit(STATUS_STANDBY)
        
    @property
    def armed(self):
        return self._check_bit(STATUS_ARMED)

    @property
    def ready(self):
        return self._check_bit(STATUS_READY)
        
    @property
    def coil_present(self):
        return self._check_bit(STATUS_COIL_PRESENT)
        
    @property
    def replace_coil(self):
        return self._check_bit(STATUS_REPLACE_COIL)

    @property
    def err(self):
        return self._check_bit(STATUS_ERR)

    @property
    def fatal_err(self):
        return self._check_bit(STATUS_ERR_TYPE)
        
    @property
    def remote_control(self):
        return self._check_bit(STATUS_REMOTE_CTRL)


def _get_resp_bytes(raw):
    # Given an input buffer of bytes, identify and split off any valid
    # response bytes from the beginning of the buffer + the remaining
    # buffer with those bytes removed
    resp_bytes = 0
    if raw[0] == INVALID_CMD:
        resp_bytes = 1
    elif len(raw) >= 3:
        expected_bytes = resp_lengths[raw[0]]
        if raw[1] == INVALID_DATA or raw[1] == SETTINGS_CONFLICT:
            resp_bytes = 3
        elif len(raw) >= expected_bytes:
            resp_bytes = expected_bytes

    return (raw[:resp_bytes], raw[resp_bytes:])


def _serial_connect(port):
    connection = serial.Serial(
        port,
        baudrate=9600,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE,
    )
    connection.write_timeout = 0.5
    return connection


def comm_loop(port, q_in, q_out):
    # NOTE: To avoid partial reads, make a table of expected response lengths per
    # each response character & ensure that many bytes have been read before
    # passing to the main thread? 
    ctrl_cmd = build_command(ENABLE_REMOTE_CTRL)
    last_ping = time.time()
    ping_freq = 0.5

    buf = b"" # serial port input buffer
    comm = _serial_connect(port)
    while comm.is_open:

        # Read incoming data
        if comm.in_waiting > 0:
            new_bytes = comm.read(comm.in_waiting)
            buf += new_bytes.lstrip(b'\x00')
            resp, buf = _get_resp_bytes(buf)
            if len(resp):
                q_in.put(resp)
        
        # Send any queued commands
        now = time.time()
        if not q_out.empty():
            cmd = q_out.get()
            comm.write(cmd)
            last_ping = now

        # If no command sent for a while, ping the unit to maintain control
        if (now - last_ping) > ping_freq:
            comm.write(ctrl_cmd)
            last_ping = now

        time.sleep(0.05)
