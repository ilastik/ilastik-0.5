# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 10:38:02 2010

@author: Anna
"""

import os, glob
import vigra
import sys
import getopt
import h5py
import numpy

import loadOptions

from PyQt4 import QtCore, QtGui, uic

class FileLoader(QtGui.QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        
        self.fileList = []
        self.options = loadOptions.loadOptions()
        
        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to the file:"))
        self.layout.addLayout(tempLayout)
        
        tempLayout = QtGui.QHBoxLayout()
        self.multiChannel = QtGui.QCheckBox("MultiChannel Data:")
        self.connect(self.multiChannel, QtCore.SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout)
       
        self.multiChannelFrame = QtGui.QFrame()
        tempLayout = QtGui.QVBoxLayout()
        tempLayout1 = QtGui.QHBoxLayout()
        self.redPath = QtGui.QLineEdit("")
        self.redButton = QtGui.QPushButton("Select")
        tempLayout1.addWidget(self.redPath)
        tempLayout1.addWidget(self.redButton)
        tempLayout.addLayout(tempLayout1)
        tempLayout1 = QtGui.QHBoxLayout()
        self.greenPath = QtGui.QLineEdit("")
        self.greenButton = QtGui.QPushButton("Select")
        tempLayout1.addWidget(self.greenPath)
        tempLayout1.addWidget(self.greenButton)
        tempLayout.addLayout(tempLayout1)
        tempLayout1 = QtGui.QHBoxLayout()
        self.bluePath = QtGui.QLineEdit("")
        self.blueButton = QtGui.QPushButton("Select")
        tempLayout1.addWidget(self.bluePath)
        tempLayout1.addWidget(self.blueButton)
        tempLayout.addLayout(tempLayout1)
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
            #this call fills the shape
            self.pathChanged("")
        
    def toggleMultiChannel(self, int):
	    if self.multiChannel.checkState() == 0:
	        self.multiChannelFrame.setVisible(False)
	    else:
	        self.multiChannelFrame.setVisible(True)
            #this call fills the line edits with channel filenames
            self.pathChanged("")    
        
    def pathChanged(self, text):
        self.fileList = []
        path = str(self.path.text())
        templist = sorted(glob.glob(path), key=str.lower)
        if (len(templist)>0):
            if self.multiChannel.checkState() == 0:
                self.fileList.append(templist)
                #self.fileList.append(glob.glob(str(self.path.text())))
                self.options.channels.append(0)
            else:
                print templist
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
            if self.optionCheck.checkState() != 0:
                self.optionsWidget.setShapeInfo(self.fileList)
            
    
    def slotLoad(self):
        print "Empty"
    
    def slotDir(self):
        print "Empty"
    
    def slotPreviewFiles(self):
        print "Empty"    