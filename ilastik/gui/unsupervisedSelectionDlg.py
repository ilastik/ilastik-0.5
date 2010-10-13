#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, M Hanselmann, U Koethe, FA Hamprecht. All rights reserved.
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

import core.unsupervised
from core.unsupervised import *

class UnsupervisedSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastik):
        QtGui.QWidget.__init__(self, ilastik)
        self.setWindowTitle("Spectral Features")
        self.ilastik = ilastik
        self.previousUnsupervisedDecomposer = self.currentUnsupervisedDecomposer = self.ilastik.project.unsupervisedDecomposer


        #get the absolute path of the 'ilastik' module
        path = os.path.dirname(__file__)
        uic.loadUi(path + '/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, QtCore.SIGNAL('pressed()'), self.unsupervisedSettings)

        self.unsupervisedDecomposers = core.unsupervised.unsupervisedBase.UnsupervisedBase.__subclasses__()
        j = 0
        for i, c in enumerate(self.unsupervisedDecomposers):
            print c.name
            self.listWidget.addItem(c.name)
            if c == self.currentUnsupervisedDecomposer.__class__:
                j = i

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(j)

    def currentRowChanged(self, current):
        if self.unsupervisedDecomposers[current] != self.previousUnsupervisedDecomposer.__class__:
            c = self.currentUnsupervisedDecomposer = self.unsupervisedDecomposers[current]()
        else:
            c = self.currentUnsupervisedDecomposer = self.previousUnsupervisedDecomposer
        self.name.setText(c.name)
        self.homepage.setText(c.homepage)
        self.description.setText(c.description)
        self.author.setText(c.author)
        self.settingsButton.setVisible(True)


    def unsupervisedSettings(self):
        self.currentUnsupervisedDecomposer.settings()


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            if self.currentUnsupervisedDecomposer != self.previousUnsupervisedDecomposer:
                return  self.currentUnsupervisedDecomposer
            else:
                return None
        else:
            return None #self.previousSegmentor

def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = UnsupervisedSelectionDlg()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
