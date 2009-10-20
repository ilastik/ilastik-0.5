#!/usr/bin/env python

# profile with python -m cProfile ilastikMain.py
# python -m cProfile -o profiling.prf  ilastikMain.py
# import pstats
# p = pstats.Stats('fooprof')
# p.sort_statsf('time').reverse_order().print_stats()
# possible sort order: "stdname" "calls" "time" "cumulative". more in p.sort_arg_dic


import sys
import numpy
sys.path.append("..")
import pdb
from PyQt4 import QtCore, QtGui, uic
from core import version, dataMgr, projectMgr, featureMgr, classificationMgr
from gui import ctrlRibbon, imgLabel
from PIL import Image, ImageQt
from Queue import PriorityQueue as pq
import numpy

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setGeometry(50, 50, 768, 512)
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
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Train'], QtCore.SIGNAL('clicked()'), self.classificationTrain)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Interactive'], QtCore.SIGNAL('clicked()'), self.classificationCompute)
        
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
        self.projectModified() 
        
    def editProjectDlg(self):
        if hasattr(self, 'projectDlg'):
            self.projectDlg.show()
            return
        if not hasattr(self, 'project'):
            self.newProjectDlg()
            return
        self.projectDlg = ProjectDlg(self)
        self.projectDlg.updateDlg(self.project)
        self.projectModified()
            
        
    def projectModified(self):
        self.labelWidget.updateProject(self.project)
        
    def newFeatureDlg(self):
        self.newFeatureDlg = FeatureDlg(self)
        
    def initImageWindows(self):
        self.labelDocks = []
        
    
    def createImageWindows(self):
        label_w = imgLabel.labelWidget(self, ['rgb1.jpg', 'rgb2.tif'])
        
        dock = QtGui.QDockWidget("ImageDock_main", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(label_w)
        self.labelWidget = label_w  # todo: user defined list of labelwidgets
        
        area = QtCore.Qt.BottomDockWidgetArea
        
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)
    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        self.myTimer = QtCore.QTimer()
        self.connect(self.myTimer, QtCore.SIGNAL("timeout()"), self.updateFeatureProgress)
        
        numberOfJobs = self.project.featureMgr.prepareCompute(self.project.dataMgr)  
        self.initFeatureProgress(numberOfJobs)
        self.project.featureMgr.triggerCompute()
        self.myTimer.start(200) 
        
#        featureListRib = ctrlRibbon.RibbonListItem(ctrlRibbon.RibbonEntry("featureList","", "fatureList", ctrlRibbon.RibbonListItem))
#        for f in self.project.featureMgr.featureItems:
#            featureListRib.addItem(str(f))       
#        self.ribbon.tabDict['Features'].addItem(featureListRib)
#        self.connect(self.ribbon.tabDict['Features'].itemDict['featureList'], QtCore.SIGNAL('itemDoubleClicked(QListWidgetItem)'), self.featureShow)
#        self.connect(self.ribbon.tabDict['Features'].itemDict['featureList'], QtCore.SIGNAL('itemDoubleClicked()'), self.featureShow)

    def classificationTrain(self):
        if not self.project:
            return

        shape = self.project.dataMgr.dataFeatures[0][0][0].shape
        print shape
        res_labeledFeatures = []
        res_labels = []
        res_names = []
        dataItemNr = 0
        for dataItem in self.project.dataMgr.dataFeatures:
            # todo: generalize to nD.
            # problem: feature-dimension can be higher than image-dimension.
            if dataItem[0][0].shape[0] != shape[0]:
                print "dimensions do not match, skipping dataItem."
                continue
            if dataItem[0][0].shape[1] != shape[1]:
                print "dimensions do not match, skipping dataItem."
                continue
            #todo:
            #if !self.labelWidget.hasLabels(dataItemNr):
            #    continue
            
            # get label-matrix:
            labelmatrix = numpy.ndarray(shape)
            # todo: generalize to nD.
            for pixX in xrange(shape[0]):
                print "generating labelImage: ", pixX, " / ", shape[0]
                for pixY in xrange(shape[1]):
                    labelmatrix[pixX,pixY] = self.labelWidget.getLabel(dataItemNr, [pixY,pixX])
            res_labels = labelmatrix.nonzero()
            for featureImage, featureString in dataItem:
                print featureImage
                print featureImage.shape
                # todo: fix hardcoded 2D:
                n = 1   # n: number of feature-values per pixel
                if featureImage.shape.__len__() > 2:
                    n = featureImage.shape[2]
                if n<=1:
                    res_labeledFeatures.append( featureImage[labelmatrix.nonzero()] )
                    res_names.append( featureString )
                else:
                    for featureDim in xrange(n):
                        print featureImage.shape
                        print labelmatrix.shape
                        print featureImage[:,:,featureDim].shape
                        print labelmatrix.nonzero().shape
                        res_labeledFeatures.append( (featureImage[:,:,featureDim])[labelmatrix.nonzero()] )
                        res_names.append( featureString + "_%i" %(featureDim))
            dataItemNr+=1
        trainingMatrix = numpy.concatenate( res_labeledFeatures)
        
        return
        if self.project:
            TrainingFeatureList = []    # each list entry is a feature vector for a training example.
            TrainingLabelList = []
            shape = self.project.dataMgr.dataFeatures[0][0][0].shape
            nFeatures = 0
            for featureImage, featureString in self.project.dataMgr.dataFeatures[0]:
                nFeatures += featureImage.shape.__len__()
                
            # ToDo: get label matrix from label-widget. something like that: iw.renderLabelMatrix(shape)
            # for now, use this ugly code:
            dataItemNr = 0
            for dataItem in self.project.dataMgr.dataFeatures:
                if True:  # todo:
                #if self.project. labelWidget.hasLabels(dataItemNr):
                    for pixelNr in xrange( shape[0]*shape[1] ):
                        ###pos = 
                        label = self.labelWidget.getLabel(dataItemNr, pixelNr)
                        if label > 0:
                            featureVector = numpy.ndarray( nFeatures )
                            featureNr = 0
                            for featureImage, featureString in dataItem:  # featureImage can be multi-dimensional, e.g. 3 dim for hesse-matrix
                                # todo: fix hardcoded 2D:
                                n = 1   # n: number of feature-values per pixel
                                if featureImage.shape.__len__() > 2:
                                    n = featureImage.shape[2]
                                for i in xrange( n ):
                                    if n==1:
                                        featureValues = featureImage
                                    else:
                                        featureValues = featureImage[:,:,i]
                                        featureVector[featureNr] = featureImage.flat[pixelNr]
                                featureNr+=1 
                            TrainingFeatureList.append()
                            TrainingLabelList.append(label)
            

    def initFeatureProgress(self, numberOfJobs):
        print numberOfJobs
        statusBar = self.statusBar()
        self.myFeatureProgressBar = QtGui.QProgressBar()
        self.myFeatureProgressBar.setMinimum(0)
        self.myFeatureProgressBar.setMaximum(numberOfJobs)
        self.myFeatureProgressBar.setFormat(' Features... %p%')
        statusBar.addWidget(self.myFeatureProgressBar)
        statusBar.show()
        #self.setStatusBar(self.myStatusBar)
    
    def updateFeatureProgress(self):
        val = self.project.featureMgr.getCount() 
        self.myFeatureProgressBar.setValue(val)
        if not self.project.featureMgr.featureProcess.is_alive():
            print "Alive = ", self.project.featureMgr.featureProcess.is_alive()
            self.myTimer.stop()
            print "Finished"
            self.terminateFeatureProgressBar()
            self.project.featureMgr.joinCompute(self.project.dataMgr)
            
    def terminateFeatureProgressBar(self):
        self.statusBar().removeWidget(self.myFeatureProgressBar)
        self.statusBar().hide()
        
    def featureShow(self, item):
        print "egg"
        print item
        
    def classificationCompute(self):
        if not self.ribbon.tabDict['Classification'].itemDict['Interactive'].isChecked():
            self.classificationProcess.stopped = True
            self.myTimer.stop()
            print "Classification Finished"
            self.classificationProcess.join()
            self.terminateClassificationProgressBar()
            return
                      
        self.myTimer = QtCore.QTimer()
        self.connect(self.myTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)
        
        numberOfJobs = 100
        self.initClassificationProgress(numberOfJobs)
        F = numpy.random.rand(500,10)
        L = numpy.floor(numpy.random.rand(500,1)+0.5)
        L = numpy.array(L,dtype=numpy.uint32)
        featLabelTupel = pq()
        featLabelTupel.put((F,L))
       
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, featLabelTupel)
        self.classificationProcess.start()
        self.myTimer.start(200) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Classifier... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationProcess.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationProcess.is_alive():
            self.myTimer.stop()
            print "Classification Finished"
            self.classificationProcess.join()
            self.terminateClassificationProgressBar()
            
            
                
            
    def terminateClassificationProgressBar(self):
        self.statusBar().removeWidget(self.myClassificationProgressBar)
        self.statusBar().hide()
        

class ProjectDlg(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        # this enables   self.columnPos['File']:
        self.columnPos = {}
        self.labelColor = {}
        self.parent = parent
        self.fileList = []
        self.thumbList = []        
        self.initDlg()
        self.on_cmbLabelName_currentIndexChanged(0)
        for i in xrange(self.tableWidget.columnCount()):
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
        self.on_cmbLabelName_currentIndexChanged(0)
        self.show()
        

    @QtCore.pyqtSignature("int")
    def on_cmbLabelName_currentIndexChanged(self, nr):
        nr+=1 # 0 is unlabeled !!
        self.txtLabelName.setText(self.cmbLabelName.currentText())
        #col = QtGui.QColor.fromRgb(self.labelColor.get(nr, QtGui.QColor(QtCore.Qt.red).rgb()))
        if not self.labelColor.get(nr,None):
            self.labelColor[nr] = self.labelColor[1] = QtGui.QColor(QtCore.Qt.red).rgb()  # default: red
        col = QtGui.QColor.fromRgb(self.labelColor[nr])
        self.setLabelColorButtonColor(col)

    @QtCore.pyqtSignature("")
    def on_btnAddLabel_clicked(self):
        self.cmbLabelName.addItem("label")
        self.cmbLabelName.setCurrentIndex(self.cmbLabelName.count() - 1)
        #self.on_cmbLabelName_currentIndexChanged( self.cmbLabelName.count()-1 )
        
    def setLabelColorButtonColor(self, col):
        self.btnLabelColor.setAutoFillBackground(True)
        fgcol = QtGui.QColor()
        fgcol.setRed(255 - col.red())
        fgcol.setGreen(255 - col.green())
        fgcol.setBlue(255 - col.blue())
        self.btnLabelColor.setStyleSheet("background-color: %s; color: %s" % (col.name(), fgcol.name()))

    @QtCore.pyqtSignature("") 
    def on_btnLabelColor_clicked(self):
        colordlg = QtGui.QColorDialog()
        col = colordlg.getColor()
        labelnr = self.cmbLabelName.currentIndex()+1
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
        #picture = Image.open(file_name.__str__())
        #picture.thumbnail((68, 68), Image.ANTIALIAS)
        #icon = QtGui.QPixmap.fromImage(ImageQt.ImageQt(picture))
        #self.thumbList.append(icon)
        #In Windows I get strange seg faults from time to time, sometimes the image is not displayed properly, why?
        #self.thumbnailImage.setPixmap(self.thumbList[-1])
        #picture.save('c:/test_pil.jpg')
        #print icon.save('c:/test_qt.jpg')
        pass
                    
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
        for i in xrange(self.cmbLabelName.count()):
            self.parent.project.labelNames.append(str(self.cmbLabelName.itemText(i)))
            
        
        rowCount = self.tableWidget.rowCount()
        dataItemList = []
        for k in range(0, rowCount):
            fileName = self.tableWidget.item(k, self.columnPos['File']).text()
            theDataItem = dataMgr.DataItemImage(fileName)
            dataItemList.append(theDataItem)
            
            groups = []
            for i in xrange(self.tableWidget.cellWidget(k, self.columnPos['Groups']).count()):
                groups.append(str(self.tableWidget.cellWidget(k, self.columnPos['Groups']).itemText(i)))
            theDataItem.groupMembership = groups
            
            theDataItem.hasLabels = self.tableWidget.item(k, self.columnPos['Labels']).checkState() == QtCore.Qt.Checked
            theDataItem.isTraining = self.tableWidget.item(k, self.columnPos['Train']).checkState() == QtCore.Qt.Checked
            theDataItem.isTesting = self.tableWidget.item(k, self.columnPos['Test']).checkState() == QtCore.Qt.Checked
            
            contained = False
            for pr in theDataItem.projects:
                if pr == self.parent.project:
                    contained = true
            if not contained:
                theDataItem.projects.append(self.parent.project)
            
        self.parent.project.dataMgr.setDataList(dataItemList) 
        self.parent.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.parent.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        
        self.parent.projectModified()
        
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
        self.parent.projectModified()
        
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()

        
                
            
            
            
            
            
        
                     




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow()  
    mainwindow.show()
    sys.exit(app.exec_())
