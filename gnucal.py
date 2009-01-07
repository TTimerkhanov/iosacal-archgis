#! /usr/bin/env python
# -*- coding: utf-8 -*-
# filename: gnucal.py
# Copyright 2008 Stefano Costa <steko@iosa.it>
# 
# This file is part of GNUCal.

# GNUCal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# GNUCal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with GNUCal.  If not, see <http://www.gnu.org/licenses/>.


import sys
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

from csv import reader
from math import pow, exp, sqrt
from numpy import array, asarray, sort
from optparse import OptionParser, OptionGroup
from pylab import normpdf

from hpd import alsuren_hpd, prev_next


## OptionParser

usage = "usage: %prog [option] arg1 [option] arg2 ..."

parser = OptionParser(usage = usage)
parser.add_option("-d",
                "--date",
                action="store",
                type="int",
                dest="date",
                help="non calibrated radiocarbon BP date for sample",
                metavar="DATE")
parser.add_option("-s",
                "--sigma",
                action="store",
                type="int",
                dest="sigma",
                help="standard deviation for date",
                metavar="SIGMA")
group = OptionGroup(parser, 'BP or BC/AD output',
                    'Use these two mutually exclusive options to choose which '
                    'type of dates you like as output.')
parser.set_defaults(BP=True)
group.add_option("--bp",
                action="store_true",
                dest="BP",
                help="express date in Calibrated BP Age (default action)")
group.add_option("--ad",
                action="store_false",
                dest="BP",
                help="express date in Calibrated BC/AD Calendar Age")
parser.add_option_group(group)

(options, args) = parser.parse_args()
if not (options.date and options.sigma):
    sys.exit('Please provide date and standard deviation')


## GNUCal itself

intcal04 = open('intcal04.14c') # Atmospheric data from Reimer et al (2004);
intlines = intcal04.readlines()
intnotcomment = [ l for l in intlines if not '#' in l]
intcal04 = reader(intnotcomment, skipinitialspace = True)
intarray = array(list(intcal04)).astype('d') # calibration curve values are floats


def calibrate(f_m, sigma_m, f_t, sigma_t):
    '''Formula as defined by Bronk Ramsey 2008 doi: 10.1111/j.1475-4754.2008.00394.x'''
    sigma_sum = pow(sigma_m, 2) + pow(sigma_t, 2)
    P_t = ( exp( - pow(f_m - f_t, 2 ) / ( 2 * ( sigma_sum ) ) ) / sqrt(sigma_sum) )
    return P_t

f_m, sigma_m = options.date, options.sigma

calibrated_list = []
for i in intarray:
    f_t, sigma_t = i[1:3]
    ca = calibrate(f_m, sigma_m, f_t, sigma_t)
    # FIXME this treshold value is completely arbitrary
    if ca > 0.000000001:
        calibrated_list.append((i[0],ca))
calibrated_curve = asarray(calibrated_list)
print calibrated_curve[:,1].max() / 0.00000001

# Normal (Gaussian) curve, used only for plotting!
sample_curve = normpdf(intarray[:,0], f_m, sigma_m)

# Confidence intervals
intervals68 = alsuren_hpd(calibrated_curve,0.318)
intervals95 = alsuren_hpd(calibrated_curve,0.046)
#print prev_next(15000.0, intarray)

## Plots

ax1 = plt.subplot(111)
plt.title("Radiocarbon Age vs Calibrated Age")
plt.xlabel("Calibrated date (BP)")
plt.ylabel("Radiocarbon determination (BP)")
plt.text(0.5, 0.95,r'$STEKO: %d \pm %d BP$' % (f_m, sigma_m),
     horizontalalignment='center',
     verticalalignment='center',
     transform = ax1.transAxes,
     bbox=dict(facecolor='white', alpha=0.9, edgecolor=None))
plt.text(0.95, 0.90,'68.2%% probability\n%s' % str(intervals68),
     horizontalalignment='center',
     verticalalignment='center',
     transform = ax1.transAxes,
     bbox=dict(facecolor='white', alpha=0.9, edgecolor=None))
plt.text(0.0, 1.0,'GNUCal 0.1; IntCal04 atmospheric curve (Reimer et al. 2004)',
     horizontalalignment='left',
     verticalalignment='center',
     transform = ax1.transAxes,
     size=7,
     bbox=dict(facecolor='white', alpha=0.9, lw=0))


# Calendar Age

ax2 = plt.twinx()
ax2.fill(
    calibrated_curve[:,0],
    calibrated_curve[:,1],
    'k',
    alpha=0.3,
    label='Calendar Age'
    )
ax2.plot(
    calibrated_curve[:,0],
    calibrated_curve[:,1],
    'k',
    alpha=0
    )
ax2.set_ybound(min(calibrated_curve[:,1]),max(calibrated_curve[:,1])*3)
ax2.set_axis_off()

# Radiocarbon Age

ax3 = plt.twiny(ax1)
ax3.fill(
    sample_curve,
    intarray[:,0],
    'r',
    alpha=0.3
    )
ax3.plot(
    sample_curve,
    intarray[:,0],
    'r',
    alpha=0.3,
    label='Radiocarbon determination (BP)'
    )
ax3.set_xbound(min(sample_curve),max(sample_curve)*3)
ax3.set_axis_off()

# Calibration Curve

mlab_low  = [ n[1] - n[2] for n in intarray ]
mlab_high = [ n[1] + n[2] for n in intarray ]

xs, ys = mlab.poly_between(intarray[:,0],
                           mlab_low,
                           mlab_high)
ax1.fill(xs, ys, 'b', alpha=0.3)

# Confidence intervals

for i in intervals95:
    ax1.axvspan(min(i), max(i), ymin=0, ymax=0.02, facecolor='k', alpha=0.5)
for i in intervals68:
    ax1.axvspan(min(i), max(i), ymin=0, ymax=0.02, facecolor='k', alpha=0.8)

plt.savefig('image_%d±%d.png' %(f_m, sigma_m))

