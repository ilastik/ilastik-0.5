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

from PyQt4.QtCore import QTimer, SIGNAL
from PyQt4.QtGui import QProgressBar

#*******************************************************************************
# C C                                                                          *
#*******************************************************************************

class CC(object):
    #Connected components

    def __init__(self, parent):
        #A list of labels which denote 'background'
        #The corresponding connected components will not be displayed in 3D
        self.backgroundClasses = set()
        
        self.parent = parent
        self.ilastik = parent
        #self.start()

    def start(self, backgroundClasses):
        self.parent.ribbon.getTab('Connected Components').btnCC.setEnabled(False)
        self.parent.ribbon.getTab('Connected Components').btnCCBack.setEnabled(False)
        self.timer = QTimer()
        self.parent.connect(self.timer, SIGNAL("timeout()"), self.updateProgress)

        # call core function
        self.cc = self.parent.project.dataMgr.Connected_Components.computeResults(backgroundClasses)

        self.timer.start(200)
        self.initCCProgress()
        
    def initCCProgress(self):
        statusBar = self.parent.statusBar()
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(1)

        self.progressBar.setFormat(' Connected Components... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        if not self.cc.isRunning():
            print "finalizing connected components"
            self.timer.stop()
            self.cc.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        self.parent.project.dataMgr.Connected_Components.finalizeResults()
        
        #Update overlay with information on how to display it in 3D (if possible)
        ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Results"]
        if len(self.backgroundClasses) > 0:
            ov.displayable3D = True
            ov.backgroundClasses = set([0])
        
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
