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

import numpy
import threading as threading
import threading
import time
import sys
from core import jobMachine
from collections import deque
from core.utilities import irange
from core import dataMgr
import copy
import traceback

import vigra
at = vigra.arraytypes

from gui.volumeeditor import VolumeEditor as VolumeEditor

    
class FeatureMgr():
    """
    Manages selected features (merkmale) for classificator.
    """
    def __init__(self, dataMgr, featureItems=None):
        self.dataMgr = dataMgr
        self.featureSizes = []
        self.featureOffsets = []
        if featureItems is None:
            featureItems = []
        self.maxSigma = 0
        self.setFeatureItems(featureItems)
        self.featuresComputed = [False] * len(self.featureItems)
        self.parent_conn = None
        self.child_conn = None
        
        
    def setFeatureItems(self, featureItems):
        self.featureItems = featureItems
        self.featureSizes = []
        self.featureOffsets = []
        if len(featureItems) > 0:
            if self.dataMgr[0].dataVol.data.shape[1] > 1:
                #3D
                dimSel = 1
            else:
                #2D
                dimSel = 0
                
            numChannels = self.dataMgr[0].dataVol.data.shape[-1]
            totalSize = reduce(lambda x, y: x + y, [k.numOfOutputs[dimSel] for k in featureItems])
            for i, f in enumerate(featureItems):
                if f.args[0] > self.maxSigma:
                    self.maxSigma = f.args[0]

                if i != 0:
                    offset = reduce(lambda x, y: x + y, [k.numOfOutputs[dimSel] for k in featureItems[0:i]])
                else:
                    offset = 0 
                size = f.numOfOutputs[dimSel]
                self.featureSizes.append(size)
                self.featureOffsets.append(offset)
            try:
                for i, di in enumerate(self.dataMgr):
                    if di.featureCacheDS is None:
                        di._featureM = numpy.zeros(di.dataVol.data.shape + (totalSize,),'float32')
                    else:
                        di.featureCacheDS.resize(di.dataVol.data.shape + (totalSize,))
                        di._featureM = di.featureCacheDS
                    di.featureBlockAccessor = dataMgr.BlockAccessor(di._featureM, 128)

            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                return False
        else:
            print "setFeatureItems(): no features selected"
        return True
    
    def prepareCompute(self, dataMgr):
        self.dataMgr = dataMgr

        self.featureProcess = FeatureThread(self, dataMgr)

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
        
    def setArguments(self, args):
        self.args = args
    
    def serialize(self, h5grp):
        h5grp.create_dataset('name',data=self.name)
        h5grp.create_dataset('argNames',data=self.argNames)
        h5grp.create_dataset('numOfOutputs',data=self.numOfOutputs)
        h5grp.create_dataset('featureFunktor',data=self.featureFunktor.__name__)
        
        try:
            dummy = self.featureFunktor.__module__
            vigraFunktor = False
        except AttributeError:
            vigraFunktor = True
            
        h5grp.create_dataset('vigraFunktor',data=vigraFunktor)
        
    @classmethod
    def deserialize(cls, h5grp):
        name = h5grp['name']
        argNames = h5grp['argNames'].value
        numOfOutputs = h5grp['numOfOutputs'].value
        featureFunktor = h5grp['featureFunktor'].value
        vigraFunktor = h5grp['vigraFunktor'].value
        
        # TODO This is quite hacky, but didn found better way.
        # This approach of course will not work for other featurers 
        # than filters
        if vigraFunktor:
            funktor = eval('vigra.filters.' + featureFunktor)
        else:
            funktor = eval(featureFunktor)
            
        return cls(name, argNames, numOfOutputs, funktor)
    
    def __call__(self, channel):
        # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
        # the result of featureFunktor is numpy.ndarray and NOT a vigra type!? I don't know why... (see dateMgr loadData)
        result = []
        for i in range(channel.shape[0]):
            if channel.shape[1] > 1: #3D Case
                temp = self.featureFunktor(channel[i, :, :, :], * self.args)
                if len(temp.shape) == 3:
                    result.append(temp.reshape(temp.shape + (1,)))
                else:
                    result.append(temp)
            else: #2D
                temp = self.featureFunktor(channel[i, 0, :, :], * self.args)
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
    def __init__(self, featureMgr, dataMgr):
        self.count = 0
        self.jobs = 0
        self.featureMgr = featureMgr
        self.dataMgr = dataMgr
        self.computeNumberOfJobs()
    
    def computeNumberOfJobs(self):
        for image in self.dataMgr:
            self.jobs += image.dataVol.data.shape[-1] * len(self.featureMgr.featureItems) * image.featureBlockAccessor.blockCount

class FeatureThread(threading.Thread, FeatureParallelBase):
    def __init__(self, featureMgr, datMgr):
        FeatureParallelBase.__init__(self, featureMgr, datMgr)
        threading.Thread.__init__(self)  
        self.jobMachine = jobMachine.JobMachine()    
        self.printLock = threading.Lock()


    def calcFeature(self, image, offset, size, feature, blockNum):
        for c_ind in range(image.dataVol.data.shape[-1]):
            try:
                #TODO: ceil(blockNum,feature.args[0]*3) means sigma*3, make nicer
                overlap = int(numpy.ceil(feature.args[0]*3))
                bounds = image.featureBlockAccessor.getBlockBounds(blockNum, overlap)
                result = feature(image.dataVol.data[:,bounds[0]:bounds[1],bounds[2]:bounds[3],bounds[4]:bounds[5], c_ind])
                bounds1 = image.featureBlockAccessor.getBlockBounds(blockNum,0)
                
                sx = bounds1[0]-bounds[0]
                ex = bounds[1]-bounds1[1]
                sy = bounds1[2]-bounds[2]
                ey = bounds[3]-bounds1[3]
                sz = bounds1[4]-bounds[4]
                ez = bounds[5]-bounds1[5]
                
                ex = result[0].shape[0] - ex
                ey = result[0].shape[1] - ey
                ez = result[0].shape[2] - ez
                
                for t in range(len(result)):
                    tres = result[t][sx:ex,sy:ey,sz:ez]
                    image.featureBlockAccessor[t,bounds1[0]:bounds1[1],bounds1[2]:bounds1[3],bounds1[4]:bounds1[5],c_ind,offset:offset+size] = tres
            except Exception, e:
                print "########################## exception in FeatureThread ###################"
                print e
                traceback.print_exc(file=sys.stdout)
            self.count += 1
            # print "Feature Job ", self.count, "/", self.jobs, " finished"
        
    
    def run(self):
        for image in self.dataMgr:
            jobs = []
            for blockNum in range(image.featureBlockAccessor.blockCount):
                for i, feature in enumerate(self.featureMgr.featureItems):
                    job = jobMachine.IlastikJob(FeatureThread.calcFeature, [self, image, self.featureMgr.featureOffsets[i], self.featureMgr.featureSizes[i], feature, blockNum])
                    jobs.append(job)
                    
            self.jobMachine.process(jobs)

    
#    def calcFeature(self, image, offset,size, feature):
#        for c_ind in range(image.dataVol.data.shape[-1]):
#            print image.dataVol.data.shape[0:5], str(feature)
#            result = feature(image.dataVol.data[:,:,:,:,c_ind])
#            try:
#                image._featureM[:,:,:,:,c_ind,offset:offset+size] = result
#            except Exception as e:
#                print e
#            self.count += 1
#
#        
#    
#    def run(self):
#        for image in self.dataMgr:
#            self.resultImage = deque()
#            jobs = []
#                            
#            for i, feature in enumerate(self.featureMgr.featureItems):
#                job = jobMachine.IlastikJob(FeatureThread.calcFeature, [self, image, self.featureMgr.featureOffsets[i], self.featureMgr.featureSizes[i], feature])
#                jobs.append(job)
#            self.jobMachine.process(jobs)
    

###########################################################################
###########################################################################
class FeatureGroups(object):
    """
    Groups LocalFeature objects to predefined feature sets, selectable in the gui
    initializes the LucalFeature objects with vigra functors and needed
    calculation parameters (for example sigma)
    """
    def __init__(self):
        self.groupNames = ['Color', 'Texture', 'Edge', 'Orientation']#, 'ChannelRep']
        self.groupScaleNames = ['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        self.selection = [ [False for k in self.groupScaleNames] for j in self.groupNames ]
        self.groupScaleValues = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        
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

        #self.members['ChannelRep'].append(channels4)

    def createList(self):
        resList = []
        for groupIndex, scaleList in irange(self.selection):
            for scaleIndex, selected in irange(scaleList):
                for feature in self.members[self.groupNames[groupIndex]]:
                    if selected:
                        scaleValue = self.groupScaleValues[scaleIndex]
                        #TODO: This should be replaced by somethon more genric
                        fc = copy.copy(feature)
                        fc.setArguments([scaleValue for k in fc.argNames])
                        resList.append(fc)
        return resList
    
def myHessianOfGaussian(x, s):
    if x.ndim == 2:
        return vigra.filters.hessianOfGaussian2D(x, s)
    elif x.ndim == 3:
        return vigra.filters.hessianOfGaussian3D(x, s)
    else:
        print "Error: Dimension must be 2 or 3 dimensional"
        return None
    
def myHessianOfGaussianEigenvalues(x, s):
    if x.ndim == 2:
        return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian2D(x, s))
    elif x.ndim == 3:
        return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(x, s))
    else:
        print "Error: Dimension must be 2 or 3 dimensional"
        return None
def myStructureTensorEigenvalues(x, s1, s2):
    return vigra.filters.structureTensorEigenvalues(x, s1, s1 / 2.0)
    


def Channels4(x,s1):
    if len(x.shape) == 3: #3D
        res = numpy.zeros(x.shape + (4*4,),'float32')
        for index, i in enumerate(range(80,190,32)):
            center = numpy.exp(-(x-i)**2 / (11)**2)
            res[:,:,:,index*3] = vigra.filters.gaussianSmoothing(center, s1).view(numpy.ndarray)
            res[:,:,:,index*3+1:index*3+4] = vigra.filters.structureTensorEigenvalues(center, s1, s1 / 2.0)
    else:#2D
        res = numpy.zeros(x.shape + (4*3,),'float32')
        for index, i in enumerate(range(80,190,32)):
            center = numpy.exp(-(x-i)**2 / (11)**2)
            res[:,:,index*2] = vigra.filters.gaussianSmoothing(center, s1).view(numpy.ndarray)
            res[:,:,index*2+1:index*2+3] = vigra.filters.structureTensorEigenvalues(center, s1, s1 / 2.0)

    return res
        


def svenSpecial(x):
    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
    if numpy.max(res) == 0:
        res[:, :] = 3000
        return res
    else:
        return vigra.filters.distanceTransform2D(res)

def svenSpecialSpecial(x):
    temp = numpy.zeros(x.shape + (4,))
    
    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
    if numpy.max(res) == 0:
        res[:, :] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:, :, 0] = res

    res = vigra.analysis.cannyEdgeImage(x, 2.2, 0.42, 1)
    if numpy.max(res) == 0:
        res[:, :] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:, :, 1] = res

    res = vigra.analysis.cannyEdgeImage(x, 1.9, 0.38, 1)
    if numpy.max(res) == 0:
        res[:, :] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:, :, 2] = res

    res = vigra.analysis.cannyEdgeImage(x, 1.8, 0.38, 1)
    if numpy.max(res) == 0:
        res[:, :] = 3000
    else:
        res = vigra.filters.distanceTransform2D(res)
    temp[:, :, 3] = res


    return temp


gaussianGradientMagnitude = LocalFeature('Gradient Magnitude', ['Sigma' ], (1, 1), vigra.filters.gaussianGradientMagnitude)
gaussianSmooth = LocalFeature('Gaussian', ['Sigma' ], (1, 1), vigra.filters.gaussianSmoothing)
structureTensor = LocalFeature('Structure Tensor', ['InnerScale', 'OuterScale'], (3, 6), vigra.filters.structureTensor)
hessianMatrixOfGaussian = LocalFeature('Hessian', ['Sigma' ], (3, 6), myHessianOfGaussian)
eigStructureTensor2d = LocalFeature('Eigenvalues of Structure Tensor', ['InnerScale', 'OuterScale'], (2, 3), myStructureTensorEigenvalues)
laplacianOfGaussian = LocalFeature('LoG', ['Sigma' ], (1, 1), vigra.filters.laplacianOfGaussian)
morphologicalOpening = LocalFeature('Morph Opening', ['Sigma' ], (1, 1), lambda x, s: vigra.morphology.discOpening(x.astype(numpy.uint8), int(s * 1.5 + 1)))
morphologicalClosing = LocalFeature('Morph Colosing', ['Sigma' ], (1, 1), lambda x, s: vigra.morphology.discClosing(x.astype(numpy.uint8), int(s * 1.5 + 1)))
eigHessianTensor2d = LocalFeature('Eigenvalues of Hessian', ['Sigma' ], (2, 3), myHessianOfGaussianEigenvalues)
differenceOfGaussians = LocalFeature('DoG', ['Sigma' ], (1, 1), lambda x, s: vigra.filters.gaussianSmoothing(x, s) - vigra.filters.gaussianSmoothing(x, s / 3 * 2))
cannyEdge = LocalFeature('Canny', ['Sigma' ], (1, 1), lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1))
svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 1', [], (1, 1), lambda x: svenSpecial(x))
svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 2', [], (1, 1), lambda x: svenSpecialSpecial(x))
channels4 = LocalFeature('Channels4', ['Sigma' ], (4*3, 4*4), lambda x, s: Channels4(x,s))

ilastikFeatureGroups = FeatureGroups()
ilastikFeatures = ilastikFeatureGroups.createList()


