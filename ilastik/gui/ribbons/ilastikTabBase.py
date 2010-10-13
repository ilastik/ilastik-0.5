
class IlastikTabBase(object):
    name = "Ribbon Base Class for Tab Pages" 
    description = "Virtual base class" 
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    position = 99 #position of the tab
    
    def __init__(self, parent=None):
        self.ilastik = self.parent = parent

    def on_activation(self):
        print "Tab changed: on_activation() not implementated by this tab"
    
    def on_deActivation(self):
        pass
    
    def on_imageChanged(self):
        print "Image changed: on_imageChanged() not implementated by this tab"
        

