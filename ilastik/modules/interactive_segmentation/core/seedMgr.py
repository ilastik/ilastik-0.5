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

class SeedMgr(object):
    """
    manages the seeds of all dataItems and stuff.
    seeds (as labels) should be synchronized across all dataItems because it is a good idead.
    """
    def __init__(self,  dataMgr):
        self.dataMgr = dataMgr
        
    def addLabel(self, name,number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        
        for imageIndex, imageItem in  enumerate(self.dataMgr):
            descr = description.clone()
            descr._prediction = numpy.zeros(imageItem._dataVol._data.shape[0:-1],  'uint8')
            imageItem.Interactive_Segmentation.seeds.descriptions.append(descr)
            

    def changedLabel(self,  label):
        for imageIndex, imageItem in  enumerate(self.dataMgr):
            for labelIndex,  labelItem in enumerate(imageItem.Interactive_Segmentation.seeds):
                labelItem.name = label.name
                labelItem.number = label.number
                labelItem.color = label.color
                
    def removeLabel(self, number):
        self.dataMgr.featureLock.acquire()
        for index, item in enumerate(self.dataMgr):
            ldnr = -1
            for j, ld in enumerate(item.Interactive_Segmentation.seeds.descriptions):
                if ld.number == number:
                    ldnr = j
            if ldnr != -1:
                item.Interactive_Segmentation.seeds.descriptions.pop(ldnr)
                for j, ld in enumerate(item.Interactive_Segmentation.seeds.descriptions):
                    if ld.number > number:
                        ld.number -= 1
                temp = numpy.where(item.Interactive_Segmentation.seeds._data[:,:,:,:,:] == number, 0, item.Interactive_Segmentation.seeds._data[:,:,:,:,:])
                temp = numpy.where(temp[:,:,:,:,:] > number, temp[:,:,:,:,:] - 1, temp[:,:,:,:,:])
                item.Interactive_Segmentation.seeds._data[:,:,:,:,:] = temp[:,:,:,:,:]
                if item.Interactive_Segmentation.seeds._history is not None:
                    item.Interactive_Segmentation.seeds._history.removeLabel(number)
            item.Interactive_Segmentation.clearSeeds()
            
        self.dataMgr.featureLock.release()

        
    def newLabels(self,  newLabels):
        self.dataMgr[self.dataMgr._activeImageNumber].Interactive_Segmentation.updateSeeds(newLabels)
