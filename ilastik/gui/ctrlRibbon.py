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
#    ADVISED OF THE POSSIBILITY OF SUCH 
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4 import QtCore, QtGui

#*******************************************************************************
# I l a s t i k T a b W i d g e t                                              *
#*******************************************************************************

class IlastikTabWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabWidget.__init__(self, parent)
        self.setContentsMargins(0,0,0,0)
        self.tabDict = {}
        self.currentTabNumber = 0
        if parent:     
            self.connect(parent,QtCore.SIGNAL("orientationChanged(Qt::Orientation)"),self.orientationEvent)

    def orientationEvent(self, orientation):
        if orientation == QtCore.Qt.Horizontal: 
            self.setTabPosition(self.North)            
        if orientation == QtCore.Qt.Vertical: 
            self.setTabPosition(self.West)
        for tab in self.tabDict.values():
            lo = tab.layout()
            if orientation == 1:
                orientation = 0
            lo.setDirection(lo.Direction(orientation))
          
    def moveEvent(self, event):
        QtGui.QTabWidget.moveEvent(self, event)
    
    def addTab(self, page, tabName):
        self.tabDict[tabName] = page
        QtGui.QTabWidget.addTab(self, page, tabName)  
 
    def getTab(self, tabName):
        return self.tabDict[tabName] 
                   
        
        
