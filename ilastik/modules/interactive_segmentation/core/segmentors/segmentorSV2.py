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
Watershed iterative segmentation plugin
"""

from segmentorBase import *
from enthought.traits.api import Float, Int
from enthought.traits.ui.api import View, Item
#from segmentorWSit import SegmentorWSiter

ok = False

try:
    import vigra.tws
    ok = True
except Exception, e:
    pass

if 0:
#*******************************************************************************
# S e g m e n t o r S V 2                                                      *
#*******************************************************************************

    class SegmentorSV2(SegmentorBase):
        name = "Supervoxel Segmentation 2"
        description = "Segmentation plugin using sparse Basin graph"
        author = "HCI, University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        bias = Float(64*8)
        biasedLabel = Int(1)
        maxHeight = Float(1024)
        
        view = View( Item('bias'),  Item('maxHeight'), Item('biasedLabel'), buttons = ['OK', 'Cancel'],  )        
        
#*******************************************************************************
# I n d e x e d A c c e s s o r                                                *
#*******************************************************************************

        class IndexedAccessor:
            """
            Helper class that behaves like an ndarray, but does a Lookuptable access
            """

            def __init__(self, volumeBasins, basinLabels):
                self.volumeBasins = volumeBasins
                self.basinLabels = basinLabels
                self.dtype = basinLabels.dtype
                self.shape = volumeBasins.shape

            def __getitem__(self, key):
                return self.basinLabels[self.volumeBasins[tuple(key)]]

            def __setitem__(self, key, data):
                #self.data[tuple(key)] = data
                print "##########ERROR ######### : SegmentationDataAccessor setitem should not be called"

        def segment3D(self, labelVolume, labelValues, labelIndices):
            self.ws.setBias(self.bias,  self.biasedLabel, self.maxHeight)
            self.basinLabels = self.ws.flood(labelValues, labelIndices)
            self.acc = SegmentorWSiter.IndexedAccessor(self.volumeBasins, self.basinLabels)
            return self.acc

        def segment2D(self, labels):
            #TODO: implement
            return labelVolume


        def setupWeights(self, weights):
            print "Incoming weights :", weights.shape
            #self.weights = numpy.average(weights, axis = 3).astype(numpy.uint8)#.swapaxes(0,2).view(vigra.ScalarVolume)#
            if weights.dtype != numpy.uint8:
                print "converting weights to uint8"
                self.weights = weights.astype(numpy.uint8)
#            self.weights = numpy.zeros(weights.shape[0:-1], 'uint8')
#            self.weights[:] = 3
#            self.weights[:,:,0::4] = 10
#            self.weights[:,0::4,:] = 10
#            self.weights[0::4,:,:] = 10
#            self.weights = self.weights

            self.ws = vigra.tws.IncrementalWS2(self.weights)
            self.volumeBasins = self.ws.getVolumeBasins() #WithBorders()
            print "Outgoing weights :", self.volumeBasins.shape

            self.volumeBasins.shape = self.volumeBasins.shape + (1,)
