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

import numpy

from segmentorBase import SegmentorBase
from enthought.traits.ui.api import View, Item

ok = False

try:
    import vigra.cutKolmogorov
    ok = True
except Exception, e:
    pass

if ok:
#*******************************************************************************
# S e g m e n t o r G C                                                        *
#*******************************************************************************

    class SegmentorGC(SegmentorBase):
        name = "GraphCut Segmentation"
        description = "Segmentation plug-in using the Graph Cut algorithm"
        author = "C. N. Straehle, HCI - University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        gamma = Float(30)
        difference = Bool(False)
        useHistogram = Bool(False)
        alpha = Float(10)
        
        view = View( Item('gamma'), Item('difference'), Item('useHistogram'), Item('alpha'), buttons = ['OK', 'Cancel'],  )       

        def segment3D(self, labelVolume, labelValues, labelIndices):
            tweights = numpy.zeros(self.weights.shape[0:-1] + (2,), numpy.float32)
            
            
            weights = numpy.exp( - (self.weights)**2 / self.gamma**2)

            b = numpy.ndarray(self.weights.shape[0:-1] + (1,) , numpy.float32)
            b[:,:,:,0] = (weights[:,:,:,0] + weights[:,:,:,1] + weights[:,:,:,2]) * 2
            b[1:,:,:,0] += weights[:-1,:,:,0] * 2
            b[:,1:,:,0] += weights[:,:-1,:,1] * 2
            b[:,:,1:,0] += weights[:,:,:-1,2] * 2
            
            b[:,:,:,0] += 99999
            
            a = numpy.where(labelVolume == 1, b, 0)
            tweights[:,:,:,0] = a[:,:,:,0]
            a = numpy.where(labelVolume == 2, b, 0)
            tweights[:,:,:,1] = a[:,:,:,0]

            if self.useHistogram:
                middle, larger, smaller = self.calculateSeparation(self.origWeights, labelVolume)
                tw = self.origWeights - middle
                tw1 = numpy.where(tw > 0, tw * self.alpha, 0)
                tw2 = numpy.where(tw < 0, - tw * self.alpha, 0)
                tweights[:,:,:,larger - 1] += tw1
                tweights[:,:,:,smaller - 1] += tw2
                
            print "Executing Graph cut with gamma ", self.gamma
            print "shapes : ", tweights.shape
            
            res = vigra.cutKolmogorov.cutKolmogorov(tweights, weights)
                      
            res.shape = res.shape + (1,)
            
            return res

        def segment2D(self, labelVolume, labelValues, labelIndices):
            #TODO: implement
            return labelVolume


        def setupWeights(self, weights):
            self.origWeights = weights
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
                
                
                
        def calculateSeparation(self, image, labelVolume):
            lv = labelVolume[:,:,:,0]
            indices = numpy.nonzero(numpy.where(lv == 1, 1, 0))
            values = image[indices]
            avg1 = numpy.average(values)
            
            indices = numpy.nonzero(numpy.where(lv == 2, 1, 0))
            values = image[indices]
            avg2 = numpy.average(values)
            
            larger = 1
            smaller = 2
            
            if avg2 > avg1:
                larger = 2
                smaller = 1                
                
            return (avg1 + avg2) / 2.0, larger, smaller
            