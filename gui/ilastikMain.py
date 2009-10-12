#!/usr/bin/env python
import sys
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui, uic
from core import version, dataMgr, projectMgr
from gui import ctrlRibbon, imgLabel
from PIL import Image, ImageQt


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
        self.parent = parent
        self.fileList = []
        self.thumbList = []        
        self.initDlg()
        
    def initDlg(self):
        self.projectDlgNew = uic.loadUi('dlgProject.ui') 
        self.projectDlgNew.tableWidget.resizeRowsToContents()
        self.projectDlgNew.tableWidget.resizeColumnsToContents()
        self.projectDlgNew.tableWidget.setColumnWidth(0,350)
        self.projectDlgNew.tableWidget.setAlternatingRowColors(True)
        self.projectDlgNew.tableWidget.setShowGrid(False)
        
        self.projectDlgNew.connect(self.projectDlgNew.addFile, QtCore.SIGNAL("clicked()"), self.addFile)
        self.projectDlgNew.connect(self.projectDlgNew.confirmButtons, QtCore.SIGNAL("accepted()"), self.accept)
        self.projectDlgNew.connect(self.projectDlgNew.confirmButtons, QtCore.SIGNAL("rejected()"), self.reject)
        self.projectDlgNew.connect(self.projectDlgNew.tableWidget, QtCore.SIGNAL("cellPressed(int, int)"), self.updateThumbnail)
        
        
        self.projectDlgNew.fileDialog = QtGui.QFileDialog()
        self.projectDlgNew.show()
        

    
    def addFile(self):
        
        file_name = self.projectDlgNew.fileDialog.getOpenFileName(self.parent, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")    
        if file_name:
            self.fileList.append(file_name)
            rowCount = self.projectDlgNew.tableWidget.rowCount()
            self.projectDlgNew.tableWidget.insertRow(0)
            self.projectDlgNew.r = []
            r = QtGui.QTableWidgetItem()
            r.setText(file_name)
            self.projectDlgNew.r.append(r)
            self.projectDlgNew.tableWidget.setItem(0, 0, r)
            for i in range(0,4):
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Checked)
                self.projectDlgNew.r.append(r)
                self.projectDlgNew.tableWidget.setItem(0, i+1, r)
            self.initThumbnail(file_name)
    
    def initThumbnail(self, file_name):
        picture = Image.open(file_name.__str__())
        picture.thumbnail((68, 68), Image.ANTIALIAS)
        w,h = picture.size
        print "Thumbnail size = ", w, " width and ", h ," height"
        icon = QtGui.QPixmap.fromImage(ImageQt.ImageQt(picture))
        self.thumbList.append(icon)
        #In Windows I get strange seg faults from time to time, sometimes the image is not displayed properly, why?
        # self.projectDlgNew.thumbnailImage.setPixmap(self.thumbList[-1])
                    
    def updateThumbnail(self, row=0, col=0):
        #In Windows I get strange seg faults from time to time, sometimes the image is not displayed properly, why?
#        self.projectDlgNew.thumbnailImage.clear()
#        self.projectDlgNew.thumbnailImage.setPixmap(self.thumbList[-row-1])  
                
    def accept(self):
        projectName = self.projectDlgNew.projectName
        labeler = self.projectDlgNew.labeler
        description = self.projectDlgNew.description
        self.parent.project = projectMgr.Project(projectName, labeler, description,[])
        
        rowCount = self.projectDlgNew.tableWidget.rowCount()
        dataItemList = []
        for k in range(0, rowCount):
            fileName = self.projectDlgNew.tableWidget.itemAt(k, 0).text()
            dataItemList.append(dataMgr.DataItemImage(fileName))             
        self.projectDlgNew.close()
        return dataItemList
        
    def reject(self):
        self.projectDlgNew.close()

        
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())