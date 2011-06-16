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
from PyQt4.QtGui import QApplication, QDialog, QListWidgetItem, QWidget
from PyQt4.uic import loadUi

import ilastik
from ilastik.modules.classification.core.classifiers import classifierBase

import os

#*******************************************************************************
# C l a s s i f i e r S e l e c t i o n D l g                                  *
#*******************************************************************************

class ClassifierSelectionDlg(QDialog):
    def __init__(self, ilastikMain):
        QWidget.__init__(self, ilastikMain)
        self.setWindowTitle("Select Classifier")
        self.ilastik = ilastikMain
        self.previousClassifier = self.currentClassifier = self.ilastik.project.dataMgr.module["Classification"].classifier

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        loadUi(ilastikPath+'/modules/classification/gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, SIGNAL('pressed()'), self.classifierSettings)

        self.classifiers = classifierBase.ClassifierBase.__subclasses__()
        j = 0
        for i, c in enumerate(self.classifiers):
            #qli = QListWidgetItem(c.name)
            self.listWidget.addItem(c.name)
            if c == self.currentClassifier:
                j = i

        self.connect(self.listWidget, SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(j)

    def currentRowChanged(self, current):
        c = self.currentClassifier = self.classifiers[current]
        self.name.setText(c.name)
        self.homepage.setText(c.homepage)
        self.description.setText(c.description)
        self.author.setText(c.author)
        #check wether the plugin writer provided a settings method
        func = getattr(c, "settings", None)
        if callable(func):
            self.settingsButton.setVisible(True)
        else:
            self.settingsButton.setVisible(False)


    def classifierSettings(self):
        self.currentClassifier.settings()


    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return self.currentClassifier
        else:
            return self.previousClassifier

def test():
    #from spyderlib.utils.qthelpers import qapplication
    app = QApplication([""])

    dialog = ClassifierSelectionDlg()
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()
    test()