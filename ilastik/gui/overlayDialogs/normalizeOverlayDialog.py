from PyQt4 import QtCore, QtGui
import overlayDialogBase
import ilastik.gui.overlaySelectionDlg
from ilastik.core.overlays.normalizeOverlay import NormalizeOverlay

    
class NormalizeOverlayDialog(overlayDialogBase.OverlayDialogBase, QtGui.QDialog):
    configuresClass = "ilastik.core.overlays.normalizeOverlay.NormalizeOverlay"
    name = "Normalize Overlay"
    author = "C. M. S."
    homepage = ""
    description = """Use this overlay to normalize the color or intensity values to a min / max range (e.g. to make raw data in 16-bit visible)"""
            
    
    def __init__(self, ilastik_, instance = None):
        QtGui.QDialog.__init__(self, ilastik_)
        self.setWindowTitle("Normalize OVerlay")
        
        self.ilastik = ilastik_
        d = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.ilastik, singleSelection = True)
        o = d.exec_()
        if o is not None:
            self.overlayItem = NormalizeOverlay(o[0], 50, 200)
            self.volumeEditor = ilastik_.labelWidget
            self.project = ilastik_.project
            self.mainlayout = QtGui.QVBoxLayout()
            self.setLayout(self.mainlayout)
            self.mainwidget = QtGui.QWidget()
            self.mainlayout.addWidget(self.mainwidget)
    
            self.acceptButton = QtGui.QPushButton("Ok")
            self.connect(self.acceptButton, QtCore.SIGNAL('clicked()'), self.okClicked)
            self.acceptButton = QtGui.QPushButton("Ok")
            self.mainlayout.addWidget(self.acceptButton)      

        
    def okClicked(self):
        self.accept()
        
    def exec_(self):
        return self.overlayItem