#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Interaction processes
"""

import logging
from pleiades_wayfinder.places import PlacesCollection

ITIN_PLACE_TYPES = {"settlement", "port", "fort", "station", "bridge", "pass", "oasis"}


def get_candidate_places(
    from_pid: str, distance: float, max_count: int, pc: PlacesCollection
) -> list:
    logger = logging.getLogger(f"pleiades_wayfinder.process.get_candidate_places")
    nearby_places = []
    increment = 1000.0
    while True:
        nearby_places = pc.get_nearby_places(from_pid, max_distance_meters=distance)

        logger.debug(
            f"{len(nearby_places)} nearby places in {distance / 1000.0:,} km (all types)"
        )
        nearby_places = [
            p
            for p in nearby_places
            if set(p.place_types).intersection(ITIN_PLACE_TYPES)
        ]
        logger.debug(
            f"{len(nearby_places)} nearby places in {distance / 1000.0:,} km (itiner-e types)"
        )
        if len(nearby_places) < max_count:
            distance += increment
        else:
            break
    return nearby_places
