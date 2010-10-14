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
import gc
from Queue import Queue as queue
from copy import copy
import os
import threading
import h5py
from utilities import irange, debug, irangeIfTrue
try:
    from PyQt4 import QtGui
    have_qt = True
except:
    have_qt = False

from ilastik.core.volume import DataAccessor as DataAccessor
from ilastik.core.volume import Volume as Volume, VolumeLabels, VolumeLabelDescriptionMgr

from ilastik.core import activeLearning
from ilastik.core import overlayMgr
from ilastik.core.baseModuleMgr import PropertyMgr

from ilastik.core.baseModuleMgr import BaseModuleMgr, BaseModuleDataItemMgr

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
    Data Base class, serves as an interface for the specialized _data structures, e.g. images, multispectral, volume etc.  
    """
    #3D: important
    def __init__(self, fileName):
        self.fileName = str(fileName)
        self._name = os.path.split(self.fileName)[1]
        self._hasLabels = False
        self._isTraining = True
        self._isTesting = False
        self._groupMember = []
        self._projects = []
        
        self.thumbnail = None


class BlockAccessor():
    def __init__(self, data, blockSize = None):
        self._data = data
        if blockSize is None:
            max = int(numpy.max(self._data.shape[1:4]))
            if max > 128:
                self._blockSize = blockSize = 128
            else:
                self._blockSize = blockSize = max / 2
        else:
            self._blockSize = blockSize
        
        self._cX = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[1] % self._blockSize
        if self._cXend > 0 and self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0
                
        self._cY = int(numpy.ceil(1.0 * data.shape[2] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[2] % self._blockSize
        if self._cYend > 0 and self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0

        self._cZ = int(numpy.ceil(1.0 * data.shape[3] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cZend = data.shape[3] % self._blockSize
        if self._cZend > 0 and self._cZend < self._blockSize / 3 and self._cZ > 1:
            self._cZ -= 1
        else:
            self._cZend = 0

        self._blockCount = self._cX * self._cY * self._cZ
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True
        
    def getBlockBounds(self, blockNum, overlap):
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX
        
        startx = max(0, x*self._blockSize - overlap) 
        endx = min(self._data.shape[1], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[1]
        
        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[2], (y+1)*self._blockSize + overlap) 
        if y+1 >= self._cY:
            endy = self._data.shape[2]
    
        startz = max(0, z*self._blockSize - overlap)
        endz = min(self._data.shape[3], (z+1)*self._blockSize + overlap)
        if z+1 >= self._cZ:
            endz = self._data.shape[3]
        return [startx,endx,starty,endy,startz,endz]

    def __getitem__(self, args):
        if self._fileBacked is False:
            return self._data[args]
        else:
            self._lock.acquire()
            temp =  self._data[args]
            self._lock.release()
            return temp

    def __setitem__(self, args, data):
        if self._fileBacked is False:
            self._data[args] = data
        else:
            self._lock.acquire()
            self._data[args] = data
            self._lock.release()
            
class BlockAccessor2D():
    def __init__(self, data, blockSize = 128):
        self._data = data
        self._blockSize = blockSize

        self._cX = int(numpy.ceil(1.0 * data.shape[0] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[0] % self._blockSize
        if self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0

        self._cY = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[1] % self._blockSize
        if self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0


        self._blockCount = self._cX * self._cY
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True


    def getBlockBounds(self, blockNum, overlap):
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX

        startx = max(0, x*self._blockSize - overlap)
        endx = min(self._data.shape[0], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[0]

        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[1], (y+1)*self._blockSize + overlap)
        if y+1 >= self._cY:
            endy = self._data.shape[1]


        return [startx,endx,starty,endy]


    def __getitem__(self, args):
        if self._fileBacked is False:
            return self._data[args]
        else:
            self._lock.acquire()
            temp =  self._data[args]
            self._lock.release()
            return temp
            
    def __setitem__(self, args, data):
        if self._fileBacked is False:
            self._data[args] = data
        else:
            self._lock.acquire()
            self._data[args] = data
            self._lock.release()

    
class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName)
        self._dataVol = None
        self._featureM = None
        
        self._readBegin = (0,0,0)
        self._readEnd = (0,0,0)
        
        self._writeBegin = (0,0,0)
        self._writeEnd = (0,0,0)
        
        self.overlayMgr = overlayMgr.OverlayMgr()

        self.initModules()
    
    def initModules(self):
        self.module = PropertyMgr(self)
        
        mods = BaseModuleDataItemMgr.__subclasses__()
        
        for m in mods:
            self.module[m.name] = m(self) 
         

                
    def setDataVol(self, dataVol):
        self._dataVol = dataVol
        self._writeBegin = (0,0,0)
        self._writeEnd = (dataVol.shape[1], dataVol.shape[2], dataVol.shape[3])
        
    def setReadBounds(self, begin, end):
        self._readBegin = begin
        self._readEnd  = end
    
    def setWriteBounds(self, begin, end, shape):
        self._writeBegin = begin
        self._writeEnd  = end
        self._writeShape = shape
    

    def __getitem__(self, args):
        return self._dataVol._data[args]
            
    def __setitem__(self, args, data):
        self._dataVol._data[args] = data


    def __getattr__(self, name):
        if name == "dtype":
            return self._dataVol._data.dtype
        elif name == "shape":
            return self._dataVol._data.shape
        else:
            raise AttributeError, name
        
    
    def updateBackground(self, newLabels, key):
        """
        This function returns the classes which correspond to background
        """
        setAdd = set()
        setRemove = set()
        for nl in newLabels:
            try:
                indic =  list(numpy.nonzero(nl._data))
                indic[0] = indic[0] + nl.offsets[0]
                indic[1] += nl.offsets[1]
                indic[2] += nl.offsets[2]
                indic[3] += nl.offsets[3]
                indic[4] += nl.offsets[4]
                for i in range(0, len(indic[0])):
                    backclass = self.overlayMgr[key]._data[(indic[0][i],indic[1][i],indic[2][i],indic[3][i],indic[4][i])]
                    if nl.erasing == False:
                        setAdd.add(backclass)
                    else:
                        setRemove.add(backclass)
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
        
        return setAdd, setRemove


    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self._dataVol = None
        self._data = None
        
     
    def loadFromFile(self):
        f = h5py.File(self.fileName, 'r')
        g = f["volume"]
        self.deserialize(g)
    
    def serialize(self, h5G, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        if destend != (0,0,0):
            self._dataVol.serialize(h5G, destbegin, destend, srcbegin, srcend, destshape)
        elif self._writeEnd != (0,0,0):
            
            destbegin = self._writeBegin
            destend =  self._writeEnd
            srcbegin =  self._readBegin
            srcend =  self._readEnd
            destshape = self._writeShape
            
            self._dataVol.serialize(h5G, destbegin, destend, srcbegin, srcend, destshape)
        else:
            self._dataVol.serialize(h5G)
            
        for k in self.module.keys():
            if hasattr(self.module[k], "serialize"):
                print "serializing ", k
                try:
                    self.module[k].serialize(h5G, destbegin, destend, srcbegin, srcend, destshape)
                except Exception as e:
                    print e
                    print traceback.print_exc()
                    print "couldn't serialize something"
                    
    def updateOverlays(self):
        ov = overlayMgr.OverlayItem(self, self._dataVol._data, color = QtGui.QColor(255, 255, 255), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = True, autoAlphaChannel = False, min = 0, max = 255)
        self.overlayMgr["Raw Data"] = ov

#        if self._dataVol.labels is not None:
#            #create an overlay for labels
#            ov = overlayMgr.OverlayItem(self._dataVol.labels._data, color = 0, alpha = 1.0, colorTable = self._dataVol.labels.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
#            self.overlayMgr["Classification/Labels"] = ov
#            for p_i, descr in enumerate(self._dataVol.labels.descriptions):
#                #create Overlay for _prediction:
#                ov = overlayMgr.OverlayItem(descr._prediction, color = QtGui.QColor.fromRgba(long(descr.color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True)
#                self.overlayMgr["Classification/Prediction/" + descr.name] = ov
#
#        if self._dataVol.uncertainty is not None:
#            #create Overlay for uncertainty:
#            ov = overlayMgr.OverlayItem(self._dataVol.uncertainty, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
#            self.overlayMgr["Classification/Uncertainty"] = ov

            
    def deserialize(self, h5G, offsets = (0,0,0), shape = (0,0,0)):
        self._dataVol = Volume.deserialize(self, h5G, offsets, shape)
        
        #load obsolete file format parts (pre version 0.5)
        #and store them in the properties
        #the responsible modules will take care of them
            
        for k in self.module.keys():
            if hasattr(self.module[k], "deserialize"):
                print "deserializing ", k
                self.module[k].deserialize(h5G, offsets, shape)

        self.updateOverlays()




class MultiPartDataItemAccessor(object):
    def __init__(self, data, blocksize = 128, overlap = 10):
        self._data = data
        self.overlap = overlap
        self._blockAccessor = BlockAccessor(self._data, blocksize)
        
    def getBlockCount(self):
        return self._blockAccessor._blockCount
    
    def getDataItem(self, blockNr):
        di = DataItemImage("block " + str(blockNr))
        boundsa = self._blockAccessor.getBlockBounds(blockNr, self.overlap)
        tempdata = DataAccessor(self._data[:,boundsa[0]:boundsa[1],boundsa[2]:boundsa[3],boundsa[4]:boundsa[5],:])
        di.setDataVol(Volume(tempdata))
        boundsb = self._blockAccessor.getBlockBounds(blockNr, 0)
        di.setWriteBounds( (boundsb[0], boundsb[2], boundsb[4]), (boundsb[1], boundsb[3], boundsb[5]), self._data.shape[1:-1])
        di.setReadBounds( (boundsb[0]-boundsa[0], boundsb[2]-boundsa[2], boundsb[4]-boundsa[4]), (boundsb[0]-boundsa[0] + boundsb[1] - boundsb[0], boundsb[2]-boundsa[2] + boundsb[3] - boundsb[2], boundsb[4]-boundsa[4] + boundsb[5] - boundsb[4]))
        return di



        
            
class DataMgr():
    """
    Manages Project structure and associated files, e.g. images volumedata
    """
    # does not unload _data, maybe implement some sort of reference 
    # counting if memory scarceness manifests itself
    
    def __init__(self, featureCacheFile=None):
        self._dataItems = []            
        self.featureLock = threading.Semaphore(1) #prevent chaining of _activeImageNumber during thread stuff
        self._dataItemsLoaded = []
        self.channels = -1
        self._activeImageNumber = 0
        
        #TODO: Maybe it shouldn't be here...
        self.connCompBackgroundKey = ""    
        self.connCompBackgroundClasses = set()
        
        self.initModules()
        
        
    def initModules(self):
        self.module = PropertyMgr(self)
        for m in BaseModuleMgr.__subclasses__():
            print "DataMgr initializing module:", m.__name__
            self.module[m.name] = m(self)
                
    
    def onNewImage(self, dataItemImage):
        for v in self.module.values():
            v.onNewImage(dataItemImage)
    
    def append(self, dataItem, alreadyLoaded=False):
        if alreadyLoaded == False:
            try:
                dataItem.loadFromFile()
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory to load this file !")
                raise e

            alreadyLoaded = True
            
        if self.channels == -1 or dataItem.shape[-1] == self.channels:
            self.channels = dataItem.shape[-1]
            
            self.selectedChannels = range(self.channels)
            
            self._dataItems.append(dataItem)
            self._dataItemsLoaded.append(alreadyLoaded)
            self.onNewImage(dataItem)
        else:
            raise TypeError('DataMgr.append: DataItem has wrong number of channels, a project can contain only images that have the same number of channels !')
        
    def clearAll(self):
        self._dataItems = []
        gc.collect()
        
    
    def updateBackground(self, newLabels, imageNr = None):
        if self.connCompBackgroundKey == "":
            #TODO: make a real error message
            print "Select an overlay first!"
            return
        if imageNr is None:
            imageNr = self._activeImageNumber
        setAdd, setRemove = self[imageNr].updateBackground(newLabels, self.connCompBackgroundKey)
        self.connCompBackgroundClasses = self.connCompBackgroundClasses.union(setAdd)
        self.connCompBackgroundClasses = self.connCompBackgroundClasses.difference(setRemove)

    def getDataList(self):
        return self._dataItems
               
    def __getitem__(self, ind):
        if not self._dataItemsLoaded[ind]:
            self._dataItems[ind].loadData()
            self._dataItemsLoaded[ind] = True
        return self._dataItems[ind]
    
    def __setitem__(self, ind, val):
        self._dataItems[ind] = val
        self._dataItemsLoaded[ind] = True
    
    def getIndexFromFileName(self, fileName):
        for k, dataItem in irange(self._dataItems):
            if fileName == dataItem.fileName:
                return k
        return False
    
    def remove(self, dataItemIndex):
        del self._dataItems[dataItemIndex]
        del self._dataItemsLoaded[dataItemIndex]
        if len(self) == 0:
            self.channels = -1
    
    def __len__(self):
        return len(self._dataItems)
    
    def serialize(self, h5grp):
        for v in self.module.values():
            v.serialize(h5grp)
        
    @staticmethod
    def deserialize(self):
        pass

        
    
    
        
        
        
        
        

                    
                    
                    
                
        
        


        
