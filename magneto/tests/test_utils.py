
import pytest
from magneto.utils import _check_error
from magneto.constants import *


def test_check_error():
    # Test no error on regular response
    assert _check_error(b"Q\x8a$") == None
    # Test invalid command error
    assert _check_error(b"?") == INVALID_CMD
    # Test invalid data error
    assert _check_error(b"@?o") == INVALID_DATA
    # Test setttings conflict error
    assert _check_error(b"ESg") == SETTINGS_CONFLICT
    # Test CRC mismatch error
    assert _check_error(b"Q\x8a0") == CRC_ERROR
