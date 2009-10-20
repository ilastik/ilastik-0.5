from PyQt4 import QtCore, QtGui
import sys

class Ribbon(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabBar.__init__(self, parent)
        self.tabDict = {}
        if parent:     
            self.connect(parent,QtCore.SIGNAL("orientationChanged(Qt::Orientation)"),self.orientationEvent)

    def orientationEvent(self, orientation):
        for tab in self.tabList:
            lo = tab[0].layout()
            lo.setDirection(lo.Direction(orientation))
        if orientation == QtCore.Qt.Horizontal: 
            self.setTabPosition(self.North)            
        if orientation == QtCore.Qt.Vertical: 
            self.setTabPosition(self.West)
            
    def moveEvent(self, event):
        QtGui.QTabWidget.moveEvent(self, event)
    
    def addTab(self, w, s="TabName"):
        self.tabDict[s] = w
        QtGui.QTabWidget.insertTab(self, w.position, w, s)              

class RibbonBaseItem(QtGui.QWidget):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        self.name = ribbon_entry.name
        self.setToolTip(ribbon_entry.tool_tip)
        self.setMaximumSize(QtCore.QSize(128,48)) 
        
class RibbonButtonItem(QtGui.QPushButton,RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        RibbonBaseItem.__init__(self,  ribbon_entry)
        self.setIcon(ribbon_entry.icon)   
        self.setIconSize(ribbon_entry.size)
        self.setText(ribbon_entry.name)

class RibbonToggleButtonItem(QtGui.QToolButton,RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QToolButton.__init__(self)
        RibbonBaseItem.__init__(self,  ribbon_entry)
        self.setIcon(ribbon_entry.icon)   
        self.setIconSize(ribbon_entry.size)
        self.setText(ribbon_entry.name)
        self.setCheckable(True)

class RibbonListItem(QtGui.QListWidget, RibbonBaseItem):
    def __init__(self,  ribbon_entry):
        QtGui.QPushButton.__init__(self)
        RibbonBaseItem.__init__(self, ribbon_entry)
        self.setMaximumSize(QtCore.QSize(300,40)) 

class RibbonTabContainer(QtGui.QWidget):
    def __init__(self, position, parent=None, ):
        QtGui.QWidget.__init__(self)
        #careful: QWidget.layout() is a member function - don't overwrite!
        layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight)
        layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.position = position
        self.setLayout(layout)
        self.itemDict = {}
        self.signalList = []
    def addItem(self, item):
        self.itemDict[item.name] = item
        #self.signalList.append(QtCore.SIGNAL('clicked()'))
        self.layout().addWidget(item)

class RibbonEntry():
    def __init__(self, name, icon_file=None, tool_tip=None, type=RibbonButtonItem, callback=None):
        self.name = name
        self.icon_file = icon_file
        self.tool_tip = tool_tip
        self.callback = callback
        self.icon = QtGui.QIcon('../../icons/32x32/' + str(self.icon_file)) 
        self.type = type
        self.size = QtCore.QSize(32,32)
    
class RibbonEntryGroup():
    def __init__(self, name, position):
        self.name = name
        self.entries = []
        self.position = position
        
    def append(self, entry):
        self.entries.append(entry)
        
    def makeTab(self):
        tabs = RibbonTabContainer(self.position)
        for rib in self.entries:
            item = rib.type(rib)
            tabs.addItem(item)  
        return tabs   

def createRibbons():
    RibbonGroupObjects = {}
    RibbonGroupObjects["Projects"] = RibbonEntryGroup("Projects",0)       
    RibbonGroupObjects["Features"] = RibbonEntryGroup("Features",1)   
    RibbonGroupObjects["Classification"] = RibbonEntryGroup("Classification",2)   
    
    RibbonGroupObjects["Projects"].append(RibbonEntry("New", "actions/document-new.png" ,"New"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Open", "actions/document-open.png" ,"Open"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Save", "actions/document-save.png" ,"Save"))
    RibbonGroupObjects["Projects"].append(RibbonEntry("Edit", "actions/document-properties.png" ,"Edit"))
    
    RibbonGroupObjects["Features"].append(RibbonEntry("Select", "actions/edit-select-all.png" ,"Select Features"))
    RibbonGroupObjects["Features"].append(RibbonEntry("Compute", "categories/applications-system.png" ,"Compute Features"))
    
    RibbonGroupObjects["Classification"].append(RibbonEntry("Train", "categories/applications-system.png" ,"Train Classifier"))
    RibbonGroupObjects["Classification"].append(RibbonEntry("Predict", "actions/edit-select-all.png" ,"Select Classifier")) 
    RibbonGroupObjects["Classification"].append(RibbonEntry("Interactive", "actions/media-playback-start.png" ,"Interactive Classifier",type=RibbonToggleButtonItem))
    
    return RibbonGroupObjects   
        
        