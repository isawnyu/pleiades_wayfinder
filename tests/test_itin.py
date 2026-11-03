#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the itin module
"""

import logging
from pathlib import Path
from pprint import pformat
import pytest

from pleiades_wayfinder.itin import ItinPathfinder

test_data_path = Path("tests/data")


class TestItinPathfinder:

    @classmethod
    def setup_class(cls):
        logging.basicConfig()
        logging.getLogger("normalize_space").setLevel(logging.ERROR)
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        cls.itin = ItinPathfinder()

    def test_instantiate_itin(self):
        assert isinstance(self.itin, ItinPathfinder)

    def test_find_path(self):
        from_pid = "570662"  # Sellasia
        to_pid = "570685"  # Sparta
        result = self.itin.find_path(from_pid, to_pid, month="jan")
        assert isinstance(result, dict)
        logger = logging.getLogger(__name__)
        logger.debug(f"find_path result: {pformat(result, indent=2)}")
