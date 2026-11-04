#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Code for working with itiner-e
"""

from datetime import timedelta, datetime
import logging
from pathlib import Path
from platformdirs import user_cache_path
from requests_cache import CachedSession
from statistics import mean
from time import sleep
from timeit import default_timer as timer

DEFAULT_CACHE_EXPIRE = timedelta(days=37)
DEFAULT_CACHE_PATH = user_cache_path("pleiades_wayfinder") / "itiner-e_cache"


class ItinPathfinder:
    """
    Class for fetching itiner-e data
    """

    my_headers = {
        "User-Agent": "PleiadesWayfinder/0.1",
        "From": "pleiades.admin@nyu.edu",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://itiner-e.org",
    }

    def __init__(
        self,
        cache_path: Path = DEFAULT_CACHE_PATH,
        cache_expire: timedelta = DEFAULT_CACHE_EXPIRE,
        delay_minimum: float = 0,  # minimum interval between requests in seconds
    ):
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.session = CachedSession(
            cache_name=cache_path,
            expire_after=cache_expire,
            allowable_methods=("GET", "POST"),
        )
        self.session.headers.update(self.my_headers)
        self._delay_minimum = round(delay_minimum, 2)
        self._max_request_duration = 0.0
        self._max_interval_between_requests = 0.0
        self._last_sleep_duration = 0.0
        self._last_request_end_datetime = datetime.now()

    def find_path(self, from_pid: str, to_pid: str, month="jan") -> dict:
        """
        Find a path between two Pleiades places using itiner-e
        """
        logger = logging.getLogger(self.__class__.__name__ + ".find_path")

        url = f"https://itiner-e.org/route-segments/path-finder"
        query = {
            "preferredRouteTypes": [],
            "transportationType": "foot",
            "routeCost": "fastest",
            "month": month,
            "paths": [
                {
                    "pointA": {"pleiadesPlaceId": int(from_pid)},
                    "pointB": {"pleiadesPlaceId": int(to_pid)},
                }
            ],
        }
        start = timer()
        response = self.session.post(url, json=query)
        end = timer()
        self._max_request_duration = max(self._max_request_duration, end - start)

        this_request_end_datetime = datetime.now()
        self._max_interval_between_requests = max(
            self._max_interval_between_requests,
            (
                this_request_end_datetime - self._last_request_end_datetime
            ).total_seconds(),
        )
        self._max_request_end_datetime = this_request_end_datetime

        if response.status_code != 200:
            response.raise_for_status()

        if response.from_cache:
            logger.debug(f"find_path response was from cache")
        else:
            logger.debug(f"find_path response was not from cache")
            this_sleep_duration = max(
                self._delay_minimum,
                self._max_interval_between_requests - self._last_sleep_duration / 2,
                self._max_request_duration * 2,
            )
            if this_sleep_duration > 0.00:
                if this_sleep_duration != self._last_sleep_duration:
                    logger.info(
                        f"Sleeping for {this_sleep_duration} seconds to respect rate limit"
                    )
                else:
                    logger.debug(
                        f"Sleeping for {this_sleep_duration} seconds to respect rate limit"
                    )
                sleep(this_sleep_duration)
                self._last_sleep_duration = this_sleep_duration
        return response.json()
