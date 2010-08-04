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
import vigra, numpy
from enthought.traits.api import *
from enthought.traits.ui.api import *


class SegmentorBase(HasTraits):
    #human readable information
    name = "Base Segmentation Plugin"
    description = "virtual base class"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset - segmentation plugins normally need the whole volume for segmentation
    minContext = -1

    def __init__(self):
        self.weights = None

    def segment(self, labelVolume, labelValues, labelIndices):
        """
        Arguments:
            volume : 4D scalar containing 3D Data + Color information in the last dimension
            labels : 3D uint8 scalar containing the seeds
        return:
            3D unit8 volume that contains label numbers
        """
        if labelVolume.shape[0] > 1:
            return self.segment3D(labelVolume, labelValues.astype('uint8'), labelIndices)
        else:
            res = self.segment2D(labelVolume, labelValues.astype('uint8'), labelIndices)

    def setupWeights(self, weights):
        """
        Override this function and setup the weights as needed
        you get a 3D 3Vector of the weights to the [x+1,y,z], [x,y+1,z], [x,y,z+1] neighbours
        """
        print "setting up weights"
        self.weights = weights

    def settings(self):
        self.configure_traits( kind = 'modal')

