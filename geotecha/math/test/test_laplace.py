# geotecha - A software suite for geotechncial engineering
# Copyright (C) 2013  Rohan T. Walker (rtrwalker@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/gpl.html.
"""Some test routines for the laplace module

"""
from __future__ import division, print_function

from nose import with_setup
from nose.tools.trivial import assert_almost_equal
from nose.tools.trivial import assert_raises
from nose.tools.trivial import ok_
from numpy.testing import assert_allclose

import numpy as np
import textwrap
import matplotlib.pyplot as plt

from geotecha.math.laplace import Talbot

def f1(s):
    "L-1{1/(1+s)} = e^(-t)"
    return 1/(1+s)

def f2(s,a):
    "L-1{1/(1+s+a)} = e^(-(a+1)*t)"
    return 1/(1+s+a)

def f3(s):
    "L-1{1/(s-1)} = e^t"
    return 1/(s-1)

def f4(s, a):
    "L-1{2*a*s/(s**2+a**2)**2} = t*sin(a*t)"
    return 2*a*s/(s**2+a**2)**2

def  test_talbot():
    """test for Talbot numerical inverse Laplace"""

    a = Talbot(f=f1, n=24, shift=0.0)
    #t=0 raise error:
    assert_raises(ValueError, a, 0)
    #single value of t:
    assert_allclose(a(1), np.exp(-1))
    #two values of t:
    assert_allclose(a([1,2]), np.exp(np.array([-1,-2])))
    #args
    b = Talbot(f=f2, n=24, shift=0.0)
    assert_allclose(b(1, args=(1,)), np.exp(-2))
    #shift
    c = Talbot(f=f3, n=24, shift=1.0)
    assert_allclose(c(1), np.exp(1))

    d = Talbot(f=f4, n=24, shift=0.0)
    assert_allclose(c(1), np.exp(1))




if __name__ == '__main__':

    import nose
    nose.runmodule(argv=['nose', '--verbosity=3', '--with-doctest'])
#    nose.runmodule(argv=['nose', '--verbosity=3'])