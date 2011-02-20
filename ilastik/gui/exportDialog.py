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

from PyQt4 import QtCore, QtGui
import ilastik.gui

#*******************************************************************************
# E x p o r t D i a l o g                                                      *
#*******************************************************************************

class ExportDialog(QtGui.QDialog):
    def __init__(self, formatList, timeOffset, sliceOffset, channelOffset, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Export Images")
        layout = QtGui.QVBoxLayout()
            
        l = QtGui.QHBoxLayout()
        l.addWidget(QtGui.QLabel("Path"))
        self.path = QtGui.QLineEdit("")
        l.addWidget(self.path)
        self.pathButton = QtGui.QPushButton("Select")
        l.addWidget(self.pathButton)
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        layout.addLayout(l)
        
        l = QtGui.QHBoxLayout()
        l.addWidget(QtGui.QLabel("File name/prefix"))
        self.prefix = QtGui.QLineEdit("")
        l.addWidget(self.prefix)
        self.formatList = formatList
        self.formatBox = QtGui.QComboBox()
        for item in self.formatList:
            self.formatBox.addItem(QtCore.QString(item))

        l.addWidget(self.formatBox)        
        layout.addLayout(l)
        
        l = QtGui.QHBoxLayout()
        self.timeOffsetBox = None
        self.sliceOffsetBox = None
        self.channelOffsetBox = None
        if timeOffset == True:
            self.timeOffsetBox = QtGui.QSpinBox()
            l.addWidget(QtGui.QLabel("Time Offset"))
            l.addWidget(self.timeOffsetBox)
        if sliceOffset == True:
            self.sliceOffsetBox = QtGui.QSpinBox()
            l.addWidget(QtGui.QLabel("Slice Offset"))
            l.addWidget(self.sliceOffsetBox)
        if channelOffset == True:
            self.channelOffsetBox = QtGui.QSpinBox()
            l.addWidget(QtGui.QLabel("Channel Offset"))
            l.addWidget(self.channelOffsetBox)
        if self.timeOffsetBox is not None or self.sliceOffsetBox is not None or self.channelOffsetBox is not None:
            layout.addLayout(l)
            
        l = QtGui.QHBoxLayout()
        l.addStretch()
        b = QtGui.QPushButton("Ok")
        self.connect(b, QtCore.SIGNAL("clicked()"), self.export)
        l.addWidget(b)
        b = QtGui.QPushButton("Cancel")
        self.connect(b, QtCore.SIGNAL("clicked()"), self.reject)
        l.addWidget(b)
        layout.addLayout(l)
        self.setLayout(layout)
        

    def slotDir(self):
        path = ilastik.gui.LAST_DIRECTORY
        dir = QtGui.QFileDialog.getExistingDirectory(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(dir).path()
        self.path.setText(dir)
            
    def export(self):
        self.timeOffset = self.timeOffsetBox.value() if self.timeOffsetBox else 0
        self.sliceOffset = self.sliceOffsetBox.value() if self.sliceOffsetBox else 0
        self.channelOffset = self.channelOffsetBox.value() if self.channelOffsetBox else 0
        self.format = self.formatList[self.formatBox.currentIndex()]
        self.accept()

    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return None
        else:
            return None


