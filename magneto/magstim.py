import time
import threading
from queue import Queue

from .constants import *
from .utils import build_command, get_mode_byte, int_to_ascii, _validate_response
from .communication import Response, MagstimStatus, _serial_connect, comm_loop



class Magstim(object):
    """A connection to a Magstim stimulator.

    This class is designed to be model-independent, meaning that it can be used with
    Magstim 200, BiStim, and (eventually) Rapid stimulators. This is so that experiments
    that do not require model-specific functionality (e.g. paired pulses or rTMS) can be
    easily used across different Magstims in different labs without extra tweaking or
    configuration.
    
    Experiments that require specific BiStim or Rapid functionality should use the
    :class:`BiStim` or :class:`Rapid` classes instead (not yet implemented).
    
    Args:
        port (str): The address of the serial port connected to the Magstim
            (e.g. '/dev/ttyUSB0' for Linux or 'COM1' for Windows).
        bistim_sd (bool, optional): Whether to use simultaneous discharge mode
            instead of paired-pulse mode when connecting to a BiStim unit. Has no
            effect on Magstim 200 or Rapid stimulators. Defaults to True.

    """
    def __init__(self, port, bistim_sd=True):
        self._port = port
        self._status = None
        self._to_stim = Queue()
        self._from_stim = Queue()
        self._com_thread = None
        self._simultaneous = bistim_sd

    def connect(self):
        """Initializes the connection to the stimulator.
        
        This method initializes serial communications with the Magstim and enables
        remote control of the hardware. Must be called before any other methods or
        attributes can be used.

        """
        # TODO: Add logic for ensuring connection exists in other methods/attrs
        # Initializes the Magstim serial communication thread
        self._com_thread = threading.Thread(
            target=comm_loop,
            args=(self._port, self._from_stim, self._to_stim),
            daemon=True
        )
        self._com_thread.start()

        # Request computer control over the Magstim
        self._enable_remote_control()

        # If stimulator is a BiStim, configure it into single-pulse mode
        try:
            if self._simultaneous:
                self._set_pulse_interval(0)
            else:
                self._set_pulse_interval(1)
                self._set_power_b(0)
        except RuntimeError:
            pass

    def _pump(self):
        # Pumps the TMS input queue for new response packets
        out = []
        while not self._from_stim.empty():
            resp_bytes = self._from_stim.get()
            resp = Response(resp_bytes)
            if not resp.err:
                self._status = MagstimStatus(resp.status)
            out.append(resp)
        return out

    def _send_cmd(self, cmd, data=None):
        # Sends a command to the Magstim
        self._to_stim.put(build_command(cmd, data))

    def _wait_for_reply(self, cmd, timeout=1.0):
        # Waits for a response packet corresponding to a given command
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
        # Enables remote control over the stimulator. Unsure if this should be public.
        return self._communicate(ENABLE_REMOTE_CTRL)

    def _disable_remote_control(self):
        # Disables remote control over the stimulator. Unsure if this should be public.
        return self._communicate(DISABLE_REMOTE_CTRL)

    def _get_settings(self):
        # Gets power A, power B, & pulse interval on all models. Power B & pulse 
        # interval are both BiStim-specific, so this is private for the base class.
        self._send_cmd(GET_PARAMS)
        resp = self._wait_for_reply(GET_PARAMS)
        _validate_response(resp)
        if len(resp.data) != 9:
            raise RuntimeError("Error parsing Magstim settings.")
        pwr_a = int(resp.data[:3])
        pwr_b = int(resp.data[3:6])
        pulse_interval = int(resp.data[6:])
        return (pwr_a, pwr_b, pulse_interval)

    def get_power(self):
        """Gets the current power level for the primary coil of the stimulator.

        Returns:
            int: The primary coil's current power level (from 0% to 100%).

        """
        return self._get_settings()[0]

    def set_power(self, value):
        """Sets the power level for the primary coil of the stimulator.

        Note that the stimulator requires time to charge or discharge to a new power
        level once one has been set, with the amount of time depending on the magnitude
        and direction of the change (e.g. 20% to 40% would normally take ~200 ms,
        whereas 40% to 20% would take ~2000 ms).

        To make sure the stimulator is ready to fire after changing the power level,
        check the `ready` attribute once the stimulator has been armed.

        Args:
            level (int): The power level (from 0 to 100) to set for the stimulator's
                primary coil.

        """
        if not (0 <= value <= 100):
            e = "Power level must be an integer between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        level = int_to_ascii(value, width=3)
        return self._communicate(SET_POWER_A, level)

    def arm(self):
        """Arms the stimulator.

        Once armed, the Magstim will disarm automatically if the stimulator has not
        been fired for over 1 minute. Please ensure that your code is written with
        this constraint in mind.

        """
        armed = get_mode_byte(MODE_ARMED)
        return self._communicate(SET_BASE_MODE, armed)
    
    def disarm(self):
        """Disarms the stimulator.

        See :meth:`arm` for more information.
        
        """
        disarmed = get_mode_byte(0)
        return self._communicate(SET_BASE_MODE, disarmed)
    
    def fire(self):
        """Signals the stimulator to fire.

        The stimulator must be armed and ready before this method can be called.

        .. note::
           This commands the TMS to fire via the serial port, which has a variable
           delay anywhere between 5 and 15 ms. As such, this method should usually
           only be used for testing or for tasks where precise timing is not important.
           In all other cases, the stimulator should be triggered via TTL using an
           external triggering device (e.g. LabJack).

        """
        trigger = get_mode_byte(MODE_TRIGGER)
        return self._communicate(SET_BASE_MODE, trigger)

    def _set_power_b(self, value):
        # BiStim-only: sets the power level for the second pulse when in
        # paired-pulse mode.
        if not (0 <= value <= 100):
            e = "Power level must be an integer between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        level = int_to_ascii(value, width=3)
        return self._communicate(SET_POWER_B, level)

    def _set_highres_time(self, enable=True):
        # BiStim-only: toggles whether the paired pulse interval is in units of
        # 0.1 ms (high-resolution enabled) or 1.0 ms (high-resolution disabled)
        if enable:
            return self._communicate(ENABLE_HIRES_TIME)
        else:
            return self._communicate(DISABLE_HIRES_TIME)

    def _set_pulse_interval(self, value):
        # BiStim-only: sets the paired-pulse interval for the stimulator
        # NOTE: Setting the interval to 0 enables simultaneous-discharge mode
        # NOTE: No obvious way to check current pulse interval resolution
        if not (0 <= value <= 100):
            e = "Pulse interval must be a value between 0 and 100 (got {0})"
            raise ValueError(e.format(value))
        interval = int_to_ascii(value, width=3)
        return self._communicate(SET_PULSE_INTERVAL, interval)

    @property
    def armed(self):
        """bool: True if the stimulator is currently armed, otherwise False.

        """
        # NOTE: When magstim is ready 'armed' bit is set to 0, so need to check both
        self._send_cmd(ENABLE_REMOTE_CTRL)
        resp = self._wait_for_reply(ENABLE_REMOTE_CTRL)
        _validate_response(resp)
        return self._status.armed or self._status.ready
    
    @property
    def ready(self):
        """bool: True if the stimulator is ready to fire, otherwise False.

        """
        self._send_cmd(ENABLE_REMOTE_CTRL)
        resp = self._wait_for_reply(ENABLE_REMOTE_CTRL)
        _validate_response(resp)
        return self._status.ready

    @property
    def status(self):
        # Retrieves status information from the last response from the magstim
        self._pump()
        return self._status
