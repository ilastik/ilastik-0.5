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
import sys
import os
import numpy
import ilastik
from ilastik.core.utilities import irange, debug
from ilastik.core import version, dataMgr, projectMgr, featureMgr, classificationMgr, segmentationMgr, activeLearning, onlineClassifcator
from ilastik.gui.iconMgr import ilastikIcons
import qimage2ndarray


class FeatureDlg(QtGui.QDialog):
    def __init__(self, parent=None, previewImage=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.ilastik = parent
        self.initDlg()
        #self.grscene = QtGui.QGraphicsScene()
        #pixmapImage = QtGui.QPixmap(qimage2ndarray.gray2qimage(previewImage))
        #self.grscene.addPixmap(pixmapImage)
        #self.graphicsView.setScene(self.grscene)
        if self.parent.project.featureMgr is not None:
            self.oldFeatureItems = self.parent.project.featureMgr.featureItems
        else:
            self.oldFeatureItems = []

        circle = QtGui.QGraphicsEllipseItem(48, 48, 5, 5)
        circle.setPen(QtGui.QPen(QtGui.QColor(255,0,0)))
        
        self.graphicsView.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.grscene = QtGui.QGraphicsScene()
        pixmapImage = QtGui.QPixmap(qimage2ndarray.gray2qimage(previewImage))
        self.grscene.addPixmap(pixmapImage)
        self.grscene.addItem(circle)
        self.graphicsView.setScene(self.grscene)


    def initDlg(self):

        #determine the minimum x,y,z of all images
        min = self.ilastik.project.dataMgr[0].dataVol.data.shape[3]
        for i, it in enumerate(self.ilastik.project.dataMgr):
            if it.dataVol.data.shape[2] < min:
                min = it.dataVol.data.shape[2]
            if it.dataVol.data.shape[3] < min:
                min = it.dataVol.data.shape[3]
            if it.dataVol.data.shape[1] < min and it.dataVol.data.shape[1] > 1:
                min = it.dataVol.data.shape[1]

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/gui/dlgFeature.ui', self)
        self.featureTable.viewport().installEventFilter(self)

        for featureItem in self.parent.featureList:
            self.featureList.insertItem(self.featureList.count() + 1, QtCore.QString(featureItem.__str__()))

        for k, groupName in irange(featureMgr.ilastikFeatureGroups.groups.keys()):
            rc = self.featureTable.rowCount()
            self.featureTable.insertRow(rc)
        self.featureTable.setVerticalHeaderLabels(featureMgr.ilastikFeatureGroups.groups.keys())


        for k, scaleName in irange(featureMgr.ilastikFeatureGroups.groupScaleNames):
            #only add features scales that fit within the minimum dimension of the smallest image
            if featureMgr.ilastikFeatureGroups.groupScaleValues[k]*7 + 3< min:
                rc = self.featureTable.columnCount()
                self.featureTable.insertColumn(rc)
            else:
                print "Scale ", scaleName, " too large for image of size ", min
        self.featureTable.setHorizontalHeaderLabels(featureMgr.ilastikFeatureGroups.groupScaleNames)

        #self.featureTable.resizeRowsToContents()
        #self.featureTable.resizeColumnsToContents()
        for c in range(self.featureTable.columnCount()):
            self.featureTable.horizontalHeader().resizeSection(c, 54)#(0, QtGui.QHeaderView.Stretch)

        #self.featureTable.verticalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.featureTable.setShowGrid(False)


        for r in range(self.featureTable.rowCount()):
            for c in range(self.featureTable.columnCount()):
                item = QtGui.QTableWidgetItem()
                if featureMgr.ilastikFeatureGroups.selection[r][c]:
                    item.setIcon(QtGui.QIcon(ilastikIcons.Preferences))
                self.featureTable.setItem(r, c, item)
        self.setStyleSheet("selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0.5, y2: 0.5, stop: 0 #BBBBDD, stop: 1 white)")
        self.show()

        self.featureTable.horizontalHeader().setMouseTracking(1)
        self.featureTable.horizontalHeader().installEventFilter(self)

        self.featureTableList = []
        self.selectedItemList = []
        self.boolSelection = False
        self.boolTest = True

        for i in range(self.featureTable.columnCount()):
            item = self.featureTable.horizontalHeaderItem(i)
            size = len(item.text()) * 11
            self.featureTable.setColumnWidth(i, size)

    def drawCircle(self):
        pass

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

        self.computeMemoryRequirement(featureMgr.ilastikFeatureGroups.createList())

    def deselectAllTableItems(self):
        iColumn = self.featureTable.columnCount()
        iRow = self.featureTable.rowCount()
        for i in range(iRow):
            for j in range(iColumn):
                self.featureTable.item(i, j).setSelected(False)


    def eventFilter(self, obj, event):
        if(event.type()==QtCore.QEvent.MouseButtonPress):
            if event.button() == QtCore.Qt.LeftButton:
                self.boolSelection = True
        if(event.type()==QtCore.QEvent.MouseButtonRelease):
            if event.button() == QtCore.Qt.LeftButton:
                self.selectedItemList = []
                self.deselectAllTableItems()
                self.boolSelection = False
        if event.type() == QtCore.QEvent.HoverMove:
            self.label.setText("Size: " + str(self.featureTable.horizontalHeader().logicalIndexAt(event.pos())))
        return False


    @QtCore.pyqtSignature("")
    def on_confirmButtons_accepted(self):
        self.parent.project.featureMgr = featureMgr.FeatureMgr(self.parent.project.dataMgr)
        featureSelectionList = featureMgr.ilastikFeatureGroups.createList()
        res = self.parent.project.featureMgr.setFeatureItems(featureSelectionList)
        if res is True:
            #print "features have maximum needed margin of:", self.parent.project.featureMgr.maxSigma*3
            self.parent.labelWidget.setBorderMargin(int(self.parent.project.featureMgr.maxContext))
            self.computeMemoryRequirement(featureSelectionList)
            self.close()
            self.ilastik.featureCompute()
        else:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
            return False





    @QtCore.pyqtSignature("")
    def on_confirmButtons_rejected(self):
        self.parent.ribbon.tabDict['Features'].itemDict['Select and Compute'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(True)
        self.close()

    def computeMemoryRequirement(self, featureSelectionList):
        if featureSelectionList != []:
            dataMgr = self.parent.project.dataMgr

            numOfChannels = dataMgr[0].dataVol.data.shape[-1]
            numOfEffectiveFeatures =  0
            for f in featureSelectionList:
                numOfEffectiveFeatures += f.computeSizeForShape(dataMgr[0].dataVol.data.shape)
                numOfEffectiveFeatures *= numOfChannels
                numOfPixels = numpy.sum([ numpy.prod(dataItem.dataVol.data.shape[:-1]) for dataItem in dataMgr ])
                # 7 bytes per pixel overhead
            memoryReq = numOfPixels * (7 + numOfEffectiveFeatures*4.0) /1024.0**2
            print "Total feature vector length is %d with aprox. memory demand of %8.2f MB" % (numOfEffectiveFeatures, memoryReq)
        else:
            print "No features selected"
        # return memoryReq

