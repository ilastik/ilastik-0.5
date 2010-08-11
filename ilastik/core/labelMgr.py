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

#        #TODO: this whole method is so ugly, it should be forbidden !
#        
#        activeItem = self.project.dataMgr[self.activeImage]
#        self.labelWidget.overlayView.clearOverlays()
#
#        for imageIndex, imageItem in  enumerate(self.project.dataMgr):           
#            if imageIndex != self.activeImage:
#                if imageItem.dataVol.labels is None:
#                    imageItem.dataVol.labels = ve.VolumeLabels(ve.DataAccessor(numpy.zeros((imageItem.dataVol.data.shape[0:4]),'uint8')))
#                else:
#                    for ii, itemii in enumerate(activeItem.dataVol.labels.descriptions):
#                        if ii < len(imageItem.dataVol.labels.descriptions):
#                            if not (imageItem.dataVol.labels.descriptions[ii] ==  itemii):
#                                imageItem.dataVol.labels.descriptions[ii] = itemii.clone()
#                                imageItem.dataVol.labels.descriptions[ii].prediction = None
#                        else:
#                            imageItem.dataVol.labels.descriptions.append(itemii.clone())
#                            imageItem.dataVol.labels.descriptions[ii].prediction = None
#            else:
#                if imageItem.dataVol.labels.data is None:
#                    imageItem.dataVol.labels.data = ve.DataAccessor(numpy.zeros((imageItem.dataVol.data.shape[0:4]),'uint8'))
#
#        for imageIndex, imageItem in  enumerate(self.project.dataMgr):            
#            for p_i, item in enumerate(imageItem.dataVol.labels.descriptions):
#                if item.prediction is None:
#                   item.prediction = numpy.zeros(imageItem.dataVol.data.shape[0:-1],'uint8')
#                if imageIndex == self.activeImage:
#                    color = QtGui.QColor.fromRgb(long(item.color))
#                    self.labelWidget.addOverlay(True, item.prediction, item.name, color, 0.4)
#            
#            if imageItem.dataVol.uncertainty is None:
#                imageItem.dataVol.uncertainty = numpy.zeros( imageItem.dataVol.data.shape[0:-1] ,'uint8')
#
#            if imageIndex == self.activeImage: 
#                self.labelWidget.addOverlay(False, activeItem.dataVol.uncertainty, "Uncertainty", QtGui.QColor(255,0,0), 0.9)


from ilastik.core.volume import DataAccessor, Volume, VolumeLabels, VolumeLabelDescription

class LabelMgr(object):
    def __init__(self,  dataMgr):
        self.dataMgr = dataMgr
        
    def addLabel(self, name,number, color):
        description = VolumeLabelDescription(name,number, color,  None)
        
        for imageIndex, imageItem in  enumerate(self.dataMgr):
            descr = description.clone()
            descr.prediction = numpy.zeros(imageItem.dataVol.data.shape[0:-1],  'uint8')
            imageItem.dataVol.labels.descriptions.append(descr)
            

    def changedLabel(self,  label):
        for imageIndex, imageItem in  enumerate(self.dataMgr):
            for labelIndex,  labelItem in enumerate(imageItem.dataVol.labels):
                labelItem.name = label.name
                labelItem.number = label.number
                labelItem.color = label.color
                
    def removeLabel(self,  index):
        for imageIndex, imageItem in  enumerate(self.dataMgr):
            descr = imageItem.dataVol.labels.descriptions.pop(index-1)
            descr.prediction = None
            #TODO: also remove the labelNumber from the imageItem.labels and decrease the others -1
            #TODO: also update the imageItem history !
        
    def newLabels(self,  newLabels):
        self.dataMgr.updateTrainingMatrix(newLabels)
