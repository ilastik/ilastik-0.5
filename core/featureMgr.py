# -*- coding: utf-8 -*-
import numpy
import threading as threading
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
    
    def __init__(self, name, argNames, numOfOutputs, featureFunktor):
        FeatureBase.__init__(self)
        self.name = name
        self.argNames = argNames
        self.numOfOutputs = numOfOutputs
        self.featureFunktor = featureFunktor
        
    def setArguments(self,args):
        self.args = args
    
    def __call__(self, channel):
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
        return '%s: %s' % (self.name , ', '.join(["%s = %f" % (x[0], x[1]) for x in zip(self.argNames, self.args)]))


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
                    result.append(feature(image.dataVol.data[:,:,:,:,c_ind]))
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
        self.groupNames = ['Color', 'Texture', 'Edge', 'Orientation']
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
        
        #self.members['SvenSpecial'].append(svenSpecialWaveFrontDistance)
        #self.members['SvenSpecial___Special'].append(svenSpecialWaveFrontDistance)
        
    def createList(self):
        resList = []
        for groupIndex, scaleList in irange(self.selection):
            for scaleIndex, selected in irange(scaleList):
                for feature in self.members[self.groupNames[groupIndex]]:
                    if selected:
                        scaleValue = self.groupScaleValues[scaleIndex]
                        #TODO: This should be replaced by somethon more genric
                        feature.setArguments([scaleValue for k in feature.argNames])
                        resList.append(feature)
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
        return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(x,s))
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

def svenSpecialSpecial(x):
    temp = numpy.zeros(x.shape + (4,))
    
    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
    if numpy.max(res) == 0:
        res[:,:] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:,:,0] = res

    res = vigra.analysis.cannyEdgeImage(x, 2.2, 0.42, 1)
    if numpy.max(res) == 0:
        res[:,:] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:,:,1] = res

    res = vigra.analysis.cannyEdgeImage(x, 1.9, 0.38, 1)
    if numpy.max(res) == 0:
        res[:,:] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:,:,2] = res

    res = vigra.analysis.cannyEdgeImage(x, 1.8, 0.38, 1)
    if numpy.max(res) == 0:
        res[:,:] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:,:,3] = res


    return temp


gaussianGradientMagnitude = LocalFeature('Gradient Magnitude', ['Sigma' ], (1,1), vigra.filters.gaussianGradientMagnitude)
gaussianSmooth = LocalFeature('Gaussian', ['Sigma' ], (1,1), vigra.filters.gaussianSmoothing)
structureTensor = LocalFeature('Structure Tensor', ['InnerScale', 'OuterScale'], (3,6), vigra.filters.structureTensor)
hessianMatrixOfGaussian = LocalFeature('Hessian', ['Sigma' ], (3,6), myHessianOfGaussian)
eigStructureTensor2d = LocalFeature('Eigenvalues of Structure Tensor', ['InnerScale', 'OuterScale'], (2,3), myStructureTensorEigenvalues)
laplacianOfGaussian = LocalFeature('LoG', ['Sigma' ], (1,1), vigra.filters.laplacianOfGaussian)
morphologicalOpening = LocalFeature('Morph Opening', ['Sigma' ], (1,1), lambda x,s: vigra.morphology.discOpening(x.astype(numpy.uint8),int(s*1.5+1)) )
morphologicalClosing = LocalFeature('Morph Colosing', ['Sigma' ], (1,1), lambda x,s: vigra.morphology.discClosing(x.astype(numpy.uint8),int(s*1.5+1)))
eigHessianTensor2d = LocalFeature('Eigenvalues of Hessian', ['Sigma' ], (2,3), myHessianOfGaussianEigenvalues)
differenceOfGaussians = LocalFeature('DoG', ['Sigma' ], (1,1), lambda x, s: vigra.filters.gaussianSmoothing(x,s) - vigra.filters.gaussianSmoothing(x,s/3*2))
cannyEdge = LocalFeature('Canny', ['Sigma' ], (1,1), lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1))
svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 1', [], (1,1), lambda x: svenSpecial(x))
svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 2', [], (1,1), lambda x: svenSpecialSpecial(x))
                                                        

ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()

