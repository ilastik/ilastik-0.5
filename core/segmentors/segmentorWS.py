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
Powerwatershed segmentation plugin
"""

import vigra, numpy
from segmentorBase import *
import traceback
from enthought.traits.api import *
from enthought.traits.ui.api import *

ok = False

try:
    import vigra.tws
    ok = True
except Exception, e:
    print e
    traceback.print_exc(file=sys.stdout)
    print "propably the vigra.pws module was not found, please recompile vigra with PowerWaterShed support to enable the pws segmentation plugin"


if ok:
    class SegmentorWS(SegmentorBase):
        name = "Watershed Segmentation (normal)"
        description = "Segmentation plugin using seeded Region Growing Watershed algorithm"
        author = "HCI, University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        borderIndicator = Enum("Brightness", "Darkness", "Gradient")
        sigma = CFloat(1.0)
        normalizePotential = CBool(True)



        def segment3D(self, volume , labels):


            #TODO: this , until now, only supports gray scale !
            if self.borderIndicator == "Brightness":
                weights = vigra.filters.gaussianSmoothing(volume[:,:,:,0].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), self.sigma)
            elif self.borderIndicator == "Darkness":
                weights = vigra.filters.gaussianSmoothing(255 - volume[:,:,:,0].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), self.sigma)
            elif self.borderIndicator == "Gradient":
                weights = vigra.filters.gaussianGradientMagnitude(volume[:,:,:,0].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), self.sigma)

            weights = weights.swapaxes(0,2).view(numpy.ndarray)

            if self.normalizePotential == True:
                min = numpy.min(weights)
                max = numpy.max(weights)
                weights = (weights - min)*(255.0 / (max - min))

            #real_weights = numpy.zeros(weights.shape, 'float32')
            real_weights = numpy.zeros(weights.shape, 'uint8')

            real_weights[:] = weights[:]
            real_weights = real_weights.swapaxes(0,2).view(vigra.ScalarVolume)

            seeds = numpy.zeros(labels.shape[0:-1], 'uint32')
            seeds[:,:,:] = labels[:,:,:,0]

            print real_weights.shape, seeds.shape
            print real_weights.dtype, seeds.dtype
            
            #pws = vigra.analysis.watersheds(real_weights, neighborhood=6, seeds = seeds.swapaxes(0,2).view(vigra.ScalarVolume))
            pws = vigra.tws.tws(real_weights, seeds.swapaxes(0,2).view(vigra.ScalarVolume))
            pws = pws.swapaxes(0,2).view(numpy.ndarray)
            print numpy.max(pws),numpy.min(pws)
            return pws

        def segment2D(self, slice , labels):
            #TODO: implement
            return labels
