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
import numpy, h5py
        
#*******************************************************************************
# S e e d L i s t I t e m                                                      *
#*******************************************************************************

class SeedListItem(QtGui.QListWidgetItem):
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

#*******************************************************************************
# S e e d L i s t W i d g e t                                                  *
#*******************************************************************************

class SeedListWidget(BaseLabelWidget,  QtGui.QGroupBox):
    def __init__(self,  labelMgr,  volumeLabels,  volumeEditor,  overlayItem):
        QtGui.QGroupBox.__init__(self,  "Seeds")
        BaseLabelWidget.__init__(self,None)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setMargin(5)
        
        self.listWidget = QtGui.QListWidget(self)
        self.overlayItem = overlayItem
        
        #Label selector
        self.addLabelButton = QtGui.QToolButton()
        self.addLabelButton.setText("Create Seed")
        self.addLabelButton.connect(self.addLabelButton, QtCore.SIGNAL("pressed()"), self.createLabel)

        self.layout().addWidget(self.addLabelButton)
        self.layout().addWidget(self.listWidget)
        
        self.ilastik = volumeEditor.ilastik
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
            self.addLabel("Background", 1, QtGui.QColor(255,0,0))   
    
    def currentItem(self):
        return self.listWidget.currentItem()
    
    def onImageSceneContext(self, imageScene, pos):
        overlayMgr = self.volumeEditor.ilastik._activeImage.overlayMgr
        doneOverlay = overlayMgr["Segmentation/Done"]
        if not doneOverlay: return
        c = imageScene.coordinateUnderCursor()
        print "Right click on coordinate", c
        label = doneOverlay._data[0,c[0],c[1],c[2],0]
        if label == 0: return
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        key = s.segmentKeyForLabel(label)
        
        menu = QtGui.QMenu(self)
        act = menu.addAction("Object #%d [%s]" % (label, key))
        act.setEnabled(False)
        font = QtGui.QFont( "Helvetica", 10, QtGui.QFont.Bold, True)
        act.setFont(font)
        
        display3dAction = menu.addAction("Display 3D")
        correctAction   = menu.addAction("Correct")
        removeAction    = menu.addAction("Remove")
        
        imageScene.connect(display3dAction, QtCore.SIGNAL("triggered()"), lambda label=label: self.displaySegmentation3D(label))
        imageScene.connect(correctAction,   QtCore.SIGNAL("triggered()"), lambda key=key: s.editSegmentsByKey(key)  )
        imageScene.connect(removeAction,    QtCore.SIGNAL("triggered()"), lambda key=key: s.removeSegmentsByKey(key))
        
        menu.exec_(QtGui.QCursor.pos())
    
    def displaySegmentation3D(self, label):
        segmentationOverlay = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        seg = s.segmentation
        if s.segmentation is None:
            f = h5py.File(s.outputPath+'/'+s.segmentKeyForLabel(label)+'/'+'segmentation.h5')
            seg = f['volume/data'][0,:,:,:,0]
            del f
            
        self.volumeEditor.overview.SetColorTable(segmentationOverlay.colorTable)
        self.volumeEditor.overview.DisplayObjectMeshes(seg, set([1]), True)
        
    def initFromVolumeLabels(self, volumelabel):
        self.volumeLabel = volumelabel
        for index, item in enumerate(volumelabel.descriptions):
            li = SeedListItem(item.name,item.number, QtGui.QColor.fromRgba(long(item.color)))
            self.listWidget.addItem(li)
            self.items.append(li)
        self.buildColorTab()
        
        #just select the first item in the list so we have some selection
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(0,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
    def changeText(self, text):
        self.volumeLabel.descriptions[self.currentRow()].name = text
        
    def createLabel(self):
        name = "Seed " + len(self.items).__str__()
        number = len(self.items)
        if number >= len(self.labelColorTable):
            color = QtGui.QColor.fromRgb(numpy.random.randint(255),numpy.random.randint(255),numpy.random.randint(255))
        else:
            color = self.labelColorTable[number]
        number +=1
        self.addLabel(name, number, color)
        self.buildColorTab()
        
    def addLabel(self, labelName, labelNumber, color):
        self.labelMgr.addLabel(labelName,  labelNumber,  color.rgba())
        
        label =  SeedListItem(labelName, labelNumber, color)
        self.items.append(label)
        self.listWidget.addItem(label)
        self.buildColorTab()
        
        #select the last item in the last
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(self.listWidget.model().rowCount()-1,0), QtGui.QItemSelectionModel.ClearAndSelect)
         
    def removeLabel(self, item,  index):
        self.labelMgr.removeLabel(item.number)
        
        self.volumeEditor._history.removeLabel(item.number)
        for ii, it in enumerate(self.items):
            if it.number > item.number:
                it.number -= 1
        self.items.remove(item)
        it = self.listWidget.takeItem(index.row())
        del it
        self.buildColorTab()
        self.volumeEditor.emit(QtCore.SIGNAL("seedRemoved(int)"), item.number)
        self.volumeEditor.repaint()
        
    def buildColorTab(self):
        origColorTable = self.volumeLabels.getColorTab()
        self.overlayItem.colorTable = self.colorTab = origColorTable

    def count(self):
        return self.listWidget.count()

    def onContext(self, pos):
        index = self.listWidget.indexAt(pos)

        if not index.isValid():
            return

        item = self.listWidget.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        removeAction = menu.addAction("Remove")
        colorAction = menu.addAction("Change Color")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == removeAction:
            self.removeLabel(item,  index)
        elif action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabel.descriptions[index.row()].color = color.rgba()
            
#            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
            if self.labelPropertiesChanged_callback is not None:
                self.labelPropertiesChanged_callback()
            self.buildColorTab()
            self.volumeEditor.repaint()

    def nextLabel(self):
        print "next seed"
        i = self.listWidget.selectedIndexes()[0].row()
        if i+1 == self.listWidget.model().rowCount():
            i = self.listWidget.model().index(0,0)
        else:
            i = self.listWidget.model().index(i+1,0)
        self.listWidget.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.ClearAndSelect)

    def prevLabel(self):
        print "prev seed"
        i = self.listWidget.selectedIndexes()[0].row()
        if i >  0:
            i = self.listWidget.model().index(i-1,0)
        else:
            i = self.listWidget.model().index(self.listWidget.model().rowCount()-1,0)
        self.listWidget.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.ClearAndSelect)

