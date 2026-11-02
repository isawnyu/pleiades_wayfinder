#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Handle Pleiades Places
"""

import json
import logging
from .text import norm
import os
from pathlib import Path
from pprint import pformat


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


class PlacesCollection:
    """
    A collection of Pleiades places and associated functionality
    """

    def __init__(self):
        self._places = dict()

    def get(self, pid: str) -> PleiadesPlace:
        if _pid_valid(pid):
            return self._places[pid]
        else:
            raise RuntimeError(f"Invalid PID {pid}")

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
