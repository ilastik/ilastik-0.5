import numpy
import threading 
import multiprocessing
import time
import sys
sys.path.append("..")
from core.utilities import irange

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
        self.featureProcessList = [[] for i in range(len(dataMgr))]
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
        self.featureProcess = None  
    
    def __getstate__(self): 
        # Delete This Instance for pickleling
        return {}     
                
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
        print channel.shape
        return self.featureFunktor(channel, * self.args)

    def __str__(self):
        return '%s: %s' % (self.name , ', '.join(["%s = %f" % (x[0], x[1]) for x in zip(self.arg_names, self.args)]))


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
                for c_ind, c in irange(channels):
                    for fi in features:
                        print c.shape, str(fi)
                        result.append((fi.compute(c), str(fi), c_ind))
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
                for c_ind, c in irange(channels):
                    for fi in features:
                        print c.shape, str(fi)
                        result.append(( fi.compute(c), str(fi), c_ind) )
                        self.count += 1
                        self.conn.send(self.count)
                self.result.append(result)
        self.conn.close()     

###########################################################################
###########################################################################
class FeatureGroups(object):
    def __init__(self):
        self.groupNames = ['Color', 'Texture', 'Edge']
        self.groupScaleNames = ['Tiny', 'Small', 'Medium', 'Large', 'Huge']
        self.selection = [ [False for k in self.groupScaleNames] for j in self.groupNames ]
        self.groupScaleValues = [0.2, 0.5, 1, 1.6, 3]
        
        self.members = {}
        for g in self.groupNames:
            self.members[g] = []        
        self.createMemberFeatures()
        
    def createMemberFeatures(self):
        #self.members['Color'].append(identity)
        self.members['Color'].append(gaussianSmooth)
        
        self.members['Texture'].append(structureTensor)
        #self.members['Texture'].append(eigHessianTensor2d)
        self.members['Texture'].append(eigStructureTensor2d)
        self.members['Texture'].append(hessianMatrixOfGaussian)
        self.members['Texture'].append(laplacianOfGaussian)
        #self.members['Texture'].append(morphologicalOpening)
        #self.members['Texture'].append(morphologicalClosing)
        self.members['Texture'].append(gaussianGradientMagnitude)
        self.members['Texture'].append(differenceOfGaussians)
        
        self.members['Edge'].append(gaussianGradientMagnitude)
        self.members['Edge'].append(eigStructureTensor2d)
        #self.members['Edge'].append(eigHessianTensor2d)
        self.members['Edge'].append(laplacianOfGaussian)
        self.members['Edge'].append(differenceOfGaussians)
        self.members['Edge'].append(cannyEdge)
        
    def createList(self):
        resList = []
        for groupIndex, scaleList in irange(self.selection):
            for scaleIndex, selected in irange(scaleList):
                for feat in self.members[self.groupNames[groupIndex]]:
                    featFunc = feat[0]
                    argNames = feat[1]
                    if selected:
                        scaleValue = self.groupScaleValues[scaleIndex]
                        resList.append(LocalFeature(featFunc.__name__, [scaleValue for k in argNames], argNames , featFunc))
                        print featFunc.__name__, scaleValue    
        return resList
                    
gaussianGradientMagnitude = vm.gaussianGradientMagnitude, ['Sigma' ]
gaussianSmooth = vm.gaussianSmooth2d, ['Sigma']
structureTensor = vm.structureTensor, ['Sigma']
hessianMatrixOfGaussian = vm.hessianMatrixOfGaussian, ['Sigma']
eigStructureTensor2d = vm.eigStructureTensor2d, ['InnerScale', 'OuterScale']
laplacianOfGaussian = vm.laplacianOfGaussian, ['Sigma']
morphologicalOpening = lambda x,s: vm.discOpening(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
morphologicalClosing = lambda x,s: vm.discClosing(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
eigHessianTensor2d = vm.eigHessian2d, ['Sigma']
differenceOfGaussians = lambda x, s: vm.gaussianSmooth2d(x,s) - vm.gaussianSmooth2d(x,s/3*2), ['Sigma']
cannyEdge = lambda x, s: vm.cannyEdgeImage(x, s, 0, 1), ['Sigma']

identity = lambda x: x, []
identity[0].__name__ = "identity"

ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()

