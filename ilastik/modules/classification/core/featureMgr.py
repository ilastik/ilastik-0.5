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
from ilastik.core import jobMachine
from collections import deque
from ilastik.core.utilities import irange
from ilastik.core import dataMgr
from ilastik.core.volume import DataAccessor
from ilastik.core.overlayMgr import OverlayItem

import copy
import traceback
import threading

try:
    from PyQt4 import QtCore
    ThreadBase = QtCore.QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False


import vigra
at = vigra.arraytypes

import features
from features.featureBase import FeatureBase

import os, sys

""" Import all feature plugins"""

pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/features')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/other files.
            module = __import__('ilastik.modules.classification.core.features.' + module_name)
except Exception, e:
    pass



class FeatureMgr():
    """
    Manages selected features (merkmale) for classificator.
    """
    def __init__(self, dataMgr, featureItems=[]):
        self.dataMgr = dataMgr
        self.totalFeatureSize = 1
        self.featureSizes = []
        self.featureOffsets = []
        self.maxContext = 0
        self.setFeatureItems(featureItems)
        self.parent_conn = None
        self.child_conn = None
        
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        self.featureSizes = []
        self.featureOffsets = []
        if len(featureItems) > 0:
            numChannels = self.dataMgr[0]._dataVol._data.shape[-1]
            totalSize = 0
            for i, f in enumerate(featureItems):
                oldSize = totalSize
                totalSize += f.computeSizeForShape(self.dataMgr[0]._dataVol._data.shape, self.dataMgr.selectedChannels)
                if f.minContext > self.maxContext:
                    self.maxContext = f.minContext

                self.featureSizes.append(totalSize - oldSize)
                self.featureOffsets.append(oldSize)
            try:
                self.totalFeatureSize = totalSize
                for i, di in enumerate(self.dataMgr):
                    di.module["Classification"]["featureM"] = numpy.zeros(di.shape[0:-1] + (totalSize,),'float32')

            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                return False
        else:
            print "setFeatureItems(): no features selected"
        return True
    
    def exportFeatureItems(self, h5featGrp):
        if hasattr(self, 'featureItems'):
            for k, feat in enumerate(self.featureItems):
                itemGroup = h5featGrp.create_group('feature_%03d' % k)
                feat.serialize(itemGroup)
            
    def importFeatureItems(self, h5featGrp):
        featureItems = []
        for fgrp in h5featGrp.values():
            featureItems.append(FeatureBase.deserialize(fgrp))
        
        self.setFeatureItems(featureItems)

    
    def prepareCompute(self, dataMgr):
        self.dataMgr = dataMgr

        self.featureProcess = FeatureThread(self, self.dataMgr, self.dataMgr)

        return self.featureProcess.jobs
    
    def triggerCompute(self):
        self.featureProcess.start()
    
    def getCount(self):
        return self.featureProcess.count
          
    def joinCompute(self, dataMgr):
        self.featureProcess.wait()
        self.featureProcess = None
        self.deleteFeatureOverlays()
        self.createFeatureOverlays()

    def deleteFeatureOverlays(self):
        for index2,  di in enumerate(self.dataMgr):
            keys = di.overlayMgr.keys()
            for k in keys:
                if k.startswith("Classification/Features/"):
                    di.overlayMgr.remove(k)
    
    
    def createFeatureOverlays(self):
        for index,  feature in enumerate(self.featureItems):
            offset = self.featureOffsets[index]
            size = self.featureSizes[index]

            for index2,  di in enumerate(self.dataMgr):
                #create Feature Overlays
                for c in range(0,size):
                    rawdata = di.module["Classification"]["featureM"][:, :, :, :, offset+c:offset+c+1]
                    #TODO: the min/max stuff here is slow !!!
                    #parallelize ??
                    min = numpy.min(rawdata)
                    max = numpy.max(rawdata)
                    data = DataAccessor(rawdata,  channels = True,  autoRgb = False)
                    
                    ov = OverlayItem(data, color = long(255 << 16), alpha = 1.0,  autoAdd = False, autoVisible = False)
                    ov.min = min
                    ov.max = max
                    di.overlayMgr[ feature.getKey(c)] = ov
  

    def __getstate__(self): 
        # Delete This Instance for pickleling
        return {}     
                
class FeatureThread(ThreadBase):
    def __init__(self, featureMgr, dataMgr, items):
        ThreadBase.__init__(self)
        self.count = 0
        self.jobs = 0
        self.featureMgr = featureMgr
        self.dataMgr = dataMgr
        self.items = items
        self.computeNumberOfJobs()
        self.jobMachine = jobMachine.JobMachine()
        self.printLock = threading.Lock()

    def computeNumberOfJobs(self):
        for image in self.dataMgr:
            blockA = dataMgr.BlockAccessor(image.module["Classification"]["featureM"],64)
            self.jobs += image._dataVol._data.shape[0] * len(self.featureMgr.featureItems) * blockA._blockCount

    def calcFeature(self, image, featureBlockAccessor, offset, size, feature, blockNum):
        for t_ind in range(image._dataVol._data.shape[0]):
            try:
                overlap = feature.minContext
                bounds = featureBlockAccessor.getBlockBounds(blockNum, overlap)
                dataInput = image[t_ind,bounds[0]:bounds[1],bounds[2]:bounds[3],bounds[4]:bounds[5], :].astype('float32')
                
                result = feature.compute(dataInput[..., self.dataMgr.selectedChannels])
                bounds1 = featureBlockAccessor.getBlockBounds(blockNum,0)

                sx = bounds1[0]-bounds[0]
                ex = bounds[1]-bounds1[1]
                sy = bounds1[2]-bounds[2]
                ey = bounds[3]-bounds1[3]
                sz = bounds1[4]-bounds[4]
                ez = bounds[5]-bounds1[5]

                ex = result.shape[0] - ex
                ey = result.shape[1] - ey
                ez = result.shape[2] - ez

                tres = result[sx:ex,sy:ey,sz:ez,:]
                featureBlockAccessor[t_ind,bounds1[0]:bounds1[1],bounds1[2]:bounds1[3],bounds1[4]:bounds1[5],offset:offset+size] = tres
            except Exception, e:
                self.printLock.acquire()
                print "########################## exception in FeatureThread ###################"
                print e
                traceback.print_exc(file=sys.stdout)
                self.printLock.release()
            self.count += 1
            # print "Feature Job ", self.count, "/", self.jobs, " finished"
        
    
    def run(self):
        jobs = []
        for image in self.items:
            featureBlockAccessor = dataMgr.BlockAccessor(image.module["Classification"]["featureM"],64)
            for blockNum in range(featureBlockAccessor._blockCount):
                for i, feature in enumerate(self.featureMgr.featureItems):
                    job = jobMachine.IlastikJob(FeatureThread.calcFeature, [self, image, featureBlockAccessor, self.featureMgr.featureOffsets[i], self.featureMgr.featureSizes[i], feature, blockNum])
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
        self.groupMaskSizes = map(lambda x: int(3.0*x+0.5)*2+1,self.groupScaleValues)
        self.groups = {}
        self.createGroups()
        self.selection = [ [False for k in self.groupScaleNames] for j in self.groups ]
        
    def createGroups(self):
        for c in FeatureBase.__subclasses__():
            for g in c.groups:
                print "Adding", c.__name__, " to Group", g
                if g in self.groups:
                    self.groups[g].append(c)
                else:
                    self.groups[g] = [c]

    def createList(self):
        resList = []
        for groupIndex, scaleList in enumerate(self.selection):
            for scaleIndex, selected in enumerate(scaleList):
                for feature in self.groups[self.groups.keys()[groupIndex]]:
                    if selected:
                        scaleValue = self.groupScaleValues[scaleIndex]
                        fc = feature(scaleValue)
                        resList.append(fc)
        return resList
    
ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()


