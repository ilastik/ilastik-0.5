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

import vigra
import numpy
import traceback, sys
import threading
from ilastik.core.volume import VolumeLabels, VolumeLabelDescription
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core import jobMachine
from ilastik.core.listOfNDArraysAsNDArray import ListOfNDArraysAsNDArray
from ilastik.core.volume import DataAccessor
from ilastik.modules.connected_components.core.synapseDetectionFilter import SynapseFilterAndSegmentor 

try:
    from PyQt4 import QtCore
    ThreadBase = QtCore.QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False

class BackgroundOverlayItem(OverlayItem):
    def __init__(self, backgroundListWidget, data, color = 0, alpha = 0.4, colorTable = None, autoAdd = False, autoVisible = False,  linkColorTable = False, autoAlphaChannel = True, min = None, max = None):
        self.backgroundListWidget = backgroundListWidget
        OverlayItem.__init__(self, data, color, alpha, autoAdd, autoVisible,  linkColorTable, autoAlphaChannel, min, max)
        
    def getColorTab(self):
        return self.backgroundListWidget.getColorTab()


class ConnectedComponentsItemModuleMgr(BaseModuleDataItemMgr):
    name = "Connected_Components"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.connCompBackgroundClasses = set()
        self.background = None
        self.cc = None
        self.overlays = []
        self.inputData = None
        
    def onAppend(self):
        if self.background is None:
            l = numpy.zeros(self.dataItemImage.shape[0:-1], 'uint8')
            self.background = VolumeLabels(l)      
        
    def addLabel(self, name, number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        description._prediction = numpy.zeros(self.dataItemImage.shape[0:-1],  'uint8')
        self.background.descriptions.append(description)    

    def changedLabel(self,  label):
        for labelIndex,  labelItem in enumerate(self.background):
            labelItem.name = label.name
            labelItem.number = label.number
            labelItem.color = label.color
                
        
    def newLabels(self,  newLabels):
        setAdd = set()
        setRemove = set()
        if self.inputData is not None:
            try:
                for nl in newLabels:
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]
                    for i in range(0, len(indic[0])):
                        selector = (indic[0][i],indic[1][i],indic[2][i],indic[3][i],indic[4][i])
                        backclass = self.inputData[selector]
                        if nl.erasing == False:
                            setAdd.add(backclass)
                        else:
                            setRemove.add(backclass)
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
        
        self.connCompBackgroundClasses = self.connCompBackgroundClasses.union(setAdd)
        self.connCompBackgroundClasses = self.connCompBackgroundClasses.difference(setRemove)
        
    def setInputData(self, data):
        self.inputData = data
            
class ConnectedComponentsModuleMgr(BaseModuleMgr):
    name = "Connected_Components"
    
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr

    def onNewImage(self, dataItemImage):
        dataItemImage.Connected_Components.onAppend()

    def computeResults(self, backgroundClasses):
        overlay = self.dataMgr[self.dataMgr._activeImageNumber].Connected_Components.inputData
        if backgroundClasses is None:
            self.ccThread = ConnectedComponentsThread(self.dataMgr, overlay._data)
        else:
            self.ccThread = ConnectedComponentsThread(self.dataMgr, overlay._data, backgroundClasses)
        
        self.ccThread.start()
        return self.ccThread
    
    def finalizeResults(self):
        #create Overlay for connected components:
        if self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Results"] is None:
            colortab = self.makeColorTab()
            myColor = OverlayItem.qrgb(255, 0, 0)
            ov = OverlayItem(self.ccThread.result, color = myColor, alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Results"] = ov
        else:
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Results"]._data = DataAccessor(self.ccThread.result)

    def filterSynapses(self, inputOverlay, label):
        #This is a special function to filter synapses. First, it finds the sizes of labeled objects
        #and throws away everything <0.1 of the smallest labeled object or >10 of the largest labeled
        #object. Then, it assumes that the input overlay
        #is a threhsold overlay and computes it for equal probabilities, and then dilates the
        #the current connected components to the size of their counterparts in the equal 
        #probability connected components.
        
        #FIXME: This function is very specific and is only put here until ilastik 0.6 allows 
        #to make it into a special workflow. Remove as soon as possible!
        parts = label.split(" ")
        labelnum = int(parts[0])
        #labelname = parts[1]
        thres = self.dataMgr[self.dataMgr._activeImageNumber].Connected_Components.inputData
        cc = self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Results"]
        if thres is None:
            print "no threshold overlay"
            return
        if cc is None:
            print "No cc overlay"
            return
        sfad = SynapseFilterAndSegmentor(self.dataMgr, labelnum, cc, inputOverlay)
        objs_user, goodsizes = sfad.computeSizes()
        objs_ref = sfad.computeReferenceObjects()
        goodsizes = [s for s in goodsizes if s>100]
        
        mingoodsize = min(goodsizes)
        maxgoodsize = max(goodsizes)
        objs_final = sfad.filterObjects(objs_user, objs_ref, mingoodsize, maxgoodsize)
        #create a new, filtered overlay:
        result = numpy.zeros(cc.shape, dtype = 'int32')
        objcounter = 1
        for iobj in objs_final:
            for i in range(len(iobj[0])):
                result[0, iobj[0][i], iobj[1][i], iobj[2][i], 0] = int(objcounter)
            objcounter = objcounter +1
        
        if self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Filtered"] is None:
            #colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            colortab = ConnectedComponentsModuleMgr.makeColorTab()
            myColor = OverlayItem.qrgb(255, 0, 0) #QtGui.QColor(255, 0, 0)
            ov = OverlayItem(result, color = myColor, alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Filtered"] = ov
        else:
            self.dataMgr[self.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Filtered"]._data = DataAccessor(result)        

    @classmethod
    def makeColorTab(cls):
        sublist = []
        #sublist.append(QtGui.qRgb(0, 0, 0))
        sublist.append(OverlayItem.qrgb(255, 255, 255))
        sublist.append(OverlayItem.qrgb(255, 0, 0))
        sublist.append(OverlayItem.qrgb(0, 255, 0))
        sublist.append(OverlayItem.qrgb(0, 0, 255))
        
        sublist.append(OverlayItem.qrgb(255, 255, 0))
        sublist.append(OverlayItem.qrgb(0, 255, 255))
        sublist.append(OverlayItem.qrgb(255, 0, 255))
        sublist.append(OverlayItem.qrgb(255, 105, 180)) #hot pink!
        
        sublist.append(OverlayItem.qrgb(102, 205, 170)) #dark aquamarine
        sublist.append(OverlayItem.qrgb(165,  42,  42)) #brown        
        sublist.append(OverlayItem.qrgb(0, 0, 128)) #navy
        sublist.append(OverlayItem.qrgb(255, 165, 0)) #orange
        
        sublist.append(OverlayItem.qrgb(173, 255,  47)) #green-yellow
        sublist.append(OverlayItem.qrgb(128,0, 128)) #purple
        sublist.append(OverlayItem.qrgb(192, 192, 192)) #silver
        sublist.append(OverlayItem.qrgb(240, 230, 140)) #khaki
        colorlist = []
        colorlist.append(long(0))
        colorlist.extend(sublist)
        
        for i in range(17, 256):
            color = OverlayItem.qrgb(numpy.random.randint(255),numpy.random.randint(255),numpy.random.randint(255))
            colorlist.append(color)
            
        return colorlist
    
    
class ConnectedComponents():
    def __init__(self):
        self.inputdata = None
        self.backgroundSet = set()
        
    def connect(self, inputData, background):
        vol, back_value = self.transformToVigra(inputData, background)
        res = None
        if back_value is not None:
            #FIXME: this assumes that the background value is an int
            #otherwise something does not work with vigrapython
            res = vigra.analysis.labelVolumeWithBackground(vol, 6, int(back_value))
        else:
            res = vigra.analysis.labelVolume(vol)
        if res is not None:
            res = res.swapaxes(0,2).view()
            res = numpy.asarray(res)
            res = res.reshape(res.shape + (1,))
            return res
        
    def transformToVigra(self, vol, background):
        if len(background)==0:
            return vol.swapaxes(0,2).view(), None
        else:
            vol_merged = vol
            back_value = background.pop()
            while len(background)>0:
                back_value_temp = background.pop()
                ind = numpy.where(vol_merged==back_value_temp)
                vol_merged[ind]=back_value
            return vol_merged.swapaxes(0,2).view(), back_value


class ConnectedComponentsThread(QtCore.QThread):
    def __init__(self, dataMgr, image, background=set(), connector = ConnectedComponents(), connectorOptions = None):
        QtCore.QThread.__init__(self, None)
        self._data = image
        self.backgroundSet = background
        self.dataMgr = dataMgr
        self.count = 0
        self.numberOfJobs = self._data.shape[0]
        self.stopped = False
        self.connector = connector
        self.connectorOptions = connectorOptions
        self.jobMachine = jobMachine.JobMachine()

    def connect(self, i, data, backgroundSet):
        self.result[i] = self.connector.connect(data, backgroundSet)
        self.count += 1

    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            self.result = range(0,self._data.shape[0])
            jobs = []
            for i in range(self._data.shape[0]):
                part = numpy.asarray(self._data[i, :, :, :, 0], dtype=self._data.dtype)               
                job = jobMachine.IlastikJob(ConnectedComponentsThread.connect, [self, i, part, self.backgroundSet])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.result = ListOfNDArraysAsNDArray(self.result)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ConnectedComponentsThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            
