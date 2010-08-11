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

from PyQt4 import QtCore, QtGui
import vigra, numpy
import sip

from ilastik.core.volume import DataAccessor, Volume, VolumeLabels, VolumeLabelDescription
from ilastik.core.overlayMgr import OverlayMgr,  OverlayItem, OverlaySlice

class OverlayListWidgetItem(QtGui.QListWidgetItem):
    def __init__(self, overlayItem):
        QtGui.QListWidgetItem.__init__(self,overlayItem.name)
        self.overlayItem = overlayItem
        self.name = overlayItem.name
        self.color = self.overlayItem.color
        self.colorTab = self.overlayItem.colorTable
        self.visible = True

        s = QtCore.Qt.Checked

        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        self.setCheckState(s)


class OverlayListWidget(QtGui.QListWidget):

    class QAlphaSliderDialog(QtGui.QDialog):
        def __init__(self, min, max, value):
            QtGui.QDialog.__init__(self)
            self.setWindowTitle('Change Alpha')
            self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
            self.slider.setGeometry(20, 30, 140, 20)
            self.slider.setRange(min,max)
            self.slider.setValue(value)

    def __init__(self,parent, overlays):
        QtGui.QListWidget.__init__(self, parent)
        self.volumeEditor = parent
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.connect(self, QtCore.SIGNAL("clicked(QModelIndex)"), self.onItemClick)
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.onItemDoubleClick)
        self.overlays = overlays  #array of VolumeOverlays
        self.currentItem = None
        for overlay in self.overlays:
            self.addItem(OverlayListWidgetItem(overlay))

    def onItemClick(self, itemIndex):
        item = self.itemFromIndex(itemIndex)
        if (item.checkState() == QtCore.Qt.Checked and not item.overlayItem.visible) or (item.checkState() == QtCore.Qt.Unchecked and item.overlayItem.visible):
            item.overlayItem.visible = not(item.overlayItem.visible)
            s = None
            if item.overlayItem.visible:
                s = QtCore.Qt.Checked
            else:
                s = QtCore.Qt.Unchecked
            item.setCheckState(s)
            self.volumeEditor.repaint()
            
    def onItemDoubleClick(self, itemIndex):
        self.currentItem = item = self.itemFromIndex(itemIndex)
        if item.checkState() == item.visible * 2:
            dialog = OverlayListWidget.QAlphaSliderDialog(1, 20, round(item.overlayItem.alpha*20))
            dialog.slider.connect(dialog.slider, QtCore.SIGNAL('valueChanged(int)'), self.setCurrentItemAlpha)
            dialog.exec_()
        else:
            self.onItemClick(self,itemIndex)
            
            
    def setCurrentItemAlpha(self, num):
        self.currentItem.overlayItem.alpha = 1.0 * num / 20.0
        self.volumeEditor.repaint()
        
#    def clearOverlays(self):
#        self.clear()
#        self.overlays = []

    def removeOverlay(self, item):
        itemNr = None
        if isinstance(item, str):
            for idx, it in enumerate(self.overlays):
                if it.name == item:
                    itemNr = idx
                    item = it
        else:
            itemNr = item
        if itemNr != None:
            self.overlays.pop(itemNr)
            self.takeItem(itemNr)
            return item
        else:
            return None

    def addOverlay(self, overlay):
        self.overlays.append(overlay)
        self.addItem(OverlayListWidgetItem(overlay))

    def onContext(self, pos):
        index = self.indexAt(pos)

        if not index.isValid():
           return

        item = self.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        show3dAction = menu.addAction("Display in Mayavi")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == show3dAction:
#            mlab.contour3d(item.data[0,:,:,:,0], opacity=0.6)
#            mlab.outline()
            my_model = MayaviQWidget(item[0,:,:,:,0], self.volumeEditor.image[0,:,:,:,0])
            my_model.show()
    """
    Class that manages the different labels (VolumeLabelDescriptions) for one Volume

    can serialize and deserialize into a h5py group
    """

    def getLabelNames(self):
        labelNames = []
        for idx, it in enumerate(self.descriptions):
            labelNames.append(it.name)
        return labelNames
       
      
    def toggleVisible(self,  index):
        state = not(item.overlayItem.visible)
        item.overlayItem.visible = state
        item.setCheckState(item.overlayItem.visible * 2)

    """
    Represents a data volume including labels etc.
    
    can serialize and deserialize into a h5py group
    """
