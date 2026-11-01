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


class PlacesCollection:
    """
    A collection of Pleiades places and associated functionality
    """

    def __init__(self):
        self._places = dict()

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
        self._pid = val

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
