#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the places module
"""

import json
import logging
from pathlib import Path
import pytest

from pleiades_wayfinder.places import PlacesCollection, PleiadesPlace

test_data_path = Path("tests/data")


class TestPlaces:

    @classmethod
    def setup_class(cls):
        logging.getLogger("normalize_space").setLevel(logging.ERROR)
        pc = PlacesCollection()
        pc.load(pleiades_json_path=test_data_path / "pleiades_json")
        cls.pc = pc

    def test_instantiate_places(self):
        assert isinstance(self.pc, PlacesCollection)

    def test_get_place(self):
        pid = "570662"  # Sellasia
        place = self.pc.get(pid)


class TestPleiadesPlace:

    def test_place(self):
        test_place_json_path = test_data_path / "/".join(
            ("pleiades_json", "570662.json")
        )
        with open(test_place_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        p = PleiadesPlace(raw)
        assert p.pid == "570662"
        assert p.title == "Sellasia"
