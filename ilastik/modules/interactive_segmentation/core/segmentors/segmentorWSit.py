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

import numpy

from segmentorBase import SegmentorBase
from enthought.traits.api import Enum, Bool, Float, Int, String, on_trait_change
from enthought.traits.ui.api import Item, View, Group

ok = False

try:
    import vigra.svs
    ok = True
except Exception, e:
    print "####################################"
    print
    print "    please update to the latest"
    print "    private vigra repository !!!"
    print
    print "####################################"

if ok:
#*******************************************************************************
# S e g m e n t o r W S i t e r                                                *
#*******************************************************************************

    class SegmentorWSiter(SegmentorBase):
        name = "Supervoxel Segmentation"
        description = "Segmentation plug-in using sparse basin graph"
        author = "C. N. Straehle, HCI - University of Heidelberg"
        homepage = "http://hci.iwr.uni-heidelberg.de"

        dontUseSuperVoxels = Bool(False)
        edgeWeights = Enum("Average", "Difference")
        algorithm = Enum("Watershed", "Graphcut", "Randomwalk")        
        bias = Float(0.95)
        biasThreshold = Float(128)
        biasedLabel = Int(1)
        sigma = Float(0.2)
        lis_options = String("-i bicgstab -tol 1.0e-9")
        
        viewWS = Group(Item('bias'),Item('biasThreshold'),  Item('biasedLabel'), visible_when = 'algorithm=="Watershed"')
        viewRW = Group(Item('sigma'), Item('lis_options'), visible_when = 'algorithm=="Randomwalk"')
        viewGC = Group(Item('sigma'), visible_when = 'algorithm=="Graphcut"')

        view = View( Item('edgeWeights'), Item('dontUseSuperVoxels'), Item('algorithm'), buttons = ['OK', 'Cancel'],  )        

        inlineConfig = View(Item('algorithm'), Group(viewWS, viewRW, viewGC))
        default = View(Item('bias'))
        
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
            self.segmentor.setSeeds(labelValues, labelIndices)
            if self.algorithm == "Graphcut":
                print "Executing Graphcut with sigma = %d"  % (self.sigma,)
                self.basinLabels = self.segmentor.doGC(self.sigma)
            elif self.algorithm == "Watershed":
                print "Executing Watershed with bias %d and biasedLabel %d" % (self.bias,  self.biasedLabel,)
                self.basinLabels = self.segmentor.doWS(self.bias,  self.biasThreshold, self.biasedLabel)
            elif self.algorithm == "Randomwalk":
                print "Executing Random Walk with sigma %f, and lis options %s" % (self.sigma,  self.lis_options,)
                self.basinLabels = self.segmentor.doRW(self.sigma,  self.lis_options)
                
                self.basinPotentials = self.segmentor.getBasinPotentials()
                
                self.potentials = SegmentorWSiter.IndexedAccessorWithChannel(self.volumeBasins,self.basinPotentials)
                
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
            self.segmentor = vigra.svs.segmentor(self.weights, useDifference, 0, 255, 2048, self.dontUseSuperVoxels)
    
            
            self.getBasins()
            self.volumeBasins.shape = self.volumeBasins.shape + (1,)

            self.borders = self.segmentor.getBorderVolume()   
            self.borders.shape = self.borders.shape + (1,)
            #self.borders = self.volumeBasins
            

        def getBasins(self):
            self.volumeBasins = self.segmentor.getVolumeBasins()            
                
            