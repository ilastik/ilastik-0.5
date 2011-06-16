#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtGui import QErrorMessage, QMessageBox

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
            QMessageBox.warning(self, "Error", "Please select more than one Overlay for thresholding - either more than one foreground overlays, or one foreground and one background overlay !")
        
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
            QErrorMessage.qtHandler().showMessage("Not enough memory !")
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
