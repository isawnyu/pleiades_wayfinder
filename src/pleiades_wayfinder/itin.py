#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Code for working with itiner-e
"""

from datetime import timedelta
import logging
from requests_cache import CachedSession

DEFAULT_CACHE_EXPIRE = timedelta(days=37)


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

    def __init__(self):
        self.session = CachedSession(allowable_methods=("GET", "POST"))
        self.session.headers.update(self.my_headers)

    def find_path(self, from_pid: str, to_pid: str, month="jan") -> dict:
        """
        Find a path between two Pleiades places using itiner-e
        """
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
        response = self.session.post(url, json=query)
        if response.status_code != 200:
            response.raise_for_status()
        logger = logging.getLogger(self.__class__.__name__ + ".find_path")
        if response.from_cache:
            logger.debug(f"find_path response was from cache")
        else:
            logger.debug(f"find_path response was not from cache")

        return response.json()
