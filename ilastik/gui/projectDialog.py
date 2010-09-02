from PyQt4 import QtCore, QtGui, uic
from ilastik.core import  dataMgr, projectMgr, dataImpex
import ilastik.gui
from ilastik.gui import stackloader, fileloader
import os, sys
import traceback

class ProjectDlg(QtGui.QDialog):
    def __init__(self, parent=None, newProject = True):
        QtGui.QWidget.__init__(self, parent)
        
        self.ilastik = parent
        self.newProject = newProject

        self.labelCounter = 2
        self.columnPos = {}
        self.labelColor = { 1:QtGui.QColor(QtCore.Qt.red), 2:QtGui.QColor(QtCore.Qt.green), 3:QtGui.QColor(QtCore.Qt.yellow), 4:QtGui.QColor(QtCore.Qt.blue), 5:QtGui.QColor(QtCore.Qt.magenta) , 6:QtGui.QColor(QtCore.Qt.darkYellow), 7:QtGui.QColor(QtCore.Qt.lightGray) }
        self.parent = parent
        self.fileList = []
        self.thumbList = []        
        self.initDlg()
        for i in xrange(self.tableWidget.columnCount()):
            self.columnPos[ str(self.tableWidget.horizontalHeaderItem(i).text()) ] = i
        self.defaultLabelColors = {}

        projectName = self.projectName
        labeler = self.labeler
        description = self.description

        # New project or edited project? if edited, reuse parts of old dataMgr
        if hasattr(self.ilastik,'project') and (not self.newProject):
            self.dataMgr = self.ilastik.project.dataMgr
            self.project = self.ilastik.project
        else:
            if self.ilastik.featureCache is not None:
                if 'tempF' in self.ilastik.featureCache.keys():
                    grp = self.ilastik.featureCache['tempF']
                else:
                    grp = self.ilastik.featureCache.create_group('tempF')
            else:
                grp = None
            self.dataMgr = dataMgr.DataMgr(grp)
            self.project = self.ilastik.project = projectMgr.Project(str(projectName.text()), str(labeler.text()), str(description.toPlainText()) , self.dataMgr)
                    
    def initDlg(self):
        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(__file__)
        uic.loadUi(os.path.join(ilastikPath,"dlgProject.ui"), self) 
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.connect(self.tableWidget, QtCore.SIGNAL("cellPressed(int, int)"), self.updateThumbnail)

        



    @QtCore.pyqtSignature("")
    def updateDlg(self, project):
        self.project = project
        self.dataMgr = project.dataMgr        
        self.projectName.setText(project.name)
        self.labeler.setText(project.labeler)
        self.description.setText(project.description)
        
        theFlag = QtCore.Qt.ItemIsEnabled
        flagON = ~theFlag | theFlag 
        flagOFF = ~theFlag
            
        for d in project.dataMgr.dataItems:
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            # File Name
            r = QtGui.QTableWidgetItem(d.fileName)
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
                       
            # Here comes the cool python "checker" use it for if_than_else in lambdas
            checker = lambda x: x and QtCore.Qt.Checked or QtCore.Qt.Unchecked
            
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(checker(d.dataVol.labels.data != None))
            #r.setFlags(r.flags() & flagOFF);
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
            
               
        self.exec_()


    @QtCore.pyqtSignature("")     
    def on_loadStack_clicked(self):
        sl = stackloader.StackLoader()
        #imageData = sl.exec_()
        sl.exec_()
        theDataItem = None
        try:  
            theDataItem = dataImpex.DataImpex.importDataItem(sl.fileList, sl.options)
        except MemoryError:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough memory, please select a smaller Subvolume. Much smaller !! since you may also want to calculate some features...")
        if theDataItem is not None:   
            # file name
            path = str(sl.path.text())
            dirname = os.path.basename(os.path.dirname(path))
            offsetstr =  '(' + str(sl.options.offsets[0]) + ', ' + str(sl.options.offsets[1]) + ', ' + str(sl.options.offsets[2]) + ')'
            theDataItem.Name = dirname + ' ' + offsetstr   
            #theDataItem = dataMgr.DataItemImage.initFromArray(imageData, dirname + ' ' +offsetstr)
            try:
                print theDataItem.dataVol.labels
                self.dataMgr.append(theDataItem, True)
                print theDataItem.dataVol.labels
                self.dataMgr.dataItemsLoaded[-1] = True
                print theDataItem.dataVol.labels

                theDataItem.hasLabels = True
                theDataItem.isTraining = True
                theDataItem.isTesting = True

                #self.ilastik.ribbon.getTab('Projects').btnEdit.setEnabled(True)
                #self.ilastik.ribbon.getTab('Projects').btnOptions.setEnabled(True)
                #self.ilastik.ribbon.getTab('Projects').btnSave.setEnabled(True)

                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)
                print theDataItem.dataVol.labels

                theFlag = QtCore.Qt.ItemIsEnabled
                flagON = ~theFlag | theFlag
                flagOFF = ~theFlag
               
                r = QtGui.QTableWidgetItem('Stack at ' + path + ', offsets: ' + offsetstr)
                self.tableWidget.setItem(rowCount, self.columnPos['File'], r)

                # labels
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Unchecked)

                self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
                print theDataItem.dataVol.labels
                
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
                QtGui.QErrorMessage.qtHandler().showMessage(str(e))
            
    
    @QtCore.pyqtSignature("")
    def on_loadFileButton_clicked(self):
        fl = fileloader.FileLoader()
        #imageData = sl.exec_()
        fl.exec_()
        itemList = []
        try:
            itemList = dataImpex.DataImpex.importDataItems(fl.fileList, fl.options)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print e
            QtGui.QErrorMessage.qtHandler().showMessage(str(e))
        for index, item in enumerate(itemList):
            self.dataMgr.append(item, True)
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)

            theFlag = QtCore.Qt.ItemIsEnabled
            flagON = ~theFlag | theFlag
            flagOFF = ~theFlag

            # file name
            r = QtGui.QTableWidgetItem(fl.fileList[fl.options.channels[0]][index])
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(QtCore.Qt.Checked)


            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)

            self.initThumbnail(fl.fileList[fl.options.channels[0]][index])
            self.tableWidget.setCurrentCell(0, 0)

    @QtCore.pyqtSignature("")     
    def on_addFile_clicked(self):
        #global LAST_DIRECTORY
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", ilastik.gui.LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.gif *.h5)")
        fileNames.sort()
        if fileNames:
            for file_name in fileNames:
                ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(file_name).path()
                try:
                    file_name = str(file_name)

                    #theDataItem = dataMgr.DataItemImage(file_name)
                    theDataItem = dataImpex.DataImpex.importDataItem(file_name, None)
                    if theDataItem is None:
                        print "No data item loaded"
                    self.dataMgr.append(theDataItem, True)
                    #self.dataMgr.dataItemsLoaded[-1] = True

                    rowCount = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(rowCount)

                    theFlag = QtCore.Qt.ItemIsEnabled
                    flagON = ~theFlag | theFlag
                    flagOFF = ~theFlag

                    # file name
                    r = QtGui.QTableWidgetItem(file_name)
                    self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
                    # labels
                    r = QtGui.QTableWidgetItem()
                    r.data(QtCore.Qt.CheckStateRole)
                    r.setCheckState(QtCore.Qt.Checked)


                    self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)

                    self.initThumbnail(file_name)
                    self.tableWidget.setCurrentCell(0, 0)
                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    print e
                    QtGui.QErrorMessage.qtHandler().showMessage(str(e))

                    
    @QtCore.pyqtSignature("")   
    def on_removeFile_clicked(self):
        # Get row and fileName to remove
        row = self.tableWidget.currentRow()
        fileName = str(self.tableWidget.item(row, self.columnPos['File']).text())
        print "remvoe Filename in row: ", fileName, " -- ", row
        self.dataMgr.remove(row)
        print "Remove loaded File"

        # Remove Row from display Table
        
        self.tableWidget.removeRow(row)
        try:
            del self.thumbList[row]
        except IndexError:
            pass
        
        
        
    def initThumbnail(self, file_name):
        thumb = QtGui.QPixmap(str(file_name))
        thumb = thumb.scaledToWidth(128)
        self.thumbList.append(thumb)
        self.thumbnailImage.setPixmap(self.thumbList[0])
                    
    def updateThumbnail(self, row=0, col=0):
        try:
            self.thumbnailImage.setPixmap(self.thumbList[row]) 
        except IndexError:
            pass
    
    @QtCore.pyqtSignature("")     
    def on_confirmButtons_accepted(self):
        projectName = self.projectName
        labeler = self.labeler
        description = self.description
               
        self.parent.project = projectMgr.Project(str(projectName.text()), str(labeler.text()), str(description.toPlainText()) , self.dataMgr)

            
        # Go through the rows of the table and add files if needed
        rowCount = self.tableWidget.rowCount()
               
        for k in range(0, rowCount):               
            theDataItem = self.dataMgr[k]
            
            theDataItem.hasLabels = self.tableWidget.item(k, self.columnPos['Labels']).checkState() == QtCore.Qt.Checked
            if theDataItem.hasLabels == False:
                theDataItem.dataVol.labels.clear()
                
            contained = False
            for pr in theDataItem.projects:
                if pr == self.parent.project:
                    contained = True
            if not contained:
                theDataItem.projects.append(self.parent.project)
        
        self.accept()

        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.reject() 


        
class ProjectSettingsDlg(QtGui.QDialog):
    def __init__(self, ilastik = None, project=None):
        QtGui.QWidget.__init__(self, ilastik)

        self.project = project
        self.ilastik = ilastik


        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.drawUpdateIntervalCheckbox = QtGui.QCheckBox("Train&Predict during brush strokes in Interactive Mode")
        self.drawUpdateIntervalCheckbox.setCheckState((self.project.drawUpdateInterval > 0)  * 2)
        self.connect(self.drawUpdateIntervalCheckbox, QtCore.SIGNAL("stateChanged(int)"), self.toggleUpdateInterval)
        self.layout.addWidget(self.drawUpdateIntervalCheckbox)

        self.drawUpdateIntervalFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.drawUpdateIntervalSpin = QtGui.QSpinBox()
        self.drawUpdateIntervalSpin.setRange(0,1000)
        self.drawUpdateIntervalSpin.setSuffix("ms")
        self.drawUpdateIntervalSpin.setValue(self.project.drawUpdateInterval)
        tempLayout.addWidget(QtGui.QLabel(" "))
        tempLayout.addWidget(self.drawUpdateIntervalSpin)
        tempLayout.addStretch()
        self.drawUpdateIntervalFrame.setLayout(tempLayout)
        self.layout.addWidget(self.drawUpdateIntervalFrame)
        if self.project.drawUpdateInterval == 0:
            self.drawUpdateIntervalFrame.setVisible(False)
            self.drawUpdateIntervalSpin.setValue(300)
        
        self.normalizeCheckbox = QtGui.QCheckBox("normalize Data for display in each SliceView seperately")
        self.normalizeCheckbox.setCheckState(self.project.normalizeData * 2)
        self.layout.addWidget(self.normalizeCheckbox)

        self.rgbDataCheckbox = QtGui.QCheckBox("interpret 3-Channel files as RGB Data")
        self.rgbDataCheckbox.setCheckState(self.project.rgbData * 2)
        self.layout.addWidget(self.rgbDataCheckbox)

        self.borderMarginCheckbox = QtGui.QCheckBox("show border margin indicator")
        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin * 2)
        self.layout.addWidget(self.borderMarginCheckbox)

        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin*2)
        self.normalizeCheckbox.setCheckState(self.project.normalizeData*2)

        tempLayout = QtGui.QHBoxLayout()
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.cancel)
        self.okButton = QtGui.QPushButton("Ok")
        self.connect(self.okButton, QtCore.SIGNAL('clicked()'), self.ok)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.okButton)
        self.layout.addLayout(tempLayout)

        self.layout.addStretch()

    def toggleUpdateInterval(self, state):
        state = self.drawUpdateIntervalCheckbox.checkState()
        self.project.drawUpdateInterval = int(self.drawUpdateIntervalSpin.value())
        if state > 0:
            self.drawUpdateIntervalFrame.setVisible(True)
        else:
            self.drawUpdateIntervalFrame.setVisible(False)
            self.project.drawUpdateInterval = 0


    def ok(self):
        self.project.useBorderMargin = False
        self.project.normalizeData = False
        self.project.rgbData = False
        if self.normalizeCheckbox.checkState() == QtCore.Qt.Checked:
            self.project.normalizeData = True
        if self.borderMarginCheckbox.checkState() == QtCore.Qt.Checked:
            self.project.useBorderMargin = True
        if self.rgbDataCheckbox.checkState() == QtCore.Qt.Checked:
            self.project.rgbData = True
        if self.ilastik.labelWidget is not None:
            self.ilastik.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
            self.ilastik.labelWidget.normalizeData = self.project.normalizeData
            self.ilastik.labelWidget.setRgbMode(self.project.rgbData)
            self.ilastik.labelWidget.setUseBorderMargin(self.project.useBorderMargin)
            self.ilastik.labelWidget.repaint()
            
        self.close()

    def cancel(self):
        self.close()
        
        