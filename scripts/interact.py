#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#


"""
Interact with Pleiades data and Itiner-e API to find paths between places"""

from airtight.cli import configure_commandline
from datetime import datetime
import logging
from os import environ
from pathlib import Path
from pprint import pformat, pprint
import re
from timeit import default_timer as timer

from pleiades_wayfinder.itin import ItinPathfinder
from pleiades_wayfinder.places import PlacesCollection, UnknownPIDError
from pleiades_wayfinder.process import get_candidate_places
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

idata_file = environ.get("ITINDATA_FILE")
if idata_file is None:
    raise ValueError(f"environment variable ITINDATA_FILE returns None")
DEFAULT_ITIN_FILE_PATH = Path(idata_file).resolve()
if not DEFAULT_ITIN_FILE_PATH.is_file():
    raise FileNotFoundError(DEFAULT_ITIN_FILE_PATH)

rx_puri = re.compile(r"https://pleiades.stoa.org/places/(?P<pid>\d+)")


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


def setup_places_collection(
    pleiades_json_path: Path, itin_json_path: Path
) -> PlacesCollection:
    """
    Setup the Pleiades places collection and read JSON into it from json_path
    """
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


def main(**kwargs):
    """
    main function
    """

    logging.getLogger("normalize_space").setLevel(logging.ERROR)  # hush
    logging.getLogger("PlacesCollection.load").setLevel(logging.INFO)
    logging.getLogger("requests_cache.policy.actions").setLevel(logging.ERROR)
    pleiades_json_path = Path(kwargs["pleiades_json_path"]).expanduser().resolve()
    if not pleiades_json_path.is_dir():
        raise NotADirectoryError(pleiades_json_path)
    itin_json_path = Path(kwargs["itin_json_path"]).expanduser().resolve()
    if not itin_json_path.is_file():
        raise FileNotFoundError(itin_json_path)
    pc = setup_places_collection(
        pleiades_json_path=pleiades_json_path, itin_json_path=itin_json_path
    )
    ipf = ItinPathfinder()

    distance = kwargs["distance"]
    if isinstance(distance, (str, int)):
        distance = float(distance)
    elif not isinstance(distance, float):
        raise ValueError(
            f"got distance of type {type(distance)}; expected int, float, or str"
        )
    max_count = int(kwargs["candidate_count"])
    while True:
        from_pid = input_pid()
        try:
            nearby_places = get_candidate_places(
                from_pid, kwargs["distance"], max_count, pc
            )
        except UnknownPIDError as err:
            logger.error(
                f"This PID {from_pid} is either not in Pleiades or not known to Itiner-e."
            )
            continue
        except RuntimeError as err:
            err_s = str(err)
            if err_s.startswith(f"Place {from_pid} is not") and (
                err_s.endswith("certainly located")
                or err_s.endswith("attested in the Roman era")
            ):
                logger.error(err_s)
                continue
            else:
                raise err

        print(
            f"Found the nearest {len(nearby_places)} certainly located places (as the crow flies):"
        )
        for place in sorted(nearby_places, key=lambda p: p.title.lower()):
            print(f" - {place.pid}: {place.title}")
        results = {}
        month = datetime.now().strftime("%b").lower()
        reset_courtesy = True
        for to_pid in [p.pid for p in nearby_places]:
            results[to_pid] = ipf.find_path(
                from_pid, to_pid, month=month, reset_courtesy=reset_courtesy
            )
            reset_courtesy = False
        logger.debug(pformat(results, indent=2))

        try:
            route_list = sorted(
                [
                    obj["results"][0]
                    for obj in results.values()
                    if obj["results"][0]["distanceKm"] is not None
                ],
                key=lambda r: r["distanceKm"],
            )
        except TypeError as err:
            err.add_note(pformat(results, indent=2))
            raise err
        print(
            f"There are {len(route_list)} reachable neighbors. From nearest to furthest:"
        )
        if len(route_list) == 0:
            reasons = set()
            if results:
                for attempt in results.values():
                    reasons.add(attempt["results"][0]["failedReason"])
            logger.error(", ".join(sorted(list(reasons))))
            continue
        for route in route_list:
            destination_pid = str(route["pointB"]["origin"])
            destination_place = pc.get(destination_pid)
            print(f" - {destination_place.title}: {route['distanceKm']:,.1f} km")

        # nearest neighbor

        nn_segments = route_list[0]["routeSegmentIds"]
        nn_segments_count = len(nn_segments)

        discrete_routes = [route_list[0]]
        for route in sorted(route_list[1:], key=lambda r: len(r["routeSegmentIds"])):
            if len(route["routeSegmentIds"]) < nn_segments_count:
                discrete_routes.append(route)
            else:
                unique = True
                init_seq = route["routeSegmentIds"][:nn_segments_count]
                for discrete_route in discrete_routes:
                    if (
                        init_seq
                        == discrete_route["routeSegmentIds"][:nn_segments_count]
                    ):
                        unique = False
                        break
                if unique:
                    discrete_routes.append(route)
        print(
            f"There are {len(discrete_routes)-1} routes whose initial segments differ from those in the route to the nearest place:"
        )
        for route in sorted(discrete_routes, key=lambda r: r["distanceKm"]):
            destination_pid = str(route["pointB"]["origin"])
            destination_place = pc.get(destination_pid)
            print(f" - {destination_place.title}: {route['distanceKm']:,.1f} km")


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
