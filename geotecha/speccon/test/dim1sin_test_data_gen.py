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
"""quick and dirty code to generate some results for testing against 
geotecha.speccon.integrals.dim1sin... type funcitons

generally tests by:
- 2 layers const within a layer
  - prop = 1 between [0,0.4] and prop = 2 between [0.4, 1].
- 1 layer linear within layer
  - prop varies from 1 to 2 on [0, 1].  This gives the simpole eqation 
  prop = 1 + x
  

"""

from __future__ import division, print_function

from math import pi

import sympy
from sympy import cos
from sympy import sin

import numpy



    

#This is bad form to use global variables, but it works
PTIB = [pi/2, 3*pi/2]
PTPB = [pi, 2 * pi]
MS = ['PTIB', 'PTPB']

A1 = 1
A2 = 2

def a_linear(x):
    """linear distribution where [xt, yt] = [0,1], [xb, yb] = [1,0]"""
    return 1 + x
    
def a_const(x):
    """unit"""
    return 1
    

def two_dim(f, f2 = None, xc = 0.4, x = sympy.Symbol('x')):
    """
    Evaluate string `f` then integrate between 0 and 1
    
    Populate a 2x2 matrix with the definite integral of `f` between 
    [0, 1] (or `f` between [0, `xc`] + `f2` between [`xc`, 1]).  Requires 
    MS = ['PTIB', 'PTPB'], and PTIB and PTPB global variables.  Integrals 
    at each element depend on values in PTIB and PTPB.
    
    As `f` and `f2` will be useed with eval(), all variables in the string 
    must be defined elsewhere except mi and mj which will be defined at each
    matrix element location.
                
    Parameters
    ----------
    f : ``str``
        string to be evaluated and then integrated between [0,1] (or [0, `xc`] 
        if f2 is not None)
    f2: ``str``, optional
        string to be evaluated and then integrated between [`xc`, 1] (default 
        is none, i.e. this will not contribute)
    xc: [0, 1], optional
        break point on the left of which `f` will be integrated and on the
        right of which `f2` will be integrated. (default = 0.4)
    `x`: sympy.Symbol
        integrateion varibale default = sympy.Symbol('x')
            
    Examples
    --------
    TODO
        
    """
    #global A1
    #global A2    
    for drainage in MS:
        A = [[0, 0], [0, 0]]
        for i, mi in enumerate(eval(drainage)):
            for j, mj in enumerate(eval(drainage)):
                if f2:
                    
                    A[i][j] = sympy.N(sympy.integrate(eval(f), (x, 0, xc)) + sympy.integrate(eval(f2), (x, xc, 1.0)), 8)
                else:
                    A[i][j] = sympy.N(sympy.integrate(eval(f), (x, 0, 1)), 8)                    
        print(drainage)
        print('np.array(' + str(A) + ')')

def one_dim(f, f2 = None, xc = 0.4, x = sympy.Symbol('x')):
    """
    Evaluate string `f` then integrate between 0 and 1.
    
    Populate a 1x2 matrix with the definite integral of `f` between 
    [0, 1] (or `f` between [0, `xc`] + `f2` between [`xc`, 1]).  Requires 
    MS = ['PTIB', 'PTPB'], and PTIB and PTPB global variables.  Integrals 
    at each element depend on values in PTIB and PTPB.
    
    As `f` and `f2` will be useed with eval(), all variables in the string 
    must be defined elsewhere except mi which will be defined at each
    matrix element location.
                
    Parameters
    ----------
    f : ``str``
        string to be evaluated and then integrated between [0,1] (or [0, `xc`] 
        if f2 is not None)
    f2: ``str``, optional
        string to be evaluated and then integrated between [`xc`, 1] (default 
        is none, i.e. this will not contribute)
    xc: [0, 1], optional
        break point on the left of which `f` will be integrated and on the
        right of which `f2` will be integrated. (default = 0.4)
    `x`: sympy.Symbol
        integrateion varibale default = sympy.Symbol('x')
    
    Examples
    --------
    TODO   
    
    """
    #global A1
    #global A2    
    for drainage in MS:
        A = [0, 0]
        for i, mj in enumerate(eval(drainage)):
            if f2:                    
                A[i] = sympy.N(sympy.integrate(eval(f), (x, 0, xc)) + sympy.integrate(eval(f2), (x, xc, 1.0)), 8)
            else:
                A[i] = sympy.N(sympy.integrate(eval(f), (x, 0, 1)), 8)                    
        print(drainage)
        print('np.array(' + str(A) + ')')
        
def run_cases(title, cases, fn):
    """run a bunch of cases through fn
    
    - prints title    
    - runs and prints out each case 
    Parameters
    ----------
    title: ``str``
        overall title to print out
    cases: ``list`` of ``list``
        list of cases e.g. [['case_name', ['arg1', 'arg2']]]
    fn: function
        function to be called with args from cases
    
    """
    
    print(title)
    for case, args in cases:
        print (case)
        fn(*args)

def dim1sin_abf_linear():
    """print some test case data for geotecha.speccon.integrals.dim1sin_abf_linear
    
    See Also
    --------
    geotecha.speccon.integrals.dim1sin_abf_linear : full implementation of 
    the function
    geotecha.speccon.test.test_integrals.test_dim1sin_abf_linear : data is 
    used in testing
    
    """
    cases = [
        ['a and b const', 
            ['sin(mi*x)*a_const(x)*a_const(x)*sin(mj*x)']],
        ['a const in two layers, b const', 
            ['sin(mi*x)*A1*a_const(x)*sin(mj*x)','sin(mi*x)*A2*a_const(x)*sin(mj*x)']],
        ['a linear in one layer, b const', 
            ['sin(mi*x)*a_linear(x)*a_const(x)*sin(mj*x)']],
        ['a linear in one layer, b linear in one layer', 
            ['sin(mi*x)*a_linear(x)*a_linear(x)*sin(mj*x)']],
        ]
    run_cases('dim1sin_abf_linear', cases, two_dim)

def dim1sin_af_linear():
    """print some test case data for geotecha.speccon.integrals.dim1sin_af_linear
    
    See Also
    --------
    geotecha.speccon.integrals.dim1sin_af_linear : full implementation of 
    the function
    geotecha.speccon.test.test_integrals.test_dim1sin_af_linear : data is 
    used in testing
    
    """
    cases = [
        ['a const', 
            ['sin(mi*x)*a_const(x)*sin(mj*x)']],
        ['a const in two layers', 
            ['sin(mi*x)*A1*sin(mj*x)','sin(mi*x)*A2*sin(mj*x)']],
        ['a linear in one layer', 
            ['sin(mi*x)*a_linear(x)*sin(mj*x)']],
        ]
    run_cases('dim1sin_abf_linear', cases, two_dim)

        
def main():
    """ run all the test data generations"""
    
    dim1sin_af_linear()
    #dim1sin_abf_linear()


if __name__ == '__main__':
    main()        