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
import sys
from Queue import Queue as queue
from copy import copy
import os
import threading
import h5py
import h5py as tables # TODO: exchange tables with h5py
from core.utilities import irange, debug, irangeIfTrue

from gui.volumeeditor import DataAccessor as DataAccessor
from gui.volumeeditor import Volume as Volume

from core import activeLearning
from core import segmentationMgr

import vigra
at = vigra.arraytypes
    

class DataItemBase():
    """
    Data Base class, serves as an interface for the specialized data structures, e.g. images, multispectral, volume etc.  
    """
    #3D: important
    def __init__(self, fileName):
        self.fileName = str(fileName)
        self.Name = os.path.split(self.fileName)[1]
        self.hasLabels = False
        self.isTraining = True
        self.isTesting = False
        self.groupMember = []
        self.projects = []
        
        self.data = None
        self.labels = None
        self.dataKind = None
        self.dataType = []
        self.dataDimensions = 0
        self.thumbnail = None
        self.shape = ()
        self.channelDescription = []
        self.channelUsed = []
        
    def shape(self):
        if self.dataKind in ['rgb', 'multi', 'gray']:
            return self.shape[0:2]
        
    def loadData(self):
        self.data = "This is not an Image..."
    
    def unpackChannels(self):
        if self.dataKind in ['rgb']:
            return [ self.data[:,:,k] for k in range(0,3) ]
        elif self.dataKind in ['multi']:
            return [ self.data[:,:,k] for k in irangeIfTrue(self.channelUsed)]
        elif self.dataKind in ['gray']:
            return [ self.data ]   

class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
        self.dataDimensions = 2
        self.overlayImage = None
        self.dataVol = None
        self.prediction = None
        self.trainingF = None        
        self.featureM = None
        self.features = [] #features is an array of arrays of arrays etc. like this
                           #feature, channel, time
        self.history = None
        
    def loadData(self):
        fBase, fExt = os.path.splitext(self.fileName)
        if fExt == '.h5':
            f = h5py.File(self.fileName, 'r')
            g = f['volume']
            self.deserialize(g)
        else:
            self.data = DataImpex.loadImageData(self.fileName)
            self.labels = None
        #print "Shape after Loading and width",self.data.shape, self.data.width
        if self.dataVol is None:
            dataAcc = DataAccessor(self.data)
            self.dataVol = Volume()
            self.dataVol.data = dataAcc
            self.dataVol.labels = self.labels
        
   
    @classmethod
    def initFromArray(cls, dataArray, originalFileName):
        obj = cls(originalFileName)
        obj.dataVol = Volume()
        obj.dataVol.data = DataAccessor(dataArray, True)
        return obj
        
    def getTrainingMatrixRef(self):
        #TODO: time behaviour should be discussed !
        #also adapt feature computation when doing this(4D??)!
        if self.trainingF is None:
            tempF = []
            tempL = []
    
            tempd =  self.dataVol.labels.data[0, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = self.dataVol.labels.data[0,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                        
            for i_f, it_f in enumerate(self.features): #features
                for i_c, it_c in enumerate(it_f): #channels
                    for i_t, it_t in enumerate(it_c): #time
                        t = it_t.reshape((numpy.prod(it_t.shape[0:3]),it_t.shape[3]))
                        tempF.append(t[indices, :])
            
            self.trainingIndices = indices
            self.trainingL = tempL
            if len(tempF) > 0:
                self.trainingF = numpy.hstack(tempF)
            else:
                self.trainingF = None
        return self.trainingL, self.trainingF, self.trainingIndices
    
    def getTrainingMatrix(self):
        self.getTrainingMatrixRef()
        if self.trainingF is not None:
            return self.trainingL, self.trainingF, self.trainingIndices
        else:
            return None, None, None
            
    def updateTrainingMatrix(self, newLabels):
        #TODO: this method is crazy, make it less crazy
        for nl in newLabels:
            if nl.erasing == False:
                indic =  list(numpy.nonzero(nl.data))
                indic[0] = indic[0] + nl.offsets[0]
                indic[1] += nl.offsets[1]
                indic[2] += nl.offsets[2]
                indic[3] += nl.offsets[3]
                indic[4] += nl.offsets[4]
                
                loopc = 2
                count = 1
                indices = indic[-loopc]*count
                templ = list(self.dataVol.data.shape[1:-1])
                templ.reverse()
                for s in templ:
                    loopc += 1
                    count *= s
                    indices += indic[-loopc]*count
                
                mask = numpy.in1d(self.trainingIndices,indices)
                nonzero = numpy.nonzero(mask)[0]
                if len(nonzero) > 0:
                    self.trainingIndices = numpy.concatenate((numpy.delete(self.trainingIndices,nonzero),indices))
                    tempI = numpy.nonzero(nl.data)
                    tempL = nl.data[tempI]
                    tempL.shape += (1,)
                    temp2 = numpy.delete(self.trainingL,nonzero)
                    temp2.shape += (1,)
                    self.trainingL = numpy.vstack((temp2,tempL))
                    fm = self.getFeatureMatrix()
                    if fm is not None:
                        temp2 = numpy.delete(self.trainingF,nonzero, axis = 0)
                        if len(temp2.shape) == 1:
                            temp2.shape += (1,)
                            fm.shape += (1,)
                        self.trainingF = numpy.vstack((temp2,fm[indices,:]))
                else: #no intersection, just add everything...
                    self.trainingIndices = numpy.hstack((self.trainingIndices,indices))
                    tempI = numpy.nonzero(nl.data)
                    tempL = nl.data[tempI]
                    tempL.shape += (1,)
                    temp2 = self.trainingL
                    self.trainingL = numpy.vstack((temp2,tempL))
                    fm = self.getFeatureMatrix()
                    if fm is not None:
                        temp2 = self.trainingF
                        if len(temp2.shape) == 1:
                            temp2.shape += (1,)
                            fm.shape += (1,)
                        self.trainingF = numpy.vstack((temp2,fm[indices,:]))
            else: #erasing == True
                indic =  list(numpy.nonzero(nl.data))
                indic[0] = indic[0] + nl.offsets[0]
                indic[1] += nl.offsets[1]
                indic[2] += nl.offsets[2]
                indic[3] += nl.offsets[3]
                indic[4] += nl.offsets[4]
                
                loopc = 2
                count = 1
                indices = indic[-loopc]*count
                templ = list(self.dataVol.data.shape[1:-1])
                templ.reverse()
                for s in templ:
                    loopc += 1
                    count *= s
                    indices += indic[-loopc]*count
                
                mask = numpy.in1d(self.trainingIndices,indices) #get intersection
                nonzero = numpy.nonzero(mask)[0]
                if len(nonzero) > 0:
                    self.trainingIndices = numpy.delete(self.trainingIndices,nonzero)
                    self.trainingL  = numpy.delete(self.trainingL,nonzero)
                    self.trainingL.shape += (1,) #needed because numpy.delete is stupid
                    self.trainingF = numpy.delete(self.trainingF,nonzero, axis = 0)
                else: #no intersectoin, in erase mode just pass
                    pass             

            
    def getFeatureMatrixRef(self):
        if self.featureM is None:
            tempM = []
            for i_f, it_f in enumerate(self.features): #features
               for i_c, it_c in enumerate(it_f): #channels
                   for i_t, it_t in enumerate(it_c): #time
                       tempM.append(it_t.reshape(numpy.prod(it_t.shape[0:3]),it_t.shape[3]))

            if len(tempM) > 0:
                self.featureM = numpy.hstack(tempM)
            else:
                self.featureM = None
        return self.featureM      
    
    def getFeatureMatrix(self):
        self.getFeatureMatrixRef()
        if self.featureM is not None:
            return self.featureM
        else:
            return None
        
    def clearFeaturesAndTraining(self):
        self.trainingF = None
        self.trainingL = None
        self.featureM = None
        self.trainingIndices = None
                
    def getFeatureMatrixForViewState(self, vs):
        tempM = []
        for i_f, it_f in enumerate(self.features): #features
           for i_c, it_c in enumerate(it_f): #channels
               for i_t, it_t in enumerate(it_c): #time
                   ttt = []
                   ttt.append(it_t[vs[1],:,:,:].reshape(numpy.prod(it_t.shape[1:3]),it_t.shape[3]))
                   ttt.append(it_t[:,vs[2],:,:].reshape(numpy.prod((it_t.shape[0],it_t.shape[2])),it_t.shape[3]))
                   ttt.append(it_t[:,:,vs[3],:].reshape(numpy.prod(it_t.shape[0:2]),it_t.shape[3]))
                   tempM.append(numpy.vstack(ttt))            
        if len(tempM) > 0:
            featureM = numpy.hstack(tempM)
        else:
            featureM = None
        return featureM              
            
    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self.dataVol = None
        self.data = None
        
     
    def serialize(self, h5G):
        self.dataVol.serialize(h5G)
        if self.prediction is not None:
            self.prediction.serialize(h5G, 'prediction')
            
    def deserialize(self, h5G):
        self.dataVol = Volume.deserialize(h5G)
        if 'prediction' in h5G.keys():
            self.prediction = DataAccessor.deserialize(h5G, 'prediction')
            for p_i, item in enumerate(self.dataVol.labels.descriptions):
                item.prediction = (self.prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)

            margin = activeLearning.computeEnsembleMargin(self.prediction[:,:,:,:,:])*255.0
            self.dataVol.uncertainty = margin[:,:,:,:]
            seg = segmentationMgr.LocallyDominantSegmentation(self.prediction[:,:,:,:,:], 1.0)
            self.dataVol.segmentation = seg[:,:,:,:]
            
class DataMgr():
    """
    Manages Project structure and associated files, e.g. images volumedata
    """
    # does not unload data, maybe implement some sort of reference 
    # counting if memory scarceness manifests itself
    
    def __init__(self):
        self.dataItems = []            
        self.classifiers = []
        self.featureLock = threading.Semaphore(1) #prevent chaning of activeImage during thread stuff
        self.trainingVersion = 0
        self.featureVersion = 0
        self.dataItemsLoaded = []
        self.trainingF = None
               
    def append(self, dataItem, alreadyLoaded=False):
        self.dataItems.append(dataItem)
        self.dataItemsLoaded.append(alreadyLoaded)
        
    def clearDataList(self):
        self.dataItems = []
        self.dataFeatures = []
        self.labels = {}
        
    
    def buildTrainingMatrix(self):
        trainingF = []
        trainingL = []
        indices = []
        for item in self:
            trainingLabels, trainingFeatures, indic = item.getTrainingMatrixRef()
            if trainingFeatures is not None:
                indices.append(indic)
                trainingL.append(trainingLabels)
                trainingF.append(trainingFeatures)
            
        self.trainingL = trainingL
        self.trainingF = trainingF
        self.trainingIndices = indices     
    
    def getTrainingMatrix(self):
        if self.trainingVersion < self.featureVersion:
            self.clearFeaturesAndTraining()
        self.buildTrainingMatrix()
        self.trainingVersion =  self.featureVersion
            
        if len(self.trainingF) == 0:
            self.buildTrainingMatrix()
        
        if len(self.trainingF) > 0:
            trainingF = numpy.vstack(self.trainingF)
            trainingL = numpy.vstack(self.trainingL)
        
            return trainingF, trainingL
        else:
            print "######### empty Training Matrix ##########"
            return None, None
        
    
    def updateTrainingMatrix(self, num, newLabels):
        if len(self.trainingF) == 0 or self.trainingVersion < self.featureVersion:
            self.buildTrainingMatrix()        
        self[num].updateTrainingMatrix(newLabels)



    def buildFeatureMatrix(self):
        for item in self:
            item.getFeatureMatrix()
                    
    def clearFeaturesAndTraining(self):
        self.featureVersion += 1
        self.trainingF = None
        self.trainingL = None
        self.trainingIndices = None
        self.classifiers = []
        
        for index, item in enumerate(self):
            item.clearFeaturesAndTraining()
    
    def getDataList(self):
        return self.dataItems
        
    def dataItemsShapes(self):     
        return map(DataItemBase.shape, self)
        
        
    def __getitem__(self, ind):
        if not self.dataItemsLoaded[ind]:
            self.dataItems[ind].loadData()
            self.dataItemsLoaded[ind] = True
        return self.dataItems[ind]
    
    def __setitem__(self, ind, val):
        self.dataItems[ind] = val
        self.dataItemsLoaded[ind] = True
    
    def getIndexFromFileName(self, fileName):
        for k, dataItem in irange(self.dataItems):
            if fileName == dataItem.fileName:
                return k
        return False
    
    def remove(self, dataItemIndex):
        del self.dataItems[dataItemIndex]
        del self.dataItemsLoaded[dataItemIndex]
    
    def __len__(self):
        return len(self.dataItems)
    
    def serialize(self, h5grp):
        pass
        
    @staticmethod
    def deserialize(self):
        pass
        
        

class DataImpex(object):
    """
    Data Import/Export class 
    """
        
    @staticmethod
    def loadVolumeFromGroup(h5grp):
        di = DataItemImage

    
    @staticmethod
    def loadImageData(fileName):
        # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
        # the result of vigra.impex.readImage is numpy.ndarray? I don't know why... (see featureMgr compute)
        data = vigra.impex.readImage(fileName).swapaxes(0,1).view(numpy.ndarray)
        return data

        
        
        
    
    
        
        
        
        
        

                    
                    
                    
                
        
        


        
