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

from PyQt4.QtCore import QFile, QIODevice, QTextStream, SIGNAL
from PyQt4.QtGui import QApplication, QDialog, QLabel, QPixmap, QPushButton,\
                        QTextEdit

import sys
import webbrowser
from ilastik.core import readInBuildInfo

#*******************************************************************************
# L i c e n s e                                                                *
#*******************************************************************************

class License(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------
        self.windowSizeWidth = 770
        self.windowSizeHeight = 440

        # widgets and layouts
        # ------------------------------------------------
        self.setWindowTitle('License')
        self.setMinimumWidth(self.windowSizeWidth)
        self.setMaximumWidth(self.windowSizeWidth)
        self.setMinimumHeight(self.windowSizeHeight)
        self.setMaximumHeight(self.windowSizeHeight)
        
        self.te = QTextEdit(self)
        self.te.setReadOnly(True)
        self.te.setMinimumWidth(self.windowSizeWidth)
        self.te.setMaximumWidth(self.windowSizeWidth)
        self.te.setMinimumHeight(self.windowSizeHeight)
        self.te.setMaximumHeight(self.windowSizeHeight)

        self.readInLicense()

        
    # methods
    # ------------------------------------------------
    def readInLicense(self):
        licenseFile = QFile('license.txt')
        if (not licenseFile.exists()):
            self.te.append("Warning: The license file does not exist. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "The license file does not exist."
        if (not licenseFile.open(QIODevice.ReadOnly) and licenseFile.exists()):
            self.te.append("Warning: Failed to open license file. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "Failed to open license file."
        inp = QTextStream(licenseFile)
        while (not inp.atEnd()):
            line = inp.readLine()
            self.te.append(line)
        licenseFile.close()

#*******************************************************************************
# W r i t a b l e O b j e c t                                                  *
#*******************************************************************************

class WritableObject:
    def __init__(self):
        self.content = []
    def write(self, string):
        self.content.append(string)

#*******************************************************************************
# A b o u t                                                                    *
#*******************************************************************************

class About(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------
        self.buttonsMinimumWidth = 150
        self.buttonsMaximumWidth = 150
        
        # widgets and layouts
        # ------------------------------------------------
        self.setWindowTitle('About')

        background = QLabel("", self)
        pixmap = QPixmap("ilastik/gui/logos/ilastik-splash.png")
        background.setPixmap(pixmap)
        background.adjustSize()

        self.setMinimumWidth(pixmap.size().width())
        self.setMaximumWidth(pixmap.size().width())
        self.setMinimumHeight(pixmap.size().height() + 30)
        self.setMaximumHeight(pixmap.size().height() + 30)

        self.buildLabel = QLabel("", self)
        self.buildLabel.move(270, 100)

        self.licenseButton = QPushButton("License", self)
        self.connect(self.licenseButton, SIGNAL('clicked()'), self.openLicense)
        self.licenseButton.setMinimumWidth(self.buttonsMinimumWidth)
        self.licenseButton.setMaximumWidth(self.buttonsMaximumWidth)
        self.licenseButton.move(pixmap.size().width() - self.buttonsMinimumWidth* 2 -8, pixmap.size().height() + 4)

        self.webSiteButton = QPushButton("Visit Website", self)
        self.connect(self.webSiteButton, SIGNAL('clicked()'), self.openWebSite)
        self.webSiteButton.setMinimumWidth(self.buttonsMinimumWidth)
        self.webSiteButton.setMaximumWidth(self.buttonsMaximumWidth)
        self.webSiteButton.move(pixmap.size().width() - self.buttonsMinimumWidth -4, pixmap.size().height() + 4)

        self.buildLabel.setText(readInBuildInfo())
    
        
    # methods
    # ------------------------------------------------

    def openLicense(self):
        license = License(self)
        license.exec_()

    def openWebSite(self):
        webbrowser.open('http://www.ilastik.org/')
        
#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    app = QApplication(sys.argv)
    about = About()
    about.show()
    sys.exit(app.exec_())