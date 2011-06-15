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
import os, traceback, sys
from overlaySelectionDlg import OverlaySelectionDialog, OverlayCreateSelectionDlg
from ilastik.gui import overlayDialogs
import ilastik.gui.exportDialog as exportDialog
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.core import dataImpex

#*******************************************************************************
# O v e r l a y L i s t W i d g e t I t e m                                    *
#*******************************************************************************

class OverlayListWidgetItem(QtGui.QListWidgetItem):
    def __init__(self, overlayItemReference):
        QtGui.QListWidgetItem.__init__(self,overlayItemReference.name)
        self.overlayItemReference = overlayItemReference
        self.name = overlayItemReference.name

        self.visible = overlayItemReference.visible
        self.setToolTip(self.overlayItemReference.key)

        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        
        self.setCheckState(self.visible * 2)

    def __getattr__(self,  name):
        if name == "color":
            return self.overlayItemReference.color
        raise AttributeError,  name

#*******************************************************************************
# O v e r l a y L i s t W i d g e t                                            *
#*******************************************************************************

class OverlayListWidget(QtGui.QListWidget):

#*******************************************************************************
# Q A l p h a S l i d e r D i a l o g                                          *
#*******************************************************************************

    class QAlphaSliderDialog(QtGui.QDialog):
        def __init__(self, min, max, value):
            QtGui.QDialog.__init__(self)
            self.setWindowTitle('Change Opacity')
            self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
            self.slider.setGeometry(20, 30, 140, 20)
            self.slider.setRange(min,max)
            self.slider.setValue(value)

    def __init__(self,volumeEditor,  overlayWidget):
        QtGui.QListWidget.__init__(self)
        self.volumeEditor = volumeEditor
        self.overlayWidget = overlayWidget
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.connect(self, QtCore.SIGNAL("clicked(QModelIndex)"), self.onItemClick)
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.onItemDoubleClick)
        self.currentItem = None
        #add the overlays to the gui
        for overlay in self.overlayWidget.overlays:
            if overlay.overlayItem != None:
                self.addItem(OverlayListWidgetItem(overlay))
            #dont forget to remove overlayreferences whose base overlayItem has been deleted from somewhere else by now:
            else:
                self.overlayWidget.overlays.remove(overlay)

    def onItemClick(self, itemIndex):
        item = self.itemFromIndex(itemIndex)
        if (item.checkState() == QtCore.Qt.Checked and not item.overlayItemReference.visible) or (item.checkState() == QtCore.Qt.Unchecked and item.overlayItemReference.visible):
            item.overlayItemReference.visible = not(item.overlayItemReference.visible)
            s = None
            if item.overlayItemReference.visible:
                s = QtCore.Qt.Checked
            else:
                s = QtCore.Qt.Unchecked
            item.setCheckState(s)
            self.volumeEditor.repaint()
            
    def onItemDoubleClick(self, itemIndex):
        self.currentItem = item = self.itemFromIndex(itemIndex)
        if item.checkState() == 2:
            dialog = OverlayListWidget.QAlphaSliderDialog(1, 20, round(item.overlayItemReference.alpha*20))
            dialog.slider.connect(dialog.slider, QtCore.SIGNAL('valueChanged(int)'), self.setCurrentItemAlpha)
            dialog.exec_()
        else:
            self.onItemClick(itemIndex)
    
    
    
            
    def setCurrentItemAlpha(self, num):
        self.currentItem.overlayItemReference.alpha = 1.0 * num / 20.0
        self.volumeEditor.repaint()
        
#    def clearOverlays(self):
#        self.clear()
#        self.overlayWidget.overlays = []

    def moveUp(self, row):
        item = self.takeItem(row)
        self.insertItem(row - 1, item)
        self.setCurrentRow(row - 1)    
    
    def moveDown(self, row):
        item = self.takeItem(row)
        self.insertItem(row + 1, item)
        self.setCurrentRow(row + 1)

    def removeOverlay(self, item):
        itemNr = None
        if isinstance(item, str):
            for idx, it in enumerate(self.overlayWidget.overlays):
                if it.key == item:
                    itemNr = idx
                    item = it
        else:
            itemNr = item
        if itemNr != None:
            self.overlayWidget.overlays.pop(itemNr)
            self.takeItem(itemNr)
            return item
        else:
            return None

    def addOverlayRef(self, overlayRef):
        #this dirty hack allows to keep the user interaction layer (labels, seeds, ect) on top
        if self.count()>1:
            self.insertItem(1,OverlayListWidgetItem(overlayRef))
        else:
            self.insertItem(0,OverlayListWidgetItem(overlayRef))
            
    def onContext(self, pos):
        index = self.indexAt(pos)

        if not index.isValid():
            return

        item = self.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        #Only show the "Display 3D" entry when this overlay can be reasonably
        #shown in 3D by extracting the meshes of the contained objects
        show3dAction = QtGui.QAction(self)
        if item.overlayItemReference.overlayItem.displayable3D:
            show3dAction = menu.addAction("Display 3D")
            
        if item.overlayItemReference.colorTable is None:
            colorAction = menu.addAction("Change Color")
            if item.overlayItemReference.linkColor is True:
                colorAction.setEnabled(False)
            if item.overlayItemReference.autoAlphaChannel:
                alphaChannelAction = menu.addAction("Disable intensity blending")
            else:
                alphaChannelAction = menu.addAction("Enable intensity blending")
        else:
            colorAction = -3
            alphaChannelAction = -3

        configureTransparencyAction = menu.addAction("Change Opacity")

        channelMenu = QtGui.QMenu("Select Channel", menu)
        channelActions = []
        for i in range(item.overlayItemReference.numChannels):
            action = channelMenu.addAction(str(i))
            channelActions.append(action)
            if item.overlayItemReference.channel == i:
                channelMenu.setActiveAction(action)
            
        menu.addMenu(channelMenu)
        exportAction = menu.addAction("Export")        

        configureDialogAction = -3
        
        c = item.overlayItemReference.overlayItem.__class__
        if overlayDialogs.overlayClassDialogs.has_key(c.__module__ + '.' + c.__name__):
            configureDialogAction = menu.addAction("Configure")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == show3dAction:
            print "3D view"
            suppress   = item.overlayItemReference.overlayItem.backgroundClasses
            smooth     = item.overlayItemReference.overlayItem.smooth3D
            vol        = item.overlayItemReference._data[0,:,:,:,item.overlayItemReference.channel]
            colorTable = item.overlayItemReference.colorTable
            
            print "  - will not extract the following labels:", suppress
            print "  - volume to show has shape", vol.shape, "and dtype =", vol.dtype
            #print "  - color table"
            #for i, c in enumerate(colorTable):
                #c = QtGui.QColor.fromRgba(c)
                #print "    %03d.) (%03d, %03d, %03d)" % (i, c.red(), c.green(), c.blue())
            
            self.volumeEditor.overview.SetColorTable(colorTable)
            self.volumeEditor.overview.DisplayObjectMeshes(vol, suppress, smooth)
            
        elif action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.overlayItemReference.colorTable = None
            item.overlayItemReference.color = color
            self.volumeEditor.repaint()
        elif action == alphaChannelAction:
            item.overlayItemReference.autoAlphaChannel = not(item.overlayItemReference.autoAlphaChannel)
            self.volumeEditor.repaint()
        elif action == configureDialogAction:
            c = item.overlayItemReference.overlayItem.__class__
            configDialog = overlayDialogs.overlayClassDialogs[c.__module__ + '.' + c.__name__](self.volumeEditor.ilastik, item.overlayItemReference.overlayItem)
            configDialog.exec_()
        elif action == configureTransparencyAction:
            self.currentItem = item
            dialog = OverlayListWidget.QAlphaSliderDialog(1, 20, round(item.overlayItemReference.alpha*20))
            dialog.slider.connect(dialog.slider, QtCore.SIGNAL('valueChanged(int)'), self.setCurrentItemAlpha)
            dialog.exec_()
            
        elif action == exportAction:
            timeOffset = item.overlayItemReference._data.shape[0]>1
            sliceOffset = item.overlayItemReference._data.shape[1]>1
            channelOffset = item.overlayItemReference._data.shape[-1]>1
            formatList = dataImpex.DataImpex.exportFormatList()
            formatList.append("h5")
            expdlg = exportDialog.ExportDialog(formatList, timeOffset, sliceOffset, channelOffset, parent=self.volumeEditor.ilastik)
            expdlg.exec_()
            try:
                tempname = str(expdlg.path.text()) + "/" + str(expdlg.prefix.text())
                filename = str(QtCore.QDir.convertSeparators(tempname))
                dataImpex.DataImpex.exportOverlay(filename, expdlg.format, item.overlayItemReference.overlayItem, expdlg.timeOffset, expdlg.sliceOffset, expdlg.channelOffset)
            except Exception, e:
                print e
                traceback.print_exc(file=sys.stdout)
        else:
            for index,  channelAct in enumerate(channelActions):
                if action == channelAct:
                    item.overlayItemReference.setChannel(index)
                    self.volumeEditor.repaint()

    def changeOverlayName(self, overlayItem, newName):
        for index in range(self.count()):
            item = self.item(index)
            if item.overlayItemReference.overlayItem == overlayItem:
                item.setText(newName)


    def getLabelNames(self):
        labelNames = []
        for idx, it in enumerate(self.descriptions):
            labelNames.append(it.name)
        return labelNames
       
      
    def toggleVisible(self,  item):
        state = not(item.overlayItemReference.visible)
        item.overlayItemReference.visible = state
        item.setCheckState(item.overlayItemReference.visible * 2)
        
    def setVisibility(self,  index, visible):
        item = self.item(index)
        state = item.overlayItemReference.visible
        item.overlayItemReference.visible = visible
        item.setCheckState(item.overlayItemReference.visible * 2)
        return state
        
    def wheelEvent(self, event):
        pos = event.pos()
        item = self.itemAt(pos)
        if item is not None:
            if event.delta() > 0:
                item.overlayItemReference.incChannel()
            else:
                item.overlayItemReference.decChannel()
            self.volumeEditor.repaint()
        


#*******************************************************************************
# O v e r l a y W i d g e t                                                    *
#*******************************************************************************

class OverlayWidget(QtGui.QGroupBox):
    def __init__(self,parent, dataMgr):
        QtGui.QGroupBox.__init__(self,  "Overlays")
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setMargin(5)
        
        self.dataMgr = dataMgr

        self.volumeEditor = parent
        self.overlayMgr = self.dataMgr._activeImage.overlayMgr
        
        self.overlays = self.dataMgr._activeImage.module[self.dataMgr._currentModuleName].getOverlayRefs()

        pathext = os.path.dirname(__file__)

        self.overlayListWidget = OverlayListWidget(parent, self)
        upDownLayout = QtGui.QVBoxLayout()
        upDownLayout.setMargin(0)
        upDownLayout.setSpacing(0)
        
        self.buttonUp = QtGui.QToolButton()
        self.buttonUp.setToolTip("Move the selected overlay up in the view")
        self.buttonUp.setSizePolicy(QtGui.QSizePolicy.Fixed,  QtGui.QSizePolicy.Fixed)
        self.buttonUp.setIcon(QtGui.QIcon(pathext + "/icons/22x22/actions/go-up_thin.png") )
        self.buttonUp.setEnabled(False)
        self.connect(self.buttonUp,  QtCore.SIGNAL('clicked()'),  self.buttonUpClicked)
        self.buttonDown = QtGui.QToolButton()
        self.buttonDown.setToolTip("Move the selected overlay down in the view")
        self.buttonDown.setSizePolicy(QtGui.QSizePolicy.Fixed,  QtGui.QSizePolicy.Fixed)
        self.buttonDown.setIcon(QtGui.QIcon(pathext + "/icons/22x22/actions/go-down_thin.png") )
        self.buttonDown.setEnabled(False)
        self.connect(self.buttonDown,  QtCore.SIGNAL('clicked()'),  self.buttonDownClicked)
        
        self.connect(self.overlayListWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.onRowChanged)
        self.connect(self.overlayListWidget, QtCore.SIGNAL('itemActivated()'), self.onItemActivated)
        
        upDownLayout.addWidget(self.buttonUp)
        upDownLayout.addStretch()
        upDownLayout.addWidget(self.buttonDown)
        
        overlayListLayout = QtGui.QHBoxLayout()
        overlayListLayout.setMargin(0)
        overlayListLayout.setSpacing(5)
        
        overlayListLayout.addWidget(self.overlayListWidget)
        overlayListLayout.addLayout(upDownLayout)
        
        addRemoveCreateLayout = QtGui.QHBoxLayout()
        #addRemoveCreateLayout.setMargin(0)
        #addRemoveCreateLayout.setSpacing(5)
       
        self.buttonAdd = QtGui.QToolButton()
        self.buttonAdd.setToolTip("Add an already existing overlay to this view")
        self.buttonAdd.setIcon(QtGui.QIcon(pathext + "/icons/22x22/actions/list-add.png") )
        self.connect(self.buttonAdd,  QtCore.SIGNAL('clicked()'),  self.buttonAddClicked)
        addRemoveCreateLayout.addWidget(self.buttonAdd)
        
        self.buttonRemove = QtGui.QToolButton()
        self.buttonRemove.setToolTip("Remove the selected overlay from this view")
        self.buttonRemove.setIcon(QtGui.QIcon(pathext + "/icons/22x22/actions/list-remove.png"))
        self.connect(self.buttonRemove,  QtCore.SIGNAL('clicked()'),  self.buttonRemoveClicked)
        addRemoveCreateLayout.addWidget(self.buttonRemove)
        
        self.buttonCreate = QtGui.QToolButton()
        self.buttonCreate.setToolTip("Create a completely new overlay from data")
        self.buttonCreate.setIcon(QtGui.QIcon(pathext + "/icons/22x22/actions/document-new.png") )
        self.connect(self.buttonCreate,  QtCore.SIGNAL('clicked()'),  self.buttonCreateClicked)
        addRemoveCreateLayout.addWidget(self.buttonCreate)
        addRemoveCreateLayout.addStretch()
        
        #Save the current images button
        self.saveAsImageBtn = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Save),'Export View')
        self.saveAsImageBtn.setToolTip("Export the currently rendered view as an image stack")
        self.connect(self.saveAsImageBtn, QtCore.SIGNAL("clicked()"), self.volumeEditor.on_saveAsImage)
        
        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.addLayout(overlayListLayout)
        layout.addLayout(addRemoveCreateLayout)
        layout.addWidget(self.saveAsImageBtn)
        
        self.layout().addLayout(layout)
    
    def onItemActivated(self, item):
        self.onRowChanged(self.overlayListWidget.row(item))

    def onRowChanged(self, newRow):
        self.buttonUp.setEnabled(newRow != 0)
        self.buttonDown.setEnabled(newRow != self.overlayListWidget.count()-1)
        
    
    def buttonUpClicked(self):
        number = self.overlayListWidget.currentRow()
        if number > 0:
            self.overlayListWidget.moveUp(number)
            item = self.overlays.pop(number)
            self.overlays.insert(number-1, item)
            self.overlayListWidget.volumeEditor.repaint()    
    
    def buttonDownClicked(self):
        number = self.overlayListWidget.currentRow()
        if number >= 0 and number < len(self.overlays) - 1:
            self.overlayListWidget.moveDown(number)
            item = self.overlays.pop(number)
            self.overlays.insert(number+1, item)
            self.overlayListWidget.volumeEditor.repaint()    
        
        
    def buttonCreateClicked(self):
        dlg = OverlayCreateSelectionDlg(self.volumeEditor.ilastik)
        answer = dlg.exec_()
        if answer is not None:
            dlg_creation = answer(self.volumeEditor.ilastik)
            answer = dlg_creation.exec_()
            if answer is not None:
                name = QtGui.QInputDialog.getText(self,"Edit Name", "Please Enter the name of the new Overlay:", text = "Custom Overlays/My Overlay" )
                name = str(name[0])
                self.volumeEditor.ilastik.project.dataMgr[self.volumeEditor.ilastik._activeImageNumber].overlayMgr[name] = answer
                self.volumeEditor.repaint()
        
        
    def buttonAddClicked(self):
        dlg = OverlaySelectionDialog(self.volumeEditor.ilastik,  singleSelection = False)
        answer = dlg.exec_()
        for o in answer:
            self.addOverlayRef(o.getRef())
        self.overlayListWidget.volumeEditor.repaint()
        
    def buttonRemoveClicked(self):
        number = self.overlayListWidget.currentRow()
        if number >= 0:
            self.overlayListWidget.removeOverlay(number)
            self.overlayListWidget.volumeEditor.repaint()
        
    def removeOverlay(self, item):
        """
        item can be a string, e.g. the item name, or a number
        """
        return self.overlayListWidget.removeOverlay(item)
    
    def changeOverlayName(self, overlayItem, newName):
        self.overlayListWidget.changeOverlayName(overlayItem, newName)
        
    def addOverlayRef(self, overlayRef, duplicateAllowed = False):
        if duplicateAllowed is False:
            for o in self.overlays:
                if o.key == overlayRef.key:
                    overlayRef = None
                    break
        
        if overlayRef is not None:   
            if len(self.overlays)>1: 
                self.overlays.insert(1,overlayRef)
            else:
                self.overlays.insert(0,overlayRef)
            answer = self.overlayListWidget.addOverlayRef(overlayRef)
            self.volumeEditor.repaint()
            return answer
        else:
            return None

    def getLabelNames(self):
        return self.overlayListWidget.getLabelNames()
       
    def toggleVisible(self,  item):
        return self.overlayListWidget.toggleVisible(item)

    def setVisibility(self, key, visible):
        i = -1
        for i,o in enumerate(self.overlays):
            if o.key == key:
                break
        if i != -1:
            oldState = self.overlayListWidget.setVisibility(i, visible)
            if oldState != visible:
                self.volumeEditor.repaint()

    def getOverlayRef(self,  key):
        """
        find a specific overlay via its key e.g. "Classification/Prediction" in the
        current overlays of the widget
        """
        for o in self.overlays:
            if o.key == key:
                return o
        return None
