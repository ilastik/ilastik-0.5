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
from PyQt4.QtGui import QHBoxLayout, QPushButton, QWidget
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

#*******************************************************************************
# H e l p T a b                                                                *
#*******************************************************************************

class HelpTab(IlastikTabBase, QWidget):
    name = 'Example'  #the name of your ribbon
    position = 101    #the position in the tabbar
    moduleName = "Example"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        print 'Changed to Tab: ', self.__class__.name
        
        """
        you can create some default overlays here 
        or set up your own labelWidget for the VolumeEditor
        that can handle user given pixel labels in any
        way
        """
       
    def on_deActivation(self):
        print 'Left Tab ', self.__class__.name
        
    def _initContent(self):
        tl = QHBoxLayout()
        tl.setMargin(0)
        
        self.btnExample = QPushButton('Example')
      
        self.btnExample.setToolTip('Example button')
        
        tl.addWidget(self.btnShortcuts)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        
    def _initConnects(self):
        self.connect(self.btnExample, SIGNAL('clicked()'), self.on_btnExample_clicked)
        
    def on_btnShortcuts_clicked(self):
        """
        do some interesting things here
        """