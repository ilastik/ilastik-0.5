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

from ilastik.gui.baseLabelWidget import BaseLabelWidget
from ilastik.core.overlayMgr import OverlayItem
import numpy
        
class ObjectListItem(QtGui.QListWidgetItem):
    def __init__(self, name , number, color):
        QtGui.QListWidgetItem.__init__(self, name)
        self.number = number
        self.visible = True
        self.setColor(color)
        #self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        #self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        

    def toggleVisible(self):
        self.visible = not(self.visible)

    def setColor(self, color):
        self.color = color
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(color)
        icon = QtGui.QIcon(pixmap)
        self.setIcon(icon)      


class ObjectListWidget(BaseLabelWidget,  QtGui.QGroupBox):
    def __init__(self,  labelMgr,  volumeLabels,  volumeEditor):
        QtGui.QGroupBox.__init__(self,  "Object Picker")
        BaseLabelWidget.__init__(self,None)
        self.setLayout(QtGui.QVBoxLayout())
        self.listWidget = QtGui.QListWidget(self)
        self.layout().addWidget(self.listWidget)

        self.volumeEditor = volumeEditor
        self.labelMgr = labelMgr
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.connect(self.listWidget, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.volumeLabels = volumeLabels
        self.colorTab = []
        self.items = []
        self.volumeEditor = volumeEditor
        self.labelColorTable = [QtGui.QColor(QtCore.Qt.red), QtGui.QColor(QtCore.Qt.green), QtGui.QColor(QtCore.Qt.yellow), QtGui.QColor(QtCore.Qt.blue), QtGui.QColor(QtCore.Qt.magenta) , QtGui.QColor(QtCore.Qt.darkYellow), QtGui.QColor(QtCore.Qt.lightGray)]
        #self.connect(self, QtCore.SIGNAL("currentTextChanged(QString)"), self.changeText)
        self.labelPropertiesChanged_callback = None
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.initFromVolumeLabels(volumeLabels)
        
        if self.listWidget.model().rowCount() == 0:
            self.addLabel("Picker", 1, QtGui.QColor(0,0,255))
            
        self.overlayItem = OverlayItem(self.volumeEditor.ilastik._activeImage, self.labelMgr.objects._data)
    
    def currentItem(self):
        return self.listWidget.currentItem()
    
    def initFromVolumeLabels(self, volumelabel):
        self.volumeLabel = volumelabel
        for index, item in enumerate(volumelabel.descriptions):
            li = ObjectListItem(item.name,item.number, QtGui.QColor.fromRgba(long(item.color)))
            self.listWidget.addItem(li)
            self.items.append(li)
        
        #just select the first item in the list so we have some selection
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(0,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
    def changeText(self, text):
        self.volumeLabel.descriptions[self.currentRow()].name = text
               
    def addLabel(self, labelName, labelNumber, color):
        self.labelMgr.addLabel(labelName,  labelNumber,  color.rgba())
        
        label =  ObjectListItem(labelName, labelNumber, color)
        self.items.append(label)
        self.listWidget.addItem(label)
        
        #select the last item in the last
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(self.listWidget.model().rowCount()-1,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
               

    def getColorTab(self):
        return self.volumeLabels.getColorTab()

    def onContext(self, pos):
        index = self.listWidget.indexAt(pos)

        if not index.isValid():
           return

        item = self.listWidget.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        colorAction = menu.addAction("Change Color")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabel.descriptions[index.row()].color = color.rgba()
            
#            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
            if self.labelPropertiesChanged_callback is not None:
                self.labelPropertiesChanged_callback()
            self.volumeEditor.repaint()

    def nextLabel(self):
        i = self.listWidget.selectedIndexes()[0].row()
        if i+1 == self.listWidget.model().rowCount():
            i = self.listWidget.model().index(0,0)
        else:
            i = self.listWidget.model().index(i+1,0)
        self.listWidget.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.ClearAndSelect)

    def prevLabel(self):
        i = self.listWidget.selectedIndexes()[0].row()
        if i >  0:
            i = self.listWidget.model().index(i-1,0)
        else:
            i = self.listWidget.model().index(self.listWidget.model().rowCount()-1,0)
        self.listWidget.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.ClearAndSelect)
