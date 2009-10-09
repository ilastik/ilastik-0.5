#!/usr/bin/env python
import sys
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui, uic
from core import version
from gui import ctrlRibbon
from gui import imgLabel
#import pythoncom

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setGeometry(50,50,768,512)
        self.iconPath = '../../icons/32x32/'
        self.setWindowTitle("Ilastik rev: " + version.getIlastikVersion())
        
        self.createRibbons()
        self.initImageWindows()
        self.createImageWindows()
        
        
    def createRibbons(self):                     
      
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.Ribbon(self.ribbonToolbar)
        for ribbon_group in ctrlRibbon.createRibbons():
            tabs = ribbon_group.makeTab()   
            self.ribbon.addTab(tabs, ribbon_group.name)  
        self.ribbonToolbar.addWidget(self.ribbon)
        
        # Wee, this is really ugly... anybody have better ideas for connecting 
        # the signals. This way has no future and is just a workarround
        self.connect(self.ribbon.tabList[0][0].itemList[0], QtCore.SIGNAL('clicked()'), self.newProjectDlg)
    
    def newProjectDlg(self):      
        self.projectDlg = ProjectDlg(self)
        
    def initImageWindows(self):
        self.labelDocks = []
    
    def createImageWindows(self):
        label_w = imgLabel.labelWidget(self, ["test.tif", "test2.tif"])
        
        dock = QtGui.QDockWidget("ImageDock_main", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea| QtCore.Qt.TopDockWidgetArea| QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(label_w)
        
        area=QtCore.Qt.BottomDockWidgetArea
        
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

class ProjectDlg():
    def __init__(self, parent=None):
        self.initDlg()
        self.parent = parent
        
    def initDlg(self):
        self.projectDlgNew = uic.loadUi('dlgProject.ui') 
        self.projectDlgNew.connect(self.projectDlgNew.addFile, QtCore.SIGNAL("clicked()"), self.addFile)
        self.projectDlgNew.show()
    
    def addFile(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self.parent, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")      
        print file_name

        rowCount = self.projectDlgNew.tableWidget.rowCount()
        self.projectDlgNew.r = []
        r = QtGui.QTableWidgetItem()
        r.setText(file_name)
        self.projectDlgNew.r.append(r)
        self.projectDlgNew.tableWidget.setItem(rowCount-1, 0, r)
        for i in range(0,3):
            print i
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(QtCore.Qt.Checked)
            self.projectDlgNew.r.append(r)
            self.projectDlgNew.tableWidget.setItem(rowCount-1, i+1, r)
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())