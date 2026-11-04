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
from timeit import default_timer as timer

from pleiades_wayfinder.places import PlacesCollection

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_COUNT = 10
pdata_dir = environ.get("PDATA_DIR")
if pdata_dir is None:
    raise ValueError(f"environment variable PDATA_DIR returns None")
DEFAULT_JSON_PATH = Path(pdata_dir).resolve()
if not DEFAULT_JSON_PATH.is_dir():
    raise NotADirectoryError(DEFAULT_JSON_PATH)


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
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def setup_places_collection(json_path: Path) -> PlacesCollection:
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


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
