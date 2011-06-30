#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.unsupervised_decomposition.gui.guiThread import UnsupervisedDecomposition
from ilastik.modules.unsupervised_decomposition.gui.unsupervisedSelectionDlg import UnsupervisedSelectionDlg
import volumeeditor as ve

#*******************************************************************************
# U n s u p e r v i s e d T a b                                                *
#*******************************************************************************

class UnsupervisedTab(IlastikTabBase, QWidget):
    name = 'Unsupervised Decomposition'
    position = 2
    moduleName = "Unsupervised_Decomposition"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
        self.overlays = None

    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)

        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
        
        self.btnUnsupervisedOptions.setEnabled(True)     
                
    def on_deActivation(self):
        self.btnDecompose.setEnabled(False)  
            
    def _initContent(self):
        tl = QHBoxLayout()
        tl.setMargin(0)
        
        self.btnChooseOverlays      = TabButton('Select Overlay', ilastikIcons.Select)
        self.btnDecompose           = TabButton('decompose', ilastikIcons.Play)
        self.btnUnsupervisedOptions = TabButton('Unsupervised Decomposition Options', ilastikIcons.System)

        self.btnDecompose.setEnabled(False)     
        self.btnUnsupervisedOptions.setEnabled(False)     
        
        self.btnChooseOverlays.setToolTip('Choose the overlays for unsupervised decomposition')
        self.btnDecompose.setToolTip('perform unsupervised decomposition')
        self.btnUnsupervisedOptions.setToolTip('select an unsupervised decomposition plugin and change settings')
        
        tl.addWidget(self.btnChooseOverlays)
        tl.addWidget(self.btnDecompose)
        tl.addStretch()
        tl.addWidget(self.btnUnsupervisedOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseOverlays, SIGNAL('clicked()'), self.on_btnChooseOverlays_clicked)
        self.connect(self.btnDecompose, SIGNAL('clicked()'), self.on_btnDecompose_clicked)
        self.connect(self.btnUnsupervisedOptions, SIGNAL('clicked()'), self.on_btnUnsupervisedOptions_clicked)
        
    def on_btnChooseOverlays_clicked(self):
        dlg = OverlaySelectionDialog(self.parent,  singleSelection = False)
        overlays = dlg.exec_()
        
        if len(overlays) > 0:
            self.overlays = overlays
            # add all overlays
            for overlay in overlays:
                ref = overlay.getRef()
                ref.setAlpha(0.4)
                self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
                
            self.parent.labelWidget.repaint()
            self.btnDecompose.setEnabled(True)
        else:
            self.btnDecompose.setEnabled(False)         
        
    def on_btnDecompose_clicked(self):
        self.unsDec = UnsupervisedDecomposition(self.ilastik)
        self.unsDec.start(self.overlays)

    def on_btnUnsupervisedOptions_clicked(self):
        dialog = UnsupervisedSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod = answer  
