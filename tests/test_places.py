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

    def test_get_place_invalid_pid(self):
        with pytest.raises(ValueError):
            self.pc.get("not-a-valid-pid")

    def test_iterate_places(self):
        for place in self.pc._places.values():
            assert isinstance(place, PleiadesPlace)

    def test_iterate_places_certainly_located(self):
        expectations = {
            "570662": True,
            "570330": False,  # because DARMC location with accuracy = 10,000
            "570575": True,
            "570723": False,  # because DARMC location with accuracy = 10,000
            "570323": False,  # because DARMC location with accuracy = 10,000
            "570685": True,
            "570265": False,  # because DARMC location with accuracy = 10,000
        }
        for pid, place in self.pc._places.items():
            assert place.certainly_located == expectations[pid]

    def test_build_spatial_index(self):
        self.pc.build_spatial_index()
        assert self.pc._spatial_index is not None
        assert self.pc._spatial_index_to_pid is not None
        assert len(self.pc._spatial_index_to_pid) == len(
            self.pc._spatial_index.geometries
        )
        assert (
            len(self.pc._spatial_index_to_pid) == 3
        )  # only 3 certainly located places

    def test_get_nearby_places(self):
        self.pc.build_spatial_index()
        pid = "570662"  # Sellasia
        nearby_places = self.pc.get_nearby_places(
            pid, max_distance_meters=100 * 1000
        )  # 100 km
        assert len(nearby_places) == 2
        matched_pids = {p.pid for p in nearby_places}
        assert matched_pids == {"570685", "570575"}


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

    def test_place_certainly_located(self):
        test_place_json_path = test_data_path / "/".join(
            ("pleiades_json", "570662.json")
        )
        with open(test_place_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        p = PleiadesPlace(raw)
        assert p.certainly_located is True

    def test_place_not_certainly_located(self):
        test_place_json_path = test_data_path / "/".join(
            ("pleiades_json", "570330.json")
        )
        with open(test_place_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        p = PleiadesPlace(raw)
        assert p.certainly_located is False

    def test_place_hull(self):
        test_place_json_path = test_data_path / "/".join(
            ("pleiades_json", "570662.json")
        )
        with open(test_place_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        p = PleiadesPlace(raw)
        assert p.hull is not None

    def test_place_hull_not_certainly_located(self):
        test_place_json_path = test_data_path / "/".join(
            ("pleiades_json", "570330.json")
        )
        with open(test_place_json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        p = PleiadesPlace(raw)
        assert p.hull is None
