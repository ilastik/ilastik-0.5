#!/usr/bin/env python
import sys
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui
from core import version
from gui import ctrlRibbon

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setGeometry(50,50,768,512)
        self.iconPath = '../../icons/32x32/'
        self.setWindowTitle("Ilastik rev: " + version.getIlastikVersion())
        self.createRibbons()
        
    def createRibbons(self):                     
      
        self.toolbar = self.addToolBar("ToolBarForRibbons")
        
        ribbon = ctrlRibbon.Ribbon()
        for ribbon_group in ctrlRibbon.createRibbons():
            tabs = ribbon_group.makeTab()   
            ribbon.addTab(tabs,ribbon_group.name)  
        self.toolbar.addWidget(ribbon)    
                     


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())