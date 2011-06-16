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

from PyQt4.QtGui import QColor, QColorDialog, QDialog, QErrorMessage, QFileDialog,\
                        QMessageBox
from PyQt4.uic import loadUi

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

class FileOverlayDialog(overlayDialogBase.OverlayDialogBase, QDialog):
    configuresClass = "ilastik.core.overlays.fileOverlayDialog.FileOverlayDialog"
    name = "Add File(s) Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "add a new overlay from a file"         
    
    def __init__(self, ilastik, instance = None):
        QDialog.__init__(self)
        
        self.ilastik = ilastik

        ilastikPath = os.path.dirname(ilastikModule.__file__)
        self.ui = loadUi(os.path.join(ilastikPath,"gui/overlayDialogs/fileOverlayDialog.ui"), self)
        self.ui.filenameButton.clicked.connect(self.chooseFilename)
        self.ui.colorButton.setEnabled(False)
        self.ui.customColorButton.toggled.connect(self.customColorButtonToggled)
        self.ui.grayScaleButton.setChecked(True)
        #self.ui.colorButton.setEnabled(False)
        self.ui.colorButton.clicked.connect(self.chooseColor)
        self.attrs = None                
    
    def chooseColor(self):
        initial = QColor(255,0,0)
        if self.attrs.color is not None:
            initial.fromRgba(self.attrs.color)
        self.attrs.color = QColorDialog.getColor(initial).rgba()
        self.updateColor()
    
    def customColorButtonToggled(self, checked):
        pass
        #self.ui.colorButton.setEnabled(checked)
    
    def okClicked(self):
        if len(self.overlayItem.dsets) >= 2:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please select more than one Overlay for thresholding - either more than one foreground overlays, or one foreground and one background overlay !")
    
    def updateColor(self):
        if self.attrs.color is not None:
            c = QColor()
            c.setRgba(self.attrs.color)
            self.ui.colorButton.setStyleSheet("* { background-color: rgb(%d,%d,%d) }" % (c.red(), c.green(), c.blue()));
    
    def chooseFilename(self):
        print "choose filename clicked"
        fileName = QFileDialog.getOpenFileName(self.ilastik, "Open Image", gui.LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.gif *.h5)")
        self.filenameEdit.setText(fileName)
        
        attrs = self.attrs = OverlayAttributes(str(fileName))
        
        self.ui.useColorTableFromFileButton.setEnabled(attrs.colorTable is not None)
        if(attrs.colorTable is not None):
            self.ui.useColorTableFromFileButton.setChecked(True)
       
        self.updateColor() 
       
        self.ui.nameEdit.setText(attrs.key)
        
    def exec_(self):
        if not QDialog.exec_(self):
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
            if ov is None:
                print "No _data item loaded"
    
        except Exception, e:
            traceback.print_exc()
            print e
            QErrorMessage.qtHandler().showMessage(str(e))
                    
        return None        
