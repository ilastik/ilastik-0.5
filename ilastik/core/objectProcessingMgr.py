# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 17:26:49 2010

@author: Anna_2
"""

class ConnectedComponentsThread(QtCore.QThread):
    def __init__(self, dataMgr, image, connector = ilastik.core.connectedComponents.ConnectedComponents(), connectorOptions = None):
        QtCore.QThread.__init__(self, None)
        self.dataItem = image
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = self.dataItem.dataVol.data.shape[0]
        self.stopped = False
        self.connector = connector
        self.connectorOptions = connectorOptions
        self.jobMachine = jobMachine.JobMachine()

    def connect(self, i, data):
        self.result[i] = self.connector.connect()
        self.count += 1

    def run(self):
        self.dataMgr.featureLock.acquire()
        #if self.dataItem.dataVol.segmentation is None:
        #    self.dataItem.dataVol.segmentation = numpy.zeros(self.dataItem.dataVol.data.shape[0:-1],'uint8')

        try:
            self.result = range(0,self.dataItem.dataVol.data.shape[0])
            jobs = []
            for i in range(self.dataItem.dataVol.data.shape[0]):
                job = jobMachine.IlastikJob(ConnectedComponentsThread.connect, [self, i, self.dataItem.dataVol.data[i,:,:,:,:]])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.result = ListOfNDArraysAsNDArray(self.result)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
