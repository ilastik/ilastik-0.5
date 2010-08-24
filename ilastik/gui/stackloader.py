# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:33:57 2010

@author: - 
"""


import os, glob
import vigra
import sys
import getopt
import h5py
import numpy

import loadOptions
from ilastik.core import dataImpex

from PyQt4 import QtCore, QtGui, uic

class StackLoader(QtGui.QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        #a list of filenames
        #internally, it's a list of lists of filenames
        #for each channel
        self.fileList = []
        self.options = loadOptions.loadOptions()

        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to Image Stack:"))
        self.layout.addLayout(tempLayout)

        tempLayout = QtGui.QHBoxLayout()
        self.multiChannel = QtGui.QCheckBox("MultiChannel Data:")
        self.connect(self.multiChannel, QtCore.SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout) 
        
        self.multiChannelFrame = QtGui.QFrame()
        tempLayout = QtGui.QVBoxLayout()
        tempLayout1 = QtGui.QHBoxLayout()
        tempLayout1.addWidget(QtGui.QLabel("Enter channel identifiers, e.g. GFP"))
        tempLayout.addLayout(tempLayout1)
        tempLayout2 = QtGui.QHBoxLayout()
        self.redChannelId = QtGui.QLineEdit("")
        self.connect(self.redChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.blueChannelId = QtGui.QLineEdit("")
        self.connect(self.blueChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.greenChannelId = QtGui.QLineEdit("")
        self.connect(self.greenChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        tempLayout2.addWidget(QtGui.QLabel("Red:"))
        tempLayout2.addWidget(self.redChannelId)
        tempLayout2.addWidget(QtGui.QLabel("Green:"))
        tempLayout2.addWidget(self.greenChannelId)
        tempLayout2.addWidget(QtGui.QLabel("Blue:"))
        tempLayout2.addWidget(self.blueChannelId)
        tempLayout.addLayout(tempLayout2)
        self.multiChannelFrame.setLayout(tempLayout)
        self.multiChannelFrame.setVisible(False)
        self.layout.addWidget(self.multiChannelFrame)        

        tempLayout = QtGui.QHBoxLayout()
        self.optionsWidget = loadOptions.LoadOptionsWidget()
        tempLayout.addWidget(self.optionsWidget)
        self.layout.addLayout(tempLayout)

        tempLayout = QtGui.QHBoxLayout()
        self.loadButton = QtGui.QPushButton("Load")
        self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotLoad)
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        self.previewFilesButton = QtGui.QPushButton("Preview files")
        self.connect(self.previewFilesButton, QtCore.SIGNAL('clicked()'), self.slotPreviewFiles)
        tempLayout.addWidget(self.previewFilesButton)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.loadButton)
        self.layout.addStretch()
        self.layout.addLayout(tempLayout)
                
        self.logger = QtGui.QPlainTextEdit()
        self.logger.setVisible(False)
        self.layout.addWidget(self.logger)        
        self.image = None

    def toggleMultiChannel(self, int):
	    if self.multiChannel.checkState() == 0:
	        self.multiChannelFrame.setVisible(False)
	    else:
	        self.multiChannelFrame.setVisible(True)


    def pathChanged(self, text):
        self.fileList = []
        self.options.channels = []
        if self.multiChannel.checkState() == 0:
            pathone = str(self.path.text())
            self.fileList.append(sorted(glob.glob(pathone), key=str.lower))
            #self.fileList.append(glob.glob(str(self.path.text())))
            self.options.channels.append(0)
        else:
            #not all channels have to be filled
            if (len(str(self.redChannelId.text()))>0):
                pathred = str(self.path.text())+"*"+str(self.redChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathred), key=str.lower))
                self.options.channels.append(0)
            else:
                self.fileList.append([])    
            if (len(str(self.greenChannelId.text()))>0):
                pathgreen = str(self.path.text())+"*"+str(self.greenChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathgreen), key=str.lower))
                self.options.channels.append(1)
            else:
                self.fileList.append([])
            if (len(str(self.blueChannelId.text()))>0):
                pathblue = str(self.path.text())+"*"+str(self.blueChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathblue), key=str.lower))
                self.options.channels.append(2)
            else:
                self.fileList.append([])
        self.optionsWidget.setShapeInfo(self.fileList)

    def slotDir(self):
        path = self.path.text()
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        tempname = filename + "/*"
        #This is needed, because internally Qt always uses "/" separators,
        #which is a problem on Windows, as we don't use QDir to open dirs
        self.path.setText(str(QtCore.QDir.convertSeparators(tempname)))
        print "new path: ", self.path.text()
        

    def slotPreviewFiles(self):
        self.fileTableWidget = previewTable(self)

    def slotLoad(self):
        self.optionsWidget.fillOptions(self.options)
        self.accept()
        #self.logger.clear()
        #self.logger.setVisible(True)
        #self.image = dataImpex.DataImpex.loadStack(self.fileList, self.options, self.logger)
      
        #if self.image is not None:
        #    self.logger.appendPlainText("Slices loaded")
        #    self.accept()
        #else :
        #    self.reject()
            
    #def exec_(self):
    #    if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
    #        return  self.image
    #    else:
    #        return None
       
def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])
    
    dialog = StackLoader()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()

class previewTable(QtGui.QDialog):
    def __init__(self, parent=None, newProject = True):
        QtGui.QWidget.__init__(self, parent)
        self.stackloader = parent
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.fileList = self.stackloader.fileList
        self.fileListTable = QtGui.QTableWidget()
        self.fillFileTable()        
        self.fileListTable.setHorizontalHeaderLabels(["red", "green", "blue"])
        self.fileListTable.resizeRowsToContents()
        self.fileListTable.resizeColumnsToContents()
        self.layout.addWidget(self.fileListTable)
        self.show()

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


