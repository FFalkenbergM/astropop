# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Module to handle online catalog queries."""

import numpy as np
from astroquery.simbad import Simbad
from astroquery.exceptions import TableParseError
from astropy.coordinates import SkyCoord, Angle
from ..astrometry.coords_utils import guess_coordinates
from ..py_utils import string_fix, process_list


MAX_PARALLEL_QUERY = 30
MAX_RETRIES_TIMEOUT = 10


def _timeout_retry(func, *args, **kwargs):
    """Retry a function until MAX_RETRIES_TIMEOUT is reached."""
    tried = kwargs.pop('_____retires', 0)
    try:
        q = func(*args, **kwargs)
    except (TimeoutError, TableParseError):
        if tried >= MAX_RETRIES_TIMEOUT:
            raise TimeoutError(f'TimeOut obtained in {MAX_RETRIES_TIMEOUT}'
                               ' tries, aborting.')
        return _timeout_retry(func, *args, **kwargs, _____retires=tried+1)
    return q


def _wrap_query_table(table):
    """Fix bytes and objects columns to strings."""
    for i in table.columns:
        tdtype = table[i].dtype.char
        if tdtype in ('b', 'B', 'S', 'a', 'O'):
            row = process_list(string_fix, table[i])
            table[i] = np.array(row, dtype=str)
    return table


def get_center_radius(ra, dec):
    """Get the center of a list RA and DEC.

    Parameters
    ----------
    ra, dec: pair of coordinate lists in decimal degrees.

    Returns
    -------
    center_ra: the RA of the center of the field.
    center_dec: the DEC of the center of the field.
    radius: The minimum radius to fit all objects in.
    """
    center_ra = (np.max(ra) + np.min(ra))/2
    center_dec = (np.max(dec) + np.min(dec))/2
    radius = np.max([np.max(ra) - np.min(ra),
                     np.max(dec) - np.min(dec)])
    return center_ra, center_dec, radius


def astroquery_skycoord(center, simbad=None):
    """Translate center coordinates to SkyCoord object.

    Notes
    -----
    - The supported formats are:
        - `str` or `bytes`: can be an object  name or
          `~astropy.coordinates.SkyCoord` compatible RA/DEC string.
        - `list`, `tuple` or `~numpy.array`: pair (RA, DEC) coordinates.
          Must be `~astropy.coordinates.SkyCoord` compatible.
        - `~astropy.coordinates.SkyCoord` object it self.
    """
    if isinstance(center, (str, bytes)):
        try:
            return SkyCoord(center)
        except (ValueError):
            if simbad is None:
                simbad = Simbad()
            t = simbad.query_object(center)
            if t is None:
                raise ValueError(f'Coordinates {center} could not be'
                                 ' resolved.')
            return guess_coordinates(t['RA'][0], t['DEC'][0], skycoord=True)
    elif isinstance(center, (tuple, list, np.ndarray)) and len(center) == 2:
        return guess_coordinates(center[0], center[1], skycoord=True)
    elif isinstance(center, SkyCoord):
        return center

    raise ValueError(f'Center coordinates {center} not undertood.')


def astroquery_radius(radius):
    """Convert several types of values to decimal degree angle radius.

    Notes
    -----
    - Current supported types are:
      - Any instance that can be converted to `float`.
      - `str` or `bytes` that can be converted to `astropy.coordinates.Angle`.
    """
    if isinstance(radius, (str, bytes)):
        radius = Angle(radius)

    if isinstance(radius, Angle):
        radius = radius.degree

    return f"{float(radius)}d"
