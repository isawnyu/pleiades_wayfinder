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
import os
from pathlib import Path


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
        files = [
            f
            for r, d, files in os.walk(pleiades_json_path)
            for f in files
            if f.endswith(".json")
        ]
        logger.debug(f"found {len(files)} JSON files")
