import os, glob
import vigra
import sys
import getopt
import h5py

from ilastik.core import dataImpex
from PyQt4 import QtCore, QtGui, uic

class LoadOptionsWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        #self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.rgb = 1

        tempLayout = QtGui.QHBoxLayout()
        self.offsetX = QtGui.QSpinBox()
        self.offsetX.setRange(0,10000)
        self.offsetY = QtGui.QSpinBox()
        self.offsetY.setRange(0,10000)
        self.offsetZ = QtGui.QSpinBox()
        self.offsetZ.setRange(0,10000)
        tempLayout.addWidget( self.offsetX)
        tempLayout.addWidget( self.offsetY)
        tempLayout.addWidget( self.offsetZ)
        self.layout.addWidget(QtGui.QLabel("Subvolume Offsets:"))
        self.layout.addLayout(tempLayout)
        
        tempLayout = QtGui.QHBoxLayout()
        self.sizeX = QtGui.QSpinBox()
        self.sizeX.setRange(0,10000)
        self.sizeY = QtGui.QSpinBox()
        self.sizeY.setRange(0,10000)
        self.sizeZ = QtGui.QSpinBox()
        self.sizeZ.setRange(0,10000)
        tempLayout.addWidget( self.sizeX)
        tempLayout.addWidget( self.sizeY)
        tempLayout.addWidget( self.sizeZ)
        self.layout.addWidget(QtGui.QLabel("Subvolume Size:"))
        self.layout.addLayout(tempLayout)

        tempLayout = QtGui.QHBoxLayout()
        self.resCheck = QtGui.QCheckBox("Data with varying resolution:")
        self.connect(self.resCheck, QtCore.SIGNAL("stateChanged(int)"), self.toggleResolution)
        tempLayout.addWidget(self.resCheck)
        self.layout.addLayout(tempLayout) 
        
        self.resolutionFrame = QtGui.QFrame()
        tempLayout = QtGui.QVBoxLayout()
        tempLayout1 = QtGui.QHBoxLayout()
        tempLayout1.addWidget(QtGui.QLabel("Enter relative resolution along x, y and z"))
        tempLayout.addLayout(tempLayout1)
        tempLayout2 = QtGui.QHBoxLayout()
        self.resX = QtGui.QLineEdit("1")
        self.connect(self.resX, QtCore.SIGNAL("textChanged(QString)"), self.resChanged)
        self.resY = QtGui.QLineEdit("1")
        self.connect(self.resY, QtCore.SIGNAL("textChanged(QString)"), self.resChanged)
        self.resZ = QtGui.QLineEdit("1")
        self.connect(self.resZ, QtCore.SIGNAL("textChanged(QString)"), self.resChanged)
        tempLayout2.addWidget(QtGui.QLabel("X:"))
        tempLayout2.addWidget(self.resX)
        tempLayout2.addWidget(QtGui.QLabel("Y:"))
        tempLayout2.addWidget(self.resY)
        tempLayout2.addWidget(QtGui.QLabel("Z:"))
        tempLayout2.addWidget(self.resZ)
        tempLayout.addLayout(tempLayout2)
        self.resolutionFrame.setLayout(tempLayout)
        self.resolutionFrame.setVisible(False)
        self.layout.addWidget(self.resolutionFrame)    

        tempLayout = QtGui.QHBoxLayout()
        self.invert = QtGui.QCheckBox("Invert Colors?")
        tempLayout.addWidget(self.invert)
        self.layout.addLayout(tempLayout) 

        tempLayout = QtGui.QHBoxLayout()
        self.grayscale = QtGui.QCheckBox("Convert to Grayscale ?")
        tempLayout.addWidget(self.grayscale)
        self.layout.addLayout(tempLayout) 


        tempLayout = QtGui.QHBoxLayout()
        self.normalize = QtGui.QCheckBox("Normalize Data?")
        tempLayout.addWidget(self.normalize)
        self.layout.addLayout(tempLayout) 


        tempLayout = QtGui.QHBoxLayout()
        self.downsample = QtGui.QCheckBox("Downsample Subvolume to Size:")
        self.connect(self.downsample, QtCore.SIGNAL("stateChanged(int)"), self.toggleDownsample)      
        tempLayout.addWidget(self.downsample)
        self.layout.addLayout(tempLayout)

        self.downsampleFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.downX = QtGui.QSpinBox()
        self.downX.setRange(0,10000)
        self.downY = QtGui.QSpinBox()
        self.downY.setRange(0,10000)
        self.downZ = QtGui.QSpinBox()
        self.downZ.setRange(0,10000)
        tempLayout.addWidget( self.downX)
        tempLayout.addWidget( self.downY)
        tempLayout.addWidget( self.downZ)
        self.downsampleFrame.setLayout(tempLayout)
        self.downsampleFrame.setVisible(False)
        self.layout.addWidget(self.downsampleFrame)
    
        
        tempLayout = QtGui.QHBoxLayout()
        self.alsoSave = QtGui.QCheckBox("also save to Destination File:")
        self.connect(self.alsoSave, QtCore.SIGNAL("stateChanged(int)"), self.toggleAlsoSave)
        tempLayout.addWidget(self.alsoSave)
        self.layout.addLayout(tempLayout) 

        self.alsoSaveFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.fileButton = QtGui.QPushButton("Select")
        self.connect(self.fileButton, QtCore.SIGNAL('clicked()'), self.slotFile)
        self.file = QtGui.QLineEdit("")
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

    def slotFile(self):
        filename= QtGui.QFileDialog.getSaveFileName(self, "Save to File", "*.h5")
        self.file.setText(filename)

    def fillOptions(self, options):
        options.offsets = (self.offsetX.value(),self.offsetY.value(),self.offsetZ.value())
        options.shape = (self.sizeX.value(),self.sizeY.value(),self.sizeZ.value())
        options.resolution = (int(str(self.resX.text())), int(str(self.resY.text())), int(str(self.resZ.text())))
        options.destShape = None
        if self.downsample.checkState() > 0:
            options.destShape = (self.downX.value(),self.downY.value(),self.downZ.value())
        options.file_exp = str(self.file.text())
        if self.alsoSave.checkState() == 0:
            options.file_exp = None
        options.normalize = self.normalize.checkState() > 0
        options.invert = self.invert.checkState() > 0
        options.grayscale = self.grayscale.checkState() > 0
        options.rgb = self.rgb

    def fillDefaultOptions(self, options):
        #sizes might have been filled by setShapeInfo
        options.shape = (self.sizeX.value(),self.sizeY.value(),self.sizeZ.value())

    def setShapeInfo(self, fileList, channels):
        #read the shape information from the first file in the list
        #TODO: this is calling the dataImpex - it's baaaaad, it shouldn't be done
        
        try:            
            shape = dataImpex.DataImpex.readShape(fileList[channels[0]][0])
            print shape
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

class loadOptions:
    def __init__(self):
        self.resolution = (1, 1, 1)
        self.offsets = (0, 0, 0)
        self.shape = (0, 0, 0)
        self.channels = []
        self.destShape = None
        self.invert = False
        self.normalize = False
        self.grayscale = False
        self.destfile = None
        self.rgb = 1

class previewTable(QtGui.QDialog):
    def __init__(self, fileList, parent=None, newProject = True):
        QtGui.QWidget.__init__(self, parent)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.fileList = fileList
        self.fileListTable = QtGui.QTableWidget()
        self.fillFileTable()        
        self.fileListTable.setHorizontalHeaderLabels(["red", "green", "blue"])
        self.fileListTable.resizeRowsToContents()
        self.fileListTable.resizeColumnsToContents()
        self.layout.addWidget(self.fileListTable)

    def fillFileTable(self):
        if (len(self.fileList)==0):
            self.fileListTable.setRowCount(1)
            self.fileListTable.setColumnCount(3)
            self.fileListTable.setItem(0, 0, QtGui.QTableWidgetItem(QtCore.QString("file1")))
            self.fileListTable.setItem(0, 1, QtGui.QTableWidgetItem(QtCore.QString("file2")))
            self.fileListTable.setItem(0, 2, QtGui.QTableWidgetItem(QtCore.QString("file3")))
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
                self.fileListTable.setItem(i, 0, QtGui.QTableWidgetItem(QtCore.QString(filename)))
        if (len(self.fileList)==3):
            #multichannel data
            nfiles = max([len(self.fileList[0]), len(self.fileList[1]), len(self.fileList[2])])
            self.fileListTable.setRowCount(nfiles)
            self.fileListTable.setColumnCount(3)
            for i in range(0, len(self.fileList[0])):
                filename = os.path.basename(self.fileList[0][i])
                self.fileListTable.setItem(i, 0, QtGui.QTableWidgetItem(QtCore.QString(filename)))
            for i in range(0, len(self.fileList[1])):
                filename = os.path.basename(self.fileList[1][i])
                self.fileListTable.setItem(i, 1, QtGui.QTableWidgetItem(QtCore.QString(filename)))
            for i in range(0, len(self.fileList[2])):
                filename = os.path.basename(self.fileList[2][i])
                self.fileListTable.setItem(i, 2, QtGui.QTableWidgetItem(QtCore.QString(filename)))
