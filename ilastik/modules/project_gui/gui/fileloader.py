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
from ilastik.gui.previewTable import PreviewTable
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
        
        self.channelPathWidgets = []
        self.channelButtons = []
        
        tempLayout = QHBoxLayout()
        self.path = QLineEdit("")
        self.connect(self.path, SIGNAL("textEdited(QString)"), self.pathChanged)
        self.pathButton = QPushButton("Select")
        self.connect(self.pathButton, SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QLabel("Path to the file:"))
        self.layout.addLayout(tempLayout)
        
        self.multiChannelFrame = QFrame()
             
        tempLayout = QFormLayout()
        self.addChannelButton = QPushButton("  Append more spectral channels")
        self.connect(self.addChannelButton, SIGNAL('clicked()'), self.slotAddChannel)
        tempLayout.addRow(QLabel(" "), self.addChannelButton)
        
        self.multiChannelFrame.setLayout(tempLayout)

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
        
    def pathChanged(self, text):
        path = str(self.path.text())
        templist = sorted(glob.glob(path), key=str.lower)
        self.updateFileListNew(0, templist)
        
    def slotDir(self):
        path = ilastik.gui.LAST_DIRECTORY
        filenames = QFileDialog.getOpenFileNames(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QFileInfo(filenames[0]).path()
        
        templist = []
        for item in filenames:
            templist.append(str(QDir.convertSeparators(item)))
        self.updateFileListNew(0, templist)
        if (len(templist)>0):
            path_to_display = templist[0]
            if (len(templist)>1):
                path_to_display = path_to_display + " ..."
            self.path.setText(QString(path_to_display))
        
        
    def slotAddChannel(self):
        
        newPath = QLineEdit("")
        self.channelPathWidgets.append(newPath)
        newButton = QPushButton("Select")
        self.channelButtons.append(newButton)
        nch = len(self.channelPathWidgets)
        label = "%d" % nch      
        
        #FEEL THE POWER OF PYTHON
        receiverPath = lambda callingPath=nch-1: self.channelPathChanged(callingPath)
        self.connect(self.channelPathWidgets[nch-1], SIGNAL('editingFinished()'), receiverPath)
        
        receiverButton = lambda callingButton=nch-1: self.channelButtonClicked(callingButton)
        self.connect(self.channelButtons[nch-1], SIGNAL('clicked()'), receiverButton)
        
        tempLayout = QHBoxLayout()
        tempLayout.addWidget(newPath)
        tempLayout.addWidget(newButton)
        self.multiChannelFrame.layout().addRow(QLabel(label), tempLayout)       
        
        if len(self.channelPathWidgets)==1 and len(self.path.text())>0:
            #this is the first time the button is pressed and there is already something in the path
            #replicate the first channel from the path and add space for the second one
            self.channelPathWidgets[nch-1].setText(self.path.text())
            #the file list has been updated when the path was changed, no need to do it here
            self.slotAddChannel()
        else:
            self.fileList.append([])
    

    def channelButtonClicked(self, calling):
        path = ilastik.gui.LAST_DIRECTORY
        filenames = QFileDialog.getOpenFileNames(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QFileInfo(filenames[0]).path()

        templist = []
        for f in filenames:
            templist.append(str(QDir.convertSeparators(f)))
        self.updateFileListNew(calling, templist)
        newText = filenames[0]
        if len(filenames)>1:
            newText = filenames[0]+"..."
        self.channelPathWidgets[calling].setText(newText)
        
    
    def channelPathChanged(self, calling):
        #is there more than 1 file? Not very probable, but let's check anyway
        text = self.channelPathWidgets[calling].text()
        filenames = []
        if ',' in text:
            templist = text.split(',')
            for f in templist:
                tempname = str(QDir.convertSeparators(f))
                if os.path.isfile(tempname):
                    filenames.append(tempname)
        else:
            tempname = str(QDir.convertSeparators(text))
            if os.path.isfile(tempname):
                filenames.append(tempname)
        self.updateFileListNew(calling, filenames)
        

    def updateFileListNew(self, col, filenames):
        if len(self.fileList)==0:
            self.fileList.append([])
        if len(self.fileList)<col+1:
            print "!!! something went wrong with allocating enough file lists !!!"
            return
        self.fileList[col]=filenames
        #this call fills the shape
        if (self.optionCheck.checkState()==1):
            self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)

    def slotPreviewFiles(self):
        self.fileTableWidget = PreviewTable(self.fileList)
        self.fileTableWidget.exec_()
                
    def slotLoad(self):
        #remove unused channels, we don't support loading only green or blue anymore
        newlist = []
        for f in self.fileList:
            if len(f)>0:
                newlist.append(f)
        self.fileList = newlist
        for i in range(len(self.fileList)):
            self.options.channels.append(i)
            
        if self.optionCheck.checkState() == 0:
         
            self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)
            self.optionsWidget.fillDefaultOptions(self.options)
        else:
            #options widget is open, the shape should be filled already
            #if self.options.shape == (0,0,0):
                #self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)
            self.optionsWidget.fillOptions(self.options)
        
        self.accept()

    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return  self.fileList, self.options
        else:
            return None, None    
    
    
