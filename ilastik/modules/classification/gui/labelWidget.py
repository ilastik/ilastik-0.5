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
import numpy
        
from ilastik.gui.iconMgr import ilastikIcons
#*******************************************************************************
# L a b e l L i s t I t e m                                                    *
#*******************************************************************************

class LabelListItem(QtGui.QListWidgetItem):
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
# L a b e l L i s t W i d g e t                                                *
#*******************************************************************************

class LabelListWidget(BaseLabelWidget,  QtGui.QGroupBox):
    def __init__(self,  labelMgr,  volumeLabelDescriptions, volumeEditor,  overlayItem):
        QtGui.QGroupBox.__init__(self, "Labels")
        BaseLabelWidget.__init__(self, None)
        self.setLayout(QtGui.QVBoxLayout())
        self.listWidget = QtGui.QListWidget(self)
        self.overlayItem = overlayItem
        self.volumeLabelDescriptions = volumeLabelDescriptions
        #Label selector
        self.addLabelButton = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.AddSel),"Create Class")
        #self.addLabelButton.setText("Create Class")
        self.addLabelButton.connect(self.addLabelButton, QtCore.SIGNAL("pressed()"), self.createLabel)

        self.layout().setMargin(5)
        self.layout().addWidget(self.addLabelButton)
        self.layout().addWidget(self.listWidget)
        
        self.volumeEditor = volumeEditor
        self.labelMgr = labelMgr
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.connect(self.listWidget, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.colorTab = []
        self.items = []
        self.labelColorTable = [QtGui.QColor(QtCore.Qt.red), QtGui.QColor(QtCore.Qt.green), QtGui.QColor(QtCore.Qt.yellow), QtGui.QColor(QtCore.Qt.blue), QtGui.QColor(QtCore.Qt.magenta) , QtGui.QColor(QtCore.Qt.darkYellow), QtGui.QColor(QtCore.Qt.lightGray)]
        #self.connect(self, QtCore.SIGNAL("currentTextChanged(QString)"), self.changeText)
        
        self.connect(self.listWidget, QtCore.SIGNAL("itemSelectionChanged()"), self.changeLabel)
        self.labelPropertiesChanged_callback = None
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.initFromVolumeLabelDescriptions(volumeLabelDescriptions)
    
    def onImageSceneContext(self, imageScene, pos):
        menu = QtGui.QMenu('Labeling menu', self)
       
        labelList = []
        
        volumeLabel = self.volumeEditor.labelWidget.volumeLabelDescriptions

        act = menu.addAction("Labels")
        act.setEnabled(False)
        font = QtGui.QFont( "Helvetica", 10, QtGui.QFont.Bold, True)
        act.setFont(font)
        
        for index, item in enumerate(volumeLabel):
            labelColor = QtGui.QColor.fromRgb(long(item.color))
            labelIndex = item.number
            labelName = item.name
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(labelColor)
            icon = QtGui.QIcon(pixmap)
            
            act = QtGui.QAction(icon, labelName, menu)
            i = imageScene.volumeEditor.labelWidget.listWidget.model().index(labelIndex-1,0)
            # print self.volumeEditor.labelView.selectionModel()
            imageScene.connect(act, QtCore.SIGNAL("triggered()"), lambda i=i: imageScene.onContextSetLabel(i))
            labelList.append(menu.addAction(act))
            
        if imageScene.drawManager.erasing is False:
            eraseAct = QtGui.QAction("Enable eraser", menu)
            menu.addAction(eraseAct)
            imageScene.connect(eraseAct, QtCore.SIGNAL("triggered()"), lambda: imageScene.drawManager.toggleErase())
        else:
            eraseAct = QtGui.QAction("Disable eraser", menu)
            menu.addAction(eraseAct)
            imageScene.connect(eraseAct, QtCore.SIGNAL("triggered()"), lambda: imageScene.drawManager.toggleErase())
            
        menu.addSeparator()
        # brushM = labeling.addMenu("Brush size")
        brushGroup = QtGui.QActionGroup(self)

        act = menu.addAction("Brush Sizes")
        act.setEnabled(False)
        font = QtGui.QFont( "Helvetica", 10, QtGui.QFont.Bold, True)
        act.setFont(font)
        menu.addSeparator()
        
        defaultBrushSizes = [(1, ""), (3, " Tiny"),(5, " Small"),(7, " Medium"),(11, " Large"),(23, " Huge"),(31, " Megahuge"),(61, " Gigahuge")]
        brush = []
        for ind, bSizes in enumerate(defaultBrushSizes):
            b = bSizes[0]
            desc = bSizes[1]
            act = QtGui.QAction("  " + str(b) + desc, brushGroup)
            act.setCheckable(True)
            imageScene.connect(act, QtCore.SIGNAL("triggered()"), lambda b=b: imageScene.drawManager.setBrushSize(b))
            if b == imageScene.drawManager.getBrushSize():
                act.setChecked(True)
            brush.append(menu.addAction(act))
        
        action = menu.exec_(QtGui.QCursor.pos())
        
    def currentItem(self):
        return self.listWidget.currentItem()
    
    def initFromVolumeLabelDescriptions(self, volumeLabelDescriptions):
        self.volumeLabelDescriptions = volumeLabelDescriptions
        for index, item in enumerate(volumeLabelDescriptions):
            li = LabelListItem(item.name,item.number, QtGui.QColor.fromRgba(long(item.color)))
            self.listWidget.addItem(li)
            self.items.append(li)
        self.buildColorTab()
        
        #just select the first item in the list so we have some selection
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(0,0), QtGui.QItemSelectionModel.ClearAndSelect)


    def changeLabelName(self, index, name):
        self.labelMgr.changeLabelName(index, name)
        
    def createLabel(self):
        name = "Label " + len(self.items).__str__()
        for index, item in enumerate(self.items):
            if str(item.text()) == name:
                name = name + "-2"
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
        
        label =  LabelListItem(labelName, labelNumber, color)
        self.items.append(label)
        self.listWidget.addItem(label)
        self.buildColorTab()
        
        #select the last item in the last
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(self.listWidget.model().rowCount()-1,0), QtGui.QItemSelectionModel.ClearAndSelect)
        
        
    def removeLabel(self, item,  index):
        self.labelMgr.removeLabel(item.number)
        
        self.volumeEditor._history.removeLabel(item.number)
        
        self.items.remove(item)
        it = self.listWidget.takeItem(index.row())
        del it
        for ii, it in enumerate(self.items):
            if it.number > item.number:
                it.number -= 1
        self.buildColorTab()
        self.volumeEditor.emit(QtCore.SIGNAL("labelRemoved(int)"), item.number)
        self.volumeEditor.repaint()
        

    def buildColorTab(self):
        self.overlayItem.colorTable = self.colorTab = self.volumeLabelDescriptions.getColorTab()
        


    
    def onContext(self, pos):
        if not self._contextMenuEnables:
            return
        index = self.listWidget.indexAt(pos)

        if not index.isValid():
            return

        item = self.listWidget.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        removeAction = menu.addAction("Remove")
        colorAction = menu.addAction("Change Color")
        renameAction = menu.addAction("Change Name")
        clearAction = menu.addAction("Clear Label")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == removeAction:
            if QtGui.QMessageBox.question(self, "Remove label", "Really clear " + self.volumeLabelDescriptions[index.row()].name + "?", buttons = QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)  != QtGui.QMessageBox.Cancel:
                self.removeLabel(item,  index)
        elif action == renameAction:
            newName, ok = QtGui.QInputDialog.getText(self, "Enter Labelname", "Labelname:", text = item.text())
            if ok:
                item.setText(newName)
                result = self.labelMgr.changeLabelName(index.row(),str(newName))
                #print result
        elif action == clearAction:
            if QtGui.QMessageBox.question(self, "Clear label", "Are you sure you want to clear " + self.volumeLabelDescriptions[index.row()].name + "?", buttons = QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)  != QtGui.QMessageBox.Cancel:
                number = self.volumeLabelDescriptions[index.row()].number
                self.labelMgr.clearLabel(number)        
                self.volumeEditor.repaint()        

            
            
        elif action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabelDescriptions[index.row()].color = color.rgba()
            
#            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
            if self.labelPropertiesChanged_callback is not None:
                self.labelPropertiesChanged_callback()
            self.buildColorTab()
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
        
    def changeLabel(self):
        for i in range(0, len(self.volumeEditor.imageScenes)):
            if self.listWidget.currentItem() is not None:
                self.volumeEditor.imageScenes[i].crossHairCursor.setColor(self.listWidget.currentItem().color)
            
    def ensureLabelOverlayVisible(self):
        if self.volumeEditor.overlayWidget.getOverlayRef(self.overlayItem.key) == None:
            self.volumeEditor.overlayWidget.addOverlayRef(self.overlayItem.getRef())
        self.volumeEditor.overlayWidget.setVisibility(self.overlayItem.key, True)

