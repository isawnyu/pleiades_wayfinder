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
from pathlib import Path
from pleiades_wayfinder.places import PlacesCollection
from timeit import default_timer as timer

ITIN_PLACE_TYPES = {"settlement", "port", "fort", "station", "bridge", "pass", "oasis"}


def get_candidate_places(
    from_pid: str, distance: float, max_count: int, pc: PlacesCollection
) -> list:
    """
    Find a list of candidate neighboring places to from_pid, expanding the search radius incrementally
    """
    logger = logging.getLogger(f"pleiades_wayfinder.process.get_candidate_places")
    nearby_places = []
    increment = 1000.0
    logger.info(
        f"Searching for at least {max_count} places known to both Pleiades and Itiner-E that lie within {distance / 1000.0:,} km of PID {from_pid}  ..."
    )
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
        if len(nearby_places) < max_count:
            logger.info(
                f"... found only {len(nearby_places)} so expanding search radius to {distance / 1000.0:,} km ..."
            )
            distance += increment
        else:
            logger.info(
                f"Done! Found {len(nearby_places)} within {distance / 1000.0:,} km."
            )
            break
    return nearby_places


def setup_places_collection(
    pleiades_json_path: Path, itin_json_path: Path
) -> PlacesCollection:
    """
    Setup the Pleiades places collection and read JSON into it from json_path
    """
    logger = logging.getLogger(f"pleiades_wayfinder.process.setup_places_collection")

    pc = PlacesCollection()
    logger.info(f"Loading places from {pleiades_json_path} ...")
    start = timer()
    pc.load(pleiades_json_path, itin_json_path)
    end = timer()
    elapsed = end - start
    minutes = elapsed // 60
    if minutes == 0:
        e_string = ""
        seconds = elapsed
    else:
        e_string = f"{minutes:.0f} minute"
        if minutes > 1:
            e_string += "s"
        seconds = elapsed - minutes
        if seconds:
            e_string += " and "
    if seconds:
        e_string += f"{seconds:.0f} second"
        if seconds > 1:
            e_string += "s"
    logger.info(
        f"... finished loading {len(pc._places):,} places from {pleiades_json_path}. Elapsed time: {e_string}."
    )
    return pc
