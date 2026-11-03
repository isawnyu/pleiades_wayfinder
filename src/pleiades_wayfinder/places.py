#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Handle Pleiades Places
"""

import functools
import json
import logging
from math import cos, radians
import os
from pathlib import Path
from pprint import pformat
from shapely import STRtree
from shapely.errors import GEOSException
from shapely.geometry import GeometryCollection, shape

from .text import norm


def _pid_valid(val: str) -> bool:
    """
    Determine if a Pleiades ID is valid.  Valid PIDs are strings containing integer values.
    """
    if not isinstance(val, str):
        raise TypeError(f"Got {type(val)} for pid; expected str")
    val = norm(val)
    if not val:
        raise ValueError(f"pid cannot be zero-length string")
    try:
        check_val = str(int(val))
    except ValueError:
        raise ValueError(f"pid must be a string containing an integer value")
    else:
        if check_val != val:
            raise RuntimeError(
                f"raw pid value '{val}' failed to round-trip '{check_val}'"
            )
    return True


@functools.lru_cache(maxsize=None)
def meters_to_degrees(m, origin_latitude):
    """
    Convert meters to degrees latitude/longitude at the specified origin latitude
    https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-latitude-longitude-by-some-amount-of-meters
    """
    lat = m / 111111
    lon = m / (111111 * cos(radians(origin_latitude)))
    return (lat + lon) / 2


class PlacesCollection:
    """
    A collection of Pleiades places and associated functionality
    """

    def __init__(self):
        self._places = dict()
        self._spatial_index = None  # will be set when needed
        self._spatial_index_to_pid = dict()  # will be set when needed

    def build_spatial_index(self):
        """
        Build a spatial index for the places in this collection
        """

        logger = logging.getLogger(f"{self.__class__.__name__}.build_spatial_index")
        i = 0
        hulls = []
        logger.debug(f"Building spatial index for {len(self._places)} places")
        jmod = max(1, len(self._places) // 10)
        for pi, place in enumerate(self._places.values()):
            if place.certainly_located:
                hull = place.hull
                if hull is not None:
                    self._spatial_index_to_pid[i] = place.pid
                    hulls.append(hull)
                    i += 1
            if pi % jmod == 0:
                logger.debug(
                    f"Collected {pi} of {len(self._places)} concave hulls for places"
                )
        logger.debug(
            f"Starting to build spatial index for {len(hulls)} certainly located places"
        )
        self._spatial_index = STRtree(hulls)
        logger.debug(f"Built spatial index for {len(hulls)} certainly located places")

    def get(self, pid: str) -> PleiadesPlace:
        if _pid_valid(pid):
            return self._places[pid]
        else:
            raise RuntimeError(f"Invalid PID {pid}")

    def get_nearby_places(
        self, pid: str, max_distance_meters: float
    ) -> list[PleiadesPlace]:
        """
        Return a list of PleiadesPlace objects for places within the specified distance of this place
        """
        if not self._spatial_index:
            self.build_spatial_index()
        place = self.get(pid)
        if not place.certainly_located:
            raise RuntimeError(f"Place {pid} is not certainly located")
        hull = place.hull
        if not hull:
            raise RuntimeError(f"Place {pid} has no convex hull")
        buffered_hull = hull.buffer(
            meters_to_degrees(max_distance_meters, hull.centroid.y)
        )
        match_indexes = self._spatial_index.query(buffered_hull)  # type: ignore
        matched_pids = [self._spatial_index_to_pid[i] for i in match_indexes]
        return [self.get(mpid) for mpid in matched_pids if mpid != pid]

    def load(self, pleiades_json_path: Path):
        """
        Load pleiades json from files in directory subtree
        """
        logger = logging.getLogger(f"{self.__class__.__name__}.load")
        file_paths = [
            Path(dirpath) / fn
            for dirpath, dirnames, filenames in os.walk(pleiades_json_path)
            for fn in filenames
            if fn.endswith(".json")
        ]
        logger.debug(f"found {len(file_paths)} JSON files")
        logger.debug(pformat(file_paths, indent=2))
        for fpath in file_paths:
            with open(fpath, mode="r", encoding="utf-8") as f:
                pp = PleiadesPlace(json.load(f))
            self._places[pp.pid] = pp
        logger.debug(f"read {len(self._places)} Pleiades places from JSON files")
        if len(file_paths) != len(self._places):
            raise RuntimeError(
                f"Mismatch between number of JSON files found {(len(file_paths))} and number of Pleiades places read from JSON {(len(self._places))}"
            )


class PleiadesPlace:
    """
    Object to carry data for a single Pleiades place
    """

    def __init__(self, raw_data: dict):
        self.raw_data = raw_data
        self._set_pid(raw_data["id"])
        self._set_title(raw_data["title"])
        self._set_place_types(raw_data["placeTypes"])

        # these values get set the first time they are asked for
        self._certainly_located = None
        self._hull = None

    @property
    def certainly_located(self) -> bool:
        """
        Is this place really certainly located?
        """
        if self._certainly_located is not None:
            pass  # we will use previously determined response
        else:
            self._certainly_located = True  # assume true until proven otherwise
            if "unlocated" in self.place_types:
                self._certainly_located = False
            else:
                if len(self.raw_data["locations"]) == 0:
                    if [
                        conn
                        for conn in self.raw_data["connections"]
                        if conn["connection_type"] in {"located_at", "part_of_physical"}
                    ]:
                        pass
                    else:
                        self._certainly_located = False
                else:
                    precisions = set()
                    feature_d = {
                        feature["id"]: feature for feature in self.raw_data["features"]
                    }
                    for loc in self.raw_data["locations"]:
                        loc_id = loc["id"]
                        feature = feature_d[loc_id]
                        precisions.add(feature["properties"]["location_precision"])
                    if "rough" in precisions:
                        self._certainly_located = False
                    else:
                        accuracies = {
                            loc["accuracy_value"] for loc in self.raw_data["locations"]
                        }
                        if any(acc > 1000.0 for acc in accuracies):
                            self._certainly_located = False
        return self._certainly_located

    @property
    def hull(self):
        """
        Return the convex hull of the locations for this place, or None if there are no locations
        """
        if self._hull is not None:
            return self._hull
        if not self.certainly_located:
            return None
        buffered_shapes = []
        if len(self.raw_data["locations"]) == 0:
            # make from connections
            raise NotImplementedError(
                f"Making hull from connections not yet implemented (pid: {self.pid})"
            )
        else:
            # make from locations
            for i, loc in enumerate(self.raw_data["locations"]):
                if loc["geometry"] and loc["accuracy_value"]:
                    this_shape = shape(loc["geometry"])
                    if "darmc" in self.raw_data["locations"][i]["accuracy"]:
                        radius = max(1000.0, loc["accuracy_value"])
                    else:
                        radius = loc["accuracy_value"]
                    centroid = this_shape.centroid
                    buffered = this_shape.buffer(meters_to_degrees(radius, centroid.y))
                    if buffered:
                        buffered_shapes.append(buffered)

        if buffered_shapes:
            this_hull = GeometryCollection(buffered_shapes).convex_hull
            self._hull = this_hull
            return self._hull

    @property
    def pid(self) -> str:
        """
        Return value of Pleiades ID for this place
        """
        return self._pid

    def _set_pid(self, val: str):
        """
        Private: set value of Pleiades ID for this place
        """
        if _pid_valid(val):
            self._pid = val
        else:
            raise RuntimeError(f"Invalid PID {val}")

    @property
    def place_types(self) -> list[str]:
        """
        Return value of place types for this place
        """
        return self._place_types

    def _set_place_types(self, val: list[str]):
        """
        Private: set value of place types for this place
        """
        if not isinstance(val, list):
            raise TypeError(f"Got {type(val)} for place_types; expected list")
        if not all(isinstance(v, str) for v in val):
            raise TypeError(f"Got non-str value in place_types list")
        self._place_types = list({norm(v) for v in val if norm(v)})

    @property
    def title(self) -> str:
        """
        Return value of title for this place
        """
        return self._title

    def _set_title(self, val: str):
        """
        Private: set value of title for this place
        """
        if not isinstance(val, str):
            raise TypeError(f"Got {type(val)} for title; expected str")
        val = norm(val)
        if not val:
            raise ValueError(f"title cannot be zero-length string")
        self._title = val
