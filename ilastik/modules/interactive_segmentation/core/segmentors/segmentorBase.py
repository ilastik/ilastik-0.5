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
import numpy
from enthought.traits.api import HasTraits

#*******************************************************************************
# S e g m e n t o r B a s e                                                    *
#*******************************************************************************

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
        self.volumeBasinsWithBorders = None
        self.volumeBasins = None
        self.segmentation = None

    def segment(self, labelVolume, labelValues, labelIndices):
        """
        Arguments:
            volume : 4D scalar containing 3D Data + Color information in the last dimension
            labels : 3D uint8 scalar containing the seeds
        return:
            4D uint8 (3D + channels) volume that contains label numbers
        """
        print "labelVolume:  ", labelVolume.dtype, labelVolume.shape
        print "labelValues:  ", labelValues.dtype, labelValues.shape
        print "labelIndices: ", labelIndices.dtype, labelIndices.shape
        
        if labelValues.dtype != numpy.uint8:
            print "Converting labelValues to uint8"
            labelValues = labelValues.astype('uint8')

        if labelIndices.dtype != numpy.uint32:
            print "Converting labelIndices to uint32"
            labelIndices = labelIndices.astype('uint32')

        
        #if labelVolume.shape[0] > 1:
        self.segmentation = self.segment3D(labelVolume, labelValues, labelIndices)
        return self.segmentation
        #else:
        #    res = self.segment2D(labelVolume, labelValues, labelIndices)

    def setupWeights(self, weights):
        """
        Override this function and setup the weights as needed
        you get a 3D 3Vector of the weights to the [x+1,y,z], [x,y+1,z], [x,y,z+1] neighbours
        """
        print "setting up weights"
        print "weights ", weights.dtype, weights.shape
        self.weights = weights

    def settings(self):
        self.configure_traits( kind = 'modal', view='view')

    def getInlineSettingsWidget(self, parent, view = 'inlineConfig'):
        try:
            ui = self.edit_traits(view, parent=parent, kind='subpanel').control
            return ui
        except:
            print "No inline settings provided for ", self.name
            return None
