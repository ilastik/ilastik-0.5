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
            
    
    def __init__(self, ilastik_instance, overlayItem=None):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Normalize OVerlay")
        self.ilastik = ilastik_instance
        self.selected_overlay = None
        self.project = ilastik_instance.project
        self.volumeEditor = ilastik_instance.labelWidget
        
        if overlayItem is None:
            sel_dlg = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.ilastik, singleSelection=True)
            choosen_overlay = sel_dlg.exec_()
            if choosen_overlay is not None:
                self.selected_overlay = choosen_overlay[0] 
                self.buildDlg()
                self._lbl_overlay.setText(self.selected_overlay.name)
                self._spin_min.setValue(int(self.selected_overlay._data._data.min()))
                self._spin_max.setValue(int(self.selected_overlay._data._data.max()))
                self.overlayItem = NormalizeOverlay(self.selected_overlay, int(self._spin_min.value()), int(self._spin_max.value()))
            
        else:
            self.overlayItem = overlayItem
            self.selected_overlay = overlayItem.overlay
            self.buildDlg()
            self._lbl_overlay.setText(self.overlayItem.overlay.name)
            self._spin_min.setValue(self.overlayItem.nMin)
            self._spin_max.setValue(self.overlayItem.nMax)
            
        
    def buildDlg(self):
        
        self.mainlayout = QtGui.QVBoxLayout()
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Overlay:'))
        self._lbl_overlay = QtGui.QLabel('')
        self.controls_layout.addWidget(self._lbl_overlay)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Min:'))
        self._spin_min = QtGui.QSpinBox()
        self._spin_min.setMinimum(0)
        self._spin_min.setMaximum(2**16)
        self._spin_min.setValue(0)

        self.controls_layout.addWidget(self._spin_min)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Max:'))
        self._spin_max = QtGui.QSpinBox()
        self._spin_max.setMinimum(0)
        self._spin_max.setMaximum(2**16)
        self._spin_max.setValue(255)

        self.controls_layout.addWidget(self._spin_max)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        
        self.acceptButton = QtGui.QPushButton("Ok")
        self.connect(self.acceptButton, QtCore.SIGNAL('clicked()'), self.okClicked)
        
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.acceptButton)
        self.controls_layout.addWidget(self.cancelButton)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.setLayout(self.mainlayout)
        
            
       
    def okClicked(self):
        if self.selected_overlay is not None:
            self.overlayItem.nMin = self._spin_min.value()
            self.overlayItem.nMax = self._spin_max.value()
            self.overlayItem.normalize()
            self.volumeEditor.repaint()
            self.accept()
        else:
            QtGui.QMessageBox.information(self, "Normalize Overlay", "Please choose an overlay to normalize.")
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return self.overlayItem
        else:
            return None 
    
if __name__ == "__main__":
    app = QtGui.QApplication([]) 
    dlg = NormalizeOverlayDialog('1')
    dlg.show()
    app.exec_()
    