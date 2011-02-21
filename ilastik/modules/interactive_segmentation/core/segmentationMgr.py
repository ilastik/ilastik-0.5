#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

import numpy, vigra
   
def LocallyDominantSegmentation(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)

    res = numpy.zeros( propmap.shape, dtype=numpy.float32)
    for k in range(propmap.shape[-1]):
        #TODO: time !!!
        if propmap.shape[1] == 1:
            res[0,0,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,0,:,:,k], sigma)
        else:
            res[0,:,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,:,:,:,k], sigma)

    return  numpy.argmax(res, axis=len(propmap.shape)-1) + 1


def LocallyDominantSegmentation2D(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)
        
    return  numpy.argmax(propmap, axis=len(propmap.shape)-1) + 1

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 


