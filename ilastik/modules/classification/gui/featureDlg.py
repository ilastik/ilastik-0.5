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
#    ADVISED OF THE POSSIBILITY OF SUCH
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed

from PyQt4 import QtCore, QtGui, uic
import os
import ilastik
from ilastik.core.utilities import irange
from ilastik.modules.classification.core import featureMgr
from ilastik.gui.iconMgr import ilastikIcons
import qimage2ndarray
from ilastik.modules.classification.core.featureMgr import ilastikFeatureGroups
import copy
import numpy

#*******************************************************************************
# F e a t u r e D l g                                                          *
#*******************************************************************************

class FeatureDlg(QtGui.QDialog):
    def __init__(self, parent=None, previewImage=None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(True)
        self.setWindowTitle("Select Spatial Features")
        self.parent = parent
        self.ilastik = parent
        self.initDlg()

        self.hudColor = QtGui.QColor("red")
        self.groupMaskSizesList = ilastikFeatureGroups.groupMaskSizes
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.grscene = QtGui.QGraphicsScene()
        if previewImage.dtype == numpy.uint16:
            if previewImage.max() <= 4095:
                previewImage = (previewImage.astype(numpy.float32)*255.0/4095.0).astype(numpy.uint8)
            else:
                previewImage = (previewImage.astype(numpy.float32)*255.0/65535.0).astype(numpy.uint8)      
        pixmapImage = QtGui.QPixmap(qimage2ndarray.array2qimage(previewImage))
        self.grscene.addPixmap(pixmapImage)
        self.circle = self.grscene.addEllipse(96, 96, 0, 0)
        self.circle.setPen(QtGui.QPen(self.hudColor,1))
        self.graphicsView.setScene(self.grscene)
        self.graphicsView.scale(2, 2)
        self.graphicsView.viewport().installEventFilter(self)
        self.graphicsView.setViewportUpdateMode(0)
        self.graphicsView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.size = None
        self.zoom = 2
        self.horizontalHeaderIndex = None
        tempLayoutZoomV = QtGui.QVBoxLayout(self.graphicsView)
        tempLayoutZoom = QtGui.QHBoxLayout()
        self.sizeText = QtGui.QLabel()
        self.sizeText.setStyleSheet("color: red; font-weight:bold;")
        self.sizeText.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        tempLayoutZoom.addWidget(self.sizeText)
        tempLayoutZoom.addStretch()
        tempLayoutZoomV.addLayout(tempLayoutZoom)
        tempLayoutZoomV.addStretch()
        self.featureComputation = None


    def initDlg(self):

        #determine the minimum x,y,z of all images
        min = self.ilastik.project.dataMgr[0]._dataVol._data.shape[3]
        self.min =min
        for i, it in enumerate(self.ilastik.project.dataMgr):
            if it._dataVol._data.shape[2] < min:
                min = it._dataVol._data.shape[2]
            if it._dataVol._data.shape[3] < min:
                min = it._dataVol._data.shape[3]
            if it._dataVol._data.shape[1] < min and it._dataVol._data.shape[1] > 1:
                min = it._dataVol._data.shape[1]

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/modules/classification/gui/dlgFeature.ui', self)
        self.featureTable.setMouseTracking(1)
        self.featureTable.viewport().installEventFilter(self)

        for featureItem in self.parent.featureList:
            self.featureList.insertItem(self.featureList.count() + 1, QtCore.QString(featureItem.__str__()))

        for k, groupName in irange(featureMgr.ilastikFeatureGroups.groups.keys()):
            rc = self.featureTable.rowCount()
            self.featureTable.insertRow(rc)
        self.featureTable.setVerticalHeaderLabels(featureMgr.ilastikFeatureGroups.groups.keys())


        for k, scaleName in irange(featureMgr.ilastikFeatureGroups.groupScaleNames):
            #only add features scales that fit within the minimum dimension of the smallest image
            #if featureMgr.ilastikFeatureGroups.groupScaleValues[k]*7 + 3< min:
            rc = self.featureTable.columnCount()
            self.featureTable.insertColumn(rc)
            #else:
            #    print "Scale ", scaleName, " too large for image of size ", min
            if featureMgr.ilastikFeatureGroups.groupScaleValues[k]*7 + 3> min:
                print "Scale ", scaleName, " too large for image of size ", min, ' Use only Anisotropic at Larger Scales'
                
        self.featureTable.setHorizontalHeaderLabels(featureMgr.ilastikFeatureGroups.groupScaleNames)

        #self.featureTable.resizeRowsToContents()
        #self.featureTable.resizeColumnsToContents()
        for c in range(self.featureTable.columnCount()):
            self.featureTable.horizontalHeader().resizeSection(c, 100)#(0, QtGui.QHeaderView.Stretch)

        #self.featureTable.verticalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.featureTable.setShowGrid(False)

        self.oldFeatureItems = []
        if len(featureMgr.ilastikFeatureGroups.selection) == self.featureTable.rowCount() and len(featureMgr.ilastikFeatureGroups.selection[0]) ==  self.featureTable.columnCount():
            for r in range(self.featureTable.rowCount()):
                for c in range(self.featureTable.columnCount()):
                    item = QtGui.QTableWidgetItem()
                    if featureMgr.ilastikFeatureGroups.selection[r][c]:
                        item.setIcon(QtGui.QIcon(ilastikIcons.Preferences))
                    self.featureTable.setItem(r, c, item)
            
            if self.parent.project.dataMgr.module["Classification"].featureMgr is not None:
                self.oldFeatureItems = featureMgr.ilastikFeatureGroups.createList()
                
        else:
            print " * Selected features as saved in the project file differ from the available features in this ilastik version."
            print " * reseting selection"
            featureMgr.ilastikFeatureGroups.selection = []
            for r in range(self.featureTable.rowCount()):
                featureMgr.ilastikFeatureGroups.selection.append([])
                for c in range(self.featureTable.columnCount()):
                    featureMgr.ilastikFeatureGroups.selection[r].append(False)
                    item = QtGui.QTableWidgetItem()
                    self.featureTable.setItem(r, c, item)
            
        self.setStyleSheet("selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0.5, y2: 0.5, stop: 0 #BBBBDD, stop: 1 white)")
        self.show()

        self.featureTable.horizontalHeader().setMouseTracking(1)
        self.featureTable.horizontalHeader().installEventFilter(self)

        self.featureTableList = []
        self.selectedItemList = []
        self.boolSelection = False
        self.boolTest = True
        self.ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = True

        for i in range(self.featureTable.columnCount()):
            item = self.featureTable.horizontalHeaderItem(i)
            size = len(item.text()) * 11
            self.featureTable.setColumnWidth(i, 70)
            
        self.oldSelectedFeatures = copy.deepcopy(featureMgr.ilastikFeatureGroups.selection)


    @QtCore.pyqtSignature("")
    def on_featureTable_itemSelectionChanged(self):
        tempItemSelectedList = []
        if self.boolSelection == True:
            for i in self.featureTable.selectedItems():
                if not i in self.selectedItemList:
                    if i.icon().isNull():
                        icon = QtGui.QIcon(ilastikIcons.Preferences)
                        i.setIcon(icon)
                        featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = True
                    else:
                        icon = QtGui.QIcon()
                        i.setIcon(icon)
                        featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = False

                tempItemSelectedList.append(i)

            for i in self.selectedItemList:
                if not i in self.featureTable.selectedItems():
                    if i.icon().isNull():
                        icon = QtGui.QIcon(ilastikIcons.Preferences)
                        i.setIcon(icon)
                        featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = True
                    else:
                        icon = QtGui.QIcon()
                        i.setIcon(icon)
                        featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = False

            self.selectedItemList = tempItemSelectedList
        else:
                if self.boolTest == True:
                    self.boolTest = False
                    for i in self.featureTable.selectedItems():
                        if i.icon().isNull():
                            icon = QtGui.QIcon(ilastikIcons.Preferences)
                            i.setIcon(icon)
                            featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = True
                        else:
                            icon = QtGui.QIcon()
                            i.setIcon(icon)
                            featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = False
                        i.setSelected(False)
                    self.boolTest = True

        
        memReq = self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureMgr.ilastikFeatureGroups.createList())
        self.memReq.setText("%8.2f MB" % memReq)

    def deselectAllTableItems(self):
        iColumn = self.featureTable.columnCount()
        iRow = self.featureTable.rowCount()
        for i in range(iRow):
            for j in range(iColumn):
                self.featureTable.item(i, j).setSelected(False)

    #oli todo
    def contextMenuGraphicsView(self, position):
        menu = QtGui.QMenu(self.graphicsView)
        menuChangeColor = QtGui.QMenu("change HUD color", menu)
        red = menuChangeColor.addAction("red")
        green = menuChangeColor.addAction("green")
        blue = menuChangeColor.addAction("blue")
        menu.addMenu(menuChangeColor)
        zoomMenu = QtGui.QMenu("change zoom", menu)
        zoomx1 = zoomMenu.addAction("x1")
        zoomx2 = zoomMenu.addAction("x2")
        if self.zoom == 1:
            zoomx1.setDisabled(True)
            zoomx2.setDisabled(False)
        else:
            zoomx1.setDisabled(False)
            zoomx2.setDisabled(True)
        menu.addMenu(zoomMenu)
        action = menu.exec_(self.graphicsView.mapToGlobal(position))
        if action == red:
            self.hudColor = QtGui.QColor("red")
            self.sizeText.setStyleSheet("color: red")
            self.circle.setPen(QtGui.QPen(self.hudColor,1))
        elif action == green:
            self.hudColor = QtGui.QColor("green")
            self.sizeText.setStyleSheet("color: green")
            self.circle.setPen(QtGui.QPen(self.hudColor,1))
        elif action == blue:
            self.hudColor = QtGui.QColor("blue")
            self.sizeText.setStyleSheet("color: blue")
            self.circle.setPen(QtGui.QPen(self.hudColor,1))
        elif action == zoomx1:
            self.zoom = 1
            self.graphicsView.scale(.5, .5)
            self.drawPreview()
        elif action == zoomx2:
            self.zoom = 2
            self.graphicsView.scale(2, 2)
            self.drawPreview()
    #oli todo
    def drawPreview(self):
        if not self.horizontalHeaderIndex < 0:
            self.circle.setVisible(True)
            self.sizeText.setVisible(True)
            self.size = self.groupMaskSizesList[self.horizontalHeaderIndex]
            # self.grscene.removeItem(self.circle)
            self.circle.setRect(96/self.zoom - (self.size/2), 96/self.zoom - (self.size/2), self.size, self.size)
            self.circle.setPos(self.graphicsView.mapToScene(0, 0))
            self.circle.setPen(QtGui.QPen(self.hudColor,1))
            self.sizeText.setText("Size: " + str(self.size))
        
    #oli todo
    def eventFilter(self, obj, event):
        if(event.type()==QtCore.QEvent.MouseButtonPress):
            if event.button() == QtCore.Qt.LeftButton:
                self.boolSelection = True
                self.ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = True
                
        if(event.type()==QtCore.QEvent.MouseButtonRelease):
            if event.button() == QtCore.Qt.LeftButton:
                self.ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = False
                self.selectedItemList = []
                self.deselectAllTableItems()
                self.boolSelection = False
                
        if event.type() == QtCore.QEvent.HoverMove:
            self.horizontalHeaderIndex = self.featureTable.horizontalHeader().logicalIndexAt(event.pos())
            self.drawPreview()
            
        if event.type() == QtCore.QEvent.MouseMove:
            self.circle.setPos(self.graphicsView.mapToScene(0, 0))
            if self.featureTable.itemAt(event.pos()) and self.featureTable.underMouse():
                item = self.featureTable.itemAt(event.pos())
                self.horizontalHeaderIndex = item.column()
                self.drawPreview()
        if(event.type() == QtCore.QEvent.ContextMenu and self.graphicsView.underMouse()):
            self.contextMenuGraphicsView(event.pos())

        if(event.type()==QtCore.QEvent.Wheel):
            return True
        
        if event.type() == QtCore.QEvent.Leave:
            #self.circle.setVisible(False)
            #self.sizeText.setVisible(False)
            pass

        return False


    @QtCore.pyqtSignature("")
    def on_confirmButtons_accepted(self):
        featureSelectionList = featureMgr.ilastikFeatureGroups.createList()
        self.featuresChanged = False
        if len(self.oldFeatureItems) == len(featureSelectionList):
            for a,b in zip(self.oldFeatureItems, featureSelectionList):
                if a.name != b.name or a.sigma != b.sigma:
                    featuresChanged = True
        else:
            self.featuresChanged = True
        
        
            
                    
        res = self.parent.project.dataMgr.Classification.featureMgr.setFeatureItems(featureSelectionList)
        if res is True:
            #print "features have maximum needed margin of:", self.parent.project.dataMgr.Classification.featureMgr.maxSigma*3
            self.parent.labelWidget.setBorderMargin(int(self.parent.project.dataMgr.Classification.featureMgr.maxContext))
            self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)           
            self.accept() 
        else:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
            self.reject()


    @QtCore.pyqtSignature("")
    def on_confirmButtons_rejected(self):
        for i in range(len(self.oldSelectedFeatures)):
            for j in range(len(self.oldSelectedFeatures[i])):
                featureMgr.ilastikFeatureGroups.selection[i][j] = self.oldSelectedFeatures[i][j]
        self.reject()



