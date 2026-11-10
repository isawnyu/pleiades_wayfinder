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
from copy import deepcopy
from datetime import datetime
import json
import logging
from math import floor
from os import environ, rename
from pathlib import Path
from platformdirs import user_cache_path
from sympy import nextprime
from time import sleep

from pleiades_wayfinder.itin import ItinPathfinder, DEFAULT_CACHE_EXPIRE
from pleiades_wayfinder.places import UnknownPIDError
from pleiades_wayfinder.process import (
    get_candidate_places,
    hush_noisy_loggers,
    setup_places_collection,
)

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

DEFAULT_DAILY_QUOTA = 300
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
    [
        "-q",
        "--daily-quota",
        DEFAULT_DAILY_QUOTA,
        "number of valid from-pids to try today",
        False,
    ],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]
initial_cache_bak = False


def write_cache(checked_from_pid_cache: Path, checked_from_pids: set):
    global initial_cache_bak
    if checked_from_pid_cache.is_file():
        if not initial_cache_bak:
            bak_path = Path(str(checked_from_pid_cache) + ".bak")
            rename(checked_from_pid_cache, bak_path)
            initial_cache_bak = True
    with open(checked_from_pid_cache, "w", encoding="utf-8") as f:
        json.dump(sorted(list(checked_from_pids)), f)


def main(**kwargs):
    """
    main function
    """
    logger = logging.getLogger(f"pleiades_wayfinder.scripts.incremental.main")

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

    checked_from_pid_cache = (
        user_cache_path("pleiades_wayfinder") / "incremental_pids_cache.json"
    )
    if checked_from_pid_cache.is_file():
        with open(checked_from_pid_cache, "r", encoding="utf-8") as f:
            checked_from_pids = json.load(f)
    else:
        checked_from_pids = []
    checked_from_pids = set(checked_from_pids)

    month = datetime.now().strftime("%b").lower()
    daily_quota = kwargs["daily_quota"]
    if isinstance(daily_quota, str):
        daily_quota = int(daily_quota)
    elif isinstance(daily_quota, int):
        pass
    else:
        raise TypeError(f"daily_quota expected int or str but got {type(daily_quota)}")
    sleep_duration = nextprime(5 * 60 * 60 // daily_quota * 0.9)
    if not isinstance(sleep_duration, int):
        raise TypeError(
            f"sleep_duration is supposed to be an integer, but it is instead {type(sleep_duration)}"
        )
    sleep_duration = float(sleep_duration)
    i = 0
    candidate_pids = deepcopy(pc._known_to_itinere)
    candidate_pids.difference(checked_from_pids)
    while True:
        try:
            # pick a pid not in checked_from_pids
            from_pid = candidate_pids.pop()
            p = pc.get(from_pid)
            print(
                f"⏬ Preparing to calculate neighbors and routes for PID {from_pid}: {p.title}"
            )
            try:
                nearby_places = get_candidate_places(
                    from_pid, kwargs["distance"], max_count, pc
                )
            except UnknownPIDError as err:
                logger.error(
                    f"This PID {from_pid} is either not in Pleiades or not known to Itiner-e."
                )
                checked_from_pids.add(from_pid)
                continue
            except RuntimeError as err:
                err_s = str(err)
                if err_s.startswith(f"Place {from_pid} is not") and (
                    err_s.endswith("certainly located")
                    or err_s.endswith("attested in the Roman era")
                ):
                    logger.error(err_s)
                    checked_from_pids.add(from_pid)
                    continue
                else:
                    raise err
            if len(nearby_places) > floor(max_count * 1.5):
                max_j = floor(max_count * 1.5)
                logger.warning(
                    f"Unexpectedly huge number of nearby places detected: {len(nearby_places)}. We will only request "
                    f"routes for {max_j} of them."
                )
            else:
                max_j = len(nearby_places)
            reset_courtesy = True
            for j, to_pid in enumerate([p.pid for p in nearby_places]):
                ipf.find_path(
                    from_pid, to_pid, month=month, reset_courtesy=reset_courtesy
                )  # this will put responses in the cache
                reset_courtesy = False
            i += 1

        except Exception as err:
            write_cache(checked_from_pid_cache, checked_from_pids)
            raise err
        else:
            checked_from_pids.add(from_pid)
            write_cache(checked_from_pid_cache, checked_from_pids)
        if i >= daily_quota:
            break
        else:
            print(
                f"✅ Cached Itiner-E responses for neighbors of pid {from_pid}. {i} pids "
                f"checked today (today's quota is {daily_quota}). This brings the cached "
                f"pid count to {len(checked_from_pids)}. Now we will sleep for "
                f"{sleep_duration} seconds to be kind to the Itiner-E server."
            )
            sleep(sleep_duration)


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
