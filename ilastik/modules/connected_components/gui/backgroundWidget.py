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

#*******************************************************************************
# B a c k g r o u n d I t e m                                                  *
#*******************************************************************************

class BackgroundItem(QtGui.QListWidgetItem):
    def __init__(self, name, number, color):
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


#*******************************************************************************
# B a c k g r o u n d W i d g e t                                              *
#*******************************************************************************

class BackgroundWidget(BaseLabelWidget,  QtGui.QGroupBox):
    def __init__(self,  backgroundMgr,  volumeLabels,  volumeEditor):
        QtGui.QGroupBox.__init__(self,  "Background")
        BaseLabelWidget.__init__(self,None)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setMargin(5)
        self.listWidget = QtGui.QListWidget(self)
        self.items = []
        
        self.layout().addWidget(self.listWidget)
        
        self.volumeEditor = volumeEditor
        self.labelMgr = backgroundMgr
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.connect(self.listWidget, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.volumeLabels = volumeLabels
        self.colorTab = []
        self.volumeEditor = volumeEditor
        self.labelColorTable = [QtGui.QColor(QtCore.Qt.red), QtGui.QColor(QtCore.Qt.green), QtGui.QColor(QtCore.Qt.yellow), QtGui.QColor(QtCore.Qt.blue), QtGui.QColor(QtCore.Qt.magenta) , QtGui.QColor(QtCore.Qt.darkYellow), QtGui.QColor(QtCore.Qt.lightGray)]
        #self.connect(self, QtCore.SIGNAL("currentTextChanged(QString)"), self.changeText)
        self.labelPropertiesChanged_callback = None
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        if len(volumeLabels.descriptions)>0:
            self.initFromVolumeLabels(volumeLabels)
        else:
            self.addLabel("Background", 1, self.labelColorTable[0])
        self.overlayItem = OverlayItem(self.labelMgr.background._data)    
    def currentItem(self):
        return self.listWidget.currentItem()
    
    def initFromVolumeLabels(self, volumelabel):
        self.volumeLabels = volumelabel
        #if len(volumelabel.descriptions)>0:
        for index, item in enumerate(volumelabel.descriptions):
            #item = volumelabel.descriptions[0]
            
            li = BackgroundItem(item.name,item.number, QtGui.QColor.fromRgba(long(item.color)))
            self.listWidget.addItem(li)
            self.items.append(li)
        self.buildColorTab()
        
        #just select the first item in the list so we have some selection
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(0,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
    def changeText(self, text):
        self.volumeLabel.descriptions[self.currentRow()].name = text
        
        
    def addLabel(self, labelName, labelNumber, color):
        self.labelMgr.addLabel(labelName,  labelNumber,  color.rgba())
        
        label =  BackgroundItem(labelName, labelNumber, color)
        self.items.append(label)
        self.listWidget.addItem(label)
        self.buildColorTab()
        
        #select the last item in the last
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(self.listWidget.model().rowCount()-1,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
        
    def buildColorTab(self):
        self.colorTab = self.volumeLabels.getColorTab()
        
    def getColorTab(self):
        self.buildColorTab()
        return self.colorTab 

    def onContext(self, pos):
        index = self.listWidget.indexAt(pos)

        if not index.isValid():
            return

        item = self.listWidget.itemAt(pos)

        menu = QtGui.QMenu(self)

        colorAction = menu.addAction("Change Color")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabels.descriptions[index.row()].color = color.rgba()

            self.buildColorTab()
            self.volumeEditor.repaint()

