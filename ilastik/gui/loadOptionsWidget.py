#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

from PyQt4.QtCore import QString, Qt, SIGNAL
from PyQt4.QtGui import QCheckBox, QDialog, QFileDialog, QFormLayout, QFrame,\
                        QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\
                        QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,\
                        QWidget
import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

from ilastik.core import dataImpex

#*******************************************************************************
# L o a d O p t i o n s W i d g e t                                            *
#*******************************************************************************

class LoadOptionsWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        #self.setMinimumWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.rgb = 1
        
    
        self.layout.addWidget(QLabel("Select a subvolume:"))
        #tempGrid = QGridLayout()
        #tempForm = QFormLayout()
        tempLayoutRight = QVBoxLayout()        
        tempLayout = QHBoxLayout()        
        self.offsetX = QSpinBox()
        self.offsetX.setRange(0,10000)
        self.connect(self.offsetX, SIGNAL("textChanged(QString)"), self.off1Changed)
        self.offsetY = QSpinBox()
        self.offsetY.setRange(0,10000)
        self.connect(self.offsetY, SIGNAL("textChanged(QString)"), self.off1Changed)
        self.offsetZ = QSpinBox()
        self.offsetZ.setRange(0,10000)
        self.connect(self.offsetZ, SIGNAL("textChanged(QString)"), self.off1Changed)
        tempLayout.addWidget(QLabel("X"))
        tempLayout.addWidget( self.offsetX)
        tempLayout.addWidget(QLabel("Y"))
        tempLayout.addWidget( self.offsetY)
        tempLayout.addWidget(QLabel("Z"))
        tempLayout.addWidget( self.offsetZ)
        tempLayoutRight.addLayout(tempLayout)
        #self.layout.addLayout(tempLayout)
        #tempForm.addRow(QLabel("From:"), tempLayout)
#        tempGrid.addWidget(QLabel("From:"), 0, 0)
#        tempGrid.addWidget(QLabel("X"), 0, 1)
#        tempGrid.addWidget(self.offsetX, 0, 2)
#        tempGrid.addWidget(QLabel("Y"), 0, 3)
#        tempGrid.addWidget(self.offsetY, 0, 4)
#        tempGrid.addWidget(QLabel("Z"), 0, 5)
#        tempGrid.addWidget(self.offsetZ, 0, 6)
        
        tempLayout = QHBoxLayout()
        self.sizeX = QSpinBox()
        self.sizeX.setRange(0,10000)
        self.connect(self.sizeX, SIGNAL("textChanged(QString)"), self.off2Changed)
        self.sizeY = QSpinBox()
        self.sizeY.setRange(0,10000)
        self.connect(self.sizeY, SIGNAL("textChanged(QString)"), self.off2Changed)
        self.sizeZ = QSpinBox()
        self.sizeZ.setRange(0,10000)
        self.connect(self.sizeZ, SIGNAL("textChanged(QString)"), self.off2Changed)
        tempLayout.addWidget(QLabel("X"))
        tempLayout.addWidget( self.sizeX)
        tempLayout.addWidget(QLabel("Y"))
        tempLayout.addWidget( self.sizeY)
        tempLayout.addWidget(QLabel("Z"))
        tempLayout.addWidget( self.sizeZ)
        tempLayoutRight.addLayout(tempLayout)
        #self.layout.addWidget(QLabel("Subvolume End Offsets:"))
        
        tempLayoutLeft = QVBoxLayout()
        tempLayoutLeft.addWidget(QLabel("From:"))
        tempLayoutLeft.addWidget(QLabel("To:"))
        tempLayout = QHBoxLayout()
        
        tempLayout.addLayout(tempLayoutLeft)
        tempLayout.addLayout(tempLayoutRight)
        tempLayout.addStretch()
        self.layout.addLayout(tempLayout)
#        tempForm.addRow(QLabel("To:"), tempLayout)
#        self.layout.addLayout(tempForm)
#        tempGrid.addWidget(QLabel("To:"), 1, 0)
#        x = QLabel("X")
#        x.setAlignment(Qt.AlignCenter)
#        tempGrid.addWidget(x, 1, 1)
#        tempGrid.addWidget(self.sizeX, 1, 2)
#        tempGrid.addWidget(QLabel("Y"), 1, 3)
#        tempGrid.addWidget(self.sizeY, 1, 4)
#        tempGrid.addWidget(QLabel("Z"), 1, 5)
#        tempGrid.addWidget(self.sizeZ, 1, 6)
#        self.layout.addLayout(tempGrid)
        
        
        tempLayout = QHBoxLayout()
        self.resCheck = QCheckBox("Data with varying resolution:")
        
        # TODO: renable this as soon its impemented
        self.resCheck.setVisible(False)
        
        self.connect(self.resCheck, SIGNAL("stateChanged(int)"), self.toggleResolution)
        tempLayout.addWidget(self.resCheck)
        self.layout.addLayout(tempLayout) 
        
        self.resolutionFrame = QFrame()
        tempLayout = QVBoxLayout()
        tempLayout1 = QHBoxLayout()
        tempLayout1.addWidget(QLabel("Enter relative resolution along x, y and z"))
        tempLayout.addLayout(tempLayout1)
        tempLayout2 = QHBoxLayout()
        self.resX = QLineEdit("1")
        self.connect(self.resX, SIGNAL("textChanged(QString)"), self.resChanged)
        self.resY = QLineEdit("1")
        self.connect(self.resY, SIGNAL("textChanged(QString)"), self.resChanged)
        self.resZ = QLineEdit("1")
        self.connect(self.resZ, SIGNAL("textChanged(QString)"), self.resChanged)
        tempLayout2.addWidget(QLabel("X:"))
        tempLayout2.addWidget(self.resX)
        tempLayout2.addWidget(QLabel("Y:"))
        tempLayout2.addWidget(self.resY)
        tempLayout2.addWidget(QLabel("Z:"))
        tempLayout2.addWidget(self.resZ)
        tempLayout.addLayout(tempLayout2)
        self.resolutionFrame.setLayout(tempLayout)
        self.resolutionFrame.setVisible(False)
        self.layout.addWidget(self.resolutionFrame)    

        tempLayout = QHBoxLayout()
        self.invert = QCheckBox("Invert Colors?")
        tempLayout.addWidget(self.invert)
        self.layout.addLayout(tempLayout) 

        tempLayout = QHBoxLayout()
        self.grayscale = QCheckBox("Convert to Grayscale ?")
        tempLayout.addWidget(self.grayscale)
        self.layout.addLayout(tempLayout) 


        tempLayout = QHBoxLayout()
        self.normalize = QCheckBox("Normalize Data?")
        tempLayout.addWidget(self.normalize)
        self.layout.addLayout(tempLayout) 


        tempLayout = QHBoxLayout()
        self.downsample = QCheckBox("Downsample Subvolume to Size:")
        self.connect(self.downsample, SIGNAL("stateChanged(int)"), self.toggleDownsample)      
        tempLayout.addWidget(self.downsample)
        self.layout.addLayout(tempLayout)

        self.downsampleFrame = QFrame()
        tempLayout = QHBoxLayout()
        self.downX = QSpinBox()
        self.downX.setRange(0,10000)
        self.downY = QSpinBox()
        self.downY.setRange(0,10000)
        self.downZ = QSpinBox()
        self.downZ.setRange(0,10000)
        tempLayout.addWidget( self.downX)
        tempLayout.addWidget( self.downY)
        tempLayout.addWidget( self.downZ)
        self.downsampleFrame.setLayout(tempLayout)
        self.downsampleFrame.setVisible(False)
        self.layout.addWidget(self.downsampleFrame)
    
        
        tempLayout = QHBoxLayout()
        self.alsoSave = QCheckBox("also save to Destination File:")
        self.connect(self.alsoSave, SIGNAL("stateChanged(int)"), self.toggleAlsoSave)
        tempLayout.addWidget(self.alsoSave)
        self.layout.addLayout(tempLayout) 

        self.alsoSaveFrame = QFrame()
        tempLayout = QHBoxLayout()
        self.fileButton = QPushButton("Select")
        self.connect(self.fileButton, SIGNAL('clicked()'), self.slotFile)
        self.file = QLineEdit("")
        tempLayout.addWidget(self.file)
        tempLayout.addWidget(self.fileButton)
        self.alsoSaveFrame.setLayout(tempLayout)
        self.alsoSaveFrame.setVisible(False)
        self.layout.addWidget(self.alsoSaveFrame)


    def toggleAlsoSave(self, int):
        if self.alsoSave.checkState() == 0:
            self.alsoSaveFrame.setVisible(False)
        else:
            self.alsoSaveFrame.setVisible(True)
    
    def toggleDownsample(self, int):
        if self.downsample.checkState() == 0:
            self.downsampleFrame.setVisible(False)
        else:
            self.downsampleFrame.setVisible(True)

    def toggleResolution(self, int):
        if self.resCheck.checkState() == 0:
            self.resolutionFrame.setVisible(False)
        else:
            self.resolutionFrame.setVisible(True)

    def resChanged(self):
        try:
            self.resolution[0] = float(str(self.resX.text()))
            self.resolution[1] = float(str(self.resY.text()))
            self.resolution[2] = float(str(self.resZ.text()))
        except Exception as e:
            self.resolution = [1,1,1]


    def off2Changed(self):
        try:
            if self.offsetX.value() >= self.sizeX.value():
                self.offsetX.setValue(self.sizeX.value()-1)               
            if self.offsetY.value() >= self.sizeY.value():
                self.offsetY.setValue(self.sizeY.value()-1)               
            if self.offsetZ.value() >= self.sizeZ.value():
                self.offsetZ.setValue(self.sizeZ.value()+1)               
        except Exception as e:
            pass


    def off1Changed(self):
        try:
            if self.offsetX.value() >= self.sizeX.value():
                self.sizeX.setValue(self.offsetX.value()+1)               
            if self.offsetY.value() >= self.sizeY.value():
                self.sizeY.setValue(self.offsetY.value()+1)               
            if self.offsetZ.value() >= self.sizeZ.value():
                self.sizeZ.setValue(self.offsetZ.value()+1)               
        except Exception as e:
            pass



    def slotFile(self):
        filename= QFileDialog.getSaveFileName(self, "Save to File", "*.h5")
        self.file.setText(filename)

    def fillOptions(self, options):
        options.offsets = (self.offsetX.value(),self.offsetY.value(),self.offsetZ.value())
        options.shape = (self.sizeX.value() - self.offsetX.value(),self.sizeY.value() - self.offsetY.value(),self.sizeZ.value() - self.offsetZ.value())
        options.resolution = (int(str(self.resX.text())), int(str(self.resY.text())), int(str(self.resZ.text())))
        options.destShape = None
        if self.downsample.checkState() > 0:
            options.destShape = (self.downX.value(),self.downY.value(),self.downZ.value())
        options.destfile = str(self.file.text())
        if self.alsoSave.checkState() == 0:
            options.destfile = None
        options.normalize = self.normalize.checkState() > 0
        options.invert = self.invert.checkState() > 0
        options.grayscale = self.grayscale.checkState() > 0
        options.rgb = self.rgb

    def fillDefaultOptions(self, options):
        #sizes might have been filled by setShapeInfo
        options.shape = (self.sizeX.value(),self.sizeY.value(),self.sizeZ.value())
        options.rgb = self.rgb

    def setShapeInfo(self, fileList, channels):
        #read the shape information from the first file in the list
        #TODO: this is calling the dataImpex - it's baaaaad, it shouldn't be done        
        try:            
            shape = dataImpex.DataImpex.readShape(fileList[channels[0]][0])
            self.rgb = shape[3]
            self.sizeX.setValue(shape[0])
            self.sizeY.setValue(shape[1])
            if shape[2] == 1: 
                #2d data (1, 1, x, y, c)
                self.sizeZ.setValue(len(fileList[channels[0]]))
            else:
                self.sizeZ.setValue(shape[2])
        except Exception as e:
            print e
            self.sizeZ.setValue(0)
            self.sizeX.setValue(0)
            self.sizeY.setValue(0)

#*******************************************************************************
# p r e v i e w T a b l e                                                      *
#*******************************************************************************

class previewTable(QDialog):
    def __init__(self, fileList, parent=None, newProject = True):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Preview")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.fileList = fileList
        self.fileListTable = QTableWidget()
        self.fillFileTable()        
        self.fileListTable.setHorizontalHeaderLabels(["channel 1", "channel 2", "channel 3"])
        self.fileListTable.resizeRowsToContents()
        self.fileListTable.resizeColumnsToContents()
        self.layout.addWidget(self.fileListTable)

    def fillFileTable(self):
        if (len(self.fileList)==0):
            self.fileListTable.setRowCount(1)
            self.fileListTable.setColumnCount(3)
            self.fileListTable.setItem(0, 0, QTableWidgetItem(QString("file1")))
            self.fileListTable.setItem(0, 1, QTableWidgetItem(QString("file2")))
            self.fileListTable.setItem(0, 2, QTableWidgetItem(QString("file3")))
            return
        nfiles = len(self.fileList[0])
        self.fileListTable.setRowCount(nfiles)
        self.fileListTable.setColumnCount(len(self.fileList))
        #it's so ugly... but i don't know how to fill a whole column by list slicing
        if (len(self.fileList)==1):
            #single channel data
            self.fileListTable.setRowCount(len(self.fileList[0]))
            self.fileListTable.setColumnCount(1)       
            for i in range(0, len(self.fileList[0])):
                filename = os.path.basename(self.fileList[0][i])
                self.fileListTable.setItem(i, 0, QTableWidgetItem(QString(filename)))
        if (len(self.fileList)==3):
            #multichannel data
            nfiles = max([len(self.fileList[0]), len(self.fileList[1]), len(self.fileList[2])])
            self.fileListTable.setRowCount(nfiles)
            self.fileListTable.setColumnCount(3)
            for i in range(0, len(self.fileList[0])):
                filename = os.path.basename(self.fileList[0][i])
                self.fileListTable.setItem(i, 0, QTableWidgetItem(QString(filename)))
            for i in range(0, len(self.fileList[1])):
                filename = os.path.basename(self.fileList[1][i])
                self.fileListTable.setItem(i, 1, QTableWidgetItem(QString(filename)))
            for i in range(0, len(self.fileList[2])):
                filename = os.path.basename(self.fileList[2][i])
                self.fileListTable.setItem(i, 2, QTableWidgetItem(QString(filename)))
