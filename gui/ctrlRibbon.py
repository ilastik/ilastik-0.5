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
import sys
from gui.iconMgr import ilastikIcons

class Ribbon(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabBar.__init__(self, parent)
        self.tabDict = {}
        if parent:     
            self.connect(parent,QtCore.SIGNAL("orientationChanged(Qt::Orientation)"),self.orientationEvent)

    def orientationEvent(self, orientation):
        if orientation == QtCore.Qt.Horizontal: 
            self.setTabPosition(self.North)            
        if orientation == QtCore.Qt.Vertical: 
            self.setTabPosition(self.West)
        for name, tab in self.tabDict.items():
            lo = tab.layout()
            if orientation == 1:
                orientation = 0
            lo.setDirection(lo.Direction(orientation))

            
    def moveEvent(self, event):
        QtGui.QTabWidget.moveEvent(self, event)
    
    def addTab(self, w, s="TabName"):
        self.tabDict[s] = w
        QtGui.QTabWidget.addTab(self, w, s)              

class RibbonBaseItem(QtGui.QWidget):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        self.name = ribbon_entry.name
        self.setToolTip(ribbon_entry.tool_tip)
        
class RibbonButtonItem(QtGui.QPushButton,RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        RibbonBaseItem.__init__(self,  ribbon_entry)
        self.setIcon(ribbon_entry.icon)   
        self.setText(ribbon_entry.name)

class RibbonToggleButtonItem(QtGui.QToolButton, RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QToolButton.__init__(self)
        RibbonBaseItem.__init__(self,  ribbon_entry)
        action = QtGui.QAction(self)
        action.setIcon(ribbon_entry.icon)
        action.setCheckable(True)
        action.setIconText(ribbon_entry.name)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setDefaultAction(action)
        self.setPopupMode(QtGui.QToolButton.InstantPopup)
    
class RibbonSlider(QtGui.QSlider,RibbonBaseItem):
    def __init__(self, ribbon_entry):
        QtGui.QSlider.__init__(self)
        RibbonBaseItem.__init__(self, ribbon_entry)
        self.setMinimum(1)
        self.setMaximum(6)
        self.setSliderPosition(1)
        

class RibbonDropButtonItem(QtGui.QToolButton,RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QToolButton.__init__(self)
        RibbonBaseItem.__init__(self,  ribbon_entry)
        action = QtGui.QAction(self)
        action.setIcon(ribbon_entry.icon)   
        self.setIconSize(ribbon_entry.size)
        action.setIconText(ribbon_entry.name)
        self.setCheckable(True)
        self.setToolButtonStyle(2)
        self.setDefaultAction(action)

class RibbonListItem(QtGui.QListWidget, RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QListWidget.__init__(self)
        RibbonBaseItem.__init__(self, ribbon_entry)


class RibbonTabContainer(QtGui.QWidget):
    def __init__(self, position, parent=None, ):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.position = position
        self.setLayout(layout)
        self.itemDict = {}
        self.signalList = []
        
    def addItem(self, item):
        self.itemDict[item.name] = item
        self.layout().addWidget(item)

class RibbonEntry():
    def __init__(self, name, icon_file=None, tool_tip=None, type=RibbonButtonItem, callback=None):
        self.name = name
        self.icon_file = icon_file
        self.tool_tip = tool_tip
        self.callback = callback
        self.icon = QtGui.QIcon(str(self.icon_file)) 
        self.type = type
    
class RibbonEntryGroup():
    def __init__(self, name, position):
        self.name = name
        self.entries = []
        self.position = position
        
    def append(self, entry):
        self.entries.append(entry)
        
    def makeTab(self):
        self.tabs = RibbonTabContainer(self.position)
        for rib in self.entries:
            item = rib.type(rib)
            self.tabs.addItem(item)
        self.tabs.layout().addStretch()
        return self.tabs   

def createRibbons():
    RibbonGroupObjects = {}
    RibbonGroupObjects["Projects"] = RibbonEntryGroup("Projects", 0)    
    RibbonGroupObjects["Features"] = RibbonEntryGroup("Features", 1)   
    RibbonGroupObjects["Classification"] = RibbonEntryGroup("Classification", 2)   
    #RibbonGroupObjects["Segmentation"] = RibbonEntryGroup("Segmentation", 3)
    #RibbonGroupObjects["Export"] = RibbonEntryGroup("Export", 3)
    
    RibbonGroupObjects["Projects"].append(RibbonEntry("New", ilastikIcons.New ,"New"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Open", ilastikIcons.Open ,"Open"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Save", ilastikIcons.Save,"Save"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Edit", ilastikIcons.Edit ,"Edit"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Options", ilastikIcons.Edit ,"Options"))
    
    RibbonGroupObjects["Features"].append(RibbonEntry("Select", ilastikIcons.Select ,"Select Features"))
    RibbonGroupObjects["Features"].append(RibbonEntry("Compute", ilastikIcons.System ,"Compute Features"))
    
    RibbonGroupObjects["Classification"].append(RibbonEntry("Train", ilastikIcons.System ,"Train Classifier"))
    RibbonGroupObjects["Classification"].append(RibbonEntry("Predict", ilastikIcons.Dialog ,"Predict Classifier")) 
    RibbonGroupObjects["Classification"].append(RibbonEntry("Interactive", ilastikIcons.Play ,"Interactive Classifier",type=RibbonToggleButtonItem))
    RibbonGroupObjects["Classification"].append(RibbonEntry("Batchprocess", ilastikIcons.Play ,"Batch Process Files in a Directory"))


    #RibbonGroupObjects["Segmentation"].append(RibbonEntry("Segment", ilastikIcons.Play ,"Segment Foreground/Background"))
    #RibbonGroupObjects["Segmentation"].append(RibbonEntry("BorderSegment", ilastikIcons.Play ,"Segment Foreground/Background with Border"))

    #RibbonGroupObjects["Export"].append(RibbonEntry("Export", ilastikIcons.System  ,"Export"))
    return RibbonGroupObjects   
        
        
