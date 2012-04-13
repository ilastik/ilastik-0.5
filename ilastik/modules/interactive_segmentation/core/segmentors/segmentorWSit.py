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
miminimum spanning tree segmentation plugin
"""

import numpy, traceback, sys

from segmentorBase import SegmentorBase
try:
  from enthought.traits.api import Enum, Bool, Float, Int, String, on_trait_change
  from enthought.traits.ui.api import Item, View, Group
except:
  from traits.api import Enum, Bool, Float, Int, String, on_trait_change
  from traitsui.api import Item, View, Group

ok = False

try:
    import vigra.priows
    ok = True
except Exception, e:
    print e
    traceback.print_exc(file=sys.stdout)
    print "##################################################"
    print " Interactive Segmentation 'segmentorWSit' plugin"
    print "    please update to the latest"
    print "    private vigra repository !!!"
    print "##################################################"

if ok:
#*******************************************************************************
# S e g m e n t o r W S i t e r                                                *
#*******************************************************************************

    class SegmentorWSiter(SegmentorBase):
        name = "Supervoxel MST Segmentation"
        description = "Biased Minimum spanning tree segmentation using sparse basin graph"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        dontUseSuperVoxels = Bool(False)
        edgeWeights = Enum("Average", "Difference")
        bias = Float(0.95)
        biasThreshold = Float(64)
        biasedLabel = Int(1)
        sigma = Float(0.2)
        addVirtualBackgroundSeeds = Bool(False)
        
        advanced = Bool(False)

        viewWS = Group(Item('bias'),Item('biasThreshold'),  Item('biasedLabel'), Item("addVirtualBackgroundSeeds"), visible_when = 'advanced==True')

        view = View( Item('edgeWeights'), Item('dontUseSuperVoxels'), buttons = ['OK', 'Cancel'],  )

        inlineConfig = View(Group(viewWS))
        default = View(Item('bias'), Item("advanced"),Group(viewWS))
        
        lastBorderState = False        
        
                
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
                self.flat = None
                print "Indexaccessor:", volumeBasins.shape
            def __getitem__(self, key):
                return self.basinLabels[self.volumeBasins[tuple(key)]]

            def __setitem__(self, key, data):
                #self.data[tuple(key)] = data
                print "##########ERROR ######### : IndexAccessor setitem should not be called"

#*******************************************************************************
# I n d e x e d A c c e s s o r W i t h C h a n n e l                          *
#*******************************************************************************

        class IndexedAccessorWithChannel:
            """
            Helper class that behaves like an ndarray, but does a Lookuptable access
            """

            def __init__(self, volumeBasins, basinLabels):
                self.volumeBasins = volumeBasins
                self.basinLabels = basinLabels
                self.dtype = basinLabels.dtype
                self.shape = volumeBasins.shape[:-1] + (basinLabels.shape[1],)
                
            def __getitem__(self, key):
                return self.basinLabels[:,key[-1]][self.volumeBasins[tuple(key[:-1])]]

            def __setitem__(self, key, data):
                #self.data[tuple(key)] = data
                print "##########ERROR ######### : IndexAccessor setitem should not be called"



        def segment3D(self, labelVolume, labelValues, labelIndices):
            print "setting seeds"
            self.segmentor.setSeeds(labelValues.squeeze().astype(numpy.uint8), labelIndices.squeeze().astype(numpy.uint32))
            print "Executing Watershed with bias %d and biasedLabel %d. Adding virtual background seeds: %r" % (self.bias,  self.biasedLabel,self.addVirtualBackgroundSeeds)
            self.basinLabels = self.segmentor.doWS(self.bias,  self.biasThreshold, self.biasedLabel, self.addVirtualBackgroundSeeds)
                
            self.getBasins()
            
            self.segmentation = SegmentorWSiter.IndexedAccessor(self.volumeBasins, self.basinLabels)
            return self.segmentation

        def segment2D(self, labels):
            pass

        @on_trait_change('dontUseSuperVoxels')
        def recalculateWeights(self):
            self.setupWeights(self.weights)

        def setupWeights(self, weights):
            self.weights = weights
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

            #self.ws = vigra.tws.IncrementalWS(self.weights, 0)
            print "Incoming weights :", self.weights.dtype, self.weights.shape

            if hasattr(self, "segmentor"):
                del self.segmentor
                del self.volumeBasins
            

            if self.edgeWeights == "Difference":
                useDifference = True
            else:                
                useDifference = False
            
            #print self.dontUseSuperVoxels
            self.segmentor = vigra.priows.segmentor(self.weights, useDifference, 0, 255, 2048, self.dontUseSuperVoxels)
    
            
            self.getBasins()
            self.volumeBasins.shape = self.volumeBasins.shape + (1,)

            self.borders = self.segmentor.getBorderVolume()   
            self.borders.shape = self.borders.shape + (1,)
            #self.borders = self.volumeBasins
            

        def getBasins(self):
            self.volumeBasins = self.segmentor.getVolumeBasins()            
                
            
