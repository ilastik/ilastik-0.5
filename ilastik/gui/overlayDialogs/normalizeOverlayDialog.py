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
            
    
    def __init__(self, ilastik_instance, overlay_item_ref=None):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Normalize OVerlay")
        self.ilastik = ilastik_instance
        self.selected_overlay = None
        self.project = ilastik_instance.project
        self.volumeEditor = ilastik_instance.labelWidget
        
        self.mainlayout = QtGui.QVBoxLayout()
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Overlay:'))
        self._lbl_overlay = QtGui.QLabel('no overlay selected')
        self.controls_layout.addWidget(self._lbl_overlay)
        self._btn_select_overlay = QtGui.QPushButton('Select')
        self._btn_select_overlay.clicked.connect(self.selectOverlayToNormalize)
        self.controls_layout.addWidget(self._btn_select_overlay)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Min:'))
        self._spin_min = QtGui.QSpinBox()
        self._spin_min.setMinimum(0)
        self._spin_min.setMaximum(2**16)
        self._spin_min.setValue(20)

        self.controls_layout.addWidget(self._spin_min)
        self.mainlayout.addWidget(self.controls_widget)
        
        self.controls_widget = QtGui.QWidget()
        self.controls_layout = QtGui.QHBoxLayout()
        self.controls_widget.setLayout(self.controls_layout)
        self.controls_layout.addWidget(QtGui.QLabel('Max:'))
        self._spin_max = QtGui.QSpinBox()
        self._spin_max.setMinimum(0)
        self._spin_max.setMaximum(2**16)
        self._spin_max.setValue(400)

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
        
        if overlay_item_ref is not None:
            self.selected_overlay = overlay_item_ref
            self._lbl_overlay.setText(self.selected_overlay.name)
            
    def selectOverlayToNormalize(self):
        sel_dlg = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.ilastik, singleSelection=True)
        choosen_overlay = sel_dlg.exec_()
        if choosen_overlay is not None:
            self.selected_overlay = choosen_overlay[0] 
            self._lbl_overlay.setText(self.selected_overlay.name)
       
    def okClicked(self):
        if self.selected_overlay is not None:
            self.overlayItem = NormalizeOverlay(self.selected_overlay, int(self._spin_min.value()), int(self._spin_max.value()))
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
    