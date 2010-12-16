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

import vigra, numpy
from segmentorBase import *
import traceback
from enthought.traits.api import *
from enthought.traits.ui.api import *

ok = False

try:
    import vigra.twsb
    ok = True
except Exception, e:
    pass

if ok:
    class SegmentorWS(SegmentorBase):
        name = "Watershed Segmentation (normal)"
        description = "Segmentation plugin using seeded Region Growing Watershed algorithm"
        author = "HCI, University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        twsAlgorithm = Enum("tws", "twsParallel")

        bias = Float(0.95)
        biasedLabel = Int(1)
        
        view = View( Item('bias'),  Item('biasedLabel'), buttons = ['OK', 'Cancel'],  )        

        def segment3D(self, labelVolume, labelValues, labelIndices):
            seeds = numpy.zeros(labelVolume.shape[0:-1], 'uint32')
            seeds[:,:,:] = labelVolume[:,:,:,0]
           
            #pws = vigra.analysis.watersheds(real_weights, neighborhood=6, seeds = seeds.swapaxes(0,2).view(vigra.ScalarVolume))
            if self.twsAlgorithm == "tws":
                pws = vigra.twsb.twsb(self.weights, seeds, self.biasedLabel, self.bias)#.swapaxes(0,2).view(vigra.ScalarVolume))
            else:
                pws = vigra.twsb.twsParallel(self.weights, seeds)#.swapaxes(0,2).view(vigra.ScalarVolume))
            
            ret = numpy.zeros(labelVolume.shape[0:-1], 'uint8')
            ret[:] = pws[:]#.swapaxes(0,2).view(numpy.ndarray)
            ret.shape = ret.shape + (1,)
            return ret

        def segment2D(self, labelVolume, labelValues, labelIndices):
            #TODO: implement
            return labelVolume


        def setupWeights(self, weights):
            #self.weights = numpy.average(weights, axis = 3).astype(numpy.uint8)#.swapaxes(0,2).view(vigra.ScalarVolume)
            self.weights = weights.astype(numpy.uint8)