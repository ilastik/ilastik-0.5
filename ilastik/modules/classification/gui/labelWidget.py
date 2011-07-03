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

from PyQt4.QtCore import Qt, SIGNAL, pyqtSignal
from PyQt4.QtGui import QAbstractItemView, QAction, QActionGroup, QColor,\
                        QColorDialog, QCursor, QFont, QGroupBox, QIcon,\
                        QInputDialog, QItemSelectionModel, QListWidget,\
                        QListWidgetItem, QMenu, QMessageBox, QPixmap, QPushButton,\
                        QVBoxLayout

from ilastik.gui.baseLabelWidget import BaseLabelWidget
from ilastik.gui.iconMgr import ilastikIcons

import numpy, copy
from functools import partial
        

#*******************************************************************************
# L a b e l L i s t I t e m                                                    *
#*******************************************************************************

class LabelListItem(QListWidgetItem):
    def __init__(self, name , number, color):
        QListWidgetItem.__init__(self, name)
        self.number = number
        self.visible = True
        self.setColor(color)
        #self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        #self.setFlags(self.flags() | Qt.ItemIsEditable)

    def toggleVisible(self):
        self.visible = not(self.visible)

    def setColor(self, color):
        self.color = color
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        icon = QIcon(pixmap)
        self.setIcon(icon)      

#*******************************************************************************
# L a b e l L i s t W i d g e t                                                *
#*******************************************************************************

class LabelListWidget(BaseLabelWidget,  QGroupBox):
    itemSelectionChanged = pyqtSignal()
    
    def __init__(self,  labelMgr,  volumeLabelDescriptions, volumeEditor,  overlayItem):
        QGroupBox.__init__(self, "Labels")
        BaseLabelWidget.__init__(self, None)
        self.setLayout(QVBoxLayout())
        self.listWidget = QListWidget(self)
        self.overlayItem = overlayItem
        self.volumeLabelDescriptions = volumeLabelDescriptions
        #Label selector
        self.addLabelButton = QPushButton(QIcon(ilastikIcons.AddSel),"Create Class")
        self.addLabelButton.pressed.connect(self.createLabel)

        self.layout().setMargin(5)
        self.layout().addWidget(self.addLabelButton)
        self.layout().addWidget(self.listWidget)
        
        self.volumeEditor = volumeEditor
        self.labelMgr = labelMgr
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.onContext)
        self.colorTab = []
        self.items = []
        self.labelColorTable = [QColor(Qt.red), QColor(Qt.green), QColor(Qt.yellow), QColor(Qt.blue), QColor(Qt.magenta) , QColor(Qt.darkYellow), QColor(Qt.lightGray)]
        #self.connect(self, SIGNAL("currentTextChanged(QString)"), self.changeText)
        
        self.listWidget.itemSelectionChanged.connect(self.changeLabel)
        self.labelPropertiesChanged_callback = None
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.initFromVolumeLabelDescriptions(volumeLabelDescriptions)
    
    def onImageSceneContext(self, pos):
        menu = QMenu('Labeling menu', self)
        
        labelList = []
        
        volumeLabel = self.volumeEditor.labelWidget.volumeLabelDescriptions

        act = menu.addAction("Labels")
        act.setEnabled(False)
        font = QFont( "Helvetica", 10, QFont.Bold, True)
        act.setFont(font)
        
        for index, item in enumerate(volumeLabel):
            labelColor = QColor.fromRgb(long(item.color))
            labelIndex = item.number
            labelName = item.name
            pixmap = QPixmap(16, 16)
            pixmap.fill(labelColor)
            icon = QIcon(pixmap)
            
            act = QAction(icon, labelName, menu)
            i = self.listWidget.model().index(labelIndex-1,0)
            labelList.append(menu.addAction(act))
        
        eraseAct = None    
        if self.volumeEditor.drawManager.erasing:
            eraseAct = QAction("Enable eraser", menu)
        else:
            eraseAct = QAction("Disable eraser", menu)
        menu.addAction(eraseAct)
        eraseAct.triggered.connect(lambda: self.volumeEditor.drawManager.toggleErase())
        
        menu.addSeparator()
        brushGroup = QActionGroup(self)

        act = menu.addAction("Brush Sizes")
        act.setEnabled(False)
        font = QFont( "Helvetica", 10, QFont.Bold, True)
        act.setFont(font)
        menu.addSeparator()
        
        defaultBrushSizes = [(1, ""), (3, " Tiny"), (5, " Small"), (7, " Medium"), (11, " Large"), \
                             (23, " Huge"), (31, " Megahuge"), (61, " Gigahuge")]
        for brushSize, desc in defaultBrushSizes:
            act = QAction("  %d %s" % (brushSize, desc), brushGroup)
            act.setCheckable(True)
            #see here for the suggestion to use partial
            #http://stackoverflow.com/questions/6084331/pyqt-creating-buttons-from-dictionary
            #why does a lambda not work here?
            act.triggered.connect(partial(self.volumeEditor.drawManager.setBrushSize, brushSize))
            act.setChecked(brushSize == self.volumeEditor.drawManager.getBrushSize())
            menu.addAction(act)
        
        action = menu.exec_(QCursor.pos())
        
    def currentItem(self):
        return self.listWidget.currentItem()
    
    def initFromVolumeLabelDescriptions(self, volumeLabelDescriptions):
        self.volumeLabelDescriptions = volumeLabelDescriptions
        for index, item in enumerate(volumeLabelDescriptions):
            li = LabelListItem(item.name, item.number, QColor.fromRgba(long(item.color)))
            self.listWidget.addItem(li)
            self.items.append(li)
        self.buildColorTab()
        
        #just select the first item in the list so we have some selection
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(0,0), QItemSelectionModel.ClearAndSelect)

    def changeLabelName(self, index, name):
        self.labelMgr.changeLabelName(index, name)
        
    def createLabel(self):
        name = "Label " + len(self.items).__str__()
        for index, item in enumerate(self.items):
            if str(item.text()) == name:
                name = name + "-2"
        number = len(self.items)
        if number >= len(self.labelColorTable):
            color = QColor.fromRgb(numpy.random.randint(255),numpy.random.randint(255),numpy.random.randint(255))
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
        self.listWidget.selectionModel().setCurrentIndex(self.listWidget.model().index(self.listWidget.model().rowCount()-1,0), QItemSelectionModel.ClearAndSelect)
        
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
        self.volumeEditor.emit(SIGNAL("labelRemoved(int)"), item.number)
        self.volumeEditor.repaint()

    def buildColorTab(self):
        self.overlayItem.colorTable = self.colorTab = self.volumeLabelDescriptions.getColorTab()

    def onContext(self, pos):
        index = self.listWidget.indexAt(pos)

        if not index.isValid():
            return

        item = self.listWidget.itemAt(pos)
        name = item.text()

        menu = QMenu(self)

        removeAction = menu.addAction("Remove")
        colorAction = menu.addAction("Change Color")
        renameAction = menu.addAction("Change Name")
        clearAction = menu.addAction("Clear Label")

        action = menu.exec_(QCursor.pos())
        if action == removeAction:
            if QMessageBox.question(self, "Remove label", "Really remove label" + self.volumeLabelDescriptions[index.row()].name + "?", buttons = QMessageBox.Cancel | QMessageBox.Ok)  != QMessageBox.Cancel:
                self.removeLabel(item,  index)
        elif action == renameAction:
            newName, ok = QInputDialog.getText(self, "Enter Labelname", "Labelname:", text = item.text())
            if ok:
                item.setText(newName)
                result = self.labelMgr.changeLabelName(index.row(),str(newName))
                #print result
        elif action == clearAction:
            if QMessageBox.question(self, "Clear label", "Really clear label" + self.volumeLabelDescriptions[index.row()].name + "?", buttons = QMessageBox.Cancel | QMessageBox.Ok)  != QMessageBox.Cancel:
                number = self.volumeLabelDescriptions[index.row()].number
                self.labelMgr.clearLabel(number)                
            
        elif action == colorAction:
            color = QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabelDescriptions[index.row()].color = color.rgba()
            
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
        self.listWidget.selectionModel().setCurrentIndex(i, QItemSelectionModel.ClearAndSelect)

    def prevLabel(self):
        i = self.listWidget.selectedIndexes()[0].row()
        if i >  0:
            i = self.listWidget.model().index(i-1,0)
        else:
            i = self.listWidget.model().index(self.listWidget.model().rowCount()-1,0)
        self.listWidget.selectionModel().setCurrentIndex(i, QItemSelectionModel.ClearAndSelect)
        
    def changeLabel(self):
        for i in range(0, len(self.volumeEditor.imageScenes)):
            self.volumeEditor.imageScenes[i].crossHairCursor.setColor(self.listWidget.currentItem().color)
        self.itemSelectionChanged.emit()
            
    def ensureLabelOverlayVisible(self):
        if self.volumeEditor.overlayWidget.getOverlayRef(self.overlayItem.key) == None:
            self.volumeEditor.overlayWidget.addOverlayRef(self.overlayItem.getRef())
        self.volumeEditor.overlayWidget.setVisibility(self.overlayItem.key, True)

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == '__main__':
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    import sys
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import QApplication, QColor
    from ilastik.modules.classification.core.labelMgr import LabelMgr
    from ilastik.core.dataMgr import DataMgr
    from ilastik.core.overlayMgr import OverlaySlice, OverlayItem
    from ilastik.core.volume import VolumeLabelDescriptionMgr, VolumeLabelDescription, DataAccessor
    
    dataMgr = DataMgr()
    labelMgr = LabelMgr(dataMgr, None)
    data = numpy.zeros((10,10,10))
    overlay = OverlayItem(DataAccessor(data), alpha=1.0, color=Qt.black, colorTable=OverlayItem.createDefaultColorTable('GRAY', 256), autoVisible=True, autoAlphaChannel=False)
    
    app = QApplication(sys.argv)
    
    volumeLabelMgr = VolumeLabelDescriptionMgr()
    volumeLabelMgr.append(VolumeLabelDescription("1", 0, QColor(255,0,0).rgba(), None))
    volumeLabelMgr.append(VolumeLabelDescription("2", 1, QColor(0,255,0).rgba(), None))
    volumeLabelMgr.append(VolumeLabelDescription("3", 2, QColor(0,0,255).rgba(), None))
    
    l = LabelListWidget(labelMgr, volumeLabelMgr, None, overlay)
    l.show()
    app.exec_()
    