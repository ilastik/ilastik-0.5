# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
import sys
import webbrowser
from ilastik.core import readInBuildInfo


#*******************************************************************************
# L i c e n s e                                                                *
#*******************************************************************************

class License(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

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
        
        self.te = QtGui.QTextEdit(self)
        self.te.setReadOnly(True)
        self.te.setMinimumWidth(self.windowSizeWidth)
        self.te.setMaximumWidth(self.windowSizeWidth)
        self.te.setMinimumHeight(self.windowSizeHeight)
        self.te.setMaximumHeight(self.windowSizeHeight)

        self.readInLicense()

        
    # methods
    # ------------------------------------------------
    def readInLicense(self):
        licenseFile = QtCore.QFile('license.txt')
        if (not licenseFile.exists()):
            self.te.append("Warning: The license file does not exist. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "The license file does not exist."
        if (not licenseFile.open(QtCore.QIODevice.ReadOnly) and licenseFile.exists()):
            self.te.append("Warning: Failed to open license file. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "Failed to open license file."
        inp = QtCore.QTextStream(licenseFile)
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

class About(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------
        self.buttonsMinimumWidth = 150
        self.buttonsMaximumWidth = 150
        
        # widgets and layouts
        # ------------------------------------------------
        self.setWindowTitle('About')

        background = QtGui.QLabel("", self)
        pixmap = QtGui.QPixmap("ilastik/gui/logos/ilastik-splash.png")
        background.setPixmap(pixmap)
        background.adjustSize()

        self.setMinimumWidth(pixmap.size().width())
        self.setMaximumWidth(pixmap.size().width())
        self.setMinimumHeight(pixmap.size().height() + 30)
        self.setMaximumHeight(pixmap.size().height() + 30)

        self.buildLabel = QtGui.QLabel("", self)
        self.buildLabel.move(270, 100)

        self.licenseButton = QtGui.QPushButton("License", self)
        self.connect(self.licenseButton, QtCore.SIGNAL('clicked()'), self.openLicense)
        self.licenseButton.setMinimumWidth(self.buttonsMinimumWidth)
        self.licenseButton.setMaximumWidth(self.buttonsMaximumWidth)
        self.licenseButton.move(pixmap.size().width() - self.buttonsMinimumWidth* 2 -8, pixmap.size().height() + 4)

        self.webSiteButton = QtGui.QPushButton("Visit Website", self)
        self.connect(self.webSiteButton, QtCore.SIGNAL('clicked()'), self.openWebSite)
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
    app = QtGui.QApplication(sys.argv)
    about = About()
    about.show()
    sys.exit(app.exec_())