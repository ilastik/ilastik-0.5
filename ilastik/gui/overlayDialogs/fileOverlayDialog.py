from PyQt4 import QtCore, QtGui, uic
import overlayDialogBase
import ilastik as ilastikModule
from ilastik.core import dataImpex
from ilastik.core.overlayAttributes import OverlayAttributes
from ilastik.core.overlayMgr import OverlayItem
import ilastik.gui as gui
import traceback, os

#*******************************************************************************
# F i l e O v e r l a y D i a l o g                                            *
#*******************************************************************************

class FileOverlayDialog(overlayDialogBase.OverlayDialogBase, QtGui.QDialog):
    configuresClass = "ilastik.core.overlays.fileOverlayDialog.FileOverlayDialog"
    name = "Add File(s) Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "add a new overlay from a file"         
    
    def __init__(self, ilastik, instance = None):
        QtGui.QDialog.__init__(self)
        
        self.ilastik = ilastik

        ilastikPath = os.path.dirname(ilastikModule.__file__)
        self.ui = uic.loadUi(os.path.join(ilastikPath,"gui/overlayDialogs/fileOverlayDialog.ui"), self)
        self.ui.filenameButton.clicked.connect(self.chooseFilename)
        self.ui.colorButton.setEnabled(False)
        self.ui.customColorButton.toggled.connect(self.customColorButtonToggled)
        self.ui.grayScaleButton.setChecked(True)
        #self.ui.colorButton.setEnabled(False)
        self.ui.colorButton.clicked.connect(self.chooseColor)
        self.attrs = None                
    
    def chooseColor(self):
        initial = QtGui.QColor(255,0,0)
        if self.attrs.color is not None:
            initial.fromRgba(self.attrs.color)
        self.attrs.color = QtGui.QColorDialog.getColor(initial).rgba()
        self.updateColor()
    
    def customColorButtonToggled(self, checked):
        pass
        #self.ui.colorButton.setEnabled(checked)
    
    def okClicked(self):
        if len(self.overlayItem.dsets) >= 2:
            self.accept()
        else:
            QtGui.QMessageBox.warning(self, "Error", "Please select more than one Overlay for thresholding - either more than one foreground overlays, or one foreground and one background overlay !")
    
    def updateColor(self):
        if self.attrs.color is not None:
            c = QtGui.QColor()
            c.setRgba(self.attrs.color)
            self.ui.colorButton.setStyleSheet("* { background-color: rgb(%d,%d,%d) }" % (c.red(), c.green(), c.blue()));
    
    def chooseFilename(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self.ilastik, "Open Overlay", gui.LAST_DIRECTORY, "Overlay files(*.h5)")
        self.filenameEdit.setText(fileName)
        
        try:
            attrs = self.attrs = OverlayAttributes(str(fileName))
            
            self.ui.useColorTableFromFileButton.setEnabled(attrs.colorTable is not None)
            if(attrs.colorTable is not None):
                self.ui.useColorTableFromFileButton.setChecked(True)
           
            self.updateColor() 
           
            self.ui.nameEdit.setText(attrs.key)
        except:
            QtGui.QMessageBox.warning(self, 'Open Overlay', 'Selected file is not a valid Overlay File.')
        
    def exec_(self):
        if not QtGui.QDialog.exec_(self):
            return
        
        activeItem = self.ilastik.project.dataMgr[self.ilastik._activeImageNumber]
        ovm = self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr

        try:
            file_name = str(self.ui.filenameEdit.text())
            
            if self.ui.randomColorsButton.isChecked():
                transparentValues = set()
                if self.ui.valueZeroTransparentCheck.isChecked():
                    transparentValues.add(0)
                self.attrs.colorTable = OverlayItem.createDefaultColorTable("RGB", transparentValues=transparentValues)
            elif self.ui.grayScaleButton.isChecked():
                self.attrs.colorTable = OverlayItem.createDefaultColorTable("GRAY")
            self.attrs.key = str(self.ui.nameEdit.text())
            
            ov = dataImpex.DataImpex.importOverlay(activeItem, file_name, attrs=self.attrs)
            ov.displayable3D = True
            if ov is None:
                print "No data item loaded"
    
        except Exception, e:
            traceback.print_exc()
            print e
            QtGui.QErrorMessage.qtHandler().showMessage(str(e))
                    
        return None        
