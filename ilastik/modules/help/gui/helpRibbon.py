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

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.shortcutmanager import shortcutManager
import volumeeditor as ve
from ilastik.modules.help.gui.about import About

#*******************************************************************************
# H e l p T a b                                                                *
#*******************************************************************************

class HelpTab(IlastikTabBase, QWidget):
    name = 'Help'
    position = 101
    moduleName = "Help"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        overlayWidget.setVisible(False)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
               
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        tl = QHBoxLayout()
        tl.setMargin(0)
        
        self.btnShortcuts = TabButton('Shortcuts', ilastikIcons.Help)
        self.btnAbout     = TabButton('About', ilastikIcons.Ilastik)
      
        self.btnShortcuts.setToolTip('Show a list of ilastik shortcuts')
        
        tl.addWidget(self.btnShortcuts)
        tl.addWidget(self.btnAbout)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        
    def _initConnects(self):
        self.connect(self.btnShortcuts, SIGNAL('clicked()'), self.on_btnShortcuts_clicked)
        self.connect(self.btnAbout, SIGNAL('clicked()'), self.on_btnAbout_clicked)
        
    def on_btnShortcuts_clicked(self):
        shortcutManager.showDialog(self.ilastik)

    def on_btnAbout_clicked(self):
        about = About(self.ilastik)
        about.show()