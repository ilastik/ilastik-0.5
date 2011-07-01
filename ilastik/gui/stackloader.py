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

import glob
import os
import ilastik.gui

from ilastik.gui import loadOptionsWidget
from ilastik.core import loadOptionsMgr


from PyQt4 import QtCore, QtGui

#*******************************************************************************
# S t a c k L o a d e r                                                        *
#*******************************************************************************

class StackLoader(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("Load File Stack")
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        #a list of filenames
        #internally, it's a list of lists of filenames
        #for each channel
        self.fileList = []
        self.channelIDs = []
        self.options = loadOptionsMgr.loadOptions()

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
        self.multiChannel = QtGui.QCheckBox("Load MultiChannel data from separate channel images:")
        self.connect(self.multiChannel, QtCore.SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout) 
        
        self.multiChannelFrame = QtGui.QFrame()
        tempLayout = QtGui.QFormLayout()
        self.addChannelButton = QtGui.QPushButton("  Add channel identifier")
        self.connect(self.addChannelButton, QtCore.SIGNAL('clicked()'), self.slotAddChannel)
        tempLayout.addRow(QtGui.QLabel(" "), self.addChannelButton)
        
        self.multiChannelFrame.setLayout(tempLayout)
        
        self.multiChannelFrame.setVisible(False)
        self.layout.addWidget(self.multiChannelFrame)        

        tempLayout = QtGui.QHBoxLayout()
        self.optionsWidget = loadOptionsWidget.LoadOptionsWidget()
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
            if len(self.channelIDs)==0:
                self.slotAddChannel()
    
    def slotAddChannel(self):
        newID = QtGui.QLineEdit()
        newID.setToolTip("Enter identifier for this channel's files, e.g. GFP or ch01")
        self.channelIDs.append(newID)
        nch = len(self.channelIDs)
        label = "Channel %d identifier" % nch
        receiver = lambda callingChannel=nch-1: self.channelIDChanged(callingChannel)
        self.connect(self.channelIDs[nch-1], QtCore.SIGNAL('editingFinished()'), receiver)
        
        self.multiChannelFrame.layout().addRow(QtGui.QLabel(label), newID)
        if len(self.channelIDs)>1:
            self.fileList.append([])

    def channelIDChanged(self, channel):
        #if one identifier changes, we only have to change that filelist
        if len(self.fileList)<channel+1:
            print "!!! something went wrong with allocating enough lists for channels !!!"
            return
        temp = os.path.splitext(str(self.path.text()))[0]
        chfiles = temp + "*" + str(self.channelIDs[channel].text()) + "*"
        self.fileList[channel] = sorted(glob.glob(chfiles), key=str.lower)
        self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)

    def pathChanged(self, text):
        #if path changes, we have to redo all lookups for all channels
        self.fileList = []
        self.options.channels = []
        if self.multiChannel.checkState() == 0:
            pathone = str(self.path.text())
            self.fileList.append(sorted(glob.glob(pathone), key=str.lower))
            #self.fileList.append(glob.glob(str(self.path.text())))
            self.options.channels.append(0)
        else:
            nch = len(self.channelIDs)
            temp = os.path.splitext(str(self.path.text()))[0]
            for ich in range(nch):
                chfiles = temp + "*" + str(self.channelIDs[ich].text()) + "*"
                self.fileList[ich] = sorted(glob.glob(chfiles), key=str.lower)
                self.options.channels.append(ich)                
        self.optionsWidget.setShapeInfo(self.fileList, self.options.channels)

    def slotDir(self):
        path = ilastik.gui.LAST_DIRECTORY
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(filename).path()
        tempname = filename + "/*"
        #This is needed, because internally Qt always uses "/" separators,
        #which is a problem on Windows, as we don't use QDir to open dirs
        self.path.setText(str(QtCore.QDir.convertSeparators(tempname)))
        

    def slotPreviewFiles(self):
        self.fileTableWidget = loadOptionsWidget.previewTable(self.fileList)
        self.fileTableWidget.exec_()

    def slotLoad(self):    
        self.optionsWidget.fillOptions(self.options)
        self.accept()

            
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  str(self.path.text()), self.fileList, self.options
        else:
            return None, None, None
       
def test():
    """Text editor demo"""
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])
    
    dialog = StackLoader()
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()



