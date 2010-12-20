from PyQt4 import QtCore, QtGui
import overlayDialogBase
import ilastik.gui.overlaySelectionDlg
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core import dataImpex
import ilastik.gui as gui
import traceback

class FileOverlayDialog(overlayDialogBase.OverlayDialogBase):
    configuresClass = "ilastik.core.overlays.fileOverlayDialog.FileOverlayDialog"
    name = "Add File(s) Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "add a new overlays from files"    

            
    
    def __init__(self, ilastik, instance = None):
        self.ilastik = ilastik

                    
                            
    
    def okClicked(self):
        if len(self.overlayItem.dsets) >= 2:
            self.accept()
        else:
            QtGui.QMessageBox.warning(self, "Error", "Please select more than one Overlay for thresholding - either more than one foreground overlays, or one foreground and one background overlay !")
        
    def exec_(self):
        activeItem = self.ilastik.project.dataMgr[self.ilastik._activeImageNumber]
        ovm = self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr

        #global LAST_DIRECTORY
        fileNames = QtGui.QFileDialog.getOpenFileNames(self.ilastik, "Open Image", gui.LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.gif *.h5)")
        fileNames.sort()
        if fileNames:
            for file_name in fileNames:
                gui.LAST_DIRECTORY = QtCore.QFileInfo(file_name).path()
                try:
                    file_name = str(file_name)
                    ov = dataImpex.DataImpex.importOverlay(activeItem, file_name)
                    if ov is None:
                        print "No _data item loaded"

                except Exception, e:
                    traceback.print_exc()
                    print e
                    QtGui.QErrorMessage.qtHandler().showMessage(str(e))        
        return None        
