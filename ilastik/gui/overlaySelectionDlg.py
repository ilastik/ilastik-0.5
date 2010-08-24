from PyQt4 import QtCore, QtGui



class OverlaySelectionDialog():
    def __init__(self,  mgr):
        self.mgr = mgr
    
    def exec_(self):
        list = self.mgr.keys()
        selection = QtGui.QInputDialog.getItem(None, "Select Segmentation Weights",  "Weights",  list,  editable = False)
        selection = str(selection[0])
        overlay = self.mgr[selection]        
        
        return [overlay]

