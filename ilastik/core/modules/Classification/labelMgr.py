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
from ilastik.core.classificationMgr import ClassificationMgr

class LabelMgr(object):
    def __init__(self,  dataMgr, classificationMgr):
        self.dataMgr = dataMgr
        self.classificationMgr = classificationMgr
        
    def addLabel(self, name,number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        self.dataMgr.properties["Classification"]["labelDescriptions"].append(description)
            

    def changedLabel(self,  label):
        for labelIndex,  labelItem in self.dataMgr.properties["Classification"]["labelDescriptions"]:
            labelItem.name = label.name
            labelItem.number = label.number
            labelItem.color = label.color
                
    def removeLabel(self, number):
        self.dataMgr.featureLock.acquire()
        self.classificationMgr.clearFeaturesAndTraining()
        ldnr = -1
        for labelIndex,  labelItem in enumerate(self.dataMgr.properties["Classification"]["labelDescriptions"]):
            if labelItem.number == number:
                ldnr = labelIndex
                self.dataMgr.properties["Classification"]["labelDescriptions"].pop(ldnr)
                
        for labelIndex,  labelItem in enumerate(self.dataMgr.properties["Classification"]["labelDescriptions"]):
            if labelItem.number > ldnr:
                labelItem.number -= 1
                
        for index, item in enumerate(self.dataMgr):
            if ldnr != -1:
                ldata = item.overlayMgr["Classification/Labels"] 
                temp = numpy.where(ldata[:,:,:,:,:] == number, 0, ldata[:,:,:,:,:])
                temp = numpy.where(temp[:,:,:,:,:] > number, temp[:,:,:,:,:] - 1, temp[:,:,:,:,:])
                ldata[:,:,:,:,:] = temp[:,:,:,:,:]
                if item.properties["Classification"]["labelHistory"] is not None:
                    item.properties["Classification"]["labelHistory"].removeLabel(number)
        self.dataMgr.featureLock.release()
        
    def newLabels(self,  newLabels):
        self.classificationMgr.updateTrainingMatrix(newLabels)
