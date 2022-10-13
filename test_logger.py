import unittest
import logging

from templatescript import *

class TestLogger(unittest.TestCase):

    def setUp(self):
        pass

    def test_add_new_loglevel(self):
        assert "TRACE" not in list(logging._nameToLevel.keys())
        addLoggingLevel("TRACE", logging.DEBUG - 5)
        assert "TRACE" in list(logging._nameToLevel.keys())