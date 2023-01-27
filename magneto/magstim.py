import time
import threading
from queue import Queue

from .constants import *
from .utils import build_command, get_mode_byte, int_to_ascii, _validate_response
from .communication import Response, MagstimStatus, _serial_connect, comm_loop


class Magstim(object):

    def __init__(self, port):
        self._port = port
        self._status = None
        self._to_stim = Queue()
        self._from_stim = Queue()
        self._com_thread = None

    def connect(self):
        self._com_thread = threading.Thread(
            target=comm_loop,
            args=(self._port, self._from_stim, self._to_stim),
            daemon=True
        )
        self._com_thread.start()
        self._enable_remote_control()
        # If stimulator is a BiStim, configure it into single-pulse mode
        try:
            # TODO: Add an option for choosing type of BiStim single-pulse mode
            #self._set_power_b(0)
            #self._set_pulse_interval(1)
            self._set_pulse_interval(0)
        except RuntimeError:
            pass

    def _pump(self):
        out = []
        while not self._from_stim.empty():
            resp_bytes = self._from_stim.get()
            resp = Response(resp_bytes)
            if not resp.err:
                self._status = MagstimStatus(resp.status)
            out.append(resp)
        return out

    def _send_cmd(self, cmd, data=None):
        self._to_stim.put(build_command(cmd, data))

    def _wait_for_reply(self, cmd, timeout=1.0):
        start = time.time()
        while (time.time() - start) < timeout:
            for resp in self._pump():
                if resp.cmd == cmd or resp.err == INVALID_CMD:
                    return resp

    def _communicate(self, cmd, data=None):
        # Sends a command to the magstim and wait for a response, returning its
        # current status if no error in the response
        self._send_cmd(cmd, data)
        resp = self._wait_for_reply(cmd)
        _validate_response(resp)
        return resp.status

    def _enable_remote_control(self):
        return self._communicate(ENABLE_REMOTE_CTRL)

    def _disable_remote_control(self):
        return self._communicate(DISABLE_REMOTE_CTRL)

    def set_power(self, value):
        if not (0 <= value <= 100):
            e = "Power level must be an integer between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        level = int_to_ascii(value, width=3)
        return self._communicate(SET_POWER_A, level)

    def arm(self):
        armed = get_mode_byte(MODE_ARMED)
        return self._communicate(SET_BASE_MODE, armed)
    
    def disarm(self):
        disarmed = get_mode_byte(0)
        return self._communicate(SET_BASE_MODE, disarmed)
    
    def fire(self):
        trigger = get_mode_byte(MODE_TRIGGER)
        return self._communicate(SET_BASE_MODE, trigger)

    def get_settings(self):
        self._send_cmd(GET_PARAMS)
        resp = self._wait_for_reply(GET_PARAMS)
        _validate_response(resp)
        if len(resp.data) != 9:
            raise RuntimeError("Error parsing Magstim settings.")
        pwr_a = int(resp.data[:3])
        pwr_b = int(resp.data[3:6])
        pulse_interval = int(resp.data[6:])
        return (pwr_a, pwr_b, pulse_interval)

    def _set_power_b(self, value):
        if not (0 <= value <= 100):
            e = "Power level must be an integer between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        level = int_to_ascii(value, width=3)
        return self._communicate(SET_POWER_B, level)

    def _set_highres_time(self, enable=True):
        if enable:
            return self._communicate(ENABLE_HIRES_TIME)
        else:
            return self._communicate(DISABLE_HIRES_TIME)

    def _set_pulse_interval(self, value):
        # NOTE: No obvious way to check current pulse interval resolution
        if not (0 <= value <= 100):
            e = "Pulse interval must be a value between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        interval = int_to_ascii(value, width=3)
        return self._communicate(SET_PULSE_INTERVAL, interval)

    @property
    def armed(self):
        # NOTE: When magstim is ready 'armed' bit is set to 0, so need to check both
        self._send_cmd(ENABLE_REMOTE_CTRL)
        resp = self._wait_for_reply(ENABLE_REMOTE_CTRL)
        _validate_response(resp)
        return self._status.armed or self._status.ready
    
    @property
    def ready(self):
        self._send_cmd(ENABLE_REMOTE_CTRL)
        resp = self._wait_for_reply(ENABLE_REMOTE_CTRL)
        _validate_response(resp)
        return self._status.ready

    @property
    def status(self):
        # Retrieves status information from the last response from the magstim
        self._pump()
        return self._status
