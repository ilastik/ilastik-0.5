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

"""
Watershed segmentation plugin
"""

from segmentorBase import *
from enthought.traits.api import *
from enthought.traits.ui.api import *

ok = False

try:
    import vigra.rw
    ok = True
except Exception, e:
    pass

if ok:
#*******************************************************************************
# S e g m e n t o r R W                                                        *
#*******************************************************************************

    class SegmentorRW(SegmentorBase):
        name = "Random Walk Segmentation"
        description = "Segmentation plugin using the Random Walk algorithm "
        author = "C. N. Straehle, HCI - University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        gamma = Float(10)
        difference = Bool(False)
        lisOptions = String("-p saamg -tol 1.0e-4")
        
        view = View( Item('gamma'),  Item('difference'), Item('lisOptions'), buttons = ['OK', 'Cancel'],  )       

        def segment3D(self, labelVolume, labelValues, labelIndices):
            seeds = numpy.zeros(labelVolume.shape[0:-1], numpy.uint8)
            seeds[:,:,:] = labelVolume[:,:,:,0]

            print "Executing Random walker with gamma ", self.gamma
            res = vigra.rw.randomWalk(numpy.exp( - (self.weights)**2 / self.gamma**2) , seeds, self.lisOptions)#.swapaxes(0,2).view(vigra.ScalarVolume))
            
            self.potentials = res        
            
            ret = numpy.argmax(res, 3) + 1
            
            #ret[:] =  ret.swapaxes(0,2).view(numpy.ndarray)
            
            ret.shape = ret.shape + (1,)
            
            return ret

        def segment2D(self, labelVolume, labelValues, labelIndices):
            #TODO: implement
            return labelVolume


        def setupWeights(self, weights):
            #self.weights = numpy.average(weights, axis = 3).astype(numpy.uint8)#.swapaxes(0,2).view(vigra.ScalarVolume)
            self.weights = numpy.ndarray(weights.shape + (3,), numpy.float32)
            tw = numpy.ndarray(weights.shape, numpy.float32)
            
            tw[:] = weights[:]
            
            self.weights[-1,:,:,0] = 0
            self.weights[:,-1,:,1] = 0
            self.weights[0,:,-1,2] = 0
            
            if self.difference:
                self.weights[0:-1,:,:,0] = numpy.abs(tw[1:,:,:] - tw[0:-1,:,:])
                self.weights[:,0:-1,:,1] = numpy.abs(tw[:,1:,:] - tw[:,0:-1,:])
                self.weights[:,:,0:-1,2] = numpy.abs(tw[:,:,1:] - tw[:,:,0:-1])
            else:
                self.weights[0:-1,:,:,0] = 1 - numpy.abs(tw[1:,:,:] + tw[0:-1,:,:]) / 2 
                self.weights[:,0:-1,:,1] = 1 - numpy.abs(tw[:,1:,:] + tw[:,0:-1,:]) / 2
                self.weights[:,:,0:-1,2] = 1 - numpy.abs(tw[:,:,1:] + tw[:,:,0:-1]) / 2
                
