#
# This file is part of pleiades_wayfinder
# by Tom Elliott for the Institute for the Study of the Ancient World at New York University
# (c) Copyright 2026 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Text-related functions
"""

from textnorm import normalize_space as norm_space, normalize_unicode as norm_unicode


def norm(val: str) -> str:
    """
    Normalize space and unicode in a string
    """
    if not isinstance(val, str):
        raise TypeError(f"Expected str for val; got {type(val)}")
    return norm_unicode(norm_space(val))
