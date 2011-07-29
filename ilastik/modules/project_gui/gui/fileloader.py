# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 10:38:02 2010

@author: Anna
"""

import os, glob
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
import ilastik.gui

from ilastik.gui import loadOptionsWidget
from ilastik.core import loadOptionsMgr

from PyQt4 import QtCore, QtGui

#*******************************************************************************
# F i l e L o a d e r                                                          *
#*******************************************************************************

class FileLoader(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("File Loading")
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        
        self.fileList = []
        self.options = loadOptionsMgr.loadOptions()
        
        self.channelPathWidgets = []
        self.channelButtons = []
        
        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textEdited(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to the file:"))
        self.layout.addLayout(tempLayout)
        
        self.multiChannelFrame = QtGui.QFrame()
             
        tempLayout = QtGui.QFormLayout()
        self.addChannelButton = QtGui.QPushButton("  Append more spectral channels")
        self.connect(self.addChannelButton, QtCore.SIGNAL('clicked()'), self.slotAddChannel)
        tempLayout.addRow(QtGui.QLabel(" "), self.addChannelButton)
        
        self.multiChannelFrame.setLayout(tempLayout)

        self.layout.addWidget(self.multiChannelFrame)        

        tempLayout = QtGui.QHBoxLayout()
        self.optionCheck = QtGui.QCheckBox("Additional options")
        self.connect(self.optionCheck, QtCore.SIGNAL("stateChanged(int)"), self.toggleOptions)
        tempLayout.addWidget(self.optionCheck)
        self.layout.addLayout(tempLayout)
        
        self.optionsFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.optionsWidget = loadOptionsWidget.LoadOptionsWidget()
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
        elif self.fileList != [] :
            #check if the file is the correct type for options
            fBase, fExt = os.path.splitext(str(self.fileList[0]))
            fExt=fExt[:-2]
            if fExt in [".tiff", ".jpeg", ".gif", ".jpg", ".tif", ".png"]:
                self.optionsWidget.setShapeInfo(self.fileList,self.options.channels)
                self.optionsFrame.setVisible(True)
            else:
                m = QtGui.QMessageBox(self)
                m.setText("No advanced options available for the selected type " + fExt)
                m.exec_()
                self.optionCheck.setCheckState(False)
        
    def pathChanged(self, text):
        path = str(self.path.text())
        templist = sorted(glob.glob(path), key=str.lower)
        self.updateFileListNew(0, templist)
        

                
    def slotDir(self):
        path = ilastik.gui.LAST_DIRECTORY
        filenames = QtGui.QFileDialog.getOpenFileNames(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(filenames[0]).path()
        
        templist = []
        for item in filenames:
            templist.append(str(QtCore.QDir.convertSeparators(item)))
        self.updateFileListNew(0, templist)
        if (len(templist)>0):
            path_to_display = templist[0]
            if (len(templist)>1):
                path_to_display = path_to_display + " ..."
            self.path.setText(QtCore.QString(path_to_display))
        
        
    def slotAddChannel(self):
        
        newPath = QtGui.QLineEdit("")
        self.channelPathWidgets.append(newPath)
        newButton = QtGui.QPushButton("Select")
        self.channelButtons.append(newButton)
        nch = len(self.channelPathWidgets)
        label = "%d" % nch      
        
        #FEEL THE POWER OF PYTHON
        receiverPath = lambda callingPath=nch-1: self.channelPathChanged(callingPath)
        self.connect(self.channelPathWidgets[nch-1], QtCore.SIGNAL('editingFinished()'), receiverPath)
        
        receiverButton = lambda callingButton=nch-1: self.channelButtonClicked(callingButton)
        self.connect(self.channelButtons[nch-1], QtCore.SIGNAL('clicked()'), receiverButton)
        
        tempLayout = QtGui.QHBoxLayout()
        tempLayout.addWidget(newPath)
        tempLayout.addWidget(newButton)
        self.multiChannelFrame.layout().addRow(QtGui.QLabel(label), tempLayout)       
        
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
        filenames = QtGui.QFileDialog.getOpenFileNames(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(filenames[0]).path()

        templist = []
        for f in filenames:
            templist.append(str(QtCore.QDir.convertSeparators(f)))
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
                tempname = str(QtCore.QDir.convertSeparators(f))
                if os.path.isfile(tempname):
                    filenames.append(tempname)
        else:
            tempname = str(QtCore.QDir.convertSeparators(text))
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
        self.fileTableWidget = loadOptionsWidget.previewTable(self.fileList)
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
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.fileList, self.options
        else:
            return None, None    
    
    
