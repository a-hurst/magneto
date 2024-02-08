
import pytest
from unittest import mock

import time
from queue import Queue
from magneto import Magstim
from magneto.communication import MagstimStatus
from magneto.utils import get_mode_byte
from magneto.constants import *

# NOTE: This is pretty basic for now, but tests some of the essentials

@pytest.fixture()
def mockstim():
    with mock.patch("magneto.magstim._get_available_ports") as get_ports:
        get_ports.return_value = ['COM1']
        tst = Magstim("COM1")
    tst._from_stim = Queue()
    tst._to_stim = Queue()
    tst._com_thread = True
    tst._onset = time.perf_counter()
    yield tst

def add_to_queue(magstim, cmds):
    for cmd in cmds:
        magstim._from_stim.put(cmd)


class TestMagstim(object):

    def test_init(self):
        with mock.patch("magneto.magstim._get_available_ports") as get_ports:
            get_ports.return_value = ['COM1', 'COM4']
            tst = Magstim("COM1")
            with pytest.raises(RuntimeError):
                tst = Magstim("COM3")

    def test_pump(self, mockstim):
        tst = mockstim
        add_to_queue(tst, [b'Q\x8a$', b'Q\x8c"', b'ESg'])
        responses = tst._pump()
        assert len(responses) == 3
        # Test packets parsed correctly
        assert responses[0].cmd == ENABLE_REMOTE_CTRL
        assert responses[1].cmd == ENABLE_REMOTE_CTRL
        assert responses[2].cmd == SET_BASE_MODE
        # Test that status is updated correctly
        assert isinstance(tst._status, MagstimStatus)
        assert tst._status.ready
        assert tst._status.remote_control

    def test_send_cmd(self, mockstim):
        tst = mockstim
        # Test simple command with default padding byte
        tst._send_cmd(ENABLE_REMOTE_CTRL)
        packet = tst._to_stim.get()
        assert packet == b"Q@n"
        # Test command with data byte
        tst._send_cmd(SET_BASE_MODE, get_mode_byte(MODE_ARMED))
        packet = tst._to_stim.get()
        assert packet == b"EBx"
