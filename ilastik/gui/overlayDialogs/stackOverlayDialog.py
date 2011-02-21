from PyQt4 import QtGui
import os
import overlayDialogBase
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core import dataImpex
from ilastik.gui import stackloader

#*******************************************************************************
# S t a c k O v e r l a y D i a l o g                                          *
#*******************************************************************************

class StackOverlayDialog(overlayDialogBase.OverlayDialogBase):
    configuresClass = "ilastik.core.overlays.stackOverlayDialog.StackOverlayDialog"
    name = "Add Stack Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "add a new overlays from image stack"    

            
    
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

        sl = stackloader.StackLoader(self.ilastik)
        #imageData = sl.exec_()
        path, fileList, options = sl.exec_()
        if path is None:
            return
        theDataItem = None
        try:  
            theDataItem = dataImpex.DataImpex.importDataItem(fileList, options)
        except MemoryError:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough memory !")
        if theDataItem is not None:   
            # file name
            dirname = os.path.basename(os.path.dirname(path))
            offsetstr =  '(' + str(options.offsets[0]) + ', ' + str(options.offsets[1]) + ', ' + str(options.offsets[2]) + ')'
            theDataItem._name = dirname + ' ' + offsetstr
            theDataItem.fileName = path   
                
            if theDataItem.shape[0:-1] == activeItem.shape[0:-1]:
                data = theDataItem[:,:,:,:,:]
                ov = overlayMgr.OverlayItem(data, color = long(65535 << 16), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 255)
                return ov
            else:
                print "Cannot add " + theDataItem.fileName + " due to dimensionality mismatch"

        return None        
