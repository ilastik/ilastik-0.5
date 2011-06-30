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


from PyQt4.QtGui import QGraphicsView, QVBoxLayout, QLabel, QGraphicsScene, QPixmap, QPainter, \
                        QTableWidgetItem, QItemDelegate, QStyle, QHBoxLayout, QIcon, QHeaderView, \
                        QAbstractItemView, QDialog, QToolButton, QErrorMessage, QApplication, \
                        QTableWidget, QGroupBox, QBrush, QColor, QPalette, QStyleOptionViewItem, \
                        QFont, QPen, QPolygon, QSlider, QSizePolicy
from PyQt4.QtCore import Qt, QRect, QSize, QEvent, QPointF, QPoint

import numpy
import sys
from ilastik.modules.classification.core import featureMgr
import qimage2ndarray
from ilastik.modules.classification.core.featureMgr import ilastikFeatureGroups
from ilastik.gui.iconMgr import ilastikIcons


class PreView(QGraphicsView):
    def __init__(self, previewImage=None):
        QGraphicsView.__init__(self)    
        
        self.zoom = 2
        self.scale(self.zoom, self.zoom) 
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.hudLayout = QVBoxLayout(self)
        self.hudLayout.setContentsMargins(0,0,0,0)
        
#        self.sizeTextLabel = QLabel(self)
#        self.sizeTextLabel.setStyleSheet("color: red; font-weight:bold;")
#        self.sizeTextLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
#        self.sizeTextLabel.setText("Size:")
        
#        self.hudLayout.addWidget(self.sizeTextLabel)
        
        self.ellipseLabel =  QLabel()
        self.ellipseLabel.setMinimumWidth(self.width())
        self.ellipseLabel.setMinimumHeight(self.height())
        self.hudLayout.addWidget(self.ellipseLabel)
        self.ellipseLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)  
        #self.hudLayout.addStretch()
        
        self.grscene = QGraphicsScene()
        if previewImage is None:
            previewImage = (numpy.random.rand(100,100)*256).astype(numpy.uint8)
        pixmapImage = QPixmap(qimage2ndarray.array2qimage(previewImage))
        self.grscene.addPixmap(pixmapImage)
        self.setScene(self.grscene)
            
    def setSizeToLabel(self, size):
#        self.sizeTextLabel.setText("Size: " + str(size))
        self.updateCircle(size)
        
    def updateCircle(self, s):
        size = s * self.zoom
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        #painter size text
#        painter = QPainter()
#        painter.begin(pixmap)
#        painter.setRenderHint(QPainter.Antialiasing)
#        painter.setPen(Qt.red)
#        painter.setFont(QFont("Arial", 20))
#        painter.drawText(10, 20, "Size: " + str(s))
#        painter.end()
        #painter ellipse 1
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.red)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter.end()
        #painter ellipse 2
        painter2 = QPainter()
        painter2.begin(pixmap)
        painter2.setRenderHint(QPainter.Antialiasing)
        pen2 = QPen(Qt.green)
        pen2.setStyle(Qt.DotLine)
        pen2.setWidth(3)
        painter2.setPen(pen2)
        painter2.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter2.end()
        
        self.ellipseLabel.setPixmap(QPixmap(pixmap))


class FeatureTableWidgetVHeader(QTableWidgetItem):
    def __init__(self, featureName, feature=None):
        QTableWidgetItem.__init__(self, featureName)
        # init
        # ------------------------------------------------
        self.isExpanded = True
        self.isParent = False
        self.feature = feature
        self.name = featureName
        self.children = []
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))
            
    def setExpanded(self):
        self.isExpanded = True
        self.drawIcon()
        
    def setCollapsed(self):
        self.isExpanded = False
        self.drawIcon()

    def drawIcon(self, color=Qt.black):
        self.setForeground(QBrush(color))
        
        if self.isParent:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
    #        painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(color)
            painter.setRenderHint(QPainter.Antialiasing)
            if not self.isExpanded:
                points = [QPoint(6,6), QPoint(6,14), QPoint(14, 10)]
                painter.drawPolygon(QPolygon(points))
            else:
                points = [QPoint(6,6), QPoint(15,6), QPoint(10, 14)]
                painter.drawPolygon(QPolygon(points))
            painter.end()
            self.setIcon(QIcon(pixmap))
        
    def setIconAndTextColor(self, color):
        self.drawIcon(color)
        
        
class FeatureTableWidgetHHeader(QTableWidgetItem):
    def __init__(self, sigma):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.sigma = sigma
        self.brushSize = int(3.0*self.sigma + 0.5)*2 + 1
        #self.headerSize = QSize(40,30)
        self.pixmapSize = QSize(61, 61)
        
        self.setNameAndBrush(self.sigma)
        
    def setNameAndBrush(self, sigma, color=Qt.black):
        self.sigma = sigma
        self.brushSize = int(3.0*self.sigma + 0.5)*2 + 1
        self.setText(str(self.brushSize))
        font = QFont() 
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        self.setForeground(color)
                        
        pixmap = QPixmap(self.pixmapSize)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(color)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.drawEllipse(QRect(self.pixmapSize.width()/2 - self.brushSize/2, self.pixmapSize.height()/2 - self.brushSize/2, self.brushSize, self.brushSize))
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setTextAlignment(Qt.AlignVCenter)
        #self.setSizeHint(self.headerSize)
        
    def setIconAndTextColor(self, color):
        self.setNameAndBrush(self.sigma, color)
        
        

class ItemDelegate(QItemDelegate):
    """"
     TODO: DOKU
    """
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)
        self.parent = parent
    
    def paint(self, painter, option, index):
        item = self.parent.item(index.row(), index.column())
        verticalHeader = self.parent.verticalHeaderItem(index.row())
        
        if item.featureState == Qt.Unchecked:
            option.state = QStyle.State_Off
        elif item.featureState == Qt.PartiallyChecked:
            option.state = QStyle.State_NoChange
        else:
            option.state = QStyle.State_On
        if item.isSelected() == True:
            painter.fillRect(option.rect, option.palette.highlight ())
        else:
            if verticalHeader.isParent: 
                painter.fillRect(option.rect, option.palette.alternateBase())
            else:
                painter.fillRect(option.rect, option.palette.light())
        self.parent.style().drawPrimitive(QStyle.PE_IndicatorCheckBox, option, painter)
        self.parent.update()


class FeatureTableWidgetItem(QTableWidgetItem):
    def __init__(self, feature, parent=None, featureState=0):
        QTableWidgetItem.__init__(self)

        self.isParent = False
        self.children = []
        self.featureState = featureState
        self.feature = feature
        
    def setFeatureState(self, state):
        self.featureState = state
        
    def changeState(self):
        if self.featureState == Qt.Unchecked:
            self.featureState = Qt.Checked
        else:
            self.featureState = Qt.Unchecked


class FeatureTableWidget(QTableWidget):
    def __init__(self, ilastik):
        QTableWidget.__init__(self)
        # init
        # ------------------------------------------------
        self.defaultGroupScaleValues = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        self.groupScaleValues = []
        self.tmpSelectedItems = []
        self.ilastik = ilastik
        self.setIconSize(QSize(30, 30))
        #self.setAlternatingRowColors(True)    
        self.isSliderOpen = False    
        self.selection = []
        #layout
        # ------------------------------------------------
        self.setCornerButtonEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
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
#        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        
        self.itemSelectionChanged.connect(self.tableItemSelectionChanged)
        self.cellDoubleClicked.connect(self.featureTableItemDoubleClicked)
        self.verticalHeader().sectionClicked.connect(self.expandOrCollapseVHeader)
        self.horizontalHeader().sectionDoubleClicked.connect(self.hHeaderDoubleclicked)
        
        self.loadSelection()
        self.setHHeaderNames()
        self.setVHeaderNames()
        self.collapsAllRows()
        self.fillTabelWithItems()  
        self.setOldSelectedFeatures() 
        self.updateParentCell() 
        
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
                        
    # methods
    # ------------------------------------------------
    
    def loadSelection(self):
        if not len(featureMgr.ilastikFeatureGroups.newSelection) == 0:
            self.selection = featureMgr.ilastikFeatureGroups.newSelection
            self.groupScaleValues = featureMgr.ilastikFeatureGroups.newGroupScaleValues
        else:
            self.selection = featureMgr.ilastikFeatureGroups.selection
            self.groupScaleValues = self.defaultGroupScaleValues
    
    #TODO .99999999999 
    def createSigmaList(self):
        result = []
        for c in range(self.columnCount()):
            result.append(self.horizontalHeaderItem(c).sigma)
        return result
            
    
    def hHeaderDoubleclicked(self, col):
        self.isSliderOpen = True
        sliderdlg = SliderDlg(self, self.horizontalHeaderItem(col).sigma)
        self.setHAndVHeaderForegroundColor(col, -1)
#        sliderdlg.show()
#        sliderdlg.raise_()
        self.horizontalHeaderItem(col).setNameAndBrush(sliderdlg.exec_())
        self.isSliderOpen = False
      
    def createSelectedFeatureList(self):
        result = []
        for c in range(self.columnCount()):
            for r in range(self.rowCount()):
                item = self.item(r,c)
                if not item.isParent:
                    if item.featureState == 2:
                        result.append([self.verticalHeaderItem(r).name, str(self.horizontalHeaderItem(c).sigma)])
        return result
        
    
    def setOldSelectedFeatures(self):
        if len(self.selection) == 0:
            return
        if len(self.selection[0]) == 2:
            for feature in self.selection:
                for c in range(self.columnCount()):
                    for r in range(self.rowCount()):
                        if feature[0] == self.verticalHeaderItem(r).name and feature[1] == str(self.horizontalHeaderItem(c).sigma):
                            self.item(r,c).setFeatureState(2)
        else:
            i = -1
            for r in range(self.rowCount()):
                if self.verticalHeaderItem(r).isParent:
                    i+=1
                for c in range(self.columnCount()):
                    if self.selection[i][c]:
                        self.item(r,c).setFeatureState(2)
    
    
    def createFeatureList(self):
        result = []
        for c in range(self.columnCount()):
            for r in range(self.rowCount()):
                item = self.item(r,c)
                if not item.isParent:
                    if item.featureState == 2:
                        feat = self.verticalHeaderItem(r).feature
                        sigma = self.horizontalHeaderItem(c).sigma
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
            if vHeader.isExpanded == False:
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
                if item.isParent and self.verticalHeaderItem(item.row()).isExpanded == False:
                    if item.featureState == 0 or item.featureState == 1:
                        state = 2
                    else:
                        state = 0
                    for child in item.children:
                        child.setFeatureState(state)
                else:
                    item.changeState()
                
        for item in self.tmpSelectedItems:
            if item.isParent and self.verticalHeaderItem(item.row()).isExpanded == False:
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
        if(event.type()==QEvent.MouseButtonPress):
            if event.button() == Qt.LeftButton:
                if self.itemAt(event.pos()):
                    self.setSelectionMode(2)
        if(event.type()==QEvent.MouseButtonRelease):
            if event.button() == Qt.LeftButton:
                self.setSelectionMode(0)
                self.tmpSelectedItems = []
                self.deselectAllTableItems()
        if event.type() == QEvent.MouseMove:
            if self.itemAt(event.pos()) and self.underMouse():
                item = self.itemAt(event.pos())
                hHeader = self.horizontalHeaderItem(item.column())
                self.changeSizeCallback(hHeader.brushSize)               
                self.setHAndVHeaderForegroundColor(item.column(), item.row())
        return False
        
        
    def setHAndVHeaderForegroundColor(self, c, r):       
        p = QPalette()
        for i in range(self.columnCount()):
            col = self.horizontalHeaderItem(i)
            if i == c:
                col.setIconAndTextColor(p.highlight().color())
            else:
                col.setIconAndTextColor(p.text().color())
            
        for j in range(self.rowCount()):
            row = self.verticalHeaderItem(j)
            if j == r:
                row.setIconAndTextColor(p.highlight().color())
            else:
                row.setIconAndTextColor(p.text().color())
        
        
    def featureTableItemDoubleClicked(self, row, column):
        item = self.item(row, column)
        if item.isParent and self.verticalHeaderItem(item.row()).isExpanded == True:
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
        self.setColumnCount(len(self.groupScaleValues))
        for c in range(len(self.groupScaleValues)):
            hHeader = FeatureTableWidgetHHeader(self.groupScaleValues[c])
            self.setHorizontalHeaderItem(c, hHeader)

    
    def setVHeaderNames(self):
        row = 0
        for i in featureMgr.ilastikFeatureGroups.groups.keys():
            self.insertRow(row)
            vHeader = FeatureTableWidgetVHeader(i, feature=None)
            vHeader.setSizeHint(QSize(260,30))
            self.setVerticalHeaderItem(row, vHeader)
            parent = self.verticalHeaderItem(row)
            parent.isParent = True
            row += 1
            for j in featureMgr.ilastikFeatureGroups.groups[i]:
                self.insertRow(row)
                self.setVerticalHeaderItem(row, FeatureTableWidgetVHeader(j.name, feature=j))
                #Tooltip
                #self.verticalHeaderItem(row).setData(3, j.name)
                parent.children.append(row)
                row += 1
                
                
                
class SliderDlg(QDialog):
    def __init__(self, parent, sigma):
        QDialog.__init__(self, parent, Qt.FramelessWindowHint)
        
        # init
        # ------------------------------------------------
        self.oldSigma = sigma
        self.sigma = sigma
        self.brushSize = 0
        self.setStyleSheet("background-color:window;")
        # widgets and layouts
        # ------------------------------------------------
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        labelsLayout =  QHBoxLayout()
        self.labelSigma = QLabel("Sigma: xx")
        self.labelBrushSize = QLabel("BrushSize: xx")
        labelsLayout.addWidget(self.labelSigma)
        labelsLayout.addWidget(self.labelBrushSize)
        self.layout.addLayout(labelsLayout)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(100)
        self.slider.sliderMoved.connect(self.on_sliderMoved)
        self.layout.addWidget(self.slider)
        
        buttonsLayout = QHBoxLayout()
        self.cancel = QToolButton()
        self.cancel.setText("cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)
        buttonsLayout.addWidget(self.cancel)
        
        
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        buttonsLayout.addWidget(self.ok)

        self.layout.addLayout(buttonsLayout)
        
        self.layout.setContentsMargins(10, 0, 10, 0)
        labelsLayout.setContentsMargins(0, 0, 0, 0)
        buttonsLayout.setContentsMargins(0, 0, 0, 0)
        
        self.setlabelSigma()
        self.setLabelBrushSize()
        self.setSliderPosition()
        
    def setlabelSigma(self):
        self.labelSigma.setText("Sigma: " + str(self.sigma))
        
    def setLabelBrushSize(self):
        self.brushSize = int(3.0*self.sigma + 0.5)*2 + 1
        self.labelBrushSize.setText("BrushSize: " + str(self.brushSize))
        
    def setSliderPosition(self):
        self.slider.setSliderPosition(self.sigma*10)
    
    def on_sliderMoved(self, i):
        self.sigma = float(i)/10
        self.setlabelSigma()
        self.setLabelBrushSize()
        self.parent().parent().parent().preView.setSizeToLabel(self.brushSize)
    
    def on_cancelClicked(self):
        self.reject()
        
    def on_okClicked(self):
        self.accept()
        
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return  self.sigma
        else:
            return self.oldSigma
        


class FeatureDlg(QDialog):
    def __init__(self, parent=None, previewImage=None):
        QDialog.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setWindowTitle("Spatial Features")
        self.setWindowIcon(QIcon(ilastikIcons.Select))
        self.parent = parent
        self.ilastik = parent
        # widgets and layouts
        # ------------------------------------------------
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        tableAndViewGroupBox = QGroupBox("Scales and Groups")
        tableAndViewGroupBox.setFlat(True)
        self.featureTableWidget = FeatureTableWidget(self.ilastik)
        tableAndViewLayout = QHBoxLayout()
        tableAndViewLayout.addWidget(self.featureTableWidget)
        
        viewAndButtonLayout =  QVBoxLayout() 
        self.preView = PreView(previewImage)
        viewAndButtonLayout.addWidget(self.preView)
        
        buttonsLayout = QHBoxLayout()
        self.memReqLabel = QLabel()
        buttonsLayout.addWidget(self.memReqLabel)
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.ok)
        
        self.cancel = QToolButton()
        self.cancel.setText("Cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)

        buttonsLayout.addWidget(self.cancel)
        viewAndButtonLayout.addLayout(buttonsLayout)
        tableAndViewLayout.addLayout(viewAndButtonLayout)
        tableAndViewGroupBox.setLayout(tableAndViewLayout)
        #tableAndViewGroupBox.updateGeometry()
        self.layout.addWidget(tableAndViewGroupBox)
        
        self.layout.setContentsMargins(0,0,10,10)
        tableAndViewGroupBox.setContentsMargins(0,10,0,0)
        tableAndViewLayout.setContentsMargins(0,10,0,0)
        
        self.featureTableWidget.setChangeSizeCallback(self.preView.setSizeToLabel)
        self.setMemReq()        
                
    # methods
    # ------------------------------------------------
    def setMemReq(self):
        featureSelectionList = self.featureTableWidget.createFeatureList()
        #TODO
        #memReq = self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)
        #self.memReqLabel.setText("%8.2f MB" % memReq)
    
    def on_okClicked(self):
        featureSelectionList = self.featureTableWidget.createFeatureList()
        selectedFeatureList = self.featureTableWidget.createSelectedFeatureList()
        sigmaList = self.featureTableWidget.createSigmaList()
        featureMgr.ilastikFeatureGroups.newGroupScaleValues = sigmaList
        featureMgr.ilastikFeatureGroups.newSelection = selectedFeatureList
        res = self.parent.project.dataMgr.Classification.featureMgr.setFeatureItems(featureSelectionList)
        if res is True:
            self.parent.labelWidget.setBorderMargin(int(self.parent.project.dataMgr.Classification.featureMgr.maxContext))
            self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)           
            self.accept() 
        else:
            QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
            self.on_cancelClicked()
            
    def on_cancelClicked(self):
        self.reject()
        
        
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
    
#    def onAccepted():
#        global ex
#        print ex.adfasdfdf
#    
#    g = GroupName("Banane", "Birne")
    
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    ex = FeatureDlg()
#    ex.setGrouping(g)
#    numpy.random.randint
#    ex.setRawData()
#    ex.ok.clicked.connect(onAccepted)
    
    ex.show()
    ex.raise_()
    app.exec_()
            