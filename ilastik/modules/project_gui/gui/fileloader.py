# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 10:38:02 2010

@author: Anna
"""

import os, glob
import vigra
import sys
import getopt
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py
import numpy

import loadOptions

from PyQt4 import QtCore, QtGui, uic

class FileLoader(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("File Loading")
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        
        self.fileList = []
        self.options = loadOptions.loadOptions()
        
        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textEdited(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to the file:"))
        self.layout.addLayout(tempLayout)
        
        tempLayout = QtGui.QHBoxLayout()
        self.multiChannel = QtGui.QCheckBox("Load Multichannel data as one image:")
        self.connect(self.multiChannel, QtCore.SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout)
       
        self.multiChannelFrame = QtGui.QFrame()
        tempLayout = QtGui.QFormLayout()
        tempLayout1 = QtGui.QHBoxLayout()
        self.redPath = QtGui.QLineEdit("")
        self.connect(self.redPath, QtCore.SIGNAL("textChanged(QString)"), self.redPathChanged)
        self.redButton = QtGui.QPushButton("Select")
        self.connect(self.redButton, QtCore.SIGNAL('clicked()'), self.slotRedPath)
        tempLayout1.addWidget(self.redPath)
        tempLayout1.addWidget(self.redButton)
        tempLayout.addRow(QtGui.QLabel("red:"), tempLayout1)
        
        tempLayout1 = QtGui.QHBoxLayout()
        self.greenPath = QtGui.QLineEdit("")
        self.connect(self.greenPath, QtCore.SIGNAL("textChanged(QString)"), self.greenPathChanged)
        self.greenButton = QtGui.QPushButton("Select")
        self.connect(self.greenButton, QtCore.SIGNAL('clicked()'), self.slotGreenPath)
        tempLayout1.addWidget(self.greenPath)
        tempLayout1.addWidget(self.greenButton)
        tempLayout.addRow(QtGui.QLabel("green:"), tempLayout1)
        
        tempLayout1 = QtGui.QHBoxLayout()
        self.bluePath = QtGui.QLineEdit("")
        self.connect(self.bluePath, QtCore.SIGNAL("textChanged(QString)"), self.bluePathChanged)
        self.blueButton = QtGui.QPushButton("Select")
        self.connect(self.blueButton, QtCore.SIGNAL('clicked()'), self.slotBluePath)
        tempLayout1.addWidget(self.bluePath)
        tempLayout1.addWidget(self.blueButton)
        tempLayout.addRow(QtGui.QLabel("blue:"), tempLayout1)
        
        self.multiChannelFrame.setLayout(tempLayout)
        self.multiChannelFrame.setVisible(False)
        self.layout.addWidget(self.multiChannelFrame)        

        tempLayout = QtGui.QHBoxLayout()
        self.optionCheck = QtGui.QCheckBox("Additional options")
        self.connect(self.optionCheck, QtCore.SIGNAL("stateChanged(int)"), self.toggleOptions)
        tempLayout.addWidget(self.optionCheck)
        self.layout.addLayout(tempLayout)
        
        self.optionsFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.optionsWidget = loadOptions.LoadOptionsWidget()
        tempLayout.addWidget(self.optionsWidget)
        self.optionsFrame.setLayout(tempLayout)
        self.optionsFrame.setVisible(False)
        self.layout.addWidget(self.optionsFrame)
        
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
        
    def toggleOptions(self, int):
        if self.optionCheck.checkState() == 0:
            self.optionsFrame.setVisible(False)
        else:
            self.optionsFrame.setVisible(True)
            self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
        
    def toggleMultiChannel(self, int):
        if self.multiChannel.checkState() == 0:
            self.multiChannelFrame.setVisible(False)
            templist = []
            for item in self.fileList:
                templist.extend(item)
            self.updateFileList(templist)
        else:
            self.multiChannelFrame.setVisible(True)
            #this call fills the line edits with channel filenames
            if (len(self.fileList)>0):
                templist = self.fileList[0]
                self.updateFileList(templist)    
        
    def pathChanged(self, text):
        path = str(self.path.text())
        templist = sorted(glob.glob(path), key=str.lower)
        self.updateFileList(templist)
        
    def redPathChanged(self, text):
        path = str(self.redPath.text())
        if (os.path.isfile(path)):
            if len(self.fileList) == 0:
                self.fileList.append([path])
                self.fileList.append([])
                self.fileList.append([])
                self.options.channels.append(0)
            else:
                if len(self.fileList[0]) == 0:
                    self.fileList[0] = [path]
                    self.options.channels.append(0)
                else:
                    self.fileList[0] = [path]
            if (self.optionCheck.checkState()==1):
                self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
            
    def greenPathChanged(self, text):
        path = str(self.greenPath.text())
        if (os.path.isfile(path)):
            if len(self.fileList) == 0:
                self.fileList.append([])
                self.fileList.append([])
                self.fileList.append([])
            elif len(self.fileList) == 1:
                self.fileList.append([])
                self.fileList.append([])
                
            if len(self.fileList[1]) == 0:
                self.fileList[1] = [path]
                self.options.channels.append(1)
            else:
                self.fileList[1] = [path]
            if (self.optionCheck.checkState()==1):
                self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
            
    def bluePathChanged(self, text):
        path = str(self.bluePath.text())
        if (os.path.isfile(path)):
            if len(self.fileList) == 0:
                self.fileList.append([])
                self.fileList.append([])
                self.fileList.append([])
            elif len(self.fileList) == 1:
                self.fileList.append([])
                self.fileList.append([])
                
            if len(self.fileList[2]) == 0:
                self.fileList[2] = [path]
                self.options.channels.append(2)
            else:
                self.fileList[2] = [path]
            if (self.optionCheck.checkState()==1):
                self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
                
    def slotDir(self):
        path = self.path.text()
        templist1 = QtGui.QFileDialog.getOpenFileNames(self, "", path)
        templist = []
        for item in templist1:
            templist.append(str(QtCore.QDir.convertSeparators(item)))
        self.updateFileList(templist)
        if (len(templist)>0):
            path_to_display = templist[0]
            if (len(templist)>1):
                path_to_display = path_to_display + " ..."
            self.path.setText(QtCore.QString(path_to_display))
        
    def slotRedPath(self):
        path = self.redPath.text()
        filename = QtGui.QFileDialog.getOpenFileName(self, "", path)
        self.redPath.setText(filename)
        #self.redPathChanged(filename)
        
    def slotGreenPath(self):
        path = self.greenPath.text()
        filename = QtGui.QFileDialog.getOpenFileName(self, "", path)
        self.greenPath.setText(filename)
        #self.greenPathChanged(filename)
    
    def slotBluePath(self):
        path = self.bluePath.text()
        filename = QtGui.QFileDialog.getOpenFileName(self, "",path)
        self.bluePath.setText(filename)
        #self.bluePathChanged(filename)
    
    def updateFileList(self, templist):
        self.fileList = []    
        if (len(templist)>0):
            if self.multiChannel.checkState() == 0:
                self.fileList.append(templist)
                self.options.channels.append(0)
            else:
                self.fileList.append([templist[0]])
                self.redPath.setText(QtCore.QString(self.fileList[0][0]))
                self.options.channels.append(0)
                if len(templist) > 1:
                    self.fileList.append([templist[1]])
                    self.greenPath.setText(QtCore.QString(self.fileList[1][0]))
                    self.options.channels.append(1)
                if len(templist) > 2:
                    self.fileList.append([templist[2]])
                    self.bluePath.setText(QtCore.QString(self.fileList[2][0]))
                    self.options.channels.append(2)
            #this call fills the shape
            if (self.optionCheck.checkState()==1):
                self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)

    def slotPreviewFiles(self):
        self.fileTableWidget = loadOptions.previewTable(self.fileList)
        self.fileTableWidget.exec_()
                
    def slotLoad(self):
        if self.optionCheck.checkState() == 0:
            self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)
            self.optionsWidget.fillDefaultOptions(self.options)
        else:
            #options widget is open, the shape should be filled already
            #if self.options.shape == (0,0,0):
                #self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)
            self.optionsWidget.fillOptions(self.options)
        self.accept()
    
    
    
