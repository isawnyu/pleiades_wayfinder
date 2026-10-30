#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the places module
"""

import pytest

from pleiades_wayfinder.places import PlacesCollection


@pytest.fixture()
def Places():
    yield PlacesCollection()


class TestPlaces:

    def test_instantiate_places(self, Places):
        assert isinstance(Places, PlacesCollection)

    def test_get_place(self):
        pid = "570662"  # Sellasia
        pass
