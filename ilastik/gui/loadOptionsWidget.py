import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

from ilastik.core import dataImpex
from PyQt4 import QtCore, QtGui

#*******************************************************************************
# L o a d O p t i o n s W i d g e t                                            *
#*******************************************************************************

class LoadOptionsWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        #self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.rgb = 1
        
    
        self.layout.addWidget(QtGui.QLabel("Select a subvolume:"))
        #tempGrid = QtGui.QGridLayout()
        #tempForm = QtGui.QFormLayout()
        tempLayoutRight = QtGui.QVBoxLayout()        
        tempLayout = QtGui.QHBoxLayout()        
        self.offsetX = QtGui.QSpinBox()
        self.offsetX.setRange(0,9999)
        self.connect(self.offsetX, QtCore.SIGNAL("textChanged(QString)"), self.off1Changed)
        self.offsetY = QtGui.QSpinBox()
        self.offsetY.setRange(0,9999)
        self.connect(self.offsetY, QtCore.SIGNAL("textChanged(QString)"), self.off1Changed)
        self.offsetZ = QtGui.QSpinBox()
        self.offsetZ.setRange(0,9999)
        self.connect(self.offsetZ, QtCore.SIGNAL("textChanged(QString)"), self.off1Changed)
        tempLayout.addWidget(QtGui.QLabel("X"))
        tempLayout.addWidget( self.offsetX)
        tempLayout.addWidget(QtGui.QLabel("Y"))
        tempLayout.addWidget( self.offsetY)
        tempLayout.addWidget(QtGui.QLabel("Z"))
        tempLayout.addWidget( self.offsetZ)
        tempLayoutRight.addLayout(tempLayout)
        #self.layout.addLayout(tempLayout)
        #tempForm.addRow(QtGui.QLabel("From:"), tempLayout)
#        tempGrid.addWidget(QtGui.QLabel("From:"), 0, 0)
#        tempGrid.addWidget(QtGui.QLabel("X"), 0, 1)
#        tempGrid.addWidget(self.offsetX, 0, 2)
#        tempGrid.addWidget(QtGui.QLabel("Y"), 0, 3)
#        tempGrid.addWidget(self.offsetY, 0, 4)
#        tempGrid.addWidget(QtGui.QLabel("Z"), 0, 5)
#        tempGrid.addWidget(self.offsetZ, 0, 6)
        
        tempLayout = QtGui.QHBoxLayout()
        self.sizeX = QtGui.QSpinBox()
        self.sizeX.setRange(0,9999)
        self.connect(self.sizeX, QtCore.SIGNAL("textChanged(QString)"), self.off2Changed)
        self.sizeY = QtGui.QSpinBox()
        self.sizeY.setRange(0,9999)
        self.connect(self.sizeY, QtCore.SIGNAL("textChanged(QString)"), self.off2Changed)
        self.sizeZ = QtGui.QSpinBox()
        self.sizeZ.setRange(0,9999)
        self.connect(self.sizeZ, QtCore.SIGNAL("textChanged(QString)"), self.off2Changed)
        tempLayout.addWidget(QtGui.QLabel("X"))
        tempLayout.addWidget( self.sizeX)
        tempLayout.addWidget(QtGui.QLabel("Y"))
        tempLayout.addWidget( self.sizeY)
        tempLayout.addWidget(QtGui.QLabel("Z"))
        tempLayout.addWidget( self.sizeZ)
        tempLayoutRight.addLayout(tempLayout)
        #self.layout.addWidget(QtGui.QLabel("Subvolume End Offsets:"))
        
        tempLayoutLeft = QtGui.QVBoxLayout()
        tempLayoutLeft.addWidget(QtGui.QLabel("From:"))
        tempLayoutLeft.addWidget(QtGui.QLabel("To:"))
        tempLayout = QtGui.QHBoxLayout()
        
        tempLayout.addLayout(tempLayoutLeft)
        tempLayout.addLayout(tempLayoutRight)
        tempLayout.addStretch()
        self.layout.addLayout(tempLayout)
#        tempForm.addRow(QtGui.QLabel("To:"), tempLayout)
#        self.layout.addLayout(tempForm)
#        tempGrid.addWidget(QtGui.QLabel("To:"), 1, 0)
#        x = QtGui.QLabel("X")
#        x.setAlignment(QtCore.Qt.AlignCenter)
#        tempGrid.addWidget(x, 1, 1)
#        tempGrid.addWidget(self.sizeX, 1, 2)
#        tempGrid.addWidget(QtGui.QLabel("Y"), 1, 3)
#        tempGrid.addWidget(self.sizeY, 1, 4)
#        tempGrid.addWidget(QtGui.QLabel("Z"), 1, 5)
#        tempGrid.addWidget(self.sizeZ, 1, 6)
#        self.layout.addLayout(tempGrid)
        
        
        tempLayout = QtGui.QHBoxLayout()
        self.resCheck = QtGui.QCheckBox("Data with varying resolution:")
        
        # TODO: renable this as soon its impemented
        self.resCheck.setVisible(False)
        
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
        self.invert = QtGui.QCheckBox("Invert Colors? (8-bit images)")
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
        self.downX.setRange(0,9999)
        self.downY = QtGui.QSpinBox()
        self.downY.setRange(0,9999)
        self.downZ = QtGui.QSpinBox()
        self.downZ.setRange(0,9999)
        tempLayout.addWidget(self.downX)
        tempLayout.addWidget(self.downY)
        tempLayout.addWidget(self.downZ)
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
        filename= QtGui.QFileDialog.getSaveFileName(self, "Save to File", "*.h5")
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
            if len(channels) == 0:
                channel = 0
            else:
                channel = channels[0]
            
            if channel >= len(channels):
                channel = 0
                            
            shape = dataImpex.DataImpex.readShape(fileList[channel][0])
            self.rgb = shape[3]
            self.sizeX.setValue(shape[0])
            self.downX.setValue(shape[0])
            self.sizeX.setMaximum(shape[0])
            
            self.sizeY.setValue(shape[1])
            self.downY.setValue(shape[1])
            self.sizeY.setMaximum(shape[1])
            if shape[2] == 1: 
                #2d data (1, 1, x, y, c)
                self.sizeZ.setValue(len(fileList[channel]))
                self.downZ.setValue(len(fileList[channel]))
                self.sizeZ.setMaximum(len(fileList[channel]))
            else:
                self.sizeZ.setValue(shape[2])
                self.downZ.setValue(shape[2])
                self.sizeZ.setMaximum(shape[2])
        except Exception as e:
            print "Pre-reading data shape failed"
            print e
            print "Loading the full dataset"
            self.sizeZ.setValue(0)
            self.sizeX.setValue(0)
            self.sizeY.setValue(0)

#*******************************************************************************
# p r e v i e w T a b l e                                                      *
#*******************************************************************************

class previewTable(QtGui.QDialog):
    def __init__(self, fileList, parent=None, newProject = True):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("Preview")
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.fileList = fileList
        self.fileListTable = QtGui.QTableWidget()
        self.fillFileTable()        
        #self.fileListTable.setHorizontalHeaderLabels(["channel 1", "channel 2", "channel 3"])
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

        if (len(self.fileList)==1):
            #single channel data
            self.fileListTable.setRowCount(len(self.fileList[0]))
            self.fileListTable.setColumnCount(1)       
            for i in range(0, len(self.fileList[0])):
                filename = os.path.basename(self.fileList[0][i])
                self.fileListTable.setItem(i, 0, QtGui.QTableWidgetItem(QtCore.QString(filename)))
        else:
            #multichannel data
            maxlen = len(self.fileList[0])
            for f in self.fileList:
                if len(f)>maxlen:
                    maxlen = len(f)
            self.fileListTable.setRowCount(maxlen)
            self.fileListTable.setColumnCount(len(self.fileList))
            for i in range(len(self.fileList)):
                for j in range(len(self.fileList[i])):
                    filename = os.path.basename(self.fileList[i][j])
                    self.fileListTable.setItem(j, i, QtGui.QTableWidgetItem(QtCore.QString(filename)))
        
                    
            
        
        '''
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
        '''