import numpy
import threading 
import multiprocessing
import time
from PyQt4 import QtCore

try:
    from vigra import vigranumpycmodule as vm
except ImportError:
    try:
        import vigranumpycmodule as vm
    except ImportError:
        sys.exit("vigranumpycmodule not found!")
    
class FeatureMgr():
    def __init__(self, featureItems=[]):
        self.featureItems = featureItems
        self.featuresComputed = [False] * len(self.featureItems)
        self.parent_conn = None
        self.child_conn = None
        self.parallelType = ['Process', 'Thread'][1]
        self.featureProcessList = []
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        
    def prepareCompute(self, dataMgr):
        self.featureProcessList = [[] for i in range(0, len(dataMgr))]
        for dataIndex in xrange(0, len(dataMgr)):   
            # data will be loaded, if not there yet
            data = dataMgr[dataIndex]
            print 'Data Item: %s: ' % data.fileName
            channelsList = data.unpackChannels()          
            self.featureProcessList[dataIndex].append((channelsList, self.featureItems))
        
        if self.parallelType == 'Process':
            self.parent_conn, self.child_conn = multiprocessing.Pipe()
            self.featureProcess = FeatureProcess(self.featureProcessList, self.child_conn)
        else:
            self.featureProcess = FeatureThread(self.featureProcessList)
        return self.featureProcess.jobs
    
    def triggerCompute(self):
        self.featureProcess.start()
    
    def getCount(self):
        if self.parallelType == 'Process':
            return self.parent_conn.recv()
        else:
            return self.featureProcess.count
          
    def joinCompute(self, dataMgr):
        self.featureProcess.join()                     
                
class FeatureBase(object):
    def __init__(self):
        self.featureFunktor = None
   
    def compute(self, dataItem):
        return None
    
       
    
class LocalFeature(FeatureBase):
    def __init__(self, name, maskSize, featureFunktor):
        FeatureBase.__init__(self)
        self.maskSize = maskSize
        self.sigma = maskSize / 3
        self.featureFunktor = featureFunktor
    
#    def prepareCompute(self, dataItem):
#        channels = self.unpackChannels(dataItem);
#        featureProcessList = []
#        for channel in channels:
#            featureProcessList.append(FeatureProcess(self, self.featureFunktor, (channel, self.sigma)))     
#        return featureProcessList

    
    def __str__(self):
        return '%s: Masksize=%d, Sigma=%5.3f' % (self.featureFunktor.__name__ , self.maskSize, self.sigma)


class FeatureParallelBase(object):
    def __init__(self, featureProcessList):
        self.count = 0
        self.jobs = 0
        self.result = []
        self.featureProcessList = featureProcessList
        self.computeNumberOfJobs()
    
    def computeNumberOfJobs(self):
        for data in self.featureProcessList:
            for channels, features in data:
                    self.jobs += len(channels) * len(features)

class FeatureThread(threading.Thread, FeatureParallelBase):
    def __init__(self, featureProcessList):
        FeatureParallelBase.__init__(self, featureProcessList)
        threading.Thread.__init__(self)  
    def run(self):          
        for data in self.featureProcessList:
            for channels, features in data:
                for c in channels:
                    for fi in features:
                        print c.shape, str(fi)
                        self.result.append(fi.featureFunktor()(c, fi.sigma))
                        time.sleep(0.05)
                        self.count += 1

class FeatureProcess(multiprocessing.Process, FeatureParallelBase):
    def __init__(self, featureProcessList, conn):
        FeatureParallelBase.__init__(self, featureProcessList)
        multiprocessing.Process.__init__(self)  
        self.conn = conn
        
    def run(self):          
        for channels, fi in self.featureProcessList:
            
            for c in channels:
               self.result.append(fi.featureFunktor()(c, fi.sigma))
               self.count += 1
               self.conn.send(self.count)
        self.conn.close()     

def gaussianGradientMagnitude():
    return vm.gaussianGradientMagnitude

def structureTensor():
    return vm.structureTensor

def hessianMatrixOfGaussian():
    return vm.hessianMatrixOfGaussian

def identity():
    return lambda x, sigma: x

ilastikFeatures = []
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", 7, hessianMatrixOfGaussian))
ilastikFeatures.append(LocalFeature("Identity", 0, identity))
ilastikFeatures.append(LocalFeature("GradientMag", 3, gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("GradientMag", 7, gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("structureTensor", 3, structureTensor))
ilastikFeatures.append(LocalFeature("structureTensor", 7, structureTensor))
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", 3, hessianMatrixOfGaussian))
