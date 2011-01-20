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
import traceback, os, sys

from ilastik.core.volume import DataAccessor, VolumeLabels, VolumeLabelDescription
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr
from ilastik.core.overlayMgr import OverlayItem


class ObjectOverlayItem(OverlayItem):
    def __init__(self, objectListWidget, data, color = 0, alpha = 0.4, colorTable = None, autoAdd = False, autoVisible = False,  linkColorTable = False, autoAlphaChannel = True, min = None, max = None):
        self.objectListWidget = objectListWidget
        OverlayItem.__init__(self, data, color, alpha, autoAdd, autoVisible,  linkColorTable, autoAlphaChannel, min, max)
        
    def getColorTab(self):
        return self.objectListWidget.getColorTab()


class ObjectPickingItemModuleMgr(BaseModuleDataItemMgr):
    name = "Object_Picking"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.objects = None
        self.overlays = []
        self.selectedObjects = {}
        self.selectionAccessor = None
        self.inputData = None
        
    def onAppend(self):
        if self.objects is None:
            l = numpy.zeros(self.dataItemImage.shape[0:-1] + (1, ),  'uint8')
            self.objects = VolumeLabels(l)        

    def newLabels(self,  newLabels):
        repaint = False
        if self.inputData is not None:
            try:
                for nl in newLabels:
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]
                    for index, ind0 in enumerate(indic[0]):
                        selector = (indic[0][index],indic[1][index],indic[2][index],indic[3][index],indic[4][index])
                        res = self.inputData[selector]
                        if nl.erasing == False:
                            self.selectedObjects[res] = res
                        else:
                            self.selectedObjects.pop(res, None)
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
        
        ov = self.dataItemImage.overlayMgr["Objects/Selection Result"]
        
        if ov is not None:
            ov.setSelectedNumbers(self.selectedObjects.values())


    def addLabel(self, name,number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        description._prediction = numpy.zeros(self.dataItemImage.shape[0:-1],  'uint8')
        self.objects.descriptions.append(description)
            

    def changedLabel(self,  label):
        for labelIndex,  labelItem in enumerate(self.objects):
            labelItem.name = label.name
            labelItem.number = label.number
            labelItem.color = label.color
                
    def removeLabel(self, number):
        for j, ld in enumerate(self.objects.descriptions):
            if ld.number == number:
                ldnr = j
        if ldnr != -1:
            self.objects.descriptions.pop(ldnr)
            for j, ld in enumerate(self.objects.descriptions):
                if ld.number > number:
                    ld.number -= 1
            temp = numpy.where(self.objects._data[:,:,:,:,:] == number, 0, self.objects._data[:,:,:,:,:])
            temp = numpy.where(temp[:,:,:,:,:] > number, temp[:,:,:,:,:] - 1, temp[:,:,:,:,:])
            self.objects._data[:,:,:,:,:] = temp[:,:,:,:,:]
            if self.objects._history is not None:
                self.objects._history.removeLabel(number)
       
    def setInputData(self, data):
        self.inputData = data





class ObjectPickingModuleMgr(BaseModuleMgr):
    name = "Object_Picking"
    
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        self.dataMgr = dataMgr
        
        
        
        
    def onNewImage(self, dataItemImage):
        dataItemImage.Object_Picking.onAppend()

        

        

    
    
    
