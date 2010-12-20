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

from ilastik.core.volume import DataAccessor, Volume, VolumeLabels, VolumeLabelDescription

class LabelMgr(object):
    def __init__(self,  dataMgr, classificationMgr):
        self.dataMgr = dataMgr
        self.classificationMgr = classificationMgr
        
    def addLabel(self, name,number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        self.dataMgr.module["Classification"]["labelDescriptions"].append(description)
            

    def changeLabelName(self,  index, newName):
        labelItem = self.dataMgr.module["Classification"]["labelDescriptions"][index]
        ok = True
        for ii, it in enumerate(self.dataMgr.module["Classification"]["labelDescriptions"]):
            if it.name == newName:
                ok = False
        if ok:
            oldName = labelItem.name
            labelItem.name = newName
            for index, item in enumerate(self.dataMgr):
                #rename overlays
                o = item.overlayMgr["Classification/Prediction/" + oldName]
                if o is not None:
                    o.changeKey("Classification/Prediction/" + newName)
            return True
        else:
            return False
                                    
    def removeLabel(self, number):
        self.dataMgr.featureLock.acquire()
        self.classificationMgr.clearFeaturesAndTraining()
        ldnr = -1
        labelDescriptionToBeRemoved = None
        for labelIndex,  labelItem in enumerate(self.dataMgr.module["Classification"]["labelDescriptions"]):
            if labelItem.number == number:
                labelDescriptionToBeRemoved = labelItem
                ldnr = labelIndex
                self.dataMgr.module["Classification"]["labelDescriptions"].pop(ldnr)
                
        for labelIndex,  labelItem in enumerate(self.dataMgr.module["Classification"]["labelDescriptions"]):
            if labelItem.number > ldnr:
                labelItem.number -= 1
                
        for index, item in enumerate(self.dataMgr):
            if ldnr != -1:
                ldata = item.overlayMgr["Classification/Labels"] 
                temp = numpy.where(ldata[:,:,:,:,:] == number, 0, ldata[:,:,:,:,:])
                temp = numpy.where(temp[:,:,:,:,:] > number, temp[:,:,:,:,:] - 1, temp[:,:,:,:,:])
                ldata[:,:,:,:,:] = temp[:,:,:,:,:]
                if item.module["Classification"]["labelHistory"] is not None:
                    item.module["Classification"]["labelHistory"].removeLabel(number)
                
                #remove overlays
            if labelDescriptionToBeRemoved is not None:
                o = item.overlayMgr["Classification/Prediction/" + labelDescriptionToBeRemoved.name]
                if o is not None:
                    item.overlayMgr.remove("Classification/Prediction/" + labelDescriptionToBeRemoved.name)                    
        del labelDescriptionToBeRemoved
        self.dataMgr.featureLock.release()
        
        
    def clearLabel(self, number):
        self.dataMgr.featureLock.acquire()
        self.classificationMgr.clearFeaturesAndTraining()

        di = self.dataMgr[self.dataMgr._activeImageNumber]
        ov = di.overlayMgr["Classification/Labels"] 
        
        if ov is not None:        
            data = ov[:,:,:,:,:]
            
            data = numpy.where(data == number, 0, data)
            ov[:,:,:,:,:] = data
        self.dataMgr.featureLock.release()

        
    def newLabels(self,  newLabels):
        self.classificationMgr.updateTrainingMatrix(newLabels)
