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

import numpy, vigra
import sys, os, traceback, copy, csv, shutil, time, threading, warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py

from ilastik.core import dataImpex
from ilastik.core.volume import DataAccessor as DataAccessor, VolumeLabelDescriptionMgr, VolumeLabels
from ilastik.core import overlayMgr
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr, PropertyMgr
from ilastik.modules.connected_components.gui.guiThread import CC
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponents

from PyQt4.QtCore import SIGNAL
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
        
    seedLabelsVolume = None
    done = None
    segmentation = None
    
    #if we are editing a segment that already exists on disk as
    #self.outputPath/key, this variable will hold 'key'
    _currentSegmentsKey = None
    _mapLabelsToKeys = dict()
    _mapKeysToLabels = dict()
    _hasSeeds = False
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self._dataItemImage = dataItemImage
        self.interactiveSegmentationModuleMgr = None 
        self._segmentationWeights             = None
        self._seedLabelsList                  = None
        self._seedIndicesList                 = None
        self.segmentorInstance                = None
        self.potentials                       = None
    
    def __reset(self):
        self.clearSeeds()
        self._buildSeedsWhenNotThere()
        self._currentSegmentsKey = None
        
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
    
    def init(self):
        """Handles all the initialization that can be postponed until _activation_ of the module.
           For example, big arrays are allocated only after the user has decided
           to switch to this particular tab."""
        self.__createSeedsData()
        
        if not os.path.exists(self.outputPath+'/'+'config.txt'): return
        
        f = open(self.outputPath+'/'+'config.txt')
        lines = f.readlines()
        d = dict()
        for l in lines:
            l = l.split('='); key = l[0].strip(); val = l[1].strip()
            d[key] = val
        
        #FIXME: make sure that we have the overlay loaded!!!
        self.calculateWeights(self._dataItemImage.overlayMgr[d["overlay"]]._data[0,:,:,:,0], d["borderIndicator"])
    
    def calculateWeights(self, volume, borderIndicator, normalizePotential=True, sigma=1.0):
        """Calculate the weights indicating borderness from the raw data"""
        
        #TODO: this , until now, only supports gray scale and 2D!
        if borderIndicator == "Brightness":
            weights = volume[:,:,:].view(vigra.ScalarVolume)
        elif borderIndicator == "Darkness":
            weights = (255 - volume[:,:,:]).view(vigra.ScalarVolume)
        elif borderIndicator == "Gradient Magnitude":
            weights = numpy.ndarray(volume.shape, numpy.float32)
            if weights.shape[0] == 1:
                weights[0,:,:] = vigra.filters.gaussianGradientMagnitude((volume[0,:,:]).astype(numpy.float32), sigma)
            else:
                weights = vigra.filters.gaussianGradientMagnitude((volume[:,:,:]).astype(numpy.float32), sigma)
                
        if normalizePotential == True:
            min = numpy.min(volume)
            max = numpy.max(volume)
            print "Weights min/max :", min, max
            weights = (weights - min)*(255.0 / (max - min))
            
        self.setupWeights(weights)
    
    def setupWeights(self, weights = None):
        if weights is None:
            weights = self._segmentationWeights
        else:
            self._segmentationWeights = weights
        if self.globalMgr.segmentor is not None:
            self.globalMgr.segmentor.setupWeights(weights)
        self.emit(SIGNAL('weightsSetup()'))
    
    def segmentKeyForLabel(self, label):
        """given a label in the 'done' overlay, return the key of the group that
           this segment belongs to (key is a directory in self.outputPath"""
        return self._mapLabelsToKeys[label]
    
    def segmentLabelsForKey(self, key):
        """given a key (a directory name in self.outputPath), return all
           label numbers in the 'done' overlay which refer to segments in the
           key group"""
        return self._mapKeysToLabels[key]
    
    def hasSegmentsKey(self, key):
        """whether a group of segments is already stored under name 'key' on disk""" 
        return key in self._mapKeysToLabels.keys()
    
    def saveCurrentSegment(self):
        assert self._currentSegmentsKey
        self.saveCurrentSegmentsAs(self._currentSegmentsKey, overwrite=True)
    
    def saveCurrentSegmentsAs(self, key, overwrite = False):
        """ Save the currently segmented segments as a group with the name 'key'.
            A directory with the same name is created in self.outputPath holding
            all information about seeds and segments."""
                
        print "save current segments as '%s'" %  (key)
        
        #make sure we have a 'done' overlay
        if self.done is None:
            self.done = numpy.zeros(self._dataItemImage.shape, numpy.uint32)
            self.emit(SIGNAL('doneOverlaysAvailable()'))
        
        if overwrite:
            shutil.rmtree(self.outputPath+'/'+str(key))
            labelsToDelete = copy.deepcopy(self._mapKeysToLabels[key])
            del self._mapKeysToLabels[key]
            for l in labelsToDelete:
                del self._mapLabelsToKeys[l]
            self.__rebuildDone()
            
        elif os.path.exists(self.outputPath+'/'+str(key)):
            raise RuntimeError("trying to overwrite '%s'", self.outputPath+'/'+str(key))
        #create directory to store the segment in     
        path = self.outputPath+'/'+str(key)
        print " - saving to '%s'" % (path),
        os.makedirs(path)
        
        print "segmentation",
        f = h5py.File(path + "/segmentation.h5", 'w')
        f.create_group('volume')
        tmp = self.segmentation[0,:,:,:,0]
        tmp.shape = (1,) + tmp.shape + (1,)
        f.create_dataset('volume/data', data=tmp)
        f.close(); del f
        
        print "seeds"
        f = h5py.File(path + "/seeds.h5", 'w')
        f.create_group('volume')
        f.create_dataset('volume/data', data=self.seedLabelsVolume._data[:,:,:,:,:])
        f.close(); del f

        #compute connected components on current segmentation
        print " - computing CC of current segments"  
        connectedComponentsComputer = ConnectedComponents()
        prevMaxLabel = numpy.max(self.done)
        print "   - previous number of labels was %d" % (prevMaxLabel)
        cc = connectedComponentsComputer.connect(self.segmentation[0,:,:,:,:], background=set([1]))            
        self.done[:,:,:,:,:] = numpy.where(cc>0, cc+int(prevMaxLabel), self.done)
        
        f = h5py.File(self.outputPath + "/done.h5", 'w')
        f.create_group('volume')
        f.create_dataset('volume/data', data=self.done)
        f.close()
    
        numCC = numpy.max(cc)
        print "   - there are %d segments to be saved as '%s'" % (numCC, key)
        print " - saving"
        for i in range(prevMaxLabel+1,prevMaxLabel+numCC+1):
            print "   - label %d now known as '%s'" % (i, key)
            self._mapLabelsToKeys[i] = key
            if key not in self._mapKeysToLabels.keys():
                self._mapKeysToLabels[key] = set()
            self._mapKeysToLabels[key].add(i)

        self.__saveMapping()

        self.__reset()
        
        #Clear the segmentation
        #The association with the overlay will be broken,
        #but this is not so bad because the overlay is 'fixed' via
        #the overlaysChanged() notification. This is not nice, but works...
        self.segmentation = None
        
        self.emit(SIGNAL('saveAsPossible(bool)'), False)
        self.emit(SIGNAL('savePossible(bool)'),   False)
        
        self.emit(SIGNAL('overlaysChanged()'))
    
    def discardCurrentSegmentation(self):
        self.segmentation = None
        self.__reset()
        self.emit(SIGNAL('overlaysChanged()'))
        
    def removeSegmentsByKey(self, key):
        """Remove all segments belong to 'key'.
           The segmentation on disk is removed as well."""
        
        print "removing segment '%s'" % (key)
        labelsForKey = self._mapKeysToLabels[key]
        print " - labels", [i for i in self._mapKeysToLabels[key]], "belong to '%s'" % (key)
        
        del self._mapKeysToLabels[key]
        for l in labelsForKey:
            del self._mapLabelsToKeys[l] 
        
        path = self.outputPath+'/'+str(key)
        print " - removing storage path '%s'" % (path)
        shutil.rmtree(path)
        
        #Clear the segmentation
        #The association with the overlay will be broken,
        #but this is not so bad because the overlay is 'fixed' via
        #the overlaysChanged() notification. This is not nice, but works...
        self.segmentation = None
        
        self.__reset()
        
        self.__saveMapping()
        
        self.__rebuildDone()
        
        #write out done file again
        f = h5py.File(self.outputPath + "/done.h5", 'w')
        f.create_group('volume')
        f.create_dataset('volume/data', data=self.done)
        f.close()
        
        self.emit(SIGNAL('overlaysChanged()'))
    
    def editSegmentsByKey(self, key):
        print "you want to edit '%s'" % (key)
        assert self.hasSegmentsKey(key)
        
        self._currentSegmentsKey = key
        
        self.clearSeeds()
        
        #f = h5py.File(self.outputPath+'/'+key+'/segmentation.h5', 'r')
        #self.segmentation[0,:,:,:,:] = f['volume/data'].value[0,:,:,:,:]
        #f.close()
        
        f = h5py.File(self.outputPath+'/'+key+'/seeds.h5', 'r')
        seeds = f['volume/data'].value[0,:,:,:,:]
        self.seedLabelsVolume._data[0,:,:,:,:] = seeds
        f.close()
        
        numColorsNeeded = numpy.max(seeds)
        print "XXX I will need %d seed colors" % (numColorsNeeded)
        self.emit(SIGNAL('numColorsNeeded(int)'), numColorsNeeded)
        
        self._buildSeedsWhenNotThere()
        
        #Now that we have the correct seeds loaded, segment again!
        self.segment()
        
        self.emit(SIGNAL('overlaysChanged()'))
    
    def __rebuildDone(self):
        print "rebuild 'done' overlay"
        self.done[:] = 0 #clear 'done'
        maxLabel = 0
        
        keys = copy.deepcopy(self._mapKeysToLabels.keys())
        self._mapKeysToLabels = dict()
        self._mapLabelsToKeys = dict()
        
        for key in sorted(keys):
            print " - segments '%s'" % (key)
            path = self.outputPath+'/'+str(key)
            
            f = h5py.File(path+'/'+'segmentation.h5', 'r')            
            connectedComponentsComputer = ConnectedComponents()
            #FIXME: indexing in first and last dimension
            cc = connectedComponentsComputer.connect(f['volume/data'][0,:,:,:,0], background=set([1]))
            numNewLabels = numpy.max(cc)         
            self.done = numpy.where(cc>0, cc+int(maxLabel), self.done)
            
            r = range(maxLabel+1, maxLabel+1+numNewLabels)
            self._mapKeysToLabels[key] = set(r)
            for i in r:
                print "   - label %d belongs to '%s'" % (i, key)
                self._mapLabelsToKeys[i] = key
            
            maxLabel += numNewLabels
        print " ==> there are now a total of %d segments stored as %d named groups" % (maxLabel, len(self._mapKeysToLabels.keys()))
    
    def setModuleMgr(self, interactiveSegmentationModuleMgr):
        self.interactiveSegmentationModuleMgr = interactiveSegmentationModuleMgr
        
    def __createSeedsData(self):
        if self.seedLabelsVolume is None:
            l = numpy.zeros(self._dataItemImage.shape[0:-1] + (1, ),  'uint8')
            self.seedLabelsVolume = VolumeLabels(l)
        
        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)
        
        if os.path.exists(self.outputPath + "/done.h5"):
            print "found existing done.h5 file. Loading..."
            f = h5py.File(self.outputPath + "/done.h5", 'r')
            self.done = f['volume/data'].value
            self.emit(SIGNAL('doneOverlaysAvailable()'))
            
        self.__loadMapping()
        
    def clearSeeds(self):
        self._hasSeeds = False
        self.emit(SIGNAL('seedsAvailable(bool)'), self._hasSeeds)
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
                    templ = list(self._dataItemImage.shape[1:-1])
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
                    templ = list(self._dataItemImage.shape[1:-1])
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
        
        print self._seedLabelsList.__class__ , self._seedLabelsList.shape      
        hasSeeds = self._seedLabelsList.shape[0] > 0
        if self._hasSeeds != hasSeeds:
            self._hasSeeds = hasSeeds
            self.emit(SIGNAL('seedsAvailable(bool)'), self._hasSeeds)

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
        
        self.emit(SIGNAL('newSegmentation()'))
        if self._currentSegmentsKey == None:
            self.emit(SIGNAL('saveAsPossible(bool)'), True)
            self.emit(SIGNAL('savePossible(bool)'), False)
        else:
            self.emit(SIGNAL('saveAsPossible(bool)'), False)
            self.emit(SIGNAL('savePossible(bool)'), True)
               
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
        
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   ' _ _ m a i n _ _ '                            *
#*******************************************************************************

if __name__ == '__main__':
    from ilastik.core.projectClass import Project
    from ilastik.core import jobMachine
    from ilastik.modules.interactive_segmentation.core.segmentors.segmentorBase import SegmentorBase
    from PyQt4.QtCore import *
    
    def h5equal(filename, a):
        f = h5py.File(filename, 'r')
        d = f['volume/data'].value.squeeze()
        a = a.squeeze()        
        assert a.shape == d.shape
        if a.dtype != d.dtype:
            print a.dtype, '!=', d.dtype
            assert a.dtype == d.dtype
        assert numpy.array_equal(d, a)
        return True
        
    def arrayEqual(a,b):
        assert a.shape == b.shape
        assert a.dtype == b.dtype
        if not numpy.array_equal(a,b):
            assert len(a.shape) == 3
            for x in range(a.shape[0]):
                for y in range(a.shape[1]):
                    for z in range(a.shape[2]):
                        if a[x,y,z] != b[x,y,z]:
                            print x,y,z, "a=", a[x,y,z], "b=", b[x,y,z]
            return False
        return True
    
    class TestSegmentor(SegmentorBase):
        segmentation = None
        ver = 0
        
        def setVersion(self, ver=0):
            self.ver = ver
        
        def produceSegmentationVersion(self, version):
            #first fill with the background label '1' 
            self.segmentation = numpy.ones((120,120,120,1), dtype=numpy.uint8)
            if version == 0:
                self.segmentation[5:10,5:10,5:10,0] = 2
            elif version == 1:
                self.segmentation[5:30,5:20,8:17,0]    = 3
                self.segmentation[50:70,50:70,40:60,0] = 5
            elif version == 2:
                self.segmentation[8:12,10:30,30:40,0]  = 2
                self.segmentation[20:30,10:30,30:40,0] = 4
                self.segmentation[40:50,10:30,30:40,0] = 6
        
        def segment(self, labelVolume, labelValues, labelIndices):
            assert labelVolume.shape == (120,120,120,1)
            self.produceSegmentationVersion(self.ver)
    
    # create project
    project = Project.loadFromDisk('/home/thorben/cube100.ilp', None)
    dataMgr = project.dataMgr
    segmentor = TestSegmentor()
    dataMgr.Interactive_Segmentation.segmentor = segmentor
    
    #initialize the module to test
    s = dataMgr._activeImage.module["Interactive_Segmentation"] 
    #create outputPath, make sure it is empty
    s.outputPath = str(QDir.tempPath())+"/tmpseg"
    print s.outputPath
    if os.path.exists(s.outputPath):
        shutil.rmtree(s.outputPath)
    os.makedirs(s.outputPath)
    s.init()

    shape3D = (120,120,120)
    shape4D = (120,120,120,1)
    shape5D = (1,120,120,120,1)

    print "*************************************************************************"
    print "* segment for the first time (version 0)                                *"
    print "*************************************************************************"
    
    #segment
    segmentor.setVersion(0)    
    s.segment()
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentation)
    assert not os.path.exists(s.outputPath+'/one')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    
    #save as 'one'
    s.saveCurrentSegmentsAs('one')
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/one/segmentation.h5')
    assert os.path.exists(s.outputPath+'/one/seeds.h5')
    
    h5equal(s.outputPath+'/one/segmentation.h5', segmentor.segmentation)
    
    doneGT = numpy.zeros(shape=shape4D, dtype=numpy.uint32)
    doneGT[numpy.where(segmentor.segmentation == 2)] = 1
    h5equal(s.outputPath+'/done.h5', doneGT)
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == ['1|one\r\n']
    f.close()
    
    assert s._mapKeysToLabels == {'one': set([1])}
    assert s._mapLabelsToKeys == {1: 'one'}
    assert s.segmentKeyForLabel(1) == 'one'
    assert s.segmentLabelsForKey('one') == set([1])

    s.discardCurrentSegmentation()
    assert s.segmentation == None
    assert numpy.where(s.seedLabelsVolume._data != 0) == ()

    print "*************************************************************************"
    print "* remove segment 'one'                                                  *"
    print "*************************************************************************"

    #remove segment by key
    s.removeSegmentsByKey('one')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    assert numpy.array_equal(s.done, numpy.zeros(shape=s.done.shape, dtype=s.done.dtype))
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert not os.path.exists(s.outputPath+'/one')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == []
    f.close()
    
    print "*************************************************************************"
    print "* segment for the second time (version 1)                               *"
    print "*************************************************************************"
    
    segmentor.setVersion(1)
    s.segment()
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentation)
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    
    s.saveCurrentSegmentsAs('two')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    relabeledGT = segmentor.segmentation.copy()
    relabeledGT[numpy.where(relabeledGT == 1)] = 0
    relabeledGT[numpy.where(relabeledGT == 3)] = 1
    relabeledGT[numpy.where(relabeledGT == 5)] = 2
    assert arrayEqual(s.done.squeeze(), relabeledGT.squeeze().astype(numpy.uint32))
    
    assert s._mapKeysToLabels == {'two': set([1, 2])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two'}
    
    print "*************************************************************************"
    print "* segment again (version 2)                                             *"
    print "*************************************************************************"
 
    segmentor.setVersion(2)
    s.segment()
    assert arrayEqual(s.segmentation[0,:,:,:,:], segmentor.segmentation)
    
    s.saveCurrentSegmentsAs('three')
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    assert os.path.exists(s.outputPath+'/three/segmentation.h5')
    assert os.path.exists(s.outputPath+'/three/seeds.h5')
    
    assert s._mapKeysToLabels == {'two': set([1, 2]), 'three': set([3, 4, 5])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two', 3: 'three', 4: 'three', 5: 'three'}
    
    segmentor.produceSegmentationVersion(1)
    seg1 = segmentor.segmentation
    segmentor.produceSegmentationVersion(2)
    seg2 = segmentor.segmentation
    doneGT = numpy.zeros(shape=seg1.shape, dtype=numpy.uint32)
    doneGT[numpy.where(seg1 == 3)] = 1
    doneGT[numpy.where(seg1 == 5)] = 2
    doneGT[numpy.where(seg2 == 2)] = 3
    doneGT[numpy.where(seg2 == 4)] = 4
    doneGT[numpy.where(seg2 == 6)] = 5
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    
    assert h5equal(s.outputPath+'/two/segmentation.h5', seg1)
    assert h5equal(s.outputPath+'/three/segmentation.h5', seg2)
    
    print "*************************************************************************"
    print "* remove segments 'three'                                               *"
    print "*************************************************************************"
    
    s.removeSegmentsByKey('three')
    assert s._mapKeysToLabels == {'two': set([1, 2])}
    assert s._mapLabelsToKeys == {1: 'two', 2: 'two'}
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert os.path.exists(s.outputPath+'/two/segmentation.h5')
    assert os.path.exists(s.outputPath+'/two/seeds.h5')
    assert not os.path.exists(s.outputPath+'/three')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == ['1|two\r\n', '2|two\r\n']
    f.close()
    
    doneGT = numpy.zeros(shape=seg1.shape, dtype=numpy.uint32)
    doneGT[numpy.where(seg1 == 3)] = 1
    doneGT[numpy.where(seg1 == 5)] = 2
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    assert h5equal(s.outputPath+'/done.h5', doneGT)
    
    print "*************************************************************************"
    print "* remove segments 'two'                                                 *"
    print "*************************************************************************"
    
    s.removeSegmentsByKey('two')
    assert s._mapKeysToLabels == {}
    assert s._mapLabelsToKeys == {}
    assert os.path.exists(s.outputPath)
    assert os.path.exists(s.outputPath+'/done.h5')
    assert os.path.exists(s.outputPath+'/mapping.dat')
    assert not os.path.exists(s.outputPath+'/two')
    assert not os.path.exists(s.outputPath+'/three')
    f = open(s.outputPath+'/mapping.dat')
    assert f.readlines() == []
    f.close()
    
    doneGT = numpy.zeros(shape=seg1.shape, dtype=numpy.uint32)
    assert arrayEqual(doneGT.squeeze(), s.done.squeeze())
    assert h5equal(s.outputPath+'/done.h5', doneGT)
    
    jobMachine.GLOBAL_WM.stopWorkers()
    