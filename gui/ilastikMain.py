#!/usr/bin/env python
import sys
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui, uic
from core import version, dataMgr, projectMgr, featureMgr
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
        self.createFeatures()
        
        
    def createRibbons(self):                     
      
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.Ribbon(self.ribbonToolbar)
        for ribbon_name, ribbon_group in ctrlRibbon.createRibbons().items():
            tabs = ribbon_group.makeTab()   
            self.ribbon.addTab(tabs, ribbon_group.name)  
        self.ribbonToolbar.addWidget(self.ribbon)
        
        # Wee, this is really ugly... anybody have better ideas for connecting 
        # the signals. This way has no future and is just a workarround
        
        self.connect(self.ribbon.tabDict['Projects'].itemDict['New'], QtCore.SIGNAL('clicked()'), self.newProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Save'], QtCore.SIGNAL('clicked()'), self.saveProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Open'], QtCore.SIGNAL('clicked()'), self.loadProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Edit'], QtCore.SIGNAL('clicked()'), self.editProjectDlg)
        self.connect(self.ribbon.tabDict['Features'].itemDict['Select'], QtCore.SIGNAL('clicked()'), self.newFeatureDlg)
        self.connect(self.ribbon.tabDict['Features'].itemDict['Compute'], QtCore.SIGNAL('clicked()'), self.featureCompute)
        
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(False)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(False)
        
        #self.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(False)
        #self.ribbon.tabDict['Classification'].itemDict['Compute'].setEnabled(False)
        
        self.ribbon.setCurrentIndex (0)
        
    def newProjectDlg(self):      
        self.projectDlg = ProjectDlg(self)
    
    def saveProjectDlg(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", ".", "Project Files (*.ilp)")
        self.project.saveToDisk(str(fileName))
        
    def loadProjectDlg(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Project", ".", "Project Files (*.ilp)")
        self.project = projectMgr.Project.loadFromDisk(str(fileName))
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True) 
        
    def editProjectDlg(self):
        if hasattr(self, 'projectDlg'):
            self.projectDlg.show()
            return
        if not hasattr(self, 'project'):
            self.newProjectDlg()
            return
        self.projectDlg = ProjectDlg(self)
        self.projectDlg.updateDlg(self.project)
            
        
        
        
        
    def newFeatureDlg(self):
        self.newFeatureDlg = FeatureDlg(self)
        
    def initImageWindows(self):
        self.labelDocks = []
        
    
    def createImageWindows(self):
        label_w = imgLabel.labelWidget(self, ['rgb1.jpg','rgb2.tif'])
        
        dock = QtGui.QDockWidget("ImageDock_main", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea| QtCore.Qt.TopDockWidgetArea| QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(label_w)
        
        area = QtCore.Qt.BottomDockWidgetArea
        
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)
    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        self.project.featureMgr.triggerCompute(self.project.dataMgr)   
        featureListRib = ctrlRibbon.RibbonListItem(ctrlRibbon.RibbonEntry("featureList","", "fatureList", ctrlRibbon.RibbonListItem))
        for f in self.project.featureMgr.featureItems:
            featureListRib.addItem(str(f))       
        self.ribbon.tabDict['Features'].addItem(featureListRib)
        self.connect(self.ribbon.tabDict['Features'].itemDict['featureList'], QtCore.SIGNAL('itemDoubleClicked(QListWidgetItem)'), self.featureShow)
        self.connect(self.ribbon.tabDict['Features'].itemDict['featureList'], QtCore.SIGNAL('itemDoubleClicked()'), self.featureShow)
    def featureShow(self, item):
        print "egg"
        print item
        

class ProjectDlg(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.fileList = []
        self.thumbList = []        
        self.initDlg()
        # this enables   self.columnPos['File']:
        self.columnPos = {}
        self.labelColor = {}        
        for i in xrange( self.tableWidget.columnCount() ):
            self.columnPos[ str(self.tableWidget.horizontalHeaderItem(i).text()) ] = i
        
    def initDlg(self):
        uic.loadUi('dlgProject.ui', self) 
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.connect(self.tableWidget, QtCore.SIGNAL("cellPressed(int, int)"), self.updateThumbnail)
        self.show()
        

    @QtCore.pyqtSignature("int")
    def on_cmbLabelName_currentIndexChanged(self, nr):
        self.txtLabelName.setText( self.cmbLabelName.currentText() )
        col = QtGui.QColor.fromRgb( self.labelColor.get(nr, QtGui.QColor(QtCore.Qt.red).rgb() ) )
        self.setLabelColorButtonColor(col)

    @QtCore.pyqtSignature("")
    def on_btnAddLabel_clicked(self):
        self.cmbLabelName.addItem("label")
        self.cmbLabelName.setCurrentIndex( self.cmbLabelName.count()-1 )
        #self.on_cmbLabelName_currentIndexChanged( self.cmbLabelName.count()-1 )
        
    def setLabelColorButtonColor(self, col):
        self.btnLabelColor.setAutoFillBackground(True)
        fgcol = QtGui.QColor()
        fgcol.setRed( 255-col.red())
        fgcol.setGreen( 255-col.green())
        fgcol.setBlue( 255-col.blue())
        self.btnLabelColor.setStyleSheet("background-color: %s; color: %s" % (col.name(), fgcol.name()) )

    @QtCore.pyqtSignature("") 
    def on_btnLabelColor_clicked(self):
        colordlg = QtGui.QColorDialog()
        col = colordlg.getColor()
        labelnr = self.cmbLabelName.currentIndex()
        self.labelColor[labelnr] = col.rgb()
        self.setLabelColorButtonColor(col)
        
    @QtCore.pyqtSignature("QString")
    def on_txtLabelName_textChanged(self, text):
        self.cmbLabelName.setItemText(self.cmbLabelName.currentIndex(), text)

    @QtCore.pyqtSignature("")
    def updateDlg(self, project):
        self.projectName.setText(project.name)
        self.labeler.setText(project.labeler)
        self.description.setText(project.description)
        
        theFlag = QtCore.Qt.ItemIsEnabled
        flagON = ~theFlag | theFlag 
        flagOFF = ~theFlag
            
        for d in project.dataMgr.dataItems:
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(0)
            
            # File Name
            r = QtGui.QTableWidgetItem(d.fileName)
            self.tableWidget.setItem(0, self.columnPos['File'], r)
            
            r = QtGui.QComboBox()
            r.setEditable(True)
            self.tableWidget.setCellWidget(0, self.columnPos['Groups'], r)
            
            # Here comes the cool python "checker" use it for if_than_else in lambdas
            checker = lambda x: x and QtCore.Qt.Checked or QtCore.Qt.Unchecked
            
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(checker(d.hasLabels))
            r.setFlags(r.flags() & flagOFF);
            self.tableWidget.setItem(0, self.columnPos['Labels'], r)
            
            # train
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(checker(d.isTraining))
            r.setFlags(r.flags() & flagON);
            self.tableWidget.setItem(0, self.columnPos['Train'], r)
            
            # test
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(checker(d.isTesting))
            r.setFlags(r.flags() & flagON);
            self.tableWidget.setItem(0, self.columnPos['Test'], r)                  
        
        self.cmbLabelName.clear()
        self.labelColor = project.labelColors
        for name in project.labelNames:
            print name.__class__
            self.cmbLabelName.addItem(name)

        self.update()
        
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
        self.parent.project = projectMgr.Project(str(projectName.text()), str(labeler.text()), str(description.toPlainText()) , dataMgr.DataMgr())
        self.parent.project.labelColors = self.labelColor
        self.parent.project.labelNames = []
        for i in xrange( self.cmbLabelName.count() ):
            self.parent.project.labelNames.append( str(self.cmbLabelName.itemText(i)) )
            
        
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
            
            theDataItem.hasLabels = self.tableWidget.item(k, self.columnPos['Labels']).checkState() == QtCore.Qt.Checked
            theDataItem.isTraining = self.tableWidget.item(k, self.columnPos['Train']).checkState() == QtCore.Qt.Checked
            theDataItem.isTesting = self.tableWidget.item(k, self.columnPos['Test']).checkState() == QtCore.Qt.Checked
            
            contained = False
            for pr in theDataItem.projects:
                if pr==self.parent.project:
                    contained = true
            if not contained:
                theDataItem.projects.append(self.parent.project)
            
        self.parent.project.dataMgr.setDataList(dataItemList) 
        self.parent.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.parent.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        
        self.close()
        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()

class FeatureDlg(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.initDlg()
        
    def initDlg(self):
        uic.loadUi('dlgFeature.ui', self) 
        for featureItem in self.parent.featureList:
            self.featureList.insertItem(self.featureList.count() + 1, QtCore.QString(featureItem.__str__()))        
        self.show()
        
    @QtCore.pyqtSignature("")     
    def on_confirmButtons_accepted(self):  
        self.parent.project.featureMgr = featureMgr.FeatureMgr()

        featureSelectionList = []
        for k in range(0, self.featureList.count()):
            if self.featureList.item(k).isSelected():
                featureSelectionList.append(self.parent.featureList[k])
        self.parent.project.featureMgr.setFeatureItems(featureSelectionList)
        self.close()
        
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()

        
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())