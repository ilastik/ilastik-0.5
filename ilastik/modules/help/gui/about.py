# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4 import uic
import sys, os
import webbrowser
import subprocess

class Licence(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------
        self.windowSizeWidth = 770
        self.windowSizeHeight = 440

        # widgets and layouts
        # ------------------------------------------------
        self.setWindowTitle('Licence')
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

        self.readInLicence()

        
    # methods
    # ------------------------------------------------
    def readInLicence(self):
        licenceFile = QtCore.QFile('license.txt')
        if (not licenceFile.exists()):
            self.te.append("Warning: The license file does not exist. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "The license file does not exist."
        if (not licenceFile.open(QtCore.QIODevice.ReadOnly) and licenceFile.exists()):
            self.te.append("Warning: Failed to open license file. \n Please visit the ilastik website for license informations \n http://www.ilastik.org/")
            print "Failed to open license file."
        inp = QtCore.QTextStream(licenceFile)
        while (not inp.atEnd()):
            line = inp.readLine()
            self.te.append(line)
        licenceFile.close()

class WritableObject:
    def __init__(self):
        self.content = []
    def write(self, string):
        self.content.append(string)

class About(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------
        self.setWindowTitle('About')
        
        # widgets and layouts
        # ------------------------------------------------
        self.setMinimumWidth(500)
        self.setMaximumWidth(500)
        self.setMinimumHeight(390)
        self.setMaximumHeight(390)

        background = QtGui.QLabel("", self)
        pixmap = QtGui.QPixmap("logo/ilastik-splash.png")
        background.setPixmap(pixmap)
        background.adjustSize()

        self.buildLabel = QtGui.QLabel("", self)
        self.buildLabel.move(270, 100)

        self.licenceButton = QtGui.QPushButton("License", self)
        self.connect(self.licenceButton, QtCore.SIGNAL('clicked()'), self.openLicence)
        self.licenceButton.move(190, 360)
        self.licenceButton.setMinimumWidth(150)

        self.webSiteButton = QtGui.QPushButton("Visit Website", self)
        self.connect(self.webSiteButton, QtCore.SIGNAL('clicked()'), self.openWebSite)
        self.webSiteButton.move(345, 360)
        self.webSiteButton.setMinimumWidth(150)

        self.readInBuildInfo()
    
        
    # methods
    # ------------------------------------------------
    def readInBuildInfo(self):
        buildInfo = QtCore.QFile('build.info')
        if (not buildInfo.exists()):
            self.buildLabel.setText("Build from source")
            return
        if (not buildInfo.open(QtCore.QIODevice.ReadOnly) and buildInfo.exists()):
            self.buildLabel.setText("Build is unknown")
            print "Failed to open build.info file."
            return
        inp = QtCore.QTextStream(buildInfo)
        self.buildLabel.setText("Build: " + inp.readLine())
        buildInfo.close()

    def openLicence(self):
        licence = Licence()
        licence.exec_()

    def openWebSite(self):
        webbrowser.open('http://www.ilastik.org/')
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    about = About()
    about.show()
    sys.exit(app.exec_())