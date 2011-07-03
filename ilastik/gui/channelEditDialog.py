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

from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui import QDialog, QGroupBox, QHBoxLayout, QListWidget,\
                        QListWidgetItem, QPushButton, QVBoxLayout, QWidget

#*******************************************************************************
# E d i t C h a n n e l s D i a l o g                                          *
#*******************************************************************************

class EditChannelsDialog(QDialog):
    def __init__(self, selectedChannels, numOfChannels, parent):
        QWidget.__init__(self, parent=None)
        self.setWindowTitle("Edit Channels")
        
        self.selectedChannels = selectedChannels
        self.numOfChannels = numOfChannels
        
        self.mainLayout = QVBoxLayout()
        self.channelListBox = QGroupBox('Select Channel for feature computation')
        self.channelList = QListWidget()
        
        self.tempLayout = QVBoxLayout()
        self.tempLayout.addWidget(self.channelList)
        
        self.channelListBox.setLayout(self.tempLayout)
        
        for c_ind in range(self.numOfChannels):
            channelItem = QListWidgetItem('Channel %d' % c_ind)
            sel = Qt.Unchecked
            if c_ind in self.selectedChannels:
                sel = Qt.Checked 
            channelItem.setCheckState(sel)
            self.channelList.addItem(channelItem)
            
        self.mainLayout.addWidget(self.channelListBox)
        
        confirmButtons = QHBoxLayout()
        
        self.okay = QPushButton('OK')
        self.cancel = QPushButton('Cancel')
        
        self.connect(self.okay, SIGNAL("clicked()"), self.accept)
        self.connect(self.cancel, SIGNAL("clicked()"), self.reject)
        
        confirmButtons.addStretch()
        confirmButtons.addWidget(self.okay)
        confirmButtons.addWidget(self.cancel)
        
        
        self.mainLayout.addLayout(confirmButtons)
        
        self.setLayout(self.mainLayout)
        
        
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            result = []        
            for c_ind in self.selectedChannels:
                channelItem = self.channelList.item(c_ind)
                if channelItem.checkState() == Qt.Checked:
                    result.append(c_ind)
            self.selectedChannels = result
            return result
        else:
            return None