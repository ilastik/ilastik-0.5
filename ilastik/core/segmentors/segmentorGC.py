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
    import vigra.cutKolmogorov

    ok = True
except Exception, e:
    print e
    traceback.print_exc(file=sys.stdout)
    print "propably the vigra.pws module was not found, please recompile vigra with PowerWaterShed support to enable the pws segmentation plugin"


if ok:

    class SegmentorGC(SegmentorBase):
        name = "GraphCut Segmentation"
        description = "Segmentation plugin using Kolmogorovs performant GraphCut Algorithm"
        author = "HCI, University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"


        def segment3D(self, labels):
            tweights = numpy.zeros(self.weights.shape[0:-1] + (2,), 'int32')

            a = numpy.where(labels == 1, 99999999, 0)
            tweights[:,:,:,0] = a[:,:,:,0]
            a = numpy.where(labels == 2, 99999999, 0)
            tweights[:,:,:,1] = a[:,:,:,0]




            res = vigra.cutKolmogorov.cutKolmogorov(tweights.swapaxes(0,2).view(vigra.ScalarVolume), self.weights)
            res = res.swapaxes(0,2).view(vigra.ScalarVolume)
            return res

        def segment2D(self, labels):
            #TODO
            return labels

        def setupWeights(self, weights):
            self.weights = (255 - weights).astype(numpy.int32).swapaxes(0,2).view(vigra.ScalarVolume)