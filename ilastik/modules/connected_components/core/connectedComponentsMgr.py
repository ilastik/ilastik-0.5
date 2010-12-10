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

import vigra, numpy
import traceback, sys
import threading
from ilastik.core.volume import VolumeLabels, VolumeLabelDescription
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core import jobMachine
from listOfNDArraysAsNDArray import ListOfNDArraysAsNDArray

try:
    from PyQt4 import QtCore
    ThreadBase = QtCore.QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False

class BackgroundOverlayItem(OverlayItem):
    def __init__(self, dataitemImage, backgroundListWidget, data, color = 0, alpha = 0.4, colorTable = None, autoAdd = False, autoVisible = False,  linkColorTable = False, autoAlphaChannel = True, min = None, max = None):
        self.backgroundListWidget = backgroundListWidget
        OverlayItem.__init__(self, dataitemImage, data, color, alpha, autoAdd, autoVisible,  linkColorTable, autoAlphaChannel, min, max)
        
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



class ConnectedComponents():
    def __init__(self):
        self.inputdata = None
        self.backgroundSet = set()
        
    def connect(self, inputData, background):
        vol, back_value = self.transformToVigra(inputData, background)
        res = None
        if back_value is not None:
            res = vigra.analysis.labelVolumeWithBackground(vol, 6, float(back_value))
        else:
            res = vigra.analysis.labelVolume(vol)
        if res is not None:
            res = res.swapaxes(0,2).view(vigra.ScalarVolume)
            res = res.reshape(res.shape + (1,))
            return numpy.array(res)
        
    def transformToVigra(self, vol, background):
        if len(background)==0:
            return vigra.ScalarVolume(vol), None
        else:
            vol_merged = vol
            back_value = background.pop()
            #for i in range(len(background)):
            while len(background)>0:
                back_value_temp = background.pop()
                ind = numpy.where(vol_merged==back_value_temp)
                vol_merged[ind]=float(back_value)
            return vigra.ScalarVolume(vol_merged), back_value


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
                job = jobMachine.IlastikJob(ConnectedComponentsThread.connect, [self, i, self._data[i,:,:,:,0], self.backgroundSet])
                jobs.append(job)
            self.jobMachine.process(jobs)
            self.result = ListOfNDArraysAsNDArray(self.result)
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)
            self.dataMgr.featureLock.release()
            
