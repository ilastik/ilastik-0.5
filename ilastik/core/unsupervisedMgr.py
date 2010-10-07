#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, M Hanselmann, U Koethe, FA Hamprecht. All rights reserved.
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
import traceback, os, sys

import ilastik.core.unsupervised 

from PyQt4 import QtCore
from ilastik.core import jobMachine


class UnsupervisedThread(QtCore.QThread):
    def __init__(self, dataMgr, overlays, unsupervised = ilastik.core.unsupervised.unsupervisedClasses[0], unsupervisedOptions = None):
        QtCore.QThread.__init__(self, None)
        self.dataMgr = dataMgr
        self.reshapeToFeatures(overlays)
        self.count = 0
        self.numberOfJobs = 1 #self.dataItem._dataVol._data.shape[0]
        self.stopped = False
        self.unsupervised = unsupervised
        self.unsupervisedOptions = unsupervisedOptions
        self.jobMachine = jobMachine.JobMachine()

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

        #print features.shape


    def decompose(self):
        # V contains the component spectra/scores, W contains the projected data
        print self.unsupervised
        V, W = self.unsupervised.decompose(self.features)
        self.result = (W.T).reshape((self.origshape[0], self.origshape[1], self.origshape[2], self.origshape[3], W.shape[0]))
        

    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            jobs = []
            job = jobMachine.IlastikJob(UnsupervisedThread.decompose, [self])
            jobs.append(job)
            self.jobMachine.process(jobs)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in UnsupervisedThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            