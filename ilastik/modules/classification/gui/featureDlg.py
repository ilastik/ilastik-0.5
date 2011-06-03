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


from PyQt4 import QtCore, QtGui
import sys
from ilastik.modules.classification.core import featureMgr
import qimage2ndarray
from ilastik.modules.classification.core.featureMgr import ilastikFeatureGroups
from ilastik.gui.iconMgr import ilastikIcons


class PreView(QtGui.QGraphicsView):
    def __init__(self, previewImage=None):
        QtGui.QGraphicsView.__init__(self)
        
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        self.setMaximumWidth(200)
        self.setMaximumHeight(200)        
        
        self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.hudLayout = QtGui.QVBoxLayout(self)
        
        self.sizeTextLabel = QtGui.QLabel(self)
        self.sizeTextLabel.setStyleSheet("color: red; font-weight:bold;")
        self.sizeTextLabel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.sizeTextLabel.setText("Size:")
        
        self.hudLayout.addWidget(self.sizeTextLabel)
        
        self.testLabel =  QtGui.QLabel()
        self.hudLayout.addWidget(self.testLabel)
        self.testLabel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)  
        self.hudLayout.addStretch()
        
        self.grscene = QtGui.QGraphicsScene()
        pixmapImage = QtGui.QPixmap(qimage2ndarray.array2qimage(previewImage))
        self.grscene.addPixmap(pixmapImage)
        self.setScene(self.grscene)
            
    def setSizeToLabel(self, size):
        self.sizeTextLabel.setText("Size: " + str(size))
        self.updateCircle(size)
        
    def updateCircle(self, size):
        pixmap = QtGui.QPixmap(self.width(), self.height())
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.red)
        painter.drawEllipse(QtCore.QRect(70, 70, size, size))
        painter.end()
        self.testLabel.setPixmap(QtGui.QPixmap(pixmap))


class FeatureTableWidgetVHeader(QtGui.QTableWidgetItem):
    def __init__(self, featureName, feature=None):
        QtGui.QTableWidgetItem.__init__(self, "   " + featureName)
        # init
        # ------------------------------------------------
        self.setSizeHint(QtCore.QSize(260, 0))
        self.expanded = True
        self.isParent = False
        self.feature = feature
        self.name = featureName
        self.children = []
            
    def setExpanded(self):
        QtGui.QTableWidgetItem.setText(self, "-  " + self.name)
        
        self.expanded = True
        
    def setCollapsed(self):
        QtGui.QTableWidgetItem.setText(self, "+  " + self.name)
        self.expanded = False
        
        
class FeatureTableWidgetHHeader(QtGui.QTableWidgetItem):
    def __init__(self, name):
        QtGui.QTableWidgetItem.__init__(self, "   " + name)
        # init
        # ------------------------------------------------
        self.expanded = True
        self.isParent = False
        self.name = name
        self.children = []
            
    def setExpanded(self):
        QtGui.QTableWidgetItem.setText(self, "-  " + self.name)
        
        self.expanded = True
        
    def setCollapsed(self):
        QtGui.QTableWidgetItem.setText(self, "+  " + self.name)
        self.expanded = False
        

class ItemDelegate(QtGui.QItemDelegate):
    """"
     TODO: DOKU
    """
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.parent = parent
    
    def paint(self, painter, option, index):
        item = self.parent.item(index.row(), index.column())
        
        if item.featureState == 0:
            option.state = QtGui.QStyle.State_Off
        elif item.featureState == 1:
            option.state = QtGui.QStyle.State_NoChange
        else:
            option.state = QtGui.QStyle.State_On
            
        self.parent.style().drawPrimitive(QtGui.QStyle.PE_IndicatorCheckBox, option, painter)
        self.parent.update()


class FeatureTableWidgetItem(QtGui.QTableWidgetItem):
    def __init__(self, feature, parent=None, featureState=0):
        QtGui.QTableWidgetItem.__init__(self)

        self.isParent = False
        self.children = []
        self.featureState = featureState
        self.feature = feature
        
    def setFeatureState(self, state):
        self.featureState = state
        
    def changeState(self):
        if self.featureState == 0:
            self.featureState = 2
        else:
            self.featureState = 0


class FeatureTableWidget(QtGui.QTableWidget):
    def __init__(self, ilastik):
        QtGui.QTableWidget.__init__(self)
        # init
        # ------------------------------------------------
        self.tmpSelectedItems = []
        self.ilastik = ilastik
        self.setStyleSheet("background-color:white;")
        #self.setAlternatingRowColors(True)        
        #layout
        # ------------------------------------------------
        self.setCornerButtonEnabled(False)
        self.setMinimumWidth(612)
        self.setMinimumHeight(100)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(0)
        self.setShowGrid(False)
        self.viewport().installEventFilter(self)
        self.setMouseTracking(1)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setClickable(True)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setClickable(True)
        self.itemDelegator = ItemDelegate(self)
        self.setItemDelegate(self.itemDelegator)
        self.horizontalHeader().setMouseTracking(1)
        self.horizontalHeader().installEventFilter(self)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        #self.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        
        self.itemSelectionChanged.connect(self.tableItemSelectionChanged)
        self.connect(self, QtCore.SIGNAL('cellDoubleClicked (int, int)'), self.featureTableItemDoubleClicked)
        self.connect(self.verticalHeader(), QtCore.SIGNAL('sectionClicked (int)'), self.expandOrCollapseVHeader)

        self.setHHeaderNames()
        self.setVHeaderNames()
        self.collapsAllRows()
        self.fillTabelWithItems()  
        self.setOldSelectedFeatures()           
                
    # methods
    # ------------------------------------------------    
    def setOldSelectedFeatures(self):
        if len(featureMgr.ilastikFeatureGroups.selection) == self.rowCount() and len(featureMgr.ilastikFeatureGroups.selection[0]) ==  self.columnCount():
            for c in range(self.columnCount()):
                for r in range(self.rowCount()):
                    if featureMgr.ilastikFeatureGroups.selection[r][c]:
                        self.item(r,c).setFeatureState(2)
    
    
    def createFeatureList(self):
        result = []
        for c in range(self.columnCount()):
            for r in range(self.rowCount()):
                item = self.item(r,c)
                if not item.isParent:
                    if item.featureState == 2:
                        #print r,c,self.verticalHeaderItem(r).feature,'###'
                        feat = self.verticalHeaderItem(r).feature
                        sigma = ilastikFeatureGroups.groupScaleValues[c]
                        result.append(feat(sigma))
        return result
    

    def setChangeSizeCallback(self, changeSizeCallback):
        self.changeSizeCallback = changeSizeCallback
        
   
    def fillTabelWithItems(self):
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                item = FeatureTableWidgetItem(0)
                if self.verticalHeaderItem(i).isParent:
                    item.isParent = True
                self.setItem(i,j, item)
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                if self.verticalHeaderItem(i).isParent:
                    parent = self.item(i,j)
                    continue
                parent.children.append(self.item(i,j))
    
    def expandOrCollapseVHeader(self, row):
        vHeader = self.verticalHeaderItem(row)
        if not vHeader.children == []:
            if vHeader.expanded == False:
                vHeader.setExpanded()
                for subRow in vHeader.children:
                    self.showRow(subRow)
            else:
                for subRow in vHeader.children:
                    self.hideRow(subRow)
                    vHeader.setCollapsed()
            self.deselectAllTableItems()
    
    def collapsAllRows(self):
        for i in range(self.rowCount()):
            if self.verticalHeaderItem(i).isParent == False:
                self.hideRow(i)
            else:
                self.verticalHeaderItem(i).setCollapsed()
    
    def tableItemSelectionChanged(self):
        for item in self.selectedItems():
            if item in self.tmpSelectedItems:
                self.tmpSelectedItems.remove(item)
            else:
                if item.isParent and self.verticalHeaderItem(item.row()).expanded == False:
                    if item.featureState == 0 or item.featureState == 1:
                        state = 2
                    else:
                        state = 0
                    for child in item.children:
                        child.setFeatureState(state)
                else:
                    item.changeState()
                
        for item in self.tmpSelectedItems:
            if item.isParent and self.verticalHeaderItem(item.row()).expanded == False:
                if item.featureState == 0 or item.featureState == 1:
                    state = 2
                else:
                    state = 0
                for child in item.children:
                    child.setFeatureState(state)
            else:
                item.changeState()
             
        self.updateParentCell()
        self.tmpSelectedItems = self.selectedItems()
        self.parent().parent().setMemReq()
        
        
    def updateParentCell(self):
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item.isParent:
                    x = 0
                    for child in item.children:
                        if child.featureState == 2:
                            x += 1
                    if len(item.children) == x:
                        item.featureState = 2
                    elif x == 0:
                        item.featureState = 0
                    else:
                        item.featureState = 1


    def eventFilter(self, obj, event):
#        #??? hheader change size
#        if not event.type() == QtCore.QEvent.Paint:
#            print obj, event
#        if event.type() == QtCore.QEvent.HoverMove:
#            print "hover"
#        if type(obj) == QtGui.QHeaderView and self.underMouse():
#            print obj.pos()
        if(event.type()==QtCore.QEvent.MouseButtonPress):
            if event.button() == QtCore.Qt.LeftButton:
                if self.itemAt(event.pos()):
                    self.setSelectionMode(2)
                    #self.parent().parent().ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = True
        if(event.type()==QtCore.QEvent.MouseButtonRelease):
            #self.parent().parent().ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = False
            if event.button() == QtCore.Qt.LeftButton:
                self.setSelectionMode(0)
                self.tmpSelectedItems = []
                self.deselectAllTableItems()
        if event.type() == QtCore.QEvent.MouseMove:
            if self.itemAt(event.pos()) and self.underMouse():
                item = self.itemAt(event.pos())
                self.changeSizeCallback(ilastikFeatureGroups.groupMaskSizes[item.column()])
        return False
        
        
    def featureTableItemDoubleClicked(self, row, column):
        item = self.item(row, column)
        if item.isParent and self.verticalHeaderItem(item.row()).expanded == True:
            if item.featureState == 0 or item.featureState == 1:
                state = 2
            else:
                state = 0
            for child in item.children:
                child.setFeatureState(state)
        self.updateParentCell()
        
    def deselectAllTableItems(self):
        for item in self.selectedItems():
            item.setSelected(False)

    
    def setHHeaderNames(self):
        self.setColumnCount(len(featureMgr.ilastikFeatureGroups.groupScaleNames))
        self.setHorizontalHeaderLabels(featureMgr.ilastikFeatureGroups.groupScaleNames)

    
    def setVHeaderNames(self):
        row = 0
        for i in featureMgr.ilastikFeatureGroups.groups.keys():
            self.insertRow(row)
            self.setVerticalHeaderItem(row, FeatureTableWidgetVHeader(i, feature=None))
            parent = self.verticalHeaderItem(row)
            parent.isParent = True
            row += 1
            for j in featureMgr.ilastikFeatureGroups.groups[i]:
                self.insertRow(row)
                self.setVerticalHeaderItem(row, FeatureTableWidgetVHeader(j.name, feature=j))
                self.verticalHeaderItem(row).setData(3, j.name)
                parent.children.append(row)
                row += 1
                
                
#class OkButton(QtGui.QToolButton):
#    def __init__(self, *args):
#        QtGui.QToolButton.__init__(self,  *args)
#        
#        self.connect(self, QtCore.SIGNAL('clicked()'), self.clickOnButton)
#        
#    def clickOnButton(self):
#        print "ok"
#        
#
#class CancelButton(QtGui.QToolButton):
#    def __init__(self, *args):
#        QtGui.QToolButton.__init__(self,  *args)
#        
#        self.connect(self, QtCore.SIGNAL('clicked()'), self.clickOnButton)
#        
#    def clickOnButton(self):
#        print "cancel"


class FeatureDlg(QtGui.QDialog):
    def __init__(self, parent=None, previewImage=None):
        QtGui.QDialog.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setWindowTitle("Spatial Features")
        self.setWindowIcon(QtGui.QIcon(ilastikIcons.Select))
        self.parent = parent
        self.ilastik = parent
        #self.ilastik.project.dataMgr.Classification.featureMgr.printComputeMemoryRequirement = False
        # widgets and layouts
        # ------------------------------------------------
        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)
        
        tableAndViewGroupBox = QtGui.QGroupBox("Scales and Groups")
        tableAndViewGroupBox.setFlat(True)
        self.featureTableWidget = FeatureTableWidget(self.ilastik)
        tableAndViewLayout = QtGui.QHBoxLayout()
        tableAndViewLayout.addWidget(self.featureTableWidget)
        
        viewAndButtonLayout =  QtGui.QVBoxLayout()              
        self.preView = PreView(previewImage)
        viewAndButtonLayout.addWidget(self.preView)
        
        buttonsLayout = QtGui.QHBoxLayout()
        self.memReqLabel = QtGui.QLabel()
        buttonsLayout.addWidget(self.memReqLabel)
        self.ok = QtGui.QToolButton()
        self.ok.setText("OK")
        self.connect(self.ok, QtCore.SIGNAL("clicked()"), self.on_okClicked)
        
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.ok)
        
        self.cancel = QtGui.QToolButton()
        self.cancel.setText("Cancel")
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self.on_cancelClicked)

        buttonsLayout.addWidget(self.cancel)
        viewAndButtonLayout.addLayout(buttonsLayout)
        tableAndViewLayout.addLayout(viewAndButtonLayout)
        tableAndViewGroupBox.setLayout(tableAndViewLayout)
        tableAndViewGroupBox.updateGeometry()
        self.layout.addWidget(tableAndViewGroupBox)
        
        self.layout.setContentsMargins(0,0,10,10)
        tableAndViewGroupBox.setContentsMargins(0,10,0,0)
        tableAndViewLayout.setContentsMargins(0,10,0,0)
        
        self.featureTableWidget.setChangeSizeCallback(self.preView.setSizeToLabel)   
                
    # methods
    # ------------------------------------------------
    def setMemReq(self):
        featureSelectionList = self.featureTableWidget.createFeatureList()
        memReq = self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)
        self.memReqLabel.setText("%8.2f MB" % memReq)
    
    
    def on_okClicked(self):
        featureSelectionList = self.featureTableWidget.createFeatureList()
        res = self.parent.project.dataMgr.Classification.featureMgr.setFeatureItems(featureSelectionList)
        if res is True:
            #print "features have maximum needed margin of:", self.parent.project.dataMgr.Classification.featureMgr.maxSigma*3
            self.parent.labelWidget.setBorderMargin(int(self.parent.project.dataMgr.Classification.featureMgr.maxContext))
            self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)           
            self.accept() 
        else:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
            self.on_cancelClicked()
            
    def on_cancelClicked(self):
        self.reject()
        
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    ex = FeatureDlg()
    ex.show()
    ex.raise_()
    app.exec_()
            