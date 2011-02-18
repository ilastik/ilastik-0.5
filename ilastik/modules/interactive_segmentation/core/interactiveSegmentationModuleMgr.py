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
import sys, os, traceback, copy, csv, shutil, time, threading, warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py

from ilastik.core import dataMgr as DM
from ilastik.core import dataImpex
from ilastik.core import activeLearning
from ilastik.core.volume import DataAccessor as DataAccessor, VolumeLabelDescriptionMgr, VolumeLabels
from ilastik.core import jobMachine
from ilastik.core import overlayMgr
import sys, traceback
from ilastik.core.dataMgr import BlockAccessor
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr, PropertyMgr
from ilastik.core.volume import VolumeLabels
from ilastik.modules.connected_components.gui.guiThread import CC
from ilastik.core.overlayMgr import OverlayItem
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponents

from PyQt4 import QtGui
from ilastik.core.listOfNDArraysAsNDArray import ListOfNDArraysAsNDArray

import seedMgr
from segmentors import segmentorBase

#*******************************************************************************
# L o a d i n g   o f   S e g m e n t o r s                                    *
#*******************************************************************************

pathext = os.path.dirname(__file__)
for f in os.listdir(os.path.abspath(pathext) + "/segmentors"):
    module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
    if ext == '.py' and module_name[-1] != "_": # Important, ignore .pyc/other files.
        try:
            module = __import__("ilastik.modules.interactive_segmentation.core.segmentors." + module_name)
        except Exception, e:
            print e
            traceback.print_exc(file=sys.stdout)
            pass

for i, c in enumerate(segmentorBase.SegmentorBase.__subclasses__()):
    print "Loaded segmentor:", c.name
    
segmentorClasses = segmentorBase.SegmentorBase.__subclasses__()
if len(segmentorClasses) == 0:
    segmentorClasses = [segmentorBase.SegmentorBase]

#*******************************************************************************
# G l o b a l   f u n c t i o n s                                              *
#*******************************************************************************

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

def setintersectionmask(a,b):
    if int(numpy.__version__.split('.')[1])>= 4:
        return numpy.in1d(a,b, assume_unique=True)
    else:
        return numpy.intersect1d(a,b)

#*******************************************************************************
# I n t e r a c t i v e S e g m e n t a t i o n I t e m M o d u l e M g r      *
#*******************************************************************************

class InteractiveSegmentationItemModuleMgr(BaseModuleDataItemMgr):
    name = "Interactive_Segmentation"
    
    #where to save segmentations to
    outputPath         = os.path.expanduser("~/test-segmentation")
    
    #Overlays for the current segmentation
    segmentationOverlay = None
    
    #Overlays for already 'done', previous segmentations
    doneBinaryOverlay   = None
    doneObjectsOverlay  = None
    
    _mapLabelsToKeys = dict()
    _mapKeysToLabels = dict()
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.interactiveSegmentationModuleMgr = None 
        self.overlays = []
        self.segmentation = None
        self.seedLabelsVolume = None
        self._segmentationWeights = None
        self._seedLabelsList = None#numpy.zeros((0, 1), 'uint8')
        self._seedIndicesList = None#numpy.zeros((0, 1), 'uint32')
        self.segmentorInstance = None
        self.potentials = None
    
    def init(self):
        """handles all the initialization that can be postponed until _activation_ of the module"""
        self.__createSeedsData()
    
    def __reset(self):
        self.dataItemImage.Interactive_Segmentation.clearSeeds()
        self.dataItemImage.Interactive_Segmentation._buildSeedsWhenNotThere()
    
    def __ensureOverlays(self):
        if self.doneBinaryOverlay is None:
            shape = self.dataItemImage.shape
            data = DataAccessor(numpy.zeros((shape), numpy.uint8))
            bluetable = []
            bluetable.append(long(0))
            for i in range(1, 256):
                bluetable.append(QtGui.qRgb(0, 0, 255))
            self.doneBinaryOverlay = OverlayItem(data, color = 0, colorTable=bluetable, alpha = 0.5, autoAdd = True, autoVisible = True, min = 1.0, max = 2.0)
            self.doneObjectsOverlay = OverlayItem(data, color=0, alpha=0.7, autoAdd=False, autoVisible=False)                    
            self.dataItemImage.overlayMgr["Segmentation/Done"] = self.doneBinaryOverlay
            self.dataItemImage.overlayMgr["Segmentation/Objects"] = self.doneObjectsOverlay
    
    def __loadMapping(self):
        mappingFileName = self.outputPath + "/mapping.dat"
        if os.path.exists(mappingFileName):
            r = csv.reader(open(mappingFileName, 'r'), delimiter='|')
            for entry in r:
                key   = entry[1].strip()
                label = int(entry[0])
                self._mapLabelsToKeys[label] = key
                if key not in self._mapKeysToLabels.keys():
                    self._mapKeysToLabels[key] = set()
                self._mapKeysToLabels[key].add(label)
    def __saveMapping(self):
        mappingFileName = self.outputPath + "/mapping.dat"
        r = csv.writer(open(mappingFileName, 'w'), delimiter='|')
        for i, key in self._mapLabelsToKeys.items():
            r.writerow([i,key])
    
    def segmentName(self, label):
        return self._mapLabelsToKeys[label]
    def saveCurrentSegmentsAs(self, key):        
        print "save current segments as '%s'" %  (key)
        self.__ensureOverlays()
        
        #create directory to store the segment in     
        path = self.outputPath+'/'+str(key)
        print " - saving to '%s'" % (path)
        os.makedirs(path)
        print "   - segmentation"
        dataImpex.DataImpex.exportOverlay(path + "/segmentation", "h5", self.segmentationOverlay)
        print "   - seeds"
        f = h5py.File(path + "/seeds.h5", 'w')
        f.create_group('volume')
        f.create_dataset('volume/data', data=self.seedLabelsVolume._data)
        f.close()

        #compute connected components on current segmentation
        print " - computing connected components of segments to be saved"  
        done = self.doneBinaryOverlay[0,:,:,:,:]
        seg  = self.segmentationOverlay[0,:,:,:,:]
        connectedComponentsComputer = ConnectedComponents()
        prevMaxLabel = numpy.max(done)
        print "   - previous number of labels was %d" % (prevMaxLabel)
        cc = connectedComponentsComputer.connect(seg, background=set([1]))            
        newDone = numpy.where(cc>0, cc+int(prevMaxLabel), done)
        self.doneBinaryOverlay[0,:,:,:,:] = newDone[:]        
        dataImpex.DataImpex.exportOverlay(self.outputPath+'/'+'done', "h5", self.doneBinaryOverlay)
    
        numCC = numpy.max(cc)
        print "    - there are %d segments to be saved as '%s'" % (numCC, key)
        print " - saving"
        for i in range(prevMaxLabel+1,prevMaxLabel+numCC+1):
            print "   - label %d now known as '%s'" % (i, key)
            self._mapLabelsToKeys[i] = key
            if key not in self._mapKeysToLabels.keys():
                self._mapKeysToLabels[key] = set()
            self._mapKeysToLabels[key].add(i)

        self.__saveMapping()

        self.__reset()
        
    def removeSegmentsByKey(self, key):
        print "removing segment '%s'" % (key)
        labelsForKey = self._mapKeysToLabels[key]
        print " - labels", [i for i in self._mapKeysToLabels[key]], "belong to '%s'" % (key)
        
        del self._mapKeysToLabels[key]
        for l in labelsForKey:
            del self._mapLabelsToKeys[l] 
        
        path = self.outputPath+'/'+str(key)
        print " - removing storage path '%s'" % (path)
        shutil.rmtree(path)
        
        self.__reset()
        
        self.__saveMapping()
        
        self.__rebuilddoneBinaryOverlay()
        
        self.emit('overlaysChanged()')
    
    def __rebuilddoneBinaryOverlay(self):
        print "rebuild 'done' overlay"
        doneBinaryOverlay = self.dataItemImage.overlayMgr["Segmentation/Done"]
        doneBinaryOverlay[0,:,:,:,:] = 0 #clear 'done'
        maxLabel = 0
        
        keys = copy.deepcopy(self._mapKeysToLabels.keys())
        self._mapKeysToLabels = dict()
        self._mapLabelsToKeys = dict()
        
        for key in keys:
            print " - segments '%s'" % (key)
            path = self.outputPath+'/'+str(key)
            
            f = h5py.File(path+'/'+'segmentation.h5', 'r')            
            connectedComponentsComputer = ConnectedComponents()
            #FIXME: indexing in first and last dimension
            cc = connectedComponentsComputer.connect(f['volume/data'][0,:,:,:,0], background=set([1]))
            numNewLabels = numpy.max(cc)         
            doneBinaryOverlay[0,:,:,:,:] = numpy.where(cc>0, cc+int(maxLabel), doneBinaryOverlay[0,:,:,:,:])
            
            r = range(maxLabel+1, maxLabel+1+numNewLabels)
            self._mapKeysToLabels[key] = set(r)
            for i in r:
                print "   - label %d belongs to '%s'" % (i, key)
                self._mapLabelsToKeys[i] = key
            
            maxLabel += numNewLabels
        print " ==> there are now a total of %d segments stored as %d named groups" % (maxLabel, len(self._mapKeysToLabels.keys()))
        
    def activeSegment(self):
        #get the label of the segment that we are currently 'carving'
        pass
    def activateSegment(self, label):
        pass
    def hasSegmentKey(self, key):
        return key in self._mapLabelsToKeys.values()
    
    def setModuleMgr(self, interactiveSegmentationModuleMgr):
        self.interactiveSegmentationModuleMgr = interactiveSegmentationModuleMgr
        
    def __createSeedsData(self):
        if self.seedLabelsVolume is None:
            l = numpy.zeros(self.dataItemImage.shape[0:-1] + (1, ),  'uint8')
            self.seedLabelsVolume = VolumeLabels(l)
            
        if self.segmentation is None:
            self.segmentation = numpy.zeros(self.dataItemImage.shape[0:-1] + (1, ),  'uint8')  
        
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)
        
        doneFileName         = self.outputPath + "/done.h5"
        
        if os.path.exists(doneFileName):
            dataImpex.DataImpex.importOverlay(self.dataItemImage, doneFileName, "")
            self.doneBinaryOverlay = self.dataItemImage.overlayMgr["Segmentation/Done"]
            
        self.__loadMapping()
        
    def clearSeeds(self):
        self._seedLabelsList = None
        self._seedIndicesList = None
        self.seedLabelsVolume._data[0,:,:,:,0] = 0

    def _buildSeedsWhenNotThere(self):
        if self._seedLabelsList is None:
            tempL = []
    
            tempd =  self.seedLabelsVolume._data[:, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = self.seedLabelsVolume._data[:,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                                   
            self._seedIndicesList = indices
            self._seedLabelsList = tempL
    
    def getSeeds(self):
        self._buildSeedsWhenNotThere()
        return self._seedLabelsList,  self._seedIndicesList
    
    def updateSeeds(self, newLabels):
        """
        This method updates the seedMatrix with new seeds.
        newlabels can contain completely new labels, changed labels and deleted labels
        """
        self._buildSeedsWhenNotThere()
        for nl in newLabels:
            try:
                if nl.erasing == False:
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]


                    loopc = 2
                    count = 1
                    indices = indic[-loopc]*count
                    templ = list(self.dataItemImage.shape[1:-1])
                    templ.reverse()
                    for s in templ:
                        loopc += 1
                        count *= s
                        indices += indic[-loopc]*count

                    if len(indices.shape) == 1:
                        indices.shape = indices.shape + (1,)

                    mask = setintersectionmask(self._seedIndicesList.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        tt = numpy.delete(self._seedIndicesList,nonzero)
                        if len(tt.shape) == 1:
                            tt.shape = tt.shape + (1,)
                        self._seedIndicesList = numpy.concatenate((tt,indices))
                        tempI = numpy.nonzero(nl._data)
                        tempL = nl._data[tempI]
                        tempL.shape += (1,)
                        temp2 = numpy.delete(self._seedLabelsList,nonzero)
                        temp2.shape += (1,)
                        self._seedLabelsList = numpy.vstack((temp2,tempL))


                    elif indices.shape[0] > 0: #no intersection, just add everything...
                        if len(self._seedIndicesList.shape) == 1:
                            self._seedIndicesList.shape = self._seedIndicesList.shape + (1,)
                        self._seedIndicesList = numpy.concatenate((self._seedIndicesList,indices))

                        tempI = numpy.nonzero(nl._data)
                        tempL = nl._data[tempI]
                        tempL.shape += (1,)
                        temp2 = self._seedLabelsList
                        self._seedLabelsList = numpy.vstack((temp2,tempL))

                else: #erasing == True
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]

                    loopc = 2
                    count = 1
                    indices = indic[-loopc]*count
                    templ = list(self.dataItemImage.shape[1:-1])
                    templ.reverse()
                    for s in templ:
                        loopc += 1
                        count *= s
                        indices += indic[-loopc]*count

                    mask = setintersectionmask(self._seedIndicesList.ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        if self._seedIndicesList is not None:
                            self._seedIndicesList = numpy.delete(self._seedIndicesList,nonzero)
                            self._seedLabelsList  = numpy.delete(self._seedLabelsList,nonzero)
                            self._seedLabelsList.shape += (1,) #needed because numpy.delete is stupid
                    else: #no intersection, in erase mode just pass
                        pass
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
                print self._trainingIndices.shape
                print indices.shape
                print self._trainingF.shape
                print nonzero

    def segment(self):
        labels, indices = self.getSeeds()
        self.globalMgr.segmentor.segment(self.seedLabelsVolume._data[0,:,:,:], labels, indices)
        self.segmentation = ListOfNDArraysAsNDArray([self.globalMgr.segmentor.segmentation])
        if(hasattr(self.globalMgr.segmentor, "potentials")):
            self.potentials = ListOfNDArraysAsNDArray([self.globalMgr.segmentor.potentials])
        else:
            self.potentials = None
        if(hasattr(self.globalMgr.segmentor, "borders")):
            self.borders = ListOfNDArraysAsNDArray([self.globalMgr.segmentor.borders])
        else:
            self.borders = None
               
    def serialize(self, h5G, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        print "serializing interactive segmentation"
        if self.seedLabelsVolume is not None:
            print "seeds are not None!!!"
            self.seedLabelsVolume.serialize(h5G, "seeds", destbegin, destend, srcbegin, srcend, destshape )
        else:
            print "seeds are None!!!"      

    def deserialize(self, h5G, offsets = (0,0,0), shape=(0,0,0)):
        if "seeds" in h5G.keys():
            self.seedLabelsVolume = VolumeLabels.deserialize(h5G,  "seeds")

#*******************************************************************************
# I n t e r a c t i v e S e g m e n t a t i o n M o d u l e M g r              *
#*******************************************************************************

class InteractiveSegmentationModuleMgr(BaseModuleMgr):
    name = "Interactive_Segmentation"
    
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        self.segmentor = None
        self.segmentorClasses = segmentorClasses
        self.seedMgr = seedMgr.SeedMgr(self.dataMgr)
                            
    def onNewImage(self, dataItemImage):
        dataItemImage.Interactive_Segmentation.setModuleMgr(self)
