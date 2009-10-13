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

        # this enables   self.columnPos['File']:
        self.columnPos = {}        
        for i in xrange( self.tableWidget.columnCount() ):
            self.columnPos[ str(self.tableWidget.horizontalHeaderItem(i).text()) ] = i
        
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
                
                theFlag = QtCore.Qt.ItemIsEnabled
                flagON = ~theFlag | theFlag 
                flagOFF = ~theFlag
                
                # file name
                r = QtGui.QTableWidgetItem(file_name)
                self.tableWidget.setItem(0, self.columnPos['File'], r)
                
                # group
                r = QtGui.QComboBox()
                r.setEditable(True)
                self.tableWidget.setCellWidget(0, self.columnPos['Groups'], r)
                
                # labels
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Checked)
                r.setFlags(r.flags() & flagOFF);
                self.tableWidget.setItem(0, self.columnPos['Labels'], r)
                
                # train
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Checked)
                r.setFlags(r.flags() & flagON);
                self.tableWidget.setItem(0, self.columnPos['Train'], r)
                
                # test
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Checked)
                r.setFlags(r.flags() & flagON);
                self.tableWidget.setItem(0, self.columnPos['Test'], r)
                
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
            fileName = self.tableWidget.item(k, self.columnPos['File']).text()
            theDataItem = dataMgr.DataItemImage(fileName)
            dataItemList.append( theDataItem )
            
            groups = []
            for i in xrange( self.tableWidget.cellWidget(k, self.columnPos['Groups']).count() ):
                groups.append( str(self.tableWidget.cellWidget(k, self.columnPos['Groups']).itemText(i)) )
            theDataItem.groupMembership = groups
            
            theDataItem.hasLabels = self.tableWidget.item(k, self.columnPos['Labels']) == QtCore.Qt.Checked
            theDataItem.isTraining = self.tableWidget.item(k, self.columnPos['Train']) == QtCore.Qt.Checked
            theDataItem.isTesting = self.tableWidget.item(k, self.columnPos['Test']) == QtCore.Qt.Checked
            
            contained = False
            for pr in theDataItem.projects:
                if pr==self.parent.project:
                    contained = true
            if not contained:
                theDataItem.projects.append(self.parent.project)
            
        self.parent.project.setDataList(dataItemList)        
        self.close()
        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()

        
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())