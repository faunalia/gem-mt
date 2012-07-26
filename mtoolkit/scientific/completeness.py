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
The purpose of this module is to provide functions
which implement completeness algorithms. Implemented
algorithms are:

* Stepp
"""


import numpy as np
import logging

LOGGER = logging.getLogger('mt_logger')


def stepp_analysis(year, mw, dm=0.1, dt=1, ttol=0.2, iloc=True):
    """
    Stepp algorithm

    :param year: catalog matrix year column
    :type year: numpy.ndarray
    :param mw: catalog matrix magnitude column
    :type mw: numpy.ndarray
    :keyword dm: magnitude interval/window
    :type dm: positive float
    :keyword dt: time interval
    :type dt: int
    :keyword ttol: tolerance threshold
    :type ttol: positive float
    :keyword iloc: Fix analysis such that completeness magnitude
                   can only increase with catalogue duration
                   (i.e. completess cannot increase for more recent
                   catalogues)
    :type iloc: bool
    :returns: two-column completeness table representing the earliest
              year at which the catalogue is complete above a
              given magnitude
    :rtype: numpy.ndarray
    """

    # Round off the magnitudes to 2 d.p
    mw = np.around(100.0 * mw) / 100.0
    lowm = np.floor(10. * np.min(mw)) / 10.
    highm = np.ceil(10. * np.max(mw)) / 10.
    # Determine magnitude bins
    mbin = np.arange(lowm, highm + dm, dm)
    ntb = np.max(np.shape(mbin))
    # Determine time bins
    end_time = np.max(year)
    start_time = np.min(year)
    time_range = np.arange(dt, end_time - start_time + 2, dt)
    nt = np.max(np.shape(time_range))
    t_upper_bound = end_time * np.ones(nt)
    t_lower_bound = t_upper_bound - time_range
    t_rate = 1. / np.sqrt(time_range)  # Poisson rate

    number_obs = np.zeros((nt, ntb - 1))
    lamda = np.zeros((nt, ntb - 1))
    siglam = np.zeros((nt, ntb - 1))
    ii = 0
    # count number of events catalogue and magnitude windows
    while ii <= (nt - 1):
    # Select earthquakes later than or in Year[ii]
        yrchk = year >= t_lower_bound[ii]
        mtmp = mw[yrchk]
        jj = 0
        while jj <= (ntb - 2):
            #Count earthquakes in magnitude bin
            if jj == (ntb - 2):
                number_obs[ii, jj] = np.sum(mtmp >= np.sum(mbin[jj]))
            else:
                number_obs[ii, jj] = np.sum(np.logical_and(mtmp >= mbin[jj],
                                           mtmp < mbin[jj + 1]))
            jj = jj + 1
        ii = ii + 1

    time_diff = (np.log10(t_rate[1:]) - np.log10(t_rate[:-1]))
    time_diff = time_diff / (
        np.log10(time_range[1:]) - np.log10(time_range[:-1]))
    comp_length = np.zeros((ntb - 1, 1))
    tloc = np.zeros((ntb - 1, 1), dtype=int)
    ii = 0
    while ii < (ntb - 1):
        lamda[:, ii] = number_obs[:, ii] / time_range
        siglam[:, ii] = np.sqrt(lamda[:, ii] / time_range)
        zero_find = siglam[:, ii] < 1E-14   # To avoid divide by zero
        siglam[zero_find, ii] = 1E-14
        grad1 = (np.log10(siglam[1:, ii]) - np.log10(siglam[:-1, ii]))
        grad1 = grad1 / (np.log10(time_range[1:]) - np.log10(time_range[:-1]))
        resid1 = grad1 - time_diff
        test1 = np.abs(resid1[1:] - resid1[:-1])
        tloct = np.nonzero(test1 > ttol)[0]
        if not(np.any(tloct)):
            tloct = -1
        else:
            tloct = tloct[-1]
        if tloct < 0:
            # No location passes test
            if ii > 0:
                # Use previous value
                tloc[ii] = tloc[ii - 1]
            else:
                # Print warning
                LOGGER.critical(
                    "Fitting tolerance removed all data - change parameter")
        else:
            tloc[ii] = tloct
        if tloct > np.max(np.shape(time_range)):
            tloc[ii] = np.max(np.shape(time_range))

        if ii > 0:
            # If the increasing completeness is option is set
            # and the completeness is lower than the previous value
            # then fix at previous value
            inc_check = np.logical_and(iloc, (tloc[ii] < tloc[ii - 1]))
            if inc_check:
                tloc[ii] = tloc[ii - 1]
        comp_length[ii] = time_range[tloc[ii]]

        ii = ii + 1

    completeness_table = np.column_stack(
        [end_time - comp_length, mbin[:-1].T])

    return completeness_table


def selected_eq_flag_vector(year, mw, cyear, cmw, flag_vector):
    """
    Creates a vector representing selected earthquakes events
    after declustering and completeness jobs

    :param year: catalog matrix year column
    :type year: numpy.ndarray
    :param mw: catalog matrix magnitude column
    :type mw: numpy.ndarray
    :param cyear: completeness table year column
    :type cyear: numpy.ndarray
    :param cmw: completeness table magnitude column
    :type cmw: numpy.ndarray
    :param flag_vector:
    :type flag_vector: numpy.ndarray
    :returns: selected_eq_vector representing the selected
              events after preprocessing jobs (declustering,
              completeness)
    :rtype: numpy.ndarray

    """

    neq = np.shape(year)[0]
    ncat = np.shape(cyear)[0]  # Number of magnitude-time categories
    temp_flag = np.zeros(neq, dtype=int)
    i = 0
    while i < ncat:
        id0 = np.logical_and(year < cyear[i], mw < cmw[i])
        temp_flag[id0] = 1
        i += 1

    # Flag vector is input for the catalogue and has the same
    # length as the catalogue - merge the two

    selected_flag_vector = np.zeros(neq, dtype=int)
    id0 = np.logical_or(temp_flag != 0, flag_vector != 0)
    selected_flag_vector[id0] = 1

    return selected_flag_vector
