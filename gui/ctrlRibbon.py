from PyQt4 import QtCore, QtGui
import sys

class Ribbon(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabBar.__init__(self, parent)
        self.tabList = []
        if parent:     
            self.connect(parent,QtCore.SIGNAL("orientationChanged(Qt::Orientation)"),self.orientationEvent)

    def orientationEvent(self, orientation):
        if orientation == QtCore.Qt.Horizontal: 
            self.setTabPosition(self.North)
        if orientation == QtCore.Qt.Vertical: 
            self.setTabPosition(self.West)
        
    def moveEvent(self, event):
        QtGui.QTabWidget.moveEvent(self, event)
    
    def addTab(self, w, s="TabName"):
        self.tabList.append((w,s))
        QtGui.QTabWidget.addTab(self,w,s)
        
        
        
class RibbonButtonItem(QtGui.QPushButton):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        self.setIcon(ribbon_entry.icon)   
        self.setIconSize(ribbon_entry.size)
        self.setText(ribbon_entry.name)
        self.setToolTip(ribbon_entry.tool_tip)
        self.setMaximumSize(QtCore.QSize(128,128))
        


class RibbonTabContainer(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        self.setLayout(self.layout)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
    def addItem(self, item):
        self.layout.addWidget(item)

class RibbonEntry():
    def __init__(self, name, icon_file=None, tool_tip=None, type=RibbonButtonItem, callback=None):
        self.name = name
        self.icon_file = icon_file
        self.tool_tip = tool_tip
        self.callback = callback
        self.icon = QtGui.QIcon('../../icons/32x32/' + self.icon_file) 
        self.type = type
        self.size = QtCore.QSize(32,32)
    
class RibbonEntryGroup():
    def __init__(self, name):
        self.name = name
        self.entries = []
        
    def append(self, entry):
        self.entries.append(entry)
        
    def makeTab(self):
        tabs = RibbonTabContainer()
        for rib in self.entries:
            item = rib.type(rib)
            tabs.addItem(item)  
        return tabs   

def createRibbons():
    RibbonGroupObjects = []
    RibbonGroupObjects.append(RibbonEntryGroup("Projects"))       
    RibbonGroupObjects.append(RibbonEntryGroup("Features"))   
    RibbonGroupObjects.append(RibbonEntryGroup("Classification"))   
    
    RibbonGroupObjects[0].append(RibbonEntry("New", "actions/document-new.png" ,"New"))
    RibbonGroupObjects[0].append(RibbonEntry("Open", "actions/document-open.png" ,"Open"))
    RibbonGroupObjects[0].append(RibbonEntry("Edit", "actions/document-properties.png" ,"Edit"))
    
    RibbonGroupObjects[1].append(RibbonEntry("Select", "actions/edit-select-all.png" ,"Select Features"))
    RibbonGroupObjects[1].append(RibbonEntry("Compute", "categories/applications-system.png" ,"Compute Features"))
    
    RibbonGroupObjects[2].append(RibbonEntry("Select", "actions/edit-select-all.png" ,"Select Classifier"))
    RibbonGroupObjects[2].append(RibbonEntry("Compute", "categories/applications-system.png" ,"Train Classifier"))
    return RibbonGroupObjects

 
    
        
        