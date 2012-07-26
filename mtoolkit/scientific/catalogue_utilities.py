# -*- coding: utf-8 -*-

# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.


"""
A set of utility functions for performing
calculations on features in an eq catalogue:

* decimal_year
* haversine
"""

import numpy as np


def decimal_year(year, month, day):
    """
    Allows to calculate the decimal year for a vector of dates

    :param year: year column from catalogue matrix
    :type year: numpy.ndarray
    :param month: month column from catalogue matrix
    :type month: numpy.ndarray
    :param day: day column from catalogue matrix
    :type day: numpy.ndarray
    :returns: decimal year column
    :rtype: numpy.ndarray
    """

    marker = np.array([0., 31., 59., 90., 120., 151., 181.,
                                 212., 243., 273., 304., 334.])
    tmonth = (month - 1).astype(int)
    day_count = marker[tmonth] + day - 1.
    dec_year = year + (day_count / 365.)

    return dec_year


def haversine(lon1, lat1, lon2, lat2, radians=False, earth_rad=6371.227):
    """
    Allows to calculate geographical distance
    using the haversine formula.

    :param lon1: longitude of the first set of locations
    :type lon1: numpy.ndarray
    :param lat1: latitude of the frist set of locations
    :type lat1: numpy.ndarray
    :param lon2: longitude of the second set of locations
    :type lon2: numpy.float64
    :param lat2: latitude of the second set of locations
    :type lat2: numpy.float64
    :keyword radians: states if locations are given in terms of radians
    :type radians: bool
    :keyword earth_rad: radius of the earth in km
    :type earth_rad: float
    :returns: geographical distance in km
    :rtype: numpy.ndarray
    """

    if radians == False:
        cfact = np.pi / 180.
        lon1 = cfact * lon1
        lat1 = cfact * lat1
        lon2 = cfact * lon2
        lat2 = cfact * lat2

    # Number of locations in each set of points
    if not np.shape(lon1):
        nlocs1 = 1
        lon1 = np.array([lon1])
        lat1 = np.array([lat1])
    else:
        nlocs1 = np.max(np.shape(lon1))
    if not np.shape(lon2):
        nlocs2 = 1
        lon2 = np.array([lon2])
        lat2 = np.array([lat2])
    else:
        nlocs2 = np.max(np.shape(lon2))
    # Pre-allocate array
    distance = np.zeros((nlocs1, nlocs2))
    i = 0
    while i < nlocs2:
        # Perform distance calculation
        dlat = lat1 - lat2[i]
        dlon = lon1 - lon2[i]
        aval = (np.sin(dlat / 2.) ** 2.) + (np.cos(lat1) * np.cos(lat2[i]) *
             (np.sin(dlon / 2.) ** 2.))
        distance[:, i] = (2. * earth_rad * np.arctan2(np.sqrt(aval),
                                                    np.sqrt(1 - aval))).T
        i += 1
    return distance


def greg2julian(year, month, day, hour, minute, second):
    """ Function to convert a date from Gregorian to Julian format"""
    timeut = hour + (minute / 60.0) + (second / 3600.0)
    jd = (367.0 * year) - np.floor(7.0 * (year +
             np.floor((month + 9.0) / 12.0)) / 4.0) - np.floor(3.0 *
             (np.floor((year + (month - 9.0) / 7.0) / 100.0) + 1.0) /
             4.0) + np.floor((275.0 * month) / 9.0) + day +\
             1721028.5 + (timeut / 24.0)
    return jd
