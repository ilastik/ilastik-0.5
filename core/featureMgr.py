# -*- coding: utf-8 -*-
import numpy
import dummy_threading as threading
#import threading
#import multiprocessing
import time
import sys
#sys.path.append("..")
from core.utilities import irange

import vigra
at = vigra.arraytypes

from gui.volumeeditor import VolumeEditor as VolumeEditor

    
class FeatureMgr():
    """
    Manages selected features (merkmale) for classificator.
    """
    def __init__(self, featureItems=[]):
        self.featureItems = featureItems
        self.featuresComputed = [False] * len(self.featureItems)
        self.parent_conn = None
        self.child_conn = None
        self.featureProcessList = []
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        
    def prepareCompute(self, dataMgr):
        self.dataMgr = dataMgr

        self.featureProcessList = [[] for i in range(len(dataMgr))]

        self.featureProcess = FeatureThread(self.featureItems, dataMgr)

        return self.featureProcess.jobs
    
    def triggerCompute(self):
        self.featureProcess.start()
    
    def getCount(self):
        return self.featureProcess.count
          
    def joinCompute(self, dataMgr):
        self.featureProcess.join()  
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
        # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
        # the result of featureFunktor is numpy.ndarray and NOT a vigra type!? I don't know why... (see dateMgr loadData)
        result = []
        for i in range(channel.shape[0]):
            if channel.shape[1] > 1: #3D Case
                temp = self.featureFunktor(channel[i,:,:,:].astype(numpy.float32), * self.args)
                if len(temp.shape) == 3:
                    result.append( temp.reshape( temp.shape + (1,)) )
                else:
                    result.append( temp )
            else: #2D
                temp = self.featureFunktor(channel[i,0,:,:].astype(numpy.float32), * self.args)
                if len(temp.shape) == 2:
                    result.append(temp.reshape((1,) + temp.shape + (1,)))
                else: #more dimensional filter, we only need to add the 3D dimension
                    result.append(temp.reshape((1,) + temp.shape))
        
#        tempres = result[0].view(numpy.ndarray).copy()
#        tempres.shape = (1,) + tempres.shape
#        
#        from spyderlib.utils.qthelpers import qapplication
#        
#        for f_c in range(tempres.shape[-1]):
#            temp = tempres[:,:,:,:,f_c];
#            temp = (((temp - temp.min()) / temp.max())*255).astype(numpy.uint8)
#      
#            app = qapplication()
#            
#            dialog = VolumeEditor(temp,name= self.name + str(f_c))
#            dialog.show()

        
        return result

    def __str__(self):
        return '%s: %s' % (self.name , ', '.join(["%s = %f" % (x[0], x[1]) for x in zip(self.arg_names, self.args)]))


class FeatureParallelBase(object):
    def __init__(self, featureItems, dataMgr):
        self.count = 0
        self.jobs = 0
        self.featureItems = featureItems
        self.dataMgr = dataMgr
        self.computeNumberOfJobs()
    
    def computeNumberOfJobs(self):
        for image in self.dataMgr:
            self.jobs += image.dataVol.data.shape[-1] * len(self.featureItems)

class FeatureThread(threading.Thread, FeatureParallelBase):
    def __init__(self, featureItems, datMgr):
        FeatureParallelBase.__init__(self, featureItems, datMgr)
        threading.Thread.__init__(self)  
    
    def run(self):
        imageFeatures = []
        for image in self.dataMgr:
            resultImage = []
            for feature in self.featureItems:
                result = []
                for c_ind in range(image.dataVol.data.shape[-1]):
                    print image.dataVol.data.shape[0:5], str(feature)
                    result.append(feature.compute(image.dataVol.data[:,:,:,:,c_ind]))
                    self.count += 1
                resultImage.append(result)
            imageFeatures.append(resultImage)
            
        for index, feat in enumerate(imageFeatures):
            self.dataMgr[index].features = feat
    

###########################################################################
###########################################################################
class FeatureGroups(object):
    """
    Groups LocalFeature objects to predefined feature sets, selectable in the gui
    initializes the LucalFeature objects with vigra functors and needed
    calculation parameters (for example sigma)
    """
    def __init__(self):
        self.groupNames = ['Color', 'Texture', 'Edge', 'Orientation', 'SvenSpecial']
        self.groupScaleNames = ['Tiny', 'Small', 'Medium', 'Large', 'Huge']
        self.selection = [ [False for k in self.groupScaleNames] for j in self.groupNames ]
        self.groupScaleValues = [0.2, 0.5, 1, 1.5, 3.5]
        
        self.members = {}
        for g in self.groupNames:
            self.members[g] = []        
        self.createMemberFeatures()
        
    def createMemberFeatures(self):
        #self.members['Color'].append(identity)
        self.members['Color'].append(gaussianSmooth)
        #self.members['Color'].append(location)
        
        #self.members['Texture'].append(structureTensor)
        self.members['Texture'].append(eigHessianTensor2d)
        self.members['Texture'].append(eigStructureTensor2d)
        self.members['Texture'].append(gaussianGradientMagnitude)
        #self.members['Texture'].append(morphologicalOpening)
        #self.members['Texture'].append(morphologicalClosing)

        self.members['Edge'].append(laplacianOfGaussian)
        self.members['Edge'].append(differenceOfGaussians)
        
        self.members['Orientation'].append(hessianMatrixOfGaussian)
        self.members['Orientation'].append(structureTensor)
        
        self.members['SvenSpecial'].append(svenSpecialWaveFrontDistance)
        
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
    
def myHessianOfGaussian(x,s):
    if x.ndim == 2:
        return vigra.filters.hessianOfGaussian2D(x,s)
    elif x.ndim == 3:
        return vigra.filters.hessianOfGaussian3D(x,s)
    else:
        print "Error: Dimension must be 2 or 3 dimensional"
        return None
    
def myHessianOfGaussianEigenvalues(x,s):
    if x.ndim == 2:
        return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian2D(x,s))
    elif x.ndim == 3:
        return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(x,s))[:,:,:,0]
    else:
        print "Error: Dimension must be 2 or 3 dimensional"
        return None
def myStructureTensorEigenvalues(x,s1,s2):
    return vigra.filters.structureTensorEigenvalues(x,s1,s1/2.0)
    

def svenSpecial(x):
    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
    if numpy.max(res) == 0:
        res[:,:] = 3000
        return res
    else:
        return vigra.filters.distanceTransform2D(res)

gaussianGradientMagnitude = vigra.filters.gaussianGradientMagnitude, ['Sigma' ]
gaussianSmooth = vigra.filters.gaussianSmoothing, ['Sigma']
structureTensor = vigra.filters.structureTensor, ['InnerScale', 'OuterScale']
hessianMatrixOfGaussian = myHessianOfGaussian, ['Sigma']
eigStructureTensor2d = myStructureTensorEigenvalues, ['InnerScale', 'OuterScale']
laplacianOfGaussian = vigra.filters.laplacianOfGaussian, ['Sigma']
morphologicalOpening = lambda x,s: vigra.morphology.discOpening(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
morphologicalClosing = lambda x,s: vigra.morphology.discClosing(x.astype(numpy.uint8),int(s*1.5+1)), ['Sigma']
eigHessianTensor2d = myHessianOfGaussianEigenvalues, ['Sigma']
differenceOfGaussians = lambda x, s: vigra.filters.gaussianSmoothing(x,s) - vigra.filters.gaussianSmoothing(x,s/3*2), ['Sigma']
cannyEdge = lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1), ['Sigma']
svenSpecialWaveFrontDistance = lambda x: svenSpecial(x), []

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

