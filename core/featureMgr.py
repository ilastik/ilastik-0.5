import numpy
import threading 
import multiprocessing
import time

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
        dataMgr.dataFeatures = self.featureProcess.result;                
                
class FeatureBase(object):
    def __init__(self):
        self.featureFunktor = None
   
    def compute(self, channel):
        return None  
    
class LocalFeature(FeatureBase):
    def __init__(self, name, args, arg_names, featureFunktor):
        FeatureBase.__init__(self)
        self.name = featureFunktor.__name__
        self.args = args
        self.arg_names = arg_names
        self.featureFunktor = featureFunktor
    
    def compute(self, channel):
        return self.featureFunktor()(channel, * self.args)

    def __str__(self):
        return '%s: %s' % (self.name , ', '.join(["%s = %d" % (x[0], x[1]) for x in zip(self.arg_names, self.args)]))


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
                result = []
                for c in channels:
                    for fi in features:
                        print c.shape, str(fi)
                        result.append((fi.compute(c), str(fi)))
                        self.count += 1
                self.result.append(result)

class FeatureProcess(multiprocessing.Process, FeatureParallelBase):
    def __init__(self, featureProcessList, conn):
        FeatureParallelBase.__init__(self, featureProcessList)
        multiprocessing.Process.__init__(self)  
        self.conn = conn
        
    def run(self):          
        for data in self.featureProcessList:
            for channels, features in data:
                result = []
                for c in channels:
                    for fi in features:
                        print c.shape, str(fi)
                        result.append((fi.compute(c), str(fi)))
                        self.count += 1
                        self.conn.send(self.count)
                self.result.append(result)
        self.conn.close()     

def gaussianGradientMagnitude():
    return vm.gaussianGradientMagnitude

def structureTensor():
    return vm.structureTensor

def hessianMatrixOfGaussian():
    return vm.hessianMatrixOfGaussian

def eigStructureTensor2d():
    return vm.eigStructureTensor2d

def identity():
    return lambda x: x

ilastikFeatures = []

ilastikFeatures.append(LocalFeature("Identity", [], [''],  identity))
ilastikFeatures.append(LocalFeature("GradientMag", [1], ['Sigma'], gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("GradientMag", [2], ['Sigma'], gaussianGradientMagnitude))
ilastikFeatures.append(LocalFeature("structureTensor", [1], ['Sigma'], structureTensor))
ilastikFeatures.append(LocalFeature("structureTensor", [2], ['Sigma'], structureTensor))
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", [1], ['Sigma'], hessianMatrixOfGaussian))
ilastikFeatures.append(LocalFeature("hessianMatrixOfGaussian", [2], ['Sigma'], hessianMatrixOfGaussian))
ilastikFeatures.append(LocalFeature("eigStructureTensor2d", [1, 1], ['InnerScale', 'OuterScale'] , eigStructureTensor2d))

