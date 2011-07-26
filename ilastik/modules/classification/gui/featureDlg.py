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
from PyQt4.QtCore import Qt, QRect, QSize, QEvent, QPointF, QPoint, pyqtSignal, SIGNAL

import numpy
import sys
from ilastik.modules.classification.core import featureMgr
import qimage2ndarray
from ilastik.modules.classification.core.featureMgr import ilastikFeatureGroups


#===============================================================================
# PreView
#===============================================================================
class PreView(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)    
        
        self.zoom = 2
        self.scale(self.zoom, self.zoom) 
        self.lastSize = 1
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
#        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.installEventFilter(self)
                
        self.hudLayout = QVBoxLayout(self)
        self.hudLayout.setContentsMargins(0,0,0,0)
        
        self.ellipseLabel =  QLabel()
        self.ellipseLabel.setMinimumWidth(self.width())
        self.hudLayout.addWidget(self.ellipseLabel)
        self.ellipseLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)  

        
    def setPreviewImage(self, previewImage):
        self.grscene = QGraphicsScene()
        pixmapImage = QPixmap(qimage2ndarray.array2qimage(previewImage))
        self.grscene.addPixmap(pixmapImage)
        self.setScene(self.grscene)
        

    def eventFilter(self, obj, event):
        if(event.type()==QEvent.Resize):
            self.ellipseLabel.setMinimumWidth(self.width())
            self.updateFilledCircle(self.lastSize)
        return False
    
    def sizeHint(self):
        return QSize(200, 200)


    def setSizeToLabel(self, size):
        self.updateFilledCircle(size)
        
    def updateCircle(self, s):
        size = s * self.zoom
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        #painter ellipse 1
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.red)
        pen.setWidth(3)
        painter.setPen(pen)
        brush = QBrush(Qt.green)
        painter.setBrush(brush)
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
        self.lastSize = s
        
    def updateFilledCircle(self, s):
        size = s * self.zoom
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        #painter filled ellipse
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(Qt.green)
        painter.setBrush(brush)
        painter.setOpacity(0.4)
        painter.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter.end()
        #painter ellipse 2
        painter2 = QPainter()
        painter2.begin(pixmap)
        painter2.setRenderHint(QPainter.Antialiasing)
        pen2 = QPen(Qt.red)
        pen2.setWidth(1)
        painter2.setPen(pen2)
        painter2.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter2.end()
        
        self.ellipseLabel.setPixmap(QPixmap(pixmap))
        self.lastSize = s


#===============================================================================
# FeatureTableWidgetVHeader
#===============================================================================
class FeatureTableWidgetVHeader(QTableWidgetItem):
    def __init__(self):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.isExpanded = True
        self.isRootNode = False
        self.feature = None
        self.vHeaderName = None
        self.children = []
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))
            
    def setExpanded(self):
        self.isExpanded = True
        self._drawIcon()
        
    def setCollapsed(self):
        self.isExpanded = False
        self._drawIcon()
        
    def setIconAndTextColor(self, color):
        self._drawIcon(color)
    
    def setFeatureVHeader(self, feature):
        self.feature = feature
        self.vHeaderName = feature.name
        self.setText(self.vHeaderName)
#        self.featureID = feature.id
        
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))
        
    def setGroupVHeader(self, name):
        self.vHeaderName = name
        self.setText(self.vHeaderName)
        self.isRootNode = True
        

    def _drawIcon(self, color=Qt.black):
        self.setForeground(QBrush(color))
        
        if self.isRootNode:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(color)
            painter.setRenderHint(QPainter.Antialiasing)
            if not self.isExpanded:
                arrowRightPolygon = [QPoint(6,6), QPoint(6,14), QPoint(14, 10)]
                painter.drawPolygon(QPolygon(arrowRightPolygon))
            else:
                arrowDownPolygon = [QPoint(6,6), QPoint(15,6), QPoint(10, 14)]
                painter.drawPolygon(QPolygon(arrowDownPolygon))
            painter.end()
            self.setIcon(QIcon(pixmap))
        
        
#===============================================================================
# FeatureTableWidgetHHeader
#===============================================================================
class FeatureTableWidgetHHeader(QTableWidgetItem):
    def __init__(self, sigma, name=None):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.sigma = sigma
        self.pixmapSize = QSize(61, 61)
        if not name:
            self.setNameAndBrush(self.sigma)
        else:
            self.setText(name)
    
    @property
    def brushSize(self):
        return int(3.0*self.sigma + 0.5)*2 + 1
        
    def setNameAndBrush(self, sigma, color=Qt.black):
        self.sigma = sigma
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
        
    def setIconAndTextColor(self, color):
        self.setNameAndBrush(self.sigma, color)
        
        

#===============================================================================
# ItemDelegate
#===============================================================================
class ItemDelegate(QItemDelegate):
    """"
     TODO: DOKU
    """
    def __init__(self, parent, width, height):
        QItemDelegate.__init__(self, parent)
        
        self.itemWidth = width
        self.itemHeight = height
        self.checkedIcon = None
        self.partiallyCheckedIcon = None
        self.uncheckedIcon = None
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForUnckecked()
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForCkecked()
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForPartiallyChecked()
        
    def drawPixmapForUnckecked(self):
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapUnckecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapUnckecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        painter.end()
        
    def drawPixmapForCkecked(self):
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapCkecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapCkecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(self.itemWidth/2-5, self.itemHeight/2, self.itemWidth/2, self.itemHeight-9)
        painter.drawLine(self.itemWidth/2, self.itemHeight-9, self.itemWidth/2+10, 2)
        painter.end()
        
    def drawPixmapForPartiallyChecked(self):
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapPartiallyChecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapPartiallyChecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5,5,self.itemWidth-10, self.itemHeight-10))
        pen.setWidth(4)
        pen.setColor(QColor(139,137,137))
        painter.setPen(pen)
        painter.drawLine(self.itemWidth/2-5, self.itemHeight/2, self.itemWidth/2, self.itemHeight-9)
        painter.drawLine(self.itemWidth/2, self.itemHeight-9, self.itemWidth/2+10, 2)
        painter.end()
    
    def paint(self, painter, option, index):
        tableWidgetCell = self.parent().item(index.row(), index.column())
        
        if tableWidgetCell.featureState == Qt.Unchecked:
            if not self.uncheckedIcon == None: 
                painter.drawImage(self.adjustRectForImage(option), self.uncheckedIcon)
            else:
                painter.drawPixmap(option.rect, self.pixmapUnckecked)
                option.state = QStyle.State_Off
        elif tableWidgetCell.featureState == Qt.PartiallyChecked:
            if not self.partiallyCheckedIcon == None:
                painter.drawImage(self.adjustRectForImage(option), self.partiallyCheckedIcon)
            else:
                painter.fillRect(option.rect.adjusted(3,3,-3,-3), QColor(220,220,220))
                painter.drawPixmap(option.rect, self.pixmapPartiallyChecked)
        else:
            if not self.checkedIcon == None:
                painter.drawImage(self.adjustRectForImage(option), self.checkedIcon)
            else:
                painter.fillRect(option.rect.adjusted(3,3,-3,-3), QColor(0,250,154))
                painter.drawPixmap(option.rect, self.pixmapCkecked)
        self.parent().update()
        
    def setCheckBoxIcons(self, checked, partiallyChecked, unchecked):
        self.checkedIcon = QImage(checked)
        self.partiallyCheckedIcon = QImage(partiallyChecked)
        self.uncheckedIcon = QImage(unchecked)
        
    def adjustRectForImage(self, option):
        if self.itemWidth > self.itemHeight:
            return option.rect.adjusted((self.itemWidth-self.itemHeight)/2+5, 5,-((self.itemWidth-self.itemHeight)/2)-5,-5 )
        else:
            return option.rect.adjusted(5, (self.itemHeight-self.itemWidth)/2+5, -((self.itemHeight-self.itemWidth)/2)-5,-5 )


#===============================================================================
# FeatureTableWidgetItem
#===============================================================================
class FeatureTableWidgetItem(QTableWidgetItem):
    def __init__(self, feature, parent=None, featureState=Qt.Unchecked):
        QTableWidgetItem.__init__(self, parent)

        self.isRootNode = False
        self.children = []
        self.featureState = featureState
        
    def setFeatureState(self, state):
        self.featureState = state
        
    def toggleState(self):
        if self.featureState == Qt.Unchecked:
            self.featureState = Qt.Checked
        else:
            self.featureState = Qt.Unchecked


#===============================================================================
# FeatureTableWidget
#===============================================================================
class FeatureTableWidget(QTableWidget):    
    def __init__(self):
        QTableWidget.__init__(self)
        # init
        # ------------------------------------------------
        #FIXME: move this somewhere else maybe?
        self.tmpSelectedItems = []
        #FIXME: what does this do? put a comment, why 30,30?
        self._sigmaList = None
        self._featureGroupDict = None
        #layout
        # ------------------------------------------------
        self.setCornerButtonEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setShowGrid(False)
        self.viewport().installEventFilter(self)
        self.setMouseTracking(1)
        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setClickable(True)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setClickable(True)
        
        self.horizontalHeader().setMouseTracking(True)
        self.horizontalHeader().installEventFilter(self)
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        
        self.itemSelectionChanged.connect(self._tableItemSelectionChanged)
        self.cellDoubleClicked.connect(self._featureTableItemDoubleClicked)
        self.verticalHeader().sectionClicked.connect(self._expandOrCollapseVHeader)
        self.horizontalHeader().sectionDoubleClicked.connect(self._hHeaderDoubleclicked)
        
#        self.setFeatureGroups(featureMgr.ilastikFeatureGroups.groups)
#        self.setSigmas(self.defaultGroupScaleValues)
#        self.createTable()
                        
    # methods
    # ------------------------------------------------
        
    def setChangeSizeCallback(self, changeSizeCallback):
        self.changeSizeCallback = changeSizeCallback
    
    def setSelectedFeatures(self, selectedFeatures):
        for feature in selectedFeatures:
            for r,c in self._tableEntries():
                if feature[0] == self.verticalHeaderItem(r).vHeaderName and feature[1] == str(self.horizontalHeaderItem(c).sigma):
                    self.item(r,c).setFeatureState(Qt.Checked)
        self._updateParentCell()
    
    def createSelectedFeaturesBoolMatrix(self):
        matrix = [ [False for k in range(self.columnCount())] for j in range(self.rowCount()) ]
        for r,c in self._tableEntries():
            item = self.item(r,c)
            if not item.isRootNode and item.featureState == Qt.Checked:
                matrix[c][r] = True         
        return matrix
    
    def createSelectedFeatureList(self):
        result = []
        for r,c in self._tableEntries():
            item = self.item(r,c)
            if not item.isRootNode:
                if item.featureState == Qt.Checked:
                    result.append([self.verticalHeaderItem(r).vHeaderName, str(self.horizontalHeaderItem(c).sigma)])
        return result
    
    def createTable(self, featureGroups, sigmas, text=None):
        self._sigmaList = sigmas
        self._featureGroupDict = featureGroups
        if self._sigmaList is None:
            raise RuntimeError("No sigmas set!")
        self._addHHeader(text)
        if self._featureGroupDict is None:
            raise RuntimeError("No featuregroups set!")
        self._addVHeader()
        self._setFixedSizeToHeaders()
        self._collapsAllRows()
        self._fillTabelWithItems()
        self._setSizeHintToTableWidgetItems()
        self.itemDelegate = ItemDelegate(self, self.horizontalHeader().sizeHint().width(), self.verticalHeader().sizeHint().height())
        self.setItemDelegate(self.itemDelegate)
        self._updateParentCell()

    def createSigmaList(self):
        result = []
        for c in range(self.columnCount()):
            result.append(self.horizontalHeaderItem(c).sigma)
        return result
    
    def _tableEntries(self):
        for c in range(self.columnCount()):
            for r in range(self.rowCount()):
                yield r,c
            
    def sizeHint(self):
        height = 200
        width  = self.horizontalHeader().sizeHint().width() * self.columnCount() + self.verticalHeader().sizeHint().width() + 22
        return QSize(width, height)
    
    def _setSizeHintToTableWidgetItems(self):
        width = self.horizontalHeader().sizeHint().width()
        height = self.verticalHeader().sizeHint().height()
        for r,c in self._tableEntries():
            self.item(r,c).setSizeHint(QSize(width, height))
        
    
    def _setFixedSizeToHeaders(self):
        hHeaderSize = self.horizontalHeader().sizeHint()
        vHeaderSize = self.verticalHeader().sizeHint()
        for i in range(self.columnCount()):
            self.horizontalHeaderItem(i).setSizeHint(hHeaderSize)
        for j in range(self.rowCount()):
            self.verticalHeaderItem(j).setSizeHint(vHeaderSize)
    
    def _hHeaderDoubleclicked(self, col):
        sliderdlg = SliderDlg(self, self.horizontalHeaderItem(col).sigma)
#        self._highlightHeaders(col, -1)
        self.horizontalHeaderItem(col).setNameAndBrush(sliderdlg.exec_())
   
    def _fillTabelWithItems(self):
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                item = FeatureTableWidgetItem(self, 0)
                if self.verticalHeaderItem(i).isRootNode:
                    item.isRootNode = True
                self.setItem(i,j, item)
        for j in range(self.columnCount()):
            for i in range(self.rowCount()):
                if self.verticalHeaderItem(i).isRootNode:
                    parent = self.item(i,j)
                    continue
                parent.children.append(self.item(i,j))
    
    def _expandOrCollapseVHeader(self, row):
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
            self._deselectAllTableItems()
    
    def _collapsAllRows(self):
        for i in range(self.rowCount()):
            if not self.verticalHeaderItem(i).isRootNode:
                self.hideRow(i)
            else:
                self.verticalHeaderItem(i).setCollapsed()
    
    def _tableItemSelectionChanged(self):
        for item in self.selectedItems():
            if item in self.tmpSelectedItems:
                self.tmpSelectedItems.remove(item)
            else:
                if item.isRootNode and self.verticalHeaderItem(item.row()).isExpanded == False:
                    if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                        state = Qt.Checked
                    else:
                        state = Qt.Unchecked
                    for child in item.children:
                        child.setFeatureState(state)
                else:
                    item.toggleState()
                
        for item in self.tmpSelectedItems:
            if item.isRootNode and not self.verticalHeaderItem(item.row()).isExpanded:
                if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                    state = Qt.Checked
                else:
                    state = Qt.Unchecked
                for child in item.children:
                    child.setFeatureState(state)
            else:
                item.toggleState()
             
        self._updateParentCell()
        self.tmpSelectedItems = self.selectedItems()
        self.parent().parent().setMemReq()
        
        
    def _updateParentCell(self):
        for i in range(self.rowCount()):
            for j in range(self.columnCount()):
                item = self.item(i, j)
                if item.isRootNode:
                    x = 0
                    for child in item.children:
                        if child.featureState == Qt.Checked:
                            x += 1
                    if len(item.children) == x:
                        item.featureState = Qt.Checked
                    elif x == 0:
                        item.featureState = Qt.Unchecked
                    else:
                        item.featureState = Qt.PartiallyChecked


    def eventFilter(self, obj, event):
        if(event.type()==QEvent.MouseButtonPress):
            if event.button() == Qt.LeftButton:
                if self.itemAt(event.pos()):
                    self.setSelectionMode(2)
        if(event.type()==QEvent.MouseButtonRelease):
            if event.button() == Qt.LeftButton:
                self.setSelectionMode(0)
                self.tmpSelectedItems = []
                self._deselectAllTableItems()
        if event.type() == QEvent.MouseMove:
            if self.itemAt(event.pos()) and self.underMouse():
                item = self.itemAt(event.pos())
                hHeader = self.horizontalHeaderItem(item.column())
                self.changeSizeCallback(hHeader.brushSize)               
#                self._highlightHeaders(item.column(), item.row())
        return False
        
        
    def _deselectAllTableItems(self):
        for item in self.selectedItems():
            item.setSelected(False)

    
    def _addHHeader(self, text):
        self.setColumnCount(len(self._sigmaList))
        for c in range(len(self._sigmaList)):
            if not text:
                hHeader = FeatureTableWidgetHHeader(self._sigmaList[c])
            else:
                hHeader = FeatureTableWidgetHHeader(self._sigmaList[c], text[c])
            self.setHorizontalHeaderItem(c, hHeader)

    
    def _addVHeader(self):
        row = 0
        for group in self._featureGroupDict.keys():
            self.insertRow(row)
            vGroupHeader = FeatureTableWidgetVHeader()
            vGroupHeader.setGroupVHeader(group)
            self.setVerticalHeaderItem(row, vGroupHeader)
            row += 1
            for feature in self._featureGroupDict[group]:
                self.insertRow(row)
                vFeatureHeader = FeatureTableWidgetVHeader()
                vFeatureHeader.setFeatureVHeader(feature)
                self.setVerticalHeaderItem(row, vFeatureHeader)
                #Tooltip
                #self.verticalHeaderItem(row).setData(3, j.name)
                vGroupHeader.children.append(row)
                row += 1
                
                
    def _highlightHeaders(self, c, r):       
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
        
        
    def _featureTableItemDoubleClicked(self, row, column):
        item = self.item(row, column)
        if item.isRootNode and self.verticalHeaderItem(item.row()).isExpanded == True:
            if item.featureState == Qt.Unchecked or item.featureState == Qt.PartiallyChecked:
                state = Qt.Checked
            else:
                state = Qt.Unchecked
            for child in item.children:
                child.setFeatureState(state)
        self._updateParentCell()
                
                
                
#===============================================================================
# SliderDlg
#===============================================================================
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
        
        self.buttonsLayout = QHBoxLayout()
        self.cancel = QToolButton()
        self.cancel.setText("cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)
        self.buttonsLayout.addWidget(self.cancel)
        
        
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        self.buttonsLayout.addWidget(self.ok)

        self.layout.addLayout(self.buttonsLayout)
        
        self.layout.setContentsMargins(10, 0, 10, 0)
        labelsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        
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
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setWindowTitle("Spatial Features")
        
        # widgets and layouts
        # ------------------------------------------------
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.tableAndViewGroupBox = QGroupBox(" Scales and Groups")
        self.tableAndViewGroupBox.setFlat(True)
        self.featureTableWidget = FeatureTableWidget()
        
        self.tableAndViewLayout = QHBoxLayout()
        self.tableAndViewLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.tableAndViewLayout.addWidget(self.featureTableWidget)
        
        self.viewAndButtonLayout =  QVBoxLayout() 
        self.preView = PreView()
        self.viewAndButtonLayout.addWidget(self.preView)
        
        self.buttonsLayout = QHBoxLayout()
        self.memReqLabel = QLabel()
        self.buttonsLayout.addWidget(self.memReqLabel)
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.ok)
        
        self.cancel = QToolButton()
        self.cancel.setText("Cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)

        self.buttonsLayout.addWidget(self.cancel)
        self.viewAndButtonLayout.addLayout(self.buttonsLayout)
        self.tableAndViewLayout.addLayout(self.viewAndButtonLayout)
        self.tableAndViewGroupBox.setLayout(self.tableAndViewLayout)
        self.layout.addWidget(self.tableAndViewGroupBox)
        
        self.layout.setContentsMargins(0,0,10,10)
        self.tableAndViewGroupBox.setContentsMargins(0,10,0,0)
        self.tableAndViewLayout.setContentsMargins(0,10,0,0)
        
        self.featureTableWidget.setChangeSizeCallback(self.preView.setSizeToLabel)
        self.setMemReq()        
                
    # methods
    # ------------------------------------------------
    def setMemReq(self):
#        featureSelectionList = self.featureTableWidget.createFeatureList()
        #TODO
        #memReq = self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)
        #self.memReqLabel.setText("%8.2f MB" % memReq)
        pass
    
    def on_okClicked(self):
#        featureSelectionList = self.featureTableWidget.createFeatureList()
#        selectedFeatureList = self.featureTableWidget.createSelectedFeatureList()
#        sigmaList = self.featureTableWidget.createSigmaList()
#        featureMgr.ilastikFeatureGroups.newGroupScaleValues = sigmaList
#        featureMgr.ilastikFeatureGroups.newSelection = selectedFeatureList
#        res = self.parent().project.dataMgr.Classification.featureMgr.setFeatureItems(featureSelectionList)
#        if res is True:
#            self.parent().labelWidget.setBorderMargin(int(self.parent().project.dataMgr.Classification.featureMgr.maxContext))
#            self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)           
#            self.accept() 
#        else:
#            QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
#            self.on_cancelClicked()
        self.accept()
    
    def on_cancelClicked(self):
        self.reject()
        
        
class SimpleObject:
    def __init__(self, name):
        self.name = name
        
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
    
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    ex1 = FeatureDlg()
    ex1.setWindowTitle("ex1")
    ex1.preView.setPreviewImage((numpy.random.rand(200,200)*256).astype(numpy.uint8))
    ex1.featureTableWidget.createTable({"Color": [SimpleObject("Banana")], "Edge": [SimpleObject("Mango"), SimpleObject("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    ex1.featureTableWidget.itemDelegate.setCheckBoxIcons("/Users/opetra/Desktop/CheckboxFull.png", "/Users/opetra/Desktop/CheckboxPartially.png", "/Users/opetra/Desktop/CheckboxEmpty.png")
#    print "table ", ex1.featureTableWidget.sizeHint()
#    print "horiHeader", ex1.featureTableWidget.horizontalHeader().sizeHint()
#    print "verticalHeader", ex1.featureTableWidget.verticalHeader().sizeHint().height()
#    print "HHeader columnWidth ", ex1.featureTableWidget.columnWidth(6)
#    print "tableHHeader ", ex1.featureTableWidget.horizontalHeaderItem(1).sizeHint()
#    print "tableAndViewLayout ", ex1.tableAndViewLayout.sizeHint()
#    print "tableAndViewGroupBox ", ex1.tableAndViewGroupBox.size()
#    print "layout ", ex1.layout.sizeHint()
    
    ex1.show()
    ex1.raise_()
    
    ex2 = FeatureDlg()
    ex2.setWindowTitle("ex2")
    ex2.preView.setPreviewImage((numpy.random.rand(100,100)*256).astype(numpy.uint8))
    ex2.featureTableWidget.createTable({"Color": [SimpleObject("Banananananaana")], "Edge": [SimpleObject("Mango"), SimpleObject("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    ex2.show()
    ex2.raise_()
    
    
    def test():
        selectedFeatures = ex1.featureTableWidget.createSelectedFeatureList()
        ex2.featureTableWidget.setSelectedFeatures(selectedFeatures)
            
    ex1.accepted.connect(test)
    
    
    app.exec_()       