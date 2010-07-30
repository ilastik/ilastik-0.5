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

#try:
#    import vigra.pws
#    import vigra.pws2
#    ok = True
#except Exception, e:
#    print e
#    traceback.print_exc(file=sys.stdout)
#    print "propably the vigra.pws module was not found, please recompile vigra with PowerWaterShed support to enable the pws segmentation plugin"
#
#
#if ok:
#    class SegmentorPW(SegmentorBase):
#        name = "Powerwatershed Segmentation"
#        description = "Segmentation plugin using the cool Powerwatershed formalism of Cuprie and Grady"
#        author = "HCI, University of Heidelberg"
#        homepage = "http://hci.iwr.uni-heidelberg.de"
#
#
#        def segment3D(self, labels):
#            pws = vigra.pws.q2powerwatershed3D(self.weights, labels.swapaxes(0,2).view(vigra.ScalarVolume))
#            pws = numpy.where(pws > 127, 2, 1)
#            return pws.swapaxes(0,2).view(numpy.ndarray)
#
#        def segment2D(self, labels):
#            #TODO: implement
#            return labels
#
#        def setupWeights(self, weights):
#            self.weights = (255 - numpy.average(weights, axis = 3)).astype(numpy.uint8).swapaxes(0,2).view(vigra.ScalarVolume)


try:
    import vigra.pws
    import vigra.pws2
    ok = True
except Exception, e:
    print e
    traceback.print_exc(file=sys.stdout)
    print "propably the vigra.pws module was not found, please recompile vigra with PowerWaterShed support to enable the pws segmentation plugin"


if ok:
    class SegmentorPW(SegmentorBase):
        name = "Powerwatershed Segmentation"
        description = "Segmentation plugin using the cool Powerwatershed formalism of Cuprie and Grady"
        author = "HCI, University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        pwsAlgorithm = Enum("Powerwatershed (RW)", "Powerwatershed Boute (RW)")

        def segment3D(self, labels):
            l = labels.copy()
            if self.pwsAlgorithm == 'Powerwatershed (RW)':
                pws = vigra.pws.q2powerwatershed3D(self.weights, labels.swapaxes(0,2).view(vigra.ScalarVolume))
                pws = numpy.where(pws > 127, 2, 1)
            elif self.pwsAlgorithm == 'Powerwatershed Boute (RW)':
                pws = vigra.pws2.q2powerwatershed3D(self.weights, l.swapaxes(0,2).view(vigra.ScalarVolume))
                pws = l[:,:,:,0]
                pws = pws.swapaxes(0,2)
            return pws.swapaxes(0,2).view(numpy.ndarray)

        def segment2D(self, labels):
            #TODO: implement
            return labels

        def setupWeights(self, weights):
            self.weights = (255 - numpy.average(weights, axis = 3)).astype(numpy.uint8).swapaxes(0,2).view(vigra.ScalarVolume)