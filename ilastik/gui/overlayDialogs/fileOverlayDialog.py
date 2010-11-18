from PyQt4 import QtCore, QtGui
import overlayDialogBase
import ilastik.gui.overlaySelectionDlg
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core import dataImpex
import ilastik.gui as gui
import traceback

class FileOverlayDialog(overlayDialogBase.OverlayDialogBase):
    configuresClass = "ilastik.core.overlays.fileOverlayDialog.FileOverlayDialog"
    name = "File(s) Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "add new overlays from files"    

            
    
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

                    #theDataItem = dataMgr.DataItemImage(file_name)
                    theDataItem = dataImpex.DataImpex.importDataItem(file_name, None)
                    if theDataItem is None:
                        print "No _data item loaded"
                    else:
                        if theDataItem.shape[0:-1] == activeItem.shape[0:-1]:
                            data = theDataItem[:,:,:,:,:]
                            ov = overlayMgr.OverlayItem(activeItem, data, color = long(65535 << 16), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 255)
                            activeItem.overlayMgr["File Overlays/" + theDataItem.fileName] = ov
                        else:
                            print "Cannot add " + theDataItem.fileName + " due to dimensionality mismatch"
                        

                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    print e
                    QtGui.QErrorMessage.qtHandler().showMessage(str(e))        
        return None        
