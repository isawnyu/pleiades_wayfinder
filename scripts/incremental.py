#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#


"""
Interact with Pleiades data and Itiner-e API to find paths between all known places
"""

from airtight.cli import configure_commandline
import logging
from os import environ
from pathlib import Path

from pleiades_wayfinder.itin import ItinPathfinder
from pleiades_wayfinder.process import hush_noisy_loggers, setup_places_collection

logger = logging.getLogger(__name__)

DEFAULT_CANDIDATE_COUNT = 10
DEFAULT_CANDIDATE_DISTANCE = 10000.0  # meters
pdata_dir = environ.get("PDATA_DIR")
if pdata_dir is None:
    raise ValueError(f"environment variable PDATA_DIR returns None")
DEFAULT_JSON_PATH = Path(pdata_dir).resolve()
if not DEFAULT_JSON_PATH.is_dir():
    raise NotADirectoryError(DEFAULT_JSON_PATH)

idata_file = environ.get("ITINDATA_FILE")
if idata_file is None:
    raise ValueError(f"environment variable ITINDATA_FILE returns None")
DEFAULT_ITIN_FILE_PATH = Path(idata_file).resolve()
if not DEFAULT_ITIN_FILE_PATH.is_file():
    raise FileNotFoundError(DEFAULT_ITIN_FILE_PATH)
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
    [
        "-i",
        "--itin-json-path",
        str(DEFAULT_ITIN_FILE_PATH),
        "path to JSONLD file containing Itiner-e data",
        False,
    ],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def main(**kwargs):
    """
    main function
    """

    hush_noisy_loggers()

    pleiades_json_path = Path(kwargs["pleiades_json_path"]).expanduser().resolve()
    if not pleiades_json_path.is_dir():
        raise NotADirectoryError(pleiades_json_path)
    itin_json_path = Path(kwargs["itin_json_path"]).expanduser().resolve()
    if not itin_json_path.is_file():
        raise FileNotFoundError(itin_json_path)
    pc = setup_places_collection(
        pleiades_json_path=pleiades_json_path, itin_json_path=itin_json_path
    )

    distance = kwargs["distance"]
    if isinstance(distance, (str, int)):
        distance = float(distance)
    elif not isinstance(distance, float):
        raise ValueError(
            f"got distance of type {type(distance)}; expected int, float, or str"
        )
    max_count = int(kwargs["candidate_count"])
    ipf = ItinPathfinder()


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
