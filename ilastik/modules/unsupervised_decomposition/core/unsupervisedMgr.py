#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

from PyQt4.QtCore import QThread

from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr

import numpy
import traceback, sys
from ilastik.core import jobMachine
import os
import algorithms
from ilastik.core.volume import DataAccessor
from ilastik.core.overlayMgr import OverlayItem

""" Import all algorithm plugins"""
pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/algorithms')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/othesr files.
            module = __import__('ilastik.modules.unsupervised_decomposition.core.algorithms.' + module_name)
except Exception, e:
    print e
    traceback.print_exc()
    pass

for i, c in enumerate(algorithms.unsupervisedDecompositionBase.UnsupervisedDecompositionBase.__subclasses__()):
    print "Loaded unsupervised decomposition algorithm:", c.name


#*******************************************************************************
# U n s u p e r v i s e d I t e m M o d u l e M g r                            *
#*******************************************************************************

class UnsupervisedItemModuleMgr(BaseModuleDataItemMgr):
    name = "Unsupervised_Decomposition"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.overlays = []
        self.inputData = None
        
    def setInputData(self, data):
        self.inputData = data
        
#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n M o d u l e M g r          *
#*******************************************************************************

class UnsupervisedDecompositionModuleMgr(BaseModuleMgr):
    name = "Unsupervised_Decomposition"
         
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        self.unsupervisedMethod = algorithms.unsupervisedDecompositionPCA.UnsupervisedDecompositionPCA
        if self.dataMgr.module["Unsupervised_Decomposition"] is None:
            self.dataMgr.module["Unsupervised_Decomposition"] = self
            
    def computeResults(self, inputOverlays):
        self.decompThread = UnsupervisedDecompositionThread(self.dataMgr, inputOverlays, self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod)
        self.decompThread.start()
        return self.decompThread
    
    def finalizeResults(self):
        activeItem = self.dataMgr[self.dataMgr._activeImageNumber]
        activeItem._dataVol.unsupervised = self.decompThread.result

        #create overlays for unsupervised decomposition:
        if self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname] is None:
            data = self.decompThread.result[:,:,:,:,:]
            myColor = OverlayItem.qrgb(0, 0, 0)
            for o in range(0, data.shape[4]):
                data2 = OverlayItem.normalizeForDisplay(data[:,:,:,:,o:(o+1)])
                # for some strange reason we have to invert the data before displaying it
                ov = OverlayItem(255 - data2, color = myColor, alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = True)
                self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname + " component %d" % (o+1)] = ov
            # remove outdated overlays (like PCA components 5-10 if a decomposition with 4 components is done)
            numOverlaysBefore = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
            finished = False
            while finished != True:
                o = o + 1
                # assumes consecutive numbering
                key = "Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname + " component %d" % (o+1)
                self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.remove(key)
                numOverlaysAfter = len(self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr.keys())
                if(numOverlaysBefore == numOverlaysAfter):
                    finished = True
                else:
                    numOverlaysBefore = numOverlaysAfter
        else:
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Unsupervised/" + self.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod.shortname]._data = DataAccessor(self.decompThread.result)
            
#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n T h r e a d                *
#*******************************************************************************

class UnsupervisedDecompositionThread(QThread):
    def __init__(self, dataMgr, overlays, unsupervisedMethod = algorithms.unsupervisedDecompositionPCA.UnsupervisedDecompositionPCA, unsupervisedMethodOptions = None):
        QThread.__init__(self, None)
        self.reshapeToFeatures(overlays)
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = 1
        self.stopped = False
        self.unsupervisedMethod = unsupervisedMethod
        self.unsupervisedMethodOptions = unsupervisedMethodOptions
        self.jobMachine = jobMachine.JobMachine()
        self.result = []

    def reshapeToFeatures(self, overlays):
        # transform to feature matrix
        # ...first find out how many columns and rows the feature matrix will have
        numFeatures = 0
        numPoints = overlays[0].shape[0] * overlays[0].shape[1] * overlays[0].shape[2] * overlays[0].shape[3]
        for overlay in overlays:
            numFeatures += overlay.shape[4]
        # ... then copy the data
        features = numpy.zeros((numPoints, numFeatures), dtype=numpy.float)
        currFeature = 0
        for overlay in overlays:
            currData = overlay[:,:,:,:,:]
            features[:, currFeature:currFeature+overlay.shape[4]] = currData.reshape(numPoints, (currData.shape[4]))
            currFeature += currData.shape[4]
        self.features = features
        self.origshape = overlays[0].shape
        
    def decompose(self):
        # V contains the component spectra/scores, W contains the projected data
        unsupervisedMethod = self.unsupervisedMethod()
        V, W = unsupervisedMethod.decompose(self.features)
        self.result = (W.T).reshape((self.origshape[0], self.origshape[1], self.origshape[2], self.origshape[3], W.shape[0]))

    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            jobs = []
            job = jobMachine.IlastikJob(UnsupervisedDecompositionThread.decompose, [self])
            jobs.append(job)
            self.jobMachine.process(jobs)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in UnsupervisedThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            
    