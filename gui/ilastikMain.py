#!/usr/bin/env python
import sys
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui
from core import version

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setGeometry(50,50,768,512)
        self.iconPath = '../../icons/32x32/'
        self.setWindowTitle("Ilastik rev: " + version.getIlastikVersion())

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())