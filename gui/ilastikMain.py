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
        
        area = QtCore.Qt.BottomDockWidgetArea
        
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

class ProjectDlg(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.fileList = []
        self.thumbList = []        
        self.initDlg()
        
    def initDlg(self):
        uic.loadUi('dlgProject.ui', self) 
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setColumnWidth(0,350)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        
#        self.connect(self.addFile, QtCore.SIGNAL("clicked()"), self.addFile)
#        self.connect(self.confirmButtons, QtCore.SIGNAL("accepted()"), self.accept)
#        self.connect(self.confirmButtons, QtCore.SIGNAL("rejected()"), self.reject)
        self.connect(self.tableWidget, QtCore.SIGNAL("cellPressed(int, int)"), self.updateThumbnail)
        
        # Still have to beautify a bit with sth like that 
#        self.filesTable.setHorizontalHeaderLabels(labels)
#        self.filesTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
#        self.filesTable.verticalHeader().hide()
#        self.filesTable.setShowGrid(False)
        self.show()
        

    @QtCore.pyqtSignature("")
    def on_addFile_clicked(self):
        
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", ".", "Image Files (*.png *.jpg *.bmp *.tif)")    
        if fileNames:
            for file_name in fileNames:
                self.fileList.append(file_name)
                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(0)
                r = QtGui.QTableWidgetItem(file_name)
                self.tableWidget.setItem(0, 0, r)
                for i in range(0,4):
                    r = QtGui.QTableWidgetItem()
                    r.data(QtCore.Qt.CheckStateRole)
                    r.setCheckState(QtCore.Qt.Checked)
                    self.tableWidget.setItem(0, i+1, r)
                self.initThumbnail(file_name)
    
    def initThumbnail(self, file_name):
        picture = Image.open(file_name.__str__())
        picture.thumbnail((68, 68), Image.ANTIALIAS)
        w,h = picture.size
        print "Thumbnail size = ", w, " width and ", h ," height"
        icon = QtGui.QPixmap.fromImage(ImageQt.ImageQt(picture))
        self.thumbList.append(icon)
        #In Windows I get strange seg faults from time to time, sometimes the image is not displayed properly, why?
        #self.thumbnailImage.setPixmap(self.thumbList[-1])
                    
    def updateThumbnail(self, row=0, col=0):
        #In Windows I get strange seg faults from time to time, sometimes the image is not displayed properly, why?
        #self.thumbnailImage.clear()
        #self.thumbnailImage.setPixmap(self.thumbList[-row-1]) 
        pass
    
    @QtCore.pyqtSignature("")     
    def on_confirmButtons_accepted(self):
        projectName = self.projectName
        labeler = self.labeler
        description = self.description
        self.parent.project = projectMgr.Project(projectName, labeler, description,[])
        
        rowCount = self.tableWidget.rowCount()
        dataItemList = []
        for k in range(0, rowCount):
            fileName = self.tableWidget.itemAt(k, 0).text()
            dataItemList.append(dataMgr.DataItemImage(fileName))     
        self.parent = dataItemList        
        self.close()
        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()

        
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())