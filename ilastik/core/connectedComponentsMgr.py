# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 17:26:49 2010

@author: Anna_2
"""

import numpy, vigra, os, sys
import traceback

from ilastik.core import connectedComponents
from ilastik.core.segmentationMgr import ListOfNDArraysAsNDArray

from PyQt4 import QtCore
from ilastik.core import jobMachine

class ConnectedComponentsThread(QtCore.QThread):
    def __init__(self, dataMgr, image, background=set(), connector = connectedComponents.ConnectedComponents(), connectorOptions = None):
        QtCore.QThread.__init__(self, None)
        self._data = image
        self.backgroundSet = background
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = self._data.shape[0]
        self.stopped = False
        self.connector = connector
        self.connectorOptions = connectorOptions
        self.jobMachine = jobMachine.JobMachine()

    def connect(self, i, data, backgroundSet):
        self.result[i] = self.connector.connect(data, backgroundSet)
        self.count += 1

    def run(self):
        self.dataMgr.featureLock.acquire()
        #if self.dataItem.dataVol.segmentation is None:
        #    self.dataItem.dataVol.segmentation = numpy.zeros(self.dataItem.dataVol._data.shape[0:-1],'uint8')

        try:
            self.result = range(0,self._data.shape[0])
            jobs = []
            for i in range(self._data.shape[0]):
                job = jobMachine.IlastikJob(ConnectedComponentsThread.connect, [self, i, self._data[i,:,:,:,0], self.backgroundSet])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.result = ListOfNDArraysAsNDArray(self.result)
            #for i in range(50):
            #    print self.result[0, i, i, 24, 0]
            #for i in range(10):
            #if self._data[0,i,i,0,0] != self.result[0,i,i,0,0]:
            #        print "not equal at", i
            #print self._data.shape, "  ", self._data[0,0,0,0,0]
            #print self.result.shape, "  ", self.result[0,0,0,0,0]
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            
