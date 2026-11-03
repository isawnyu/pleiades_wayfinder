#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Code for working with itiner-e
"""

import logging
from pprint import pformat

# from requests_cache import CachedSession
import requests
from http.client import HTTPConnection


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
        # self.session = CachedSession()
        # self.session.headers.update(self.my_headers)
        # logger = logging.getLogger(__name__)
        # logger.debug(f"headers: {pformat(self.my_headers, indent=2)}")
        pass

    def find_path(self, from_pid: str, to_pid: str, month="jan") -> dict:
        """
        Find a path between two Pleiades places using itiner-e
        """
        logging.basicConfig()
        logger = logging.getLogger(__name__)
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
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
        response = requests.post(url, json=query, headers=self.my_headers)
        #        response = self.session.post(url, data=query)

        return response.json()
