
import pytest
from magneto.communication import _get_resp_bytes, MagstimStatus


def test_get_resp_bytes():
    # Test with empty input
    tst = b""
    resp, buf = _get_resp_bytes(tst)
    assert resp == b""
    assert buf == tst
    # Test with partial command
    tst += b"Q\x8a"
    resp, buf = _get_resp_bytes(tst)
    assert resp == b""
    assert buf == tst
    # Test with complete command
    tst += b"c"
    resp, buf = _get_resp_bytes(tst)
    assert resp == tst
    assert buf == b""
    # Test with overflow bytes after command
    tst = b"Q\x8acE"
    resp, buf = _get_resp_bytes(tst)
    assert resp == b"Q\x8ac"
    assert buf == b"E"


def test_MagstimStatus():
    tst = MagstimStatus(b"\x89")
    assert tst.coil_present
    assert tst.standby
    assert tst.remote_control
    assert not tst.replace_coil
    assert not tst.armed
    assert not tst.ready
    assert not tst.err
    assert not tst.fatal_err
    tst = MagstimStatus(b"\x8c")
    assert tst.ready
    assert not tst.standby
