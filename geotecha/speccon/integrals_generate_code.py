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
"""use sympy to generate code for generating spectral method matrix subroutines"""

from __future__ import division, print_function

import sympy


def linear(x, x1, y1, x2, y2):
    """Interpolation between two points.

    """
    return (y2 - y1)/(x2 - x1) * (x-x1) + y1

def string_to_IndexedBase(s):
    """turn string into sympy.tensor.IndexedBase

    """
    
    return sympy.tensor.IndexedBase(s)
        
def create_layer_sympy_var_and_maps(layer_prop=['z','kv','kh','et', 'mv',
                                                'surz', 'vacz']):
    """Create sympy variables and maps for use with integrating \
    to generate 1d spectral equations.
    
    Each x in layer prop will get a 'top', and 'bot', suffix
    Each 'xtop' will get mapped to 'xt[layer]', each 'xbot' to 'xb[layer] 
    and added to `prop_map` dict.
    Each s in layer prop will get a linear representation added to the 
    `linear_expression` dict:
        x = (xbot-xtop)/(zbot-ztop)*(z-zbot) +xtop
    `prop_map` will also get a 'mi' to m[i], and mj to m[j] map.
    'z, mi, mj' will become global variables
            
    Parameters
    ----------
    layer_prop : ``list`` of ``str``, optional
        label for properties that vary in a layer
        (default is ['z','kv','kh','et', 'mv', 'surz',' vacz'])
    
         
    Returns
    -------
    prop_map : ``dict``
        maps the string version of a variable to the sympy.tensor.IndexedBase 
        version e.g. prop_map['kvtop'] = kvt[layer]
    linear_expressions : ``dict``
        maps the string version of a variable to an expression describing how 
        that varibale varies linearly within a layer    
        
    Examples
    --------
    >>> prop_map, linear_expressions = create_layer_sympy_var_and_maps(layer_prop=['z','kv'])
    >>> prop_map
    {'kvtop': kvt[layer], 'mi': m[i], 'mj': m[j], 'zbot': zb[layer], 'ztop': zt[layer], 'kvbot': kvb[layer]}
    >>> linear_expressions
    {'z': z, 'kv': kvtop + (kvbot - kvtop)*(z - ztop)/(zbot - ztop)}

    """
    #http://www.daniweb.com/software-development/python/threads/111526/setting-a-string-as-a-variable-name    
    m = sympy.tensor.IndexedBase('m')
    i = sympy.tensor.Idx('i')
    j = sympy.tensor.Idx('j')
    layer = sympy.tensor.Idx('layer')
    
    sympy.var('z, mi, mj')
    suffix={'t':'top','b': 'bot'}        
    prop_map = {}
    linear_expressions ={}
    
    prop_map['mi'] = m[i]
    prop_map['mj'] = m[j]
    
    for prop in layer_prop:            
        for s1, s3 in suffix.iteritems():
            vars()[prop + s1] = string_to_IndexedBase(prop + s1)            
            sympy.var(prop + s3)                        
            prop_map[prop + s3] = vars()[prop + s1][layer]        
        linear_expressions[prop]=linear(z, ztop, eval(prop+suffix['t']), zbot, eval(prop+suffix['b']))
    return (prop_map, linear_expressions)
    
def dim1sin_af_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * a(z) * sin(mj * z)` between [0, 1]
    where a(z) is a piecewise linear function of z.  Code is generated that
    will produce a square array with the appropriate integrals at each location
    
    Paste the resulting code (at least the loops) into `dim1sin_af_linear`.
    
    Notes
    -----
    The `dim1sin_af_linear` matrix, :math:`A` is given by:    
        
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{{a\\left(z\\right)}\\phi_i\\phi_j\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:
        
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)` is a piecewise linear function
    w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
    
    """
    
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z','a'])
    
    phi_i = sympy.sin(mi * z)
    phi_j = sympy.sin(mj * z)    
    
    fdiag = sympy.integrate(p['a'] * phi_i * phi_i, z)    
    fdiag = fdiag.subs(z, mp['zbot']) - fdiag.subs(z, mp['ztop'])
    fdiag = fdiag.subs(mp)
    
    foff = sympy.integrate(p['a'] * phi_j * phi_i, z)  
    foff = foff.subs(z, mp['zbot']) - foff.subs(z, mp['ztop'])
    foff = foff.subs(mp)
    
    text = """def dim1sin_af_linear(m, at, ab, zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros([neig, neig], float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i, i] += %s
        for i in range(neig-1):
            for j in range(i + 1, neig):
                A[i, j] += %s                
                
    #A is symmetric
    for i in range(neig - 1):        
        for j in range(i + 1, neig):
            A[j, i] = A[i, j]                
    
    return A"""
    
        
    fn = text % (fdiag, foff)
        
    return fn

def dim1sin_abf_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * a(z) *b(z) * sin(mj * z)` 
    between [0, 1] where a(z) and b(z) are piecewise linear functions of z.  
    Code is generated that will produce a square array with the appropriate 
    integrals at each location
    
    Paste the resulting code (at least the loops) into `dim1sin_abf_linear`.
    
    Notes
    -----
    The `dim1sin_abf_linear` matrix, :math:`A` is given by:
        
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{{a\\left(z\\right)}{b\\left(z\\right)}\\phi_i\\phi_j\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:    
    
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)` and :math:`b\\left(z\\right)` are piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
    
    """    
        
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z','a', 'b'])
    
    phi_i = sympy.sin(mi * z)
    phi_j = sympy.sin(mj * z)    
    
    fdiag = sympy.integrate(p['a'] * p['b'] * phi_i * phi_i, z)    
    fdiag = fdiag.subs(z, mp['zbot']) - fdiag.subs(z, mp['ztop'])
    fdiag = fdiag.subs(mp)
    
    foff = sympy.integrate(p['a'] * p['b'] * phi_j * phi_i, z)  
    foff = foff.subs(z, mp['zbot']) - foff.subs(z, mp['ztop'])
    foff = foff.subs(mp)
    
    text = """def dim1sin_abf_linear(m, at, ab, bt, bb,  zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros([neig, neig], float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i, i] += %s
        for i in range(neig-1):
            for j in range(i + 1, neig):
                A[i, j] += %s                
                
    #A is symmetric
    for i in range(neig - 1):        
        for j in range(i + 1, neig):
            A[j, i] = A[i, j]                
    
    return A"""
    
        
    fn = text % (fdiag, foff)
        
    return fn

def dim1sin_D_aDf_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * D[a(z) * D[sin(mj * z),z],z]` 
    between [0, 1] where a(z) i piecewise linear functions of z.  
    Code is generated that will produce a square array with the appropriate 
    integrals at each location
    
    Paste the resulting code (at least the loops) into `dim1sin_D_aDf_linear`.
    
    Notes
    -----    
    The `dim1sin_D_aDf_linear` matrix, :math:`A` is given by:
    
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{\\frac{d}{dz}\\left({a\\left(z\\right)}\\frac{d\\phi_j}{dz}\\right)\\phi_i\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:    
    
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)` and :math:`b\\left(z\\right)` are piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
    
    The integration requires some explanation.  The difficultly arises because 
    piecewise linear :math:`a\\left(z\\right)` is defined using step functions at 
    the top and bottom of each layer; those step functions when differentiated 
    yield dirac-delta or impulse functions which must be handled specially 
    when integrating against the spectral basis functions.  The graph below
    shows what happens when the :math:`a\\left(z\\right) distribution is 
    differentiated for one layer.
    
    ::
        
        y(x)
        ^
        |                                                                        
        |                            yb                                            
        |                          /|                                              
        |                         / |                                              
        |                        /  |                                              
        |                       /   |                                           
        |                      /    |                                              
        |                   yt|     |                                              
        |                     |     |                                              
        0--------------------xt----xb------------------------1------>x
        
    Differentiate:
    
    ::
        
        y'(x)
        ^
        |                                                                        
        |                     y(xt) * Dirac(x - xt)                                                   
        |                     ^                                                   
        |                     |                                                   
        |                     |     |                                              
        |                     |     |                                           
        |               y'(xt)|-----|                                              
        |                     |     |                                              
        |                     |     v - y(xb) * Dirac(x - xb)                                                                                                
        0--------------------xt----xb------------------------1------>x
    
    With sympy/sage I've found it easier to perform the indefinite integrals 
    first  and then sub in the bounds of integration. That is, the integral 
    of f between a and b is F(b)-F(a) where F is the anti-derivative of f.
    
    
    The general expression for :math:`{A}` is:
    
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{\\frac{d}{dz}\\left({a\\left(z\\right)}\\frac{d\\phi_j}{dz}\\right)\\phi_i\\,dz}
        :label: full
        
    Expanding out the integrals in :eq:`full` yields:
        
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{{a\\left(z\\right)}\\frac{d^2\\phi_j}{dZ^2}\\phi_i\\,dZ}+\\int_{0}^1{\\frac{d{a\\left(z\\right)}}{dZ}\\frac{d\\phi_j}{dZ}\\phi_i\\,dZ}
    
    Considering a single layer and separating the layer boundaries from the behaviour within a layer gives:
        
    .. math:: \\mathbf{A}_{i,j,\\text{layer}}=\\int_{z_t}^{z_b}{{a\\left(z\\right)}\\frac{d^2\\phi_j}{dz^2}\\phi_i\\,dZ}+\\int_{z_t}^{z_b}{\\frac{d{a\\left(z\\right)}}{dz}\\frac{d\\phi_j}{dz}\\phi_i\\,dz}+\\int_{0}^{1}{{a\\left(z\\right)}\\delta\\left(z-z_t\\right)\\frac{d\\phi_j}{dz}\\phi_i\\,dz}-\\int_{0}^{1}{{a\\left(z\\right)}\\delta\\left(z-z_b\\right)\\frac{d\\phi_j}{dz}\\phi_i\\,dz}
    
    Performing the dirac delta integrations:
        
    .. math:: \\mathbf{A}_{i,j,\\text{layer}}=\\int_{z_t}^{z_b}{{a\\left(z\\right)}\\frac{d^2\\phi_j}{dz^2}\\phi_i\\,dZ}+\\int_{z_t}^{z_b}{\\frac{d{a\\left(z\\right)}}{dz}\\frac{d\\phi_j}{dz}\\phi_i\\,dz}+\\left.{a\\left(z\\right)}\\frac{d\\phi_j}{dz}\\phi_i\\right|_{z=z_t}-\\left.{a\\left(z\\right)}\\frac{d\\phi_j}{dz}\\phi_i\\right|_{z=z_b}
    
    Now, to get it in the form of F(zb)-F(zt) we only take the zb part of the dirac integration:
        
    .. math:: F\\left(z\\right)=\\int{{a\\left(z\\right)}\\frac{d^2\\phi_j}{dz^2}\\phi_i\\,dZ}+\\int{\\frac{d{a\\left(z\\right)}}{dz}\\frac{d\\phi_j}{dz}\\phi_i\\,dz}-\\left.{a\\left(z\\right)}\\frac{d\\phi_j}{dz}\\phi_i\\right|_{z=z}
    
    Finally we get:
        
    .. math:: \\mathbf{A}_{i,j,\\text{layer}}=F\\left(z_b\\right)-F\\left(z_t\\right)
    
    TODO: explain why dirac integrations disapera at end points because in this case it will always be sin(mx)*cos(mx) and so always be zero.
    
    """
            
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z','a'])
    
    phi_i = sympy.sin(mi * z)
    phi_j = sympy.sin(mj * z)    
    
    fdiag = (sympy.integrate(p['a'] * sympy.diff(phi_i, z, 2) * phi_i, z))
    fdiag += (sympy.integrate(sympy.diff(p['a'], z) * sympy.diff(phi_i, z) * phi_i,z))
    fdiag -= (p['a'] * sympy.diff(phi_i, z) * phi_i)         
        # note the 'negative' for the diff (a) part is because the step fn 
        #at the top and bottom of the layer yields a dirac function that is 
        #positive at ztop and negative at zbot. It works because definite 
        #integral of f between ztop and zbot is F(ztop)- F(zbot). 
        #i.e. I've created the indefininte integral such that when i sub 
        #in ztop and zbot in the next step i get the correct contribution 
        #for the step functions at ztop and zbot            
    fdiag = fdiag.subs(z, mp['zbot']) - fdiag.subs(z, mp['ztop'])
    fdiag = fdiag.subs(mp)
        
    foff = (sympy.integrate(p['a'] * sympy.diff(phi_j, z, 2) * phi_i, z))
    foff += (sympy.integrate(sympy.diff(p['a'], z) * sympy.diff(phi_j, z) * phi_i,z))
    foff -= (p['a'] * sympy.diff(phi_j, z) * phi_i)                 
    foff = foff.subs(z, mp['zbot']) - foff.subs(z, mp['ztop'])
    foff = foff.subs(mp)
    
    text = """def dim1sin_D_aDf_linear(m, at, ab, zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros([neig, neig], float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i, i] += %s
        for i in range(neig-1):
            for j in range(i + 1, neig):
                A[i, j] += %s                
                
    #A is symmetric
    for i in range(neig - 1):        
        for j in range(i + 1, neig):
            A[j, i] = A[i, j]                
    
    return A"""
    
        
    fn = text % (fdiag, foff)
        
    return fn


def dim1sin_ab_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * a(z) * b(z)` 
    between [0, 1] where a(z) and b(z) are piecewise linear functions of z.  
    Code is generated that will produce a 1d array with the appropriate 
    integrals at each location.
    
    Paste the resulting code (at least the loops) into `dim1sin_ab_linear`.
    
    Notes
    -----    
    The `dim1sin_ab_linear` which should be treated as a column vector, 
    :math:`A` is given by:    
        
    .. math:: \\mathbf{A}_{i}=\\int_{0}^1{{a\\left(z\\right)}{b\\left(z\\right)}\\phi_i\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:    
    
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)` and :math:`b\\left(z\\right)` are piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
        
    """
           
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z', 'a', 'b'])
    
    phi_i = sympy.sin(mi * z)
    
    fcol = sympy.integrate(p['a'] * p['b'] * phi_i, z)        
    fcol = fcol.subs(z, mp['zbot']) - fcol.subs(z, mp['ztop'])
    fcol = fcol.subs(mp)
    
    text = """def dim1sin_ab_linear(m, at, ab, bt, bb, zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros(neig, float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i] += %s
    
    return A"""
    
        
    fn = text % fcol
    return fn

def dim1sin_abc_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * a(z) * b(z) * c(z)` 
    between [0, 1] where a(z), b(z), c(z) are piecewise linear functions of z.  
    Code is generated that will produce a 1d array with the appropriate 
    integrals at each location.
    
    Paste the resulting code (at least the loops) into `dim1sin_ab_linear`.
    
    Notes
    -----    
    The `dim1sin_ab_linear` which should be treated as a column vector, 
    :math:`A` is given by:    
        
    .. math:: \\mathbf{A}_{i}=\\int_{0}^1{{a\\left(z\\right)}{b\\left(z\\right)}{c\\left(z\\right)}\\phi_i\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:    
    
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)`, :math:`b\\left(z\\right)`, and 
    :math:`c\\left(z\\right)` are piecewise linear functions 
    w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
        
    """
           
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z', 'a', 'b', 'c'])
    
    phi_i = sympy.sin(mi * z)
    
    fcol = sympy.integrate(p['a'] * p['b'] * p['c'] * phi_i, z)        
    fcol = fcol.subs(z, mp['zbot']) - fcol.subs(z, mp['ztop'])
    fcol = fcol.subs(mp)
    
    text = """def dim1sin_abc_linear(m, at, ab, bt, bb, ct, cb, zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros(neig, float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i] += %s
    
    return A"""
    
        
    fn = text % fcol
    return fn

def dim1sin_D_aDb_linear():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * D[a(z) * D[b(z), z], z]` 
    between [0, 1] where a(z) and b(z) are piecewise linear functions of z.  
    Code is generated that will produce a 1d array with the appropriate 
    integrals at each location.
    
    Paste the resulting code (at least the loops) into `dim1sin_ab_linear`.
    
    Notes
    -----    
    The `dim1sin_D_aDb_linear` which should be treated as a column vector, 
    :math:`A` is given by:    
        
    .. math:: \\mathbf{A}_{i,j}=\\int_{0}^1{\\frac{d}{dz}\\left({a\\left(z\\right)}\\frac{d}{dz}{b\\left(z\\right)}\\right)\\phi_i\\,dz}
    
    where the basis function :math:`\\phi_i` is given by:    
    
    ..math:: \\phi_i\\left(z\\right)=\\sin\\left({m_i}z\\right)
    
    and :math:`a\\left(z\\right)` and :math:`b\\left(z\\right)` are piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
    
    TODO: explain why the dirac integrations at 0 and 1 must be omitted i.e. not for all cases do they not contribute only.    
    
    """
           
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z', 'a', 'b'])
    
    phi_i = sympy.sin(mi * z)
    
    fcol = sympy.integrate(sympy.diff(p['a'],z) * sympy.diff(p['b'],z) * phi_i, z)
    fcol -= p['a']*sympy.diff(p['b'], z) * phi_i        
    fcol = fcol.subs(z, mp['zbot']) - fcol.subs(z, mp['ztop'])
    fcol = fcol.subs(mp)
    
    
    layer = sympy.tensor.Idx('layer')
    
    ffirst = -p['a']*sympy.diff(p['b'], z) * phi_i
    ffirst = ffirst.subs(z, mp['ztop'])
    ffirst = ffirst.subs(mp)
    ffirst = ffirst.subs(layer, 0)
    
    flast = p['a']*sympy.diff(p['b'], z) * phi_i
    flast = flast.subs(z, mp['zbot'])
    flast = flast.subs(mp)
    flast = flast.subs(layer, -1)
        
    text = """def dim1sin_D_aDb_linear(m, at, ab, bt, bb, zt, zb):
    import numpy as np
    from math import sin, cos
    
    neig = len(m)
    nlayers = len(zt)
    
    A = np.zeros(neig, float)        
    for layer in range(nlayers):
        for i in range(neig):
            A[i] += %s
    
    for i in range(neig):
        A[i] += %s + %s
    
    return A"""
    
        
    fn = text % (fcol, ffirst, flast)
    return fn



def EDload_linear():
    """Generate code to perform time integration for spectral methods
    
    Perform time integrations of a piecewise linear load vs time
    
    
    Notes
    -----
    the default output for the integrals will have expression s like 
    exp(-dT*eig*t)*exp(dT*eig*loadtim[k]).  when dT*eig*loadtim[k] is large 
    the exponential may be so large as to cause an error.  YOu may need to 
    manually alter the expression to exp(is large exp(-dT*eig*(t-loadtim[k])) 
    in which case the term in the exponential will always be negative and not 
    lead to any numerical blow up.
    
    """
    
    from sympy import exp
    
    sympy.var('t, tau, dT, eig')    
    loadmag = sympy.tensor.IndexedBase('loadmag')
    loadtim = sympy.tensor.IndexedBase('loadtim')
    tvals = sympy.tensor.IndexedBase('tvals')
    eigs = sympy.tensor.IndexedBase('eigs')
    i = sympy.tensor.Idx('i')
    j = sympy.tensor.Idx('j')
    k = sympy.tensor.Idx('k')    
    
    mp = [(exp(-dT*eig*t)*exp(dT*eig*loadtim[k]),exp(-dT*eig*(t-loadtim[k]))),(exp(-dT*eig*t)*exp(dT*eig*loadtim[k+1]),exp(-dT*eig*(t-loadtim[k+1])))]
#    the default output for the integrals will have expression s like 
#    exp(-dT*eig*t)*exp(dT*eig*loadtim[k]).  when dT*eig*loadtim[k] is large 
#    the exponential may be so large as to cause an error.  YOu may need to 
#    manually alter the expression to exp(is large exp(-dT*eig*(t-loadtim[k])) 
#    in which case the term in the exponential will always be negative and not 
#    lead to any numerical blow up.
#    load = linear(tau, loadtim[k], loadmag[k], loadtim[k+1], loadmag[k+1])    
#    after_instant = (loadmag[k+1] - loadmag[k]) * exp(-dT * eig * (t - loadtim[k]))
#    mp does this automatically with subs
    
    Dload = sympy.diff(linear(tau, loadtim[k], loadmag[k], loadtim[k+1], loadmag[k+1]), tau)
    after_instant = (loadmag[k+1] - loadmag[k]) * exp(-dT * eig * (t - loadtim[k]))

    within_ramp = Dload * exp(-dT * eig * (t - tau))
    within_ramp = sympy.integrate(within_ramp, (tau, loadtim[k], t))
    within_ramp = within_ramp.subs(mp)
    
    after_ramp = Dload * exp(-dT * eig * (t - tau))          
    after_ramp = sympy.integrate(after_ramp, (tau, loadtim[k], loadtim[k+1]))
    after_ramp = after_ramp.subs(mp)    
    
    
    text = """def EDload_linear(loadtim, loadmag, eigs, tvals):
        
    from math import exp
    
    loadtim = np.asarray(loadtim)
    loadmag = np.asarray(loadmag)
    eigs = np.asarray(eigs)
    tvals = np.asarray(tvals)    

    (ramps_less_than_t, constants_less_than_t, steps_less_than_t, 
            ramps_containing_t, constants_containing_t) = segment_containing_also_segments_less_than_xi(loadtim, loadmag, tvals, steps_or_equal_to = True)
           
    A = np.zeros([len(tvals), len(eigs)])
    
        
    for i, t in enumerate(tvals):
        for k in after_instant_loads[i]:    
            for j, eig in enumerate(eigs):
                A[i,j] += %s 
        for k in within_ramp_loads[i]:
            for j, eig in enumerate(eigs):
                A[i,j] += %s 
        for k in after_ramp_loads[i]:
            for j, eig in enumerate(eigs):
                A[i,j] += %s
    return A"""
    
    fn = text % (after_instant, within_ramp, after_ramp)
    return fn

def Eload_linear():
    """Generate code to perform time integration for spectral methods
    
    Perform time integrations of a piecewise linear load vs time
    
    
    
    
    """
    
    from sympy import exp
    
    sympy.var('t, tau, dT, eig')    
    loadmag = sympy.tensor.IndexedBase('loadmag')
    loadtim = sympy.tensor.IndexedBase('loadtim')
    tvals = sympy.tensor.IndexedBase('tvals')
    eigs = sympy.tensor.IndexedBase('eigs')
    i = sympy.tensor.Idx('i')
    j = sympy.tensor.Idx('j')
    k = sympy.tensor.Idx('k')    
    
    mp = [(exp(-dT*eig*t)*exp(dT*eig*loadtim[k]),exp(-dT*eig*(t-loadtim[k]))),(exp(-dT*eig*t)*exp(dT*eig*loadtim[k+1]),exp(-dT*eig*(t-loadtim[k+1])))]
#    the default output for the integrals will have expression s like 
#    exp(-dT*eig*t)*exp(dT*eig*loadtim[k]).  when dT*eig*loadtim[k] is large 
#    the exponential may be so large as to cause an error.  YOu may need to 
#    manually alter the expression to exp(is large exp(-dT*eig*(t-loadtim[k])) 
#    in which case the term in the exponential will always be negative and not 
#    lead to any numerical blow up.
#    load = linear(tau, loadtim[k], loadmag[k], loadtim[k+1], loadmag[k+1])    
#    after_instant = (loadmag[k+1] - loadmag[k]) * exp(-dT * eig * (t - loadtim[k]))
#    mp does this automatically with subs

    within_constant = loadmag[k] * exp(-dT * eig * (t - tau))
    within_constant = sympy.integrate(within_constant, (tau, loadtim[k], t))
    within_constant = within_constant.subs(mp)

    after_constant = loadmag[k] * exp(-dT * eig * (t - tau))
    after_constant = sympy.integrate(after_constant, (tau, loadtim[k], loadtim[k+1]))
    after_constant = after_constant.subs(mp)
    
    within_ramp = load * exp(-dT * eig * (t - tau))
    within_ramp = sympy.integrate(within_ramp, (tau, loadtim[k], t))
    within_ramp = within_ramp.subs(mp)
    
    after_ramp = load * exp(-dT * eig * (t - tau))          
    after_ramp = sympy.integrate(after_ramp, (tau, loadtim[k], loadtim[k+1]))
    after_ramp = after_ramp.subs(mp)
    
    
    text = """def Eload_linear(loadtim, loadmag, eigs, tvals):
        
    from math import exp
    
    loadtim = np.asarray(loadtim)
    loadmag = np.asarray(loadmag)
    eigs = np.asarray(eigs)
    tvals = np.asarray(tvals)    

    (ramps_less_than_t, constants_less_than_t, steps_less_than_t, 
            ramps_containing_t, constants_containing_t) = segment_containing_also_segments_less_than_xi(loadtim, loadmag, tvals, steps_or_equal_to = True)
           
    A = np.zeros([len(tvals), len(eigs)])
    
        
    for i, t in enumerate(tvals):
        for k in within_constant_loads[i]:    
            for j, eig in enumerate(eigs):
                A[i,j] += %s
        for k in after_constant_loads[i]:    
            for j, eig in enumerate(eigs):
                A[i,j] += %s 
        for k in within_ramp_loads[i]:
            for j, eig in enumerate(eigs):
                A[i,j] += %s 
        for k in after_ramp_loads[i]:
            for j, eig in enumerate(eigs):
                A[i,j] += %s
    return A"""
    
    fn = text % (within_constant, after_constant, within_ramp, after_ramp)
    return fn
    
    
def dim1sin_a_linear_between():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `sin(mi * z) * a(z)` 
    between [z1, z2] where a(z) is a piecewise linear functions of z.  
      
    calculates array A[len(z), len(m)]
    
    Paste the resulting code (at least the loops) into `dim1sin_a_linear_between`.
    
    Notes
    -----    
    The `dim1sin_a_linear_between`, :math:`A`, is given by:    
        
    .. math:: \\mathbf{A}_{i}=\\int_{z_1}^z_2{{a\\left(z\\right)}\\phi_j\\,dz}
    
    where the basis function :math:`\\phi_j` is given by:    
    
    ..math:: \\phi_j\\left(z\\right)=\\sin\\left({m_j}z\\right)
    
    and :math:`a\\left(z\\right)` is a piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
        
    """
           
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z', 'a', 'b'])
    sympy.var('z1, z2')        
    
    z1 = sympy.tensor.IndexedBase('z1')
    z2 = sympy.tensor.IndexedBase('z2')
    i = sympy.tensor.Idx('i')
    j = sympy.tensor.Idx('j')
        
    
    
    phi_j = sympy.sin(mj * z)
    
    f = sympy.integrate(p['a'] * phi_j, z)
    
    both = f.subs(z, z2[i]) - f.subs(z, z1[i])
    both = both.subs(mp)
    
    between = f.subs(z, mp['zbot']) - f.subs(z, mp['ztop'])
    between = between.subs(mp)
    
    z1_only = f.subs(z, mp['zbot']) - f.subs(z, z1[i])
    z1_only = z1_only.subs(mp)
    
    z2_only = f.subs(z, z2[i]) - f.subs(z, mp['ztop'])
    z2_only = z2_only.subs(mp)
           
    text = """dim1sin_a_linear_between(m, at, ab, zt, zb, z):
    import numpy as np
    from math import sin, cos
    m = np.asarray(m)
    z = np.asarray(z)
    
    a = z[:,0]
    b = z[:,1]    
    
    z_for_interp=zt[:].append(zb[-1])
    
    
    (segment_both, segment_z1_only, segment_z2_only, segments_between) = segments_between_xi_and_xj(z_for_interp,a,b)
        
    nz = len(z)
    neig = len(m)        
    for i in range(nz):        
        for layer in segment_both:
            for j in range(neig):
                A[i,j] += %s
        for layer in segment_z1_only:
            for j in range(neig):
                A[i,j] += %s
        for layer in segments_between:
            for j in range(neig):
                A[i,j] += %s
        for layer in segment_z2_only:
            for j in range(neig):
                A[i,j] += %s
    return A"""
    
        
    fn = text % (both, z1_only, between, z2_only)
    
    return fn    
    
def dim1_ab_linear_between():
    """Generate code to calculate spectral method integrations
    
    Performs integrations of `a(z) * b(z)` 
    between [z1, z2] where a(z) is a piecewise linear functions of z.      
    calculates array A[len(z)]
    
    Paste the resulting code (at least the loops) into `piecewise_linear_1d.integrate_x1a_x2a_y1a_y2a_multiply_x1b_x2b_y1b_y2b_between`.
    
    Notes
    -----    
    The `dim1sin_a_linear_between`, :math:`A`, is given by:    
        
    .. math:: \\mathbf{A}_{i}=\\int_{z_1}^z_2{{a\\left(z\\right)}{b\\left(z\\right)}\\,dz}
    
    where :math:`a\\left(z\\right)` is a piecewise 
    linear functions w.r.t. :math:`z`, that within a layer are defined by:
        
    ..math:: a\\left(z\\right) = a_t+\\frac{a_b-a_t}{z_b-z_t}\\left(z-z_t\\right)
    
    with :math:`t` and :math:`b` subscripts representing 'top' and 'bottom' of 
    each layer respectively.
        
    """


#    Because this integration goes into piecewise_linear_1d rather than speccon.integrals I have had to use a separate map funciton to massage the variable names into a naming convention consistent with piecewise_linear_1d (this is m2 below).
#    As such don't base anything off this funciton unless you know what you are doing
    mp, p = create_layer_sympy_var_and_maps(layer_prop=['z', 'a', 'b'])
    sympy.var('z1, z2')        
    
    z1 = sympy.tensor.IndexedBase('z1')
    z2 = sympy.tensor.IndexedBase('z2')
    i = sympy.tensor.Idx('i')
    j = sympy.tensor.Idx('j')


    sympy.var('x1a, x2a, y1a, y2a, x1b, x2b, y1b, y2b')
    seg = sympy.tensor.Idx('seg')    
    x1a = sympy.tensor.IndexedBase('x1a')    
    x2a = sympy.tensor.IndexedBase('x2a')    
    y1a = sympy.tensor.IndexedBase('y1a')    
    y2a = sympy.tensor.IndexedBase('y2a')    
    y1b = sympy.tensor.IndexedBase('y1b')    
    y2b = sympy.tensor.IndexedBase('y2b')    
    xi = sympy.tensor.IndexedBase('xi')
    xj = sympy.tensor.IndexedBase('xj')
    #mp2 = {'zb[layer]': x2a[seg]}
    mp2 = [(mp['zbot'], x2a[seg]),
           (mp['ztop'], x1a[seg]),
           (mp['abot'], y2a[seg]),
           (mp['atop'], y1a[seg]),
           (mp['bbot'], y2b[seg]),
           (mp['btop'], y1b[seg]),
           (z1[i], xi[i]),
           (z2[i], xj[i])]
    #phi_j = sympy.sin(mj * z)
    
    f = sympy.integrate(p['a'] * p['b'], z)
    
    both = f.subs(z, z2[i]) - f.subs(z, z1[i])
    both = both.subs(mp).subs(mp2)
    
    between = f.subs(z, mp['zbot']) - f.subs(z, mp['ztop'])
    between = between.subs(mp).subs(mp2)
    
    z1_only = f.subs(z, mp['zbot']) - f.subs(z, z1[i])
    z1_only = z1_only.subs(mp).subs(mp2)
    
    z2_only = f.subs(z, z2[i]) - f.subs(z, mp['ztop'])
    z2_only = z2_only.subs(mp).subs(mp2)
           
    text = """A = np.zeros(len(xi))      
    for i in range(len(xi)):        
        for seg in segment_both[i]:
            A[i] += %s
        for seg in segment_xi_only[i]:
            A[i] += %s          
        for seg in segments_between[i]:
            A[i] += %s
        for seg in segment_xj_only[i]:
            A[i] += %s
            
    return A"""
    
        
    fn = text % (both, z1_only, between, z2_only)
    
    return fn 
    
        
    fn = text % (both, xi_only, between, xj_only)
    
    return fn       
if __name__ == '__main__':
    #print(generate_gamma_code())
    print('#'*65)
    #print(generate_psi_code())
    #print(generate_theta_two_prop())
    #print(generate_dim1sin_abf_linear())
    #print(dim1sin_ab_linear())
    #print(dim1sin_af_linear())
    #print(dim1sin_abf_linear())
    #print(dim1sin_D_aDf_linear())
    #print(dim1sin_abc_linear())
    #print(dim1sin_D_aDb_linear())    
    #print(EDload_linear())
    #print(Eload_linear())
    #print(dim1sin_a_linear_between())
    print(dim1_ab_linear_between())
    pass
        
    
#==============================================================================
# from sympy import symbols
# from sympy.utilities.codegen import codegen
# from sympy import Eq
# n,m = symbols('n m', integer=True)
# A = IndexedBase('A')
# x = IndexedBase('x')
# y = IndexedBase('y')
# i = Idx('i', m)
# j = Idx('j', n)
#  
# [(c_name, c_code), (h_name, c_header)] = \
# codegen(name_expr=('matrix_vector', Eq(y[i], A[i, j]*x[j])), language = "F95",prefix = "file", header=False,
#  
# empty=False)
# print c_name
# print c_code
# print h_name
# print c_header
#==============================================================================

