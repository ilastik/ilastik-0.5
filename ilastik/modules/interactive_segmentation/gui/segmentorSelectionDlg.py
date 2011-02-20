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

from PyQt4 import QtCore, QtGui, uic
import sys, os


#*******************************************************************************
# S e g m e n t o r S e l e c t i o n D l g                                    *
#*******************************************************************************

class SegmentorSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastik):
        QtGui.QWidget.__init__(self, ilastik)
        self.setWindowTitle("Select Segmentation Algorithm")
        self.ilastik = ilastik
        
        self.previousSegmentor = self.currentSegmentor = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor
        
        #get the absolute path of the 'ilastik' module
        path = os.path.dirname(__file__)
        uic.loadUi(path + '/segmentorSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, QtCore.SIGNAL('pressed()'), self.segmentorSettings)

        self.segmentors = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentorClasses
        
        j = 0
        for i, c in enumerate(self.segmentors):
            print c.name
            self.listWidget.addItem(c.name)
            if c == self.currentSegmentor.__class__:
                j = i

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(j)

    def currentRowChanged(self, current):
        if self.segmentors[current] != self.previousSegmentor.__class__:
            c = self.currentSegmentor = self.segmentors[current]()
        else:
            c = self.currentSegmentor = self.previousSegmentor
        self.name.setText(c.name)
        self.homepage.setText(c.homepage)
        self.description.setText(c.description)
        self.author.setText(c.author)
        self.settingsButton.setVisible(True)


    def segmentorSettings(self):
        self.currentSegmentor.settings()


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            if self.currentSegmentor != self.previousSegmentor:
                return  self.currentSegmentor
            else:
                return None
        else:
            return None #self.previousSegmentor

def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = SegmentorSelectionDlg()
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()
