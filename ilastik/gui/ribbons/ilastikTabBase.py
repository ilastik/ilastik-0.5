from PyQt4.QtGui import QToolButton, QIcon
from PyQt4.QtCore import Qt

#*******************************************************************************
# I l a s t i k T a b B a s e                                                  *
#*******************************************************************************

class TabButton(QToolButton):
    def __init__(self, text, ilastikIcon, tooltip=""):
        QToolButton.__init__(self)
        self.setText(text)
        self.setIcon(QIcon(ilastikIcon))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setToolTip(tooltip)

class IlastikTabBase(object):
    name = "Ribbon Base Class for Tab Pages" 
    description = "Virtual base class" 
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    position = 99 #position of the tab
    
    moduleName = "Module Name" # you have to set this to the module that handles this tab
                                # displayed overlays get stored there
    
    def __init__(self, parent=None):
        self.ilastik = self.parent = parent
        # these properties are assigned and available 
        # when the tab is active
        self.localMgr = None
        self.globalMgr = None
        self.dataMgr = None
        self.activeImage = None
        
    def on_activation(self):
        #print "Tab changed: on_activation() not implementated by this tab"
        pass

    
    def on_deActivation(self):
        #print "Tab changed: on_deActivation() not implementated by this tab"
        pass

    def on_otherProject(self):
        pass

    
    def on_imageChanged(self):
        #print "Image changed: on_imageChanged() not implementated by this tab"
        pass
        

