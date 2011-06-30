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

from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QHBoxLayout, QWidget

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.modules.classification.gui import *
from ilastik.modules.classification.gui.batchProcessDlg import BatchProcess

import volumeeditor as ve

#*******************************************************************************
# A u t o m a t e T a b                                                        *
#*******************************************************************************

class AutomateTab(IlastikTabBase, QWidget):
    name = 'Automate'
    position = 100
    moduleName = "Classification"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
    
    def on_activation(self):
        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        overlayWidget.setVisible(False)
        
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
                                
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        tl = QHBoxLayout()
        tl.setMargin(0)
        
        self.btnBatchProcess = TabButton('Batch Process', ilastikIcons.Play)
       
        self.btnBatchProcess.setToolTip('Select and batch predict files with the currently trained classifier')
        tl.addWidget(self.btnBatchProcess)
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnBatchProcess, SIGNAL('clicked()'), self.on_btnBatchProcess_clicked)
        
    def on_btnBatchProcess_clicked(self): 
        dialog = BatchProcess(self.parent)
        dialog.exec_()