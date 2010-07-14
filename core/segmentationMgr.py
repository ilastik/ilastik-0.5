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

import numpy, vigra, os, sys

from  core import segmentors
from PyQt4 import QtCore
from core import jobMachine

""" Import all segmentation plugins"""
pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/segmentors')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/other files.
            module = __import__('core.segmentors.' + module_name)
except Exception, e:
    pass

for i, c in enumerate(segmentors.segmentorBase.SegmentorBase.__subclasses__()):
    print "loaded segmentor ", c.name

    

   
def LocallyDominantSegmentation(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)

    res = numpy.zeros( propmap.shape, dtype=numpy.float32)
    for k in range(propmap.shape[-1]):
        #TODO: time !!!
        if propmap.shape[1] == 1:
            res[0,0,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,0,:,:,k], sigma)
        else:
            res[0,:,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,:,:,:,k], sigma)

    return  numpy.argmax(res, axis=len(propmap.shape)-1) + 1


def LocallyDominantSegmentation2D(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)
        
    return  numpy.argmax(propmap, axis=len(propmap.shape)-1) + 1

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 



class SegmentationThread(QtCore.QThread):
    def __init__(self, dataMgr, image, segmentor = segmentors.segmentorPW.SegmentorPW, segmentorOptions = None):
        QtCore.QThread.__init__(self, None)
        self.dataItem = image
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = self.dataItem.dataVol.data.shape[0]
        self.stopped = False
        self.segmentor = segmentor
        self.segmentorOptions = segmentorOptions
        self.jobMachine = jobMachine.JobMachine()

    def segment(self, i, data, labels):
        self.result[i,:,:,:] = self.segmentor.segment(data, labels)
        self.count += 1

    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            self.result = numpy.zeros(self.dataItem.dataVol.data.shape[0:-1], 'uint8')
            jobs = []
            for i in range(self.dataItem.dataVol.data.shape[0]):
                job = jobMachine.IlastikJob(SegmentationThread.segment, [self, i, self.dataItem.dataVol.data[i,:,:,:,:], self.dataItem.dataVol.labels.data[i,:,:,:]])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()