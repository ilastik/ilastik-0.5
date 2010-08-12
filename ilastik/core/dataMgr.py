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
from utilities import irange, debug, irangeIfTrue
try:
    from PyQt4 import QtGui
    have_qt = True
except:
    have_qt = False

from ilastik.core.volume import DataAccessor as DataAccessor
from ilastik.core.volume import Volume as Volume

from ilastik.core import activeLearning
from ilastik.core import segmentationMgr
from ilastik.core import overlayMgr

import traceback
import vigra
at = vigra.arraytypes
    
    
#def testfunc(a,b):
#    return numpy.unravel_index(a,b)
    
def unravelIndices(indices, shape):
    if len(indices.shape) == 1:
        indices.shape = indices.shape + (1,)
    try:
        ti =  numpy.apply_along_axis(numpy.unravel_index, 1, indices , shape)
    except Exception, e:
        print e
        print indices
        print shape
    return ti    


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


class BlockAccessor():
    def __init__(self, data, blockSize = None):
        self.data = data
	if blockSize is None:
		max = int(numpy.max(self.data.shape[1:4]))
		if max > 128:
			self.blockSize = blockSize = 128
		else:
			self.blockSize = blockSize = max / 2
	else:
		self.blockSize = blockSize
        
        self.cX = int(numpy.ceil(1.0 * data.shape[1] / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cXend = data.shape[1] % self.blockSize
        if self.cXend < self.blockSize / 3 and self.cX > 1:
            self.cX -= 1
        else:
            self.cXend = 0
                
        self.cY = int(numpy.ceil(1.0 * data.shape[2] / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cYend = data.shape[2] % self.blockSize
        if self.cYend < self.blockSize / 3 and self.cY > 1:
            self.cY -= 1
        else:
            self.cYend = 0

        self.cZ = int(numpy.ceil(1.0 * data.shape[3] / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cZend = data.shape[3] % self.blockSize
        if self.cZend < self.blockSize / 3 and self.cZ > 1:
            self.cZ -= 1
        else:
            self.cZend = 0

        self.blockCount = self.cX * self.cY * self.cZ
        self.lock = threading.Lock()
        if issubclass(self.data.__class__, numpy.ndarray):
            self.fileBacked = False
        else:
            self.fileBacked = True
        
        
    def getBlockBounds(self, blockNum, overlap):
        z = int(numpy.floor(blockNum / (self.cX*self.cY)))
        rest = blockNum % (self.cX*self.cY)
        y = int(numpy.floor(rest / self.cX))
        x = rest % self.cX
        
        startx = max(0, x*self.blockSize - overlap) 
        endx = min(self.data.shape[1], (x+1)*self.blockSize + overlap)
        if x+1 >= self.cX:
            endx = self.data.shape[1]
        
        starty = max(0, y*self.blockSize - overlap)
        endy = min(self.data.shape[2], (y+1)*self.blockSize + overlap) 
        if y+1 >= self.cY:
            endy = self.data.shape[2]
    
        startz = max(0, z*self.blockSize - overlap)
        endz = min(self.data.shape[3], (z+1)*self.blockSize + overlap)
        if z+1 >= self.cZ:
            endz = self.data.shape[3]
        
        return [startx,endx,starty,endy,startz,endz]

    def __getitem__(self, args):
        if self.fileBacked is False:
            return self.data[args]
        else:
            self.lock.acquire()
            temp =  self.data[args]
            self.lock.release()
            return temp

    def __setitem__(self, args, data):
        if self.fileBacked is False:
            self.data[args] = data
        else:
            self.lock.acquire()
            self.data[args] = data
            self.lock.release()
            
class BlockAccessor2D():
    def __init__(self, data, blockSize = 128):
        self.data = data
        self.blockSize = blockSize

        self.cX = int(numpy.ceil(1.0 * data.shape[0] / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cXend = data.shape[0] % self.blockSize
        if self.cXend < self.blockSize / 3 and self.cX > 1:
            self.cX -= 1
        else:
            self.cXend = 0

        self.cY = int(numpy.ceil(1.0 * data.shape[1] / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cYend = data.shape[1] % self.blockSize
        if self.cYend < self.blockSize / 3 and self.cY > 1:
            self.cY -= 1
        else:
            self.cYend = 0


        self.blockCount = self.cX * self.cY
        self.lock = threading.Lock()
        if issubclass(self.data.__class__, numpy.ndarray):
            self.fileBacked = False
        else:
            self.fileBacked = True


    def getBlockBounds(self, blockNum, overlap):
        z = int(numpy.floor(blockNum / (self.cX*self.cY)))
        rest = blockNum % (self.cX*self.cY)
        y = int(numpy.floor(rest / self.cX))
        x = rest % self.cX

        startx = max(0, x*self.blockSize - overlap)
        endx = min(self.data.shape[0], (x+1)*self.blockSize + overlap)
        if x+1 >= self.cX:
            endx = self.data.shape[0]

        starty = max(0, y*self.blockSize - overlap)
        endy = min(self.data.shape[1], (y+1)*self.blockSize + overlap)
        if y+1 >= self.cY:
            endy = self.data.shape[1]


        return [startx,endx,starty,endy]


    def __getitem__(self, args):
        if self.fileBacked is False:
            return self.data[args]
        else:
            self.lock.acquire()
            temp =  self.data[args]
            self.lock.release()
            return temp
            
    def __setitem__(self, args, data):
        if self.fileBacked is False:
            self.data[args] = data
        else:
            self.lock.acquire()
            self.data[args] = data
            self.lock.release()

class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
        self.dataDimensions = 2
        self.overlayImage = None
        self.dataVol = None
        self.prediction = None
        self.features = [] 
        self._featureM = None
        
        self.trainingF = numpy.zeros((0), 'float32')      
        self.trainingL = numpy.zeros((0, 1), 'uint8')
        self.trainingIndices = numpy.zeros((0, 1), 'uint32')
        
        self.seedL = numpy.zeros((0, 1), 'uint8')
        self.seedIndices = numpy.zeros((0, 1), 'uint32')
        
        self.history = None
        self.featureCacheDS = None
        self.featureBlockAccessor = None
        self.segmentationWeights = None
        
        self.overlayMgr = overlayMgr.OverlayMgr()
        
    def loadData(self):
        fBase, fExt = os.path.splitext(self.fileName)
        if fExt == '.h5':
            f = h5py.File(self.fileName, 'r')
            g = f['volume']
            self.deserialize(g)
        else:
            data = DataImpex.loadImageData(self.fileName)
            dataAcc = DataAccessor(data)
            self.dataVol = Volume(dataAcc)        
   
    @classmethod
    def initFromArray(cls, dataArray, originalFileName):
        obj = DataItemImage(originalFileName)
        obj.dataVol = Volume(DataAccessor(dataArray, True))
        return obj
        
        
    def getTrainingMforInd(self, ind):
#                        featureShape = self._featureM.shape[0:4]
#                        URI =  unravelIndices(indices, featureShape)
#                        tempfm = self._featureM[URI[:,0],URI[:,1],URI[:,2],URI[:,3],:]
#                        tempfm.shape = (tempfm.shape[0],) + (tempfm.shape[1]*tempfm.shape[2],)
        featureShape = self._featureM.shape[0:4]
        URI =  unravelIndices(ind, featureShape)
        if issubclass(self._featureM.__class__,numpy.ndarray): 
            trainingF = self._featureM[URI[:,0],URI[:,1],URI[:,2],URI[:,3],:]
        else:
            print ind.shape
            print self._featureM.shape
            trainingF = numpy.zeros((ind.shape[0],) + (self._featureM.shape[4],self._featureM.shape[5],), 'float32')
            for i in range(URI.shape[0]): 
                trainingF[i,:,:] = self._featureM[URI[i,0],URI[i,1],URI[i,2],URI[i,3],:]
        trainingF.shape = (trainingF.shape[0],) + (trainingF.shape[1]*trainingF.shape[2],)
        return trainingF
        
    def getTrainingMatrixRef(self):
        if len(self.trainingF) == 0 and self._featureM is not None:
            tempF = []
            tempL = []
    
            tempd =  self.dataVol.labels.data[:, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = self.dataVol.labels.data[:,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                                   
            self.trainingIndices = indices
            self.trainingL = tempL
            if len(indices) > 0:
                self.trainingF = self.getTrainingMforInd(indices)
            else:
                self.trainingF = None
        return self.trainingL, self.trainingF, self.trainingIndices
    
    def getTrainingMatrix(self):
        self.getTrainingMatrixRef()
        if len(self.trainingF) != 0:
            return self.trainingL, self.trainingF, self.trainingIndices
        else:
            return None, None, None
    
    def buildSeedsWhenNotThere(self):
        if self.seedL is None:
            tempL = []
    
            tempd =  self.dataVol.seeds.data[:, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = self.dataVol.seeds.data[:,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                                   
            self.seedIndices = indices
            self.seedL = tempL
    
    def getSeeds(self):
        self.buildSeedsWhenNotThere()
        return self.seedL,  self.seedIndices
        
    def updateTrainingMatrix(self, newLabels):
        """
        This method updates the current training Matrix with new labels.
        newlabels can contain completey new labels, changed labels and deleted labels
        """
        for nl in newLabels:
            try:
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

                    if len(indices.shape) == 1:
                        indices.shape = indices.shape + (1,)

                    mask = numpy.setmember1d(self.trainingIndices.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        tt = numpy.delete(self.trainingIndices,nonzero)
                        if len(tt.shape) == 1:
                            tt.shape = tt.shape + (1,)
                        self.trainingIndices = numpy.concatenate((tt,indices))
                        tempI = numpy.nonzero(nl.data)
                        tempL = nl.data[tempI]
                        tempL.shape += (1,)
                        temp2 = numpy.delete(self.trainingL,nonzero)
                        temp2.shape += (1,)
                        self.trainingL = numpy.vstack((temp2,tempL))


                        temp2 = numpy.delete(self.trainingF,nonzero, axis = 0)

                        if self._featureM is not None and len(indices) > 0:
                            tempfm = self.getTrainingMforInd(indices)

                            if len(temp2.shape) == 1:
                                temp2.shape += (1,)

                            self.trainingF = numpy.vstack((temp2,tempfm))
                        else:
                            self.trainingF = temp2

                    elif indices.shape[0] > 0: #no intersection, just add everything...
                        if len(self.trainingIndices.shape) == 1:
                            self.trainingIndices.shape = self.trainingIndices.shape + (1,)
                        self.trainingIndices = numpy.concatenate((self.trainingIndices,indices))

                        tempI = numpy.nonzero(nl.data)
                        tempL = nl.data[tempI]
                        tempL.shape += (1,)
                        temp2 = self.trainingL
                        self.trainingL = numpy.vstack((temp2,tempL))

                        if self._featureM is not None and len(indices) > 0:
                            if self.trainingF is not None:
                                if len(self.trainingF.shape) == 1:
                                    self.trainingF.shape += (1,)

                                tempfm = self.getTrainingMforInd(indices)
                                self.trainingF = numpy.vstack((self.trainingF,tempfm))
                            else:
                                self.trainingF = self.getTrainingMforInd(indices)

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

                    mask = numpy.setmember1d(self.trainingIndices.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        if self.trainingF is not None:
                            self.trainingIndices = numpy.delete(self.trainingIndices,nonzero)
                            self.trainingL  = numpy.delete(self.trainingL,nonzero)
                            self.trainingL.shape += (1,) #needed because numpy.delete is stupid
                            self.trainingF = numpy.delete(self.trainingF,nonzero, axis = 0)
                    else: #no intersectoin, in erase mode just pass
                        pass
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                print self.trainingIndices.shape
                print indices.shape
                print self.trainingF.shape
                print nonzero


    def updateSeeds(self, newLabels):
        """
        This method updates the seedMatrix with new seeds.
        newlabels can contain completey new labels, changed labels and deleted labels
        """
        for nl in newLabels:
            try:
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

                    if len(indices.shape) == 1:
                        indices.shape = indices.shape + (1,)

                    mask = numpy.setmember1d(self.seedIndices.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        tt = numpy.delete(self.seedIndices,nonzero)
                        if len(tt.shape) == 1:
                            tt.shape = tt.shape + (1,)
                        self.seedIndices = numpy.concatenate((tt,indices))
                        tempI = numpy.nonzero(nl.data)
                        tempL = nl.data[tempI]
                        tempL.shape += (1,)
                        temp2 = numpy.delete(self.seedL,nonzero)
                        temp2.shape += (1,)
                        self.seedL = numpy.vstack((temp2,tempL))


                    elif indices.shape[0] > 0: #no intersection, just add everything...
                        if len(self.seedIndices.shape) == 1:
                            self.seedIndices.shape = self.seedIndices.shape + (1,)
                        self.seedIndices = numpy.concatenate((self.seedIndices,indices))

                        tempI = numpy.nonzero(nl.data)
                        tempL = nl.data[tempI]
                        tempL.shape += (1,)
                        temp2 = self.seedL
                        self.seedL = numpy.vstack((temp2,tempL))

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

                    mask = numpy.setmember1d(self.seedIndices.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        if self.seedIndices is not None:
                            self.seedIndices = numpy.delete(self.seedIndices,nonzero)
                            self.seedL  = numpy.delete(self.seedL,nonzero)
                            self.seedL.shape += (1,) #needed because numpy.delete is stupid
                    else: #no intersectoin, in erase mode just pass
                        pass
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                print self.trainingIndices.shape
                print indices.shape
                print self.trainingF.shape
                print nonzero
                
    def clearSeeds(self):
        self.seedL = None
        self.seedIndices = None

    def clearFeaturesAndTraining(self):
        self.trainingF = numpy.zeros((0), 'float32')      
        self.trainingL = numpy.zeros((0, 1), 'uint8')
        self.trainingIndices = numpy.zeros((0, 1), 'uint32')
        
    def getFeatureSlicesForViewState(self, vs):
        tempM = []
        if self._featureM is not None:
            tempM.append(self._featureM[vs[0],vs[1],:,:,:,:])
            tempM.append(self._featureM[vs[0],:,vs[2],:,:,:])
            tempM.append(self._featureM[vs[0],:,:,vs[3],:,:])
            for i, f in enumerate(tempM):
                tf = f.reshape((numpy.prod(f.shape[0:2]),) + (numpy.prod(f.shape[2:]),))
                tempM[i] = tf
                
            return tempM
        else:
            return None
            
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
    
    def __init__(self, featureCacheFile=None):
        self.dataItems = []            
        self.classifiers = []
        self.featureLock = threading.Semaphore(1) #prevent chaning of activeImage during thread stuff
        self.trainingVersion = 0
        self.featureVersion = 0
        self.dataItemsLoaded = []
        self.trainingF = None
        self.featureCacheFile = featureCacheFile
        self.channels = -1
        self.activeImage = 0
            
    def append(self, dataItem, alreadyLoaded=False):
        if alreadyLoaded == False:
            try:
                dataItem.loadData()
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory to load this file !")
                raise e

            alreadyLoaded = True
            
        if self.channels == -1 or dataItem.dataVol.data.shape[-1] == self.channels:
            self.channels = dataItem.dataVol.data.shape[-1]
            if self.featureCacheFile is not None:
                cx = 1
                cy = 32
                cz = 32
                if str(len(self)) in self.featureCacheFile.keys():
                    del self.featureCacheFile[str(len(self))]
                dataItem.featureCacheDS = self.featureCacheFile.create_dataset(str(len(self)), (1,1,1,1,1,1), 'float32', maxshape = (None, None, None, None, None, None), chunks=(1,cx,cy,cz,1,1), compression=None)
            self.dataItems.append(dataItem)
            self.dataItemsLoaded.append(alreadyLoaded)
        else:
            raise TypeError('DataMgr.append: DataItem has wrong number of channels, a project can contain only images that have the same number of channels !')
        
    def clearDataList(self):
        self.dataItems = []
        self.dataFeatures = []
        self.labels = {}
        
    
    def buildTrainingMatrix(self, sigma = 0):
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
    
    def getTrainingMatrix(self, sigma = 0):
        """
        sigma: trainig data that is within sigma to the image borders is not considered to prevent
        border artifacts in training
        """
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
        
    
    def updateTrainingMatrix(self, newLabels,  imageNr = None):
        if self.trainingF is None or len(self.trainingF) == 0 or self.trainingVersion < self.featureVersion:
            self.buildTrainingMatrix()        
        if imageNr is None:
            imageNr = self.activeImage
        self[imageNr].updateTrainingMatrix(newLabels)



    def buildFeatureMatrix(self):
        print "buildFeatureMatrix should not be called !!"

                    
    def clearFeaturesAndTraining(self):
        self.featureVersion += 1
        self.trainingF = None
        self.trainingL = None
        self.trainingIndices = None
        self.classifiers = []
        
        for index, item in enumerate(self):
            item.clearFeaturesAndTraining()
            
    def clearSeeds(self):
        for index, item in enumerate(self):
            item.clearSeeds()

    def updateSeeds(self, newLabels,  imageNr = None):
        if imageNr is None:
            imageNr = self.activeImage
        self[imageNr].updateSeeds(newLabels)
        


    def getDataList(self):
        return self.dataItems
               
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
        if len(self) == 0:
            self.channels = -1
    
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

        
        
        
    
    
        
        
        
        
        

                    
                    
                    
                
        
        


        
