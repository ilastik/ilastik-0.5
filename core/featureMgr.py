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
import time
import sys
from core import jobMachine
from collections import deque
from core.utilities import irange
from core import dataMgr
import copy
import traceback
import threading
from PyQt4 import QtCore

import vigra
at = vigra.arraytypes

from gui.volumeeditor import VolumeEditor as VolumeEditor

import core.features


import os, sys

""" Import all feature plugins"""

for f in os.listdir(os.path.abspath('core/features')):
    module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
    if ext == '.py': # Important, ignore .pyc/other files.
        module = __import__('core.features.' + module_name)




class FeatureMgr():
    """
    Manages selected features (merkmale) for classificator.
    """
    def __init__(self, dataMgr, featureItems=None):
        self.dataMgr = dataMgr
        self.featureSizes = []
        self.featureOffsets = []
        if featureItems is None:
            featureItems = []
        self.maxContext = 0
        self.setFeatureItems(featureItems)
        self.featuresComputed = [False] * len(self.featureItems)
        self.parent_conn = None
        self.child_conn = None
        
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        self.featureSizes = []
        self.featureOffsets = []
        if len(featureItems) > 0:
            numChannels = self.dataMgr[0].dataVol.data.shape[-1]
            totalSize = 0
            for i, f in enumerate(featureItems):
                oldSize = totalSize
                totalSize += f.computeSizeForShape(self.dataMgr[0].dataVol.data.shape)
                if f.minContext > self.maxContext:
                    self.maxContext = f.minContext

                self.featureSizes.append(totalSize - oldSize)
                self.featureOffsets.append(oldSize)
            try:
                for i, di in enumerate(self.dataMgr):
                    if di.featureCacheDS is None:
                        di._featureM = numpy.zeros(di.dataVol.data.shape + (totalSize,),'float32')
                    else:
                        di.featureCacheDS.resize(di.dataVol.data.shape + (totalSize,))
                        di._featureM = di.featureCacheDS
                    di.featureBlockAccessor = dataMgr.BlockAccessor(di._featureM, 128)

            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                return False
        else:
            print "setFeatureItems(): no features selected"
        return True
    
    def prepareCompute(self, dataMgr):
        self.dataMgr = dataMgr

        self.featureProcess = FeatureThread(self, self.dataMgr)

        return self.featureProcess.jobs
    
    def triggerCompute(self):
        self.featureProcess.start()
    
    def getCount(self):
        return self.featureProcess.count
          
    def joinCompute(self, dataMgr):
        self.featureProcess.wait()
        self.featureProcess = None
  

    def __getstate__(self): 
        # Delete This Instance for pickleling
        return {}     
                
class FeatureThread(QtCore.QThread):
    def __init__(self, featureMgr, dataMgr):
        QtCore.QThread.__init__(self)
        self.count = 0
        self.jobs = 0
        self.featureMgr = featureMgr
        self.dataMgr = dataMgr
        self.computeNumberOfJobs()
        self.jobMachine = jobMachine.JobMachine()
        self.printLock = threading.Lock()

    def computeNumberOfJobs(self):
        for image in self.dataMgr:
            self.jobs += image.dataVol.data.shape[0]*image.dataVol.data.shape[4] * len(self.featureMgr.featureItems) * image.featureBlockAccessor.blockCount

    def calcFeature(self, image, offset, size, feature, blockNum):
        for t_ind in range(image.dataVol.data.shape[0]):
            for c_ind in range(image.dataVol.data.shape[4]):
                try:
                    overlap = feature.minContext
                    bounds = image.featureBlockAccessor.getBlockBounds(blockNum, overlap)
                    result = feature.compute(image.dataVol.data[t_ind,bounds[0]:bounds[1],bounds[2]:bounds[3],bounds[4]:bounds[5], c_ind].astype('float32'))
                    bounds1 = image.featureBlockAccessor.getBlockBounds(blockNum,0)

                    sx = bounds1[0]-bounds[0]
                    ex = bounds[1]-bounds1[1]
                    sy = bounds1[2]-bounds[2]
                    ey = bounds[3]-bounds1[3]
                    sz = bounds1[4]-bounds[4]
                    ez = bounds[5]-bounds1[5]

                    ex = result.shape[0] - ex
                    ey = result.shape[1] - ey
                    ez = result.shape[2] - ez

                    tres = result[sx:ex,sy:ey,sz:ez]
                    image.featureBlockAccessor[t_ind,bounds1[0]:bounds1[1],bounds1[2]:bounds1[3],bounds1[4]:bounds1[5],c_ind,offset:offset+size] = tres
                except Exception, e:
                    print "########################## exception in FeatureThread ###################"
                    print feature.__class__
                    #print result.shape
                    print bounds
                    print bounds1
                    print offset
                    print size
                    print e
                    traceback.print_exc(file=sys.stdout)
                self.count += 1
                # print "Feature Job ", self.count, "/", self.jobs, " finished"
        
    
    def run(self):
        for image in self.dataMgr:
            jobs = []
            for blockNum in range(image.featureBlockAccessor.blockCount):
                for i, feature in enumerate(self.featureMgr.featureItems):
                    job = jobMachine.IlastikJob(FeatureThread.calcFeature, [self, image, self.featureMgr.featureOffsets[i], self.featureMgr.featureSizes[i], feature, blockNum])
                    jobs.append(job)
                    
            self.jobMachine.process(jobs)

    

class FeatureGroups(object):
    """
    Groups LocalFeature objects to predefined feature sets, selectable in the gui
    initializes the LucalFeature objects with vigra functors and needed
    calculation parameters (for example sigma)
    """
    def __init__(self):
        self.groupScaleNames = ['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        self.groupScaleValues = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        self.groups = {}
        self.createGroups()
        self.selection = [ [False for k in self.groupScaleNames] for j in self.groups ]
        
    def createGroups(self):
        for c in core.features.featureBase.FeatureBase.__subclasses__():
            for g in c.groups:
                print "Adding ", c.__name__, " to Group ", g
                if g in self.groups:
                    self.groups[g].append(c)
                else:
                    self.groups[g] = [c]

    def createList(self):
        resList = []
        for groupIndex, scaleList in irange(self.selection):
            for scaleIndex, selected in irange(scaleList):
                for feature in self.groups[self.groups.keys()[groupIndex]]:
                    if selected:
                        scaleValue = self.groupScaleValues[scaleIndex]
                        fc = feature(scaleValue)
                        resList.append(fc)
        return resList
    
ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()


