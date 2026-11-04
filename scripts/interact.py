#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#


"""
Interact with Pleiades data and Itiner-e API to find paths between places"""

from airtight.cli import configure_commandline
import logging
from os import environ
from pathlib import Path
import re
from timeit import default_timer as timer

from pleiades_wayfinder.places import PlacesCollection
from pleiades_wayfinder.text import norm

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_COUNT = 10
DEFAULT_CANDIDATE_DISTANCE = 10000.0  # meters
pdata_dir = environ.get("PDATA_DIR")
if pdata_dir is None:
    raise ValueError(f"environment variable PDATA_DIR returns None")
DEFAULT_JSON_PATH = Path(pdata_dir).resolve()
if not DEFAULT_JSON_PATH.is_dir():
    raise NotADirectoryError(DEFAULT_JSON_PATH)
rx_puri = re.compile(r"https://pleiades.stoa.org/places/(?P<pid>\d+)")

ITIN_PLACE_TYPES = {"settlement", "port", "fort", "station", "bridge", "pass", "oasis"}

DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    [
        "-l",
        "--loglevel",
        "NOTSET",
        "desired logging level ("
        + "case-insensitive string: DEBUG, INFO, WARNING, or ERROR",
        False,
    ],
    ["-v", "--verbose", False, "verbose output (logging level == INFO)", False],
    [
        "-w",
        "--veryverbose",
        False,
        "very verbose output (logging level == DEBUG)",
        False,
    ],
    [
        "-c",
        "--candidate-count",
        DEFAULT_CANDIDATE_COUNT,
        "number of candidate paths to consider",
        False,
    ],
    [
        "-p",
        "--pleiades-json-path",
        str(DEFAULT_JSON_PATH),
        "path to directory containing Pleiades JSON files",
        False,
    ],
    [
        "-d",
        "--distance",
        DEFAULT_CANDIDATE_DISTANCE,
        "default candidate search distance in meters",
        False,
    ],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def get_candidate_places(
    from_pid: str, distance: float, max_count: int, pc: PlacesCollection
) -> list:
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


def input_pid() -> str:
    """
    Prompt the user for a Pleiades ID or URI and convert it to a pid
    """
    while True:
        while True:
            raw = norm(input("Enter a Pleiades ID or URI: "))
            if raw:
                break
        if raw.lower() in {"q", "quit", "exit"}:
            exit()
        m = rx_puri.fullmatch(raw)
        if m:
            pid = m.group("pid")
        else:
            pid = raw
        try:
            str(int(pid))
        except ValueError:
            print(f"Invalid PID '{pid}'. Try again.")
        else:
            return pid


def setup_places_collection(json_path: Path) -> PlacesCollection:
    """
    Setup the Pleiades places collection and read JSON into it from json_path
    """
    pc = PlacesCollection()
    logger.info(f"Loading places from {json_path} ...")
    start = timer()
    pc.load(json_path)
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
        f"... finished loading {len(pc._places):,} places from {json_path}. Elapsed time: {e_string}."
    )
    return pc


def main(**kwargs):
    """
    main function
    """

    json_path = Path(kwargs["pleiades_json_path"]).resolve()
    if not json_path.is_dir():
        raise NotADirectoryError(json_path)
    pc = setup_places_collection(json_path)
    from_pid = input_pid()
    distance = kwargs["distance"]
    if isinstance(distance, (str, int)):
        distance = float(distance)
    elif not isinstance(distance, float):
        raise ValueError(
            f"got distance of type {type(distance)}; expected int, float, or str"
        )
    max_count = int(kwargs["candidate_count"])
    nearby_places = get_candidate_places(from_pid, kwargs["distance"], max_count, pc)
    print(
        f"Found {len(nearby_places)} certainly located places within {distance / 1000.0:,} kilometers:"
    )
    for place in sorted(nearby_places, key=lambda p: p.title.lower()):
        print(f" - {place.pid}: {place.title}")


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
