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
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import QDir, QFileInfo, QString, SIGNAL
from PyQt4.QtGui import QCheckBox, QDialog, QFileDialog, QFormLayout, QFrame,\
                        QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,\
                        QVBoxLayout, QWidget

import os, glob
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
import ilastik.gui

from ilastik.gui import loadOptionsWidget
from ilastik.core import loadOptionsMgr

#*******************************************************************************
# F i l e L o a d e r                                                          *
#*******************************************************************************

class FileLoader(QDialog):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("File Loading")
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.fileList = []
        self.options = loadOptionsMgr.loadOptions()
        
        tempLayout = QHBoxLayout()
        self.path = QLineEdit("")
        self.connect(self.path, SIGNAL("textEdited(QString)"), self.pathChanged)
        self.pathButton = QPushButton("Select")
        self.connect(self.pathButton, SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QLabel("Path to the file:"))
        self.layout.addLayout(tempLayout)
        
        tempLayout = QHBoxLayout()
        self.multiChannel = QCheckBox("Load Multichannel data as one image:")
        self.connect(self.multiChannel, SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout)
       
        self.multiChannelFrame = QFrame()
        tempLayout = QFormLayout()
        tempLayout1 = QHBoxLayout()
        self.redPath = QLineEdit("")
        self.connect(self.redPath, SIGNAL("textChanged(QString)"), self.redPathChanged)
        self.redButton = QPushButton("Select")
        self.connect(self.redButton, SIGNAL('clicked()'), self.slotRedPath)
        tempLayout1.addWidget(self.redPath)
        tempLayout1.addWidget(self.redButton)
        tempLayout.addRow(QLabel("red:"), tempLayout1)
        
        tempLayout1 = QHBoxLayout()
        self.greenPath = QLineEdit("")
        self.connect(self.greenPath, SIGNAL("textChanged(QString)"), self.greenPathChanged)
        self.greenButton = QPushButton("Select")
        self.connect(self.greenButton, SIGNAL('clicked()'), self.slotGreenPath)
        tempLayout1.addWidget(self.greenPath)
        tempLayout1.addWidget(self.greenButton)
        tempLayout.addRow(QLabel("green:"), tempLayout1)
        
        tempLayout1 = QHBoxLayout()
        self.bluePath = QLineEdit("")
        self.connect(self.bluePath, SIGNAL("textChanged(QString)"), self.bluePathChanged)
        self.blueButton = QPushButton("Select")
        self.connect(self.blueButton, SIGNAL('clicked()'), self.slotBluePath)
        tempLayout1.addWidget(self.bluePath)
        tempLayout1.addWidget(self.blueButton)
        tempLayout.addRow(QLabel("blue:"), tempLayout1)
        
        self.multiChannelFrame.setLayout(tempLayout)
        self.multiChannelFrame.setVisible(False)
        self.layout.addWidget(self.multiChannelFrame)        

        tempLayout = QHBoxLayout()
        self.optionCheck = QCheckBox("Additional options")
        self.connect(self.optionCheck, SIGNAL("stateChanged(int)"), self.toggleOptions)
        tempLayout.addWidget(self.optionCheck)
        self.layout.addLayout(tempLayout)
        
        self.optionsFrame = QFrame()
        tempLayout = QHBoxLayout()
        self.optionsWidget = loadOptionsWidget.LoadOptionsWidget()
        tempLayout.addWidget(self.optionsWidget)
        self.optionsFrame.setLayout(tempLayout)
        self.optionsFrame.setVisible(False)
        self.layout.addWidget(self.optionsFrame)
        
        tempLayout = QHBoxLayout()
        self.loadButton = QPushButton("Load")
        self.connect(self.loadButton, SIGNAL('clicked()'), self.slotLoad)
        self.cancelButton = QPushButton("Cancel")
        self.connect(self.cancelButton, SIGNAL('clicked()'), self.reject)
        self.previewFilesButton = QPushButton("Preview files")
        self.connect(self.previewFilesButton, SIGNAL('clicked()'), self.slotPreviewFiles)
        tempLayout.addWidget(self.previewFilesButton)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.loadButton)
        self.layout.addStretch()
        self.layout.addLayout(tempLayout)
        
    def toggleOptions(self, int):
        if self.optionCheck.checkState() == 0:
            self.optionsFrame.setVisible(False)
        elif self.fileList != [] :
            #check if the file is the correct type for options
            fBase, fExt = os.path.splitext(str(self.fileList[0]))
            fExt=fExt[:-2]
            if fExt in [".tiff", ".jpeg", ".gif", ".jpg", ".tif", ".png"]:
                self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
                self.optionsFrame.setVisible(True)
            else:
                m = QMessageBox(self)
                m.setText("No advanced options available for the selected type " + fExt)
                m.exec_()
                self.optionCheck.setCheckState(False)
                
            
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
        templist1 = QFileDialog.getOpenFileNames(self, "", path)
        templist = []
        for item in templist1:
            templist.append(str(QDir.convertSeparators(item)))
        self.updateFileList(templist)
        if (len(templist)>0):
            path_to_display = templist[0]
            if (len(templist)>1):
                path_to_display = path_to_display + " ..."
            self.path.setText(QString(path_to_display))
        
    def slotRedPath(self):
        path = ilastik.gui.LAST_DIRECTORY
        filename = QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QFileInfo(filename).path()
        self.redPath.setText(filename)
        #self.redPathChanged(filename)
        
    def slotGreenPath(self):
        path = ilastik.gui.LAST_DIRECTORY
        filename = QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QFileInfo(filename).path()
        self.greenPath.setText(filename)
        #self.greenPathChanged(filename)
    
    def slotBluePath(self):
        path = ilastik.gui.LAST_DIRECTORY
        filename = QFileDialog.getOpenFileName(self, "",path)
        ilastik.gui.LAST_DIRECTORY = QFileInfo(filename).path()
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
                self.redPath.setText(QString(self.fileList[0][0]))
                self.options.channels.append(0)
                if len(templist) > 1:
                    self.fileList.append([templist[1]])
                    self.greenPath.setText(QString(self.fileList[1][0]))
                    self.options.channels.append(1)
                if len(templist) > 2:
                    self.fileList.append([templist[2]])
                    self.bluePath.setText(QString(self.fileList[2][0]))
                    self.options.channels.append(2)
            #this call fills the shape
            if (self.optionCheck.checkState()==1):
                self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)

    def slotPreviewFiles(self):
        self.fileTableWidget = loadOptionsWidget.previewTable(self.fileList)
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
    
    
    
