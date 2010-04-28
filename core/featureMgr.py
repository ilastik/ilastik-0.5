import numpy
import threading 
import multiprocessing
import time
import sys
#sys.path.append("..")
from core.utilities import irange

import vigra
import vigra.convolution
at = vigra.arraytypes

    
class FeatureMgr():
    """
    Manages selected features (merkmale) for classificator.
    """
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
        for dataIndex in xrange(len(dataMgr)):   
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
    """
    Interface for features (merkmale), at the moment only implemented by LocalFeature
    """
    def __init__(self):
        self.featureFunktor = None
   
    def compute(self, channel):
        return None  
    
class LocalFeature(FeatureBase):
    """
    Implements features that are calculated by some functor
    """
    #3D: important if using  octree optimization in the future
    
    def __init__(self, name, args, arg_names, featureFunktor):
        FeatureBase.__init__(self)
        self.name = featureFunktor.__name__
        self.args = args
        self.arg_names = arg_names
        self.featureFunktor = featureFunktor
    
    def compute(self, channel):
        print channel.shape
        # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
        # the result of featureFunktor is numpy.ndarray and NOT a vigra type!? I don't know why... (see dateMgr loadData)
        return at.Image(self.featureFunktor(channel, * self.args))

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
        #3D: might be important in the future          
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
    """
    Groups LocalFeature objects to predefined feature sets, selectable in the gui
    initializes the LucalFeature objects with vigra functors and needed
    calculation parameters (for example sigma)
    """
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
        #self.members['Color'].append(location)
        
        self.members['Texture'].append(structureTensor)
        self.members['Texture'].append(eigHessianTensor2d)
        self.members['Texture'].append(eigStructureTensor2d)
        #self.members['Texture'].append(hessianMatrixOfGaussian)
        #self.members['Texture'].append(laplacianOfGaussian)
        #self.members['Texture'].append(morphologicalOpening)
        #self.members['Texture'].append(morphologicalClosing)
        self.members['Texture'].append(gaussianGradientMagnitude)
        #self.members['Texture'].append(differenceOfGaussians)
        
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

gaussianGradientMagnitude = vigra.convolution.gaussianGradientMagnitude, ['Sigma' ]
gaussianSmooth = vigra.filters.gaussianSmoothing, ['Sigma']
structureTensor = vigra.convolution.structureTensor, ['Sigma']
hessianMatrixOfGaussian = vigra.convolution.hessianMatrixOfGaussian, ['Sigma']
eigStructureTensor2d = vigra.filters.structureTensorEigenvalues, ['InnerScale', 'OuterScale']
laplacianOfGaussian = vigra.convolution.laplacianOfGaussian, ['Sigma']
morphologicalOpening = lambda x,s: vigra.morphology.discOpening(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
morphologicalClosing = lambda x,s: vigra.morphology.discClosing(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
eigHessianTensor2d = vigra.filters.hessianOfGaussianEigenvalues, ['Sigma']
differenceOfGaussians = lambda x, s: vigra.filters.gaussianSmoothing(x,s) - vigra.filters.gaussianSmoothing(x,s/3*2), ['Sigma']
cannyEdge = lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1), ['Sigma']

def location_(x,s):
    X, Y = numpy.meshgrid(range(-x.shape[1]/2, x.shape[1]/2), range(-x.shape[0]/2, x.shape[0]/2))
    X.shape = X.shape + (1,)
    Y.shape = Y.shape + (1,)
    return vigra.Image(numpy.concatenate((X,Y),axis=2),numpy.float32)

location = (location_,['Sigma'])

identity = lambda x: x, []
identity[0].__name__ = "identity"

#from scipy import linalg
def orientation(x,s):
    st = vigra.convolution.structureTensor(x,s,s)
    for x in xrange(st.shape[0]):
        for y in xrange(st.shape[1]):
            pass
            # dummy, ev = linalg.eig(numpy.array([st[x,y,0],st[x,y,1],[st[x,y,1],st[x,y,2]]]))
                                                                        

ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()

