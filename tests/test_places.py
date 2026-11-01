#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the places module
"""

import logging
from pathlib import Path
import pytest

from pleiades_wayfinder.places import PlacesCollection

test_data_path = Path("tests/data")


@pytest.fixture()
def Places():
    yield PlacesCollection()


class TestPlaces:

    @classmethod
    def setup_class(cls):
        logging.getLogger("normalize_space").setLevel(logging.ERROR)

    def test_instantiate_places(self, Places):
        assert isinstance(Places, PlacesCollection)
        Places.load(pleiades_json_path=test_data_path / "pleiades_json")

    def test_get_place(self):
        pid = "570662"  # Sellasia
        pass
