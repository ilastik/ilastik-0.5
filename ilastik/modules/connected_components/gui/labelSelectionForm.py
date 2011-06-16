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

from PyQt4.QtCore import QString, SIGNAL
from PyQt4.QtGui import QDialog, QHBoxLayout, QIntValidator, QLabel, QLineEdit,\
                        QListWidget, QPushButton, QVBoxLayout, QWidget

#*******************************************************************************
# L a b e l S e l e c t i o n F o r m                                          *
#*******************************************************************************

class LabelSelectionForm(QDialog):
    def __init__(self, parent = None, desc_names = None):
        QWidget.__init__(self, parent)
        self.setWindowTitle('Select the synapse label, used in prediction')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.descList = QListWidget()
        for i, d in enumerate(desc_names):
            self.descList.insertItem(i, d)
        self.layout.addWidget(self.descList)
        tempLayout = QHBoxLayout()
        self.qiv = QIntValidator(100, 1000000, self)
        self.minsize = QLineEdit(QString("1000"))
        self.minsize.setValidator(self.qiv)
        self.minsize.setToolTip("Minimal synapse size in pixels")
        tempLayout.addWidget(QLabel("Min. size"))
        tempLayout.addWidget(self.minsize)
        self.maxsize = QLineEdit(QString("250000"))
        self.maxsize.setValidator(self.qiv)
        self.maxsize.setToolTip("Maximal synapse size in pixels")
        tempLayout.addWidget(QLabel("Max. size"))
        tempLayout.addWidget(self.maxsize)
        self.layout.addLayout(tempLayout)
        tempLayout = QHBoxLayout()
        self.ok_btn = QPushButton("ok")
        self.connect(self.ok_btn, SIGNAL('clicked()'), self.ok_btn_clicked)
        self.cancel_btn = QPushButton("cancel")
        self.connect(self.cancel_btn, SIGNAL('clicked()'), self.cancel_btn_clicked)
        tempLayout.addWidget(self.ok_btn)
        tempLayout.addWidget(self.cancel_btn)
        self.layout.addLayout(tempLayout)
    
    def ok_btn_clicked(self):
        self.accept()
    def cancel_btn_clicked(self):
        self.close()
        
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            chosen = self.descList.selectedItems()
            if chosen is not None:
                return chosen[0].text(), int(self.minsize.text()), int(self.maxsize.text())
            else:
                print "No label selected!"
                return None, None, None
        else:
            return None, None, None
        
        