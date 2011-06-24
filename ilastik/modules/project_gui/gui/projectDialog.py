from PyQt4 import QtCore, QtGui, uic
import ilastik.gui
import fileloader
import os, sys
import traceback
import gc
from ilastik.gui import stackloader
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.core import projectClass

#*******************************************************************************
# P r o j e c t D l g                                                          *
#*******************************************************************************

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

        self.oldFiles = 0
        projectName = self.projectName
        labeler = self.labeler
        description = self.description

        # New project or edited project? if edited, reuse parts of old dataMgr
        if hasattr(self.ilastik,'project') and (not self.newProject):
            #self.dataMgr = self.ilastik.project.dataMgr
            self.project = self.ilastik.project
        else:
            print "Create new project"
            #self.dataMgr = dataMgr.DataMgr()
            self.project = projectClass.Project(str(projectName.text()), str(labeler.text()), str(description.toPlainText()) , None)
                    
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
        self.addFile.setIcon(QtGui.QIcon(ilastikIcons.DoubleArrow))
        self.removeFile.setIcon(QtGui.QIcon(ilastikIcons.DoubleArrowBack))



    @QtCore.pyqtSignature("")
    def updateDlg(self, project):
        print "in update Dialog"
        self.project = project
        #self.dataMgr = project.dataMgr        
        self.projectName.setText(project.name)
        self.labeler.setText(project.labeler)
        self.description.setText(project.description)
        
        theFlag = QtCore.Qt.ItemIsEnabled
        flagON = ~theFlag | theFlag 
        flagOFF = ~theFlag
            
        for d in project.dataMgr:
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            # File _name
            r = QtGui.QTableWidgetItem(d.fileName)
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
                       
            # Here comes the cool python "checker" use it for if_than_else in lambdas
            checker = lambda x: x and QtCore.Qt.Checked or QtCore.Qt.Unchecked
            
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            #TODO: check for label availability
            #r.setCheckState(checker(d._dataVol.labels._data != None))
            
            #r.setFlags(r.flags() & flagOFF);
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
            
        self.oldFiles = rowCount+1
        self.exec_()


    @QtCore.pyqtSignature("")     
    def on_loadStack_clicked(self):
        sl = stackloader.StackLoader(self)
        path, fileList, options = sl.exec_()
        len0 = len(fileList[0])
        diff = 0
        for f in fileList:
            if len(f)!=len0 and len(f)!=0:
                diff = 1
                break
        if diff>0:
            QtGui.QErrorMessage.qtHandler().showMessage("Different number of files for different channels. Doesn't work.")
            return
        if path is None:
            return
        loaded = False
        try:
            loaded = self.project.loadStack(path, fileList, options) 
        except Exception, e:
            print e
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough memory, please select a smaller sub-volume. Much smaller, since you may also want to calculate some features...")
        if loaded:   
            # file name
            offsetstr =  '(' + str(options.offsets[0]) + ', ' + str(options.offsets[1]) + ', ' + str(options.offsets[2]) + ')' 
            try:
                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)
            
                r = QtGui.QTableWidgetItem('Stack at ' + path + ', offsets: ' + offsetstr)
                self.tableWidget.setItem(rowCount, self.columnPos['File'], r)

                # labels
                r = QtGui.QTableWidgetItem()
                r.data(QtCore.Qt.CheckStateRole)
                r.setCheckState(QtCore.Qt.Unchecked)

                self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
                
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
                QtGui.QErrorMessage.qtHandler().showMessage(str(e))
            
    
    @QtCore.pyqtSignature("")
    def on_loadFileButton_clicked(self):

        fl = fileloader.FileLoader(self)
        
        fileList, options = fl.exec_()
        if fileList is None:
            return
        loaded = False
        try:
            self.project.loadFile(fl.fileList, fl.options)
        except Exception, e:
            QtGui.QErrorMessage.qtHandler().showMessage(str(e))
        for filename in fl.fileList[fl.options.channels[0]]:
            
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            # file name
            r = QtGui.QTableWidgetItem(filename)
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(QtCore.Qt.Checked)
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)


            self.initThumbnail(filename)
            self.tableWidget.setCurrentCell(0, 0)

    @QtCore.pyqtSignature("")     
    def on_addFile_clicked(self):
        #global LAST_DIRECTORY
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", ilastik.gui.LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.tiff *.gif *.h5)")
        fileNames.sort()
        loaded = False
        try:
            loaded = self.project.addFile(fileNames)
        except Exception, e:
            QtGui.QErrorMessage.qtHandler().showMessage(str(e))
        if loaded:
            for file_name in fileNames:
                ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(file_name).path()
                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)

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
                
    @QtCore.pyqtSignature("")   
    def on_removeFile_clicked(self):
        # Get row and fileName to remove
        row = self.tableWidget.currentRow()
        fileName = str(self.tableWidget.item(row, self.columnPos['File']).text())
        print "remove Filename in row: ", fileName, " -- ", row
        self.project.removeFile(row)
        # Remove Row from display Table
        self.tableWidget.removeRow(row)
        try:
            del self.thumbList[row]
        except IndexError:
            pass
        
        
        
    def initThumbnail(self, file_name):
        thumb = QtGui.QPixmap(str(file_name))
        if thumb.depth() != 0:
            if thumb.width() >= thumb.height():
                thumb = thumb.scaledToWidth(128)
            else:
                thumb = thumb.scaledToHeight(128)
            self.thumbList.append(thumb)
            self.thumbnailImage.setPixmap(self.thumbList[0])
                    
    def updateThumbnail(self, row=0, col=0):
        try:
            self.thumbnailImage.setPixmap(self.thumbList[row]) 
        except IndexError:
            pass
    
    @QtCore.pyqtSignature("")     
    def on_confirmButtons_accepted(self):
        self.project.name = self.projectName.text()
        self.project.labeler = self.labeler.text()
        self.project.description = self.description.toPlainText()
        gc.collect()
        self.ilastik.project = self.project
        self.accept()

        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        for row in range(self.oldFiles, self.tableWidget.rowCount()):
            fileName = str(self.tableWidget.item(row, self.columnPos['File']).text())
            self.project.removeFile(row)
        self.reject() 


        
#*******************************************************************************
# P r o j e c t S e t t i n g s D l g                                          *
#*******************************************************************************

class ProjectSettingsDlg(QtGui.QDialog):
    def __init__(self, ilastik = None, project=None):
        QtGui.QWidget.__init__(self, ilastik)
        
        self.setWindowTitle("Project Options")

        self.project = project
        self.ilastik = ilastik
        
        


        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.drawUpdateIntervalCheckbox = QtGui.QCheckBox("Train and predict during brush strokes in Interactive Mode")
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
        
        self.normalizeCheckbox = QtGui.QCheckBox("Normalize data for display in each slice view separately")
        self.normalizeCheckbox.setCheckState(self.project.normalizeData * 2)
        self.layout.addWidget(self.normalizeCheckbox)

        self.rgbDataCheckbox = QtGui.QCheckBox("Interpret 3-Channel files as RGB images")
        self.rgbDataCheckbox.setCheckState(self.project.rgbData * 2)
        self.layout.addWidget(self.rgbDataCheckbox)

        self.borderMarginCheckbox = QtGui.QCheckBox("Show border margin indicator")
        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin * 2)
        self.layout.addWidget(self.borderMarginCheckbox)

        self.fastRepaintCheckbox = QtGui.QCheckBox("Speed up painting of slice views by tolerating flickering")
        self.fastRepaintCheckbox.setCheckState(self.project.fastRepaint * 2)
        self.layout.addWidget(self.fastRepaintCheckbox)

#        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin*2)
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
        self.project.fastRepaint = False
        self.project.useBorderMargin = False
        self.project.normalizeData = False
        self.project.rgbData = False
        if self.fastRepaintCheckbox.checkState() == QtCore.Qt.Checked:
            self.project.fastRepaint = True
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
            self.ilastik.labelWidget.setFastRepaint(self.project.fastRepaint)
            self.ilastik.labelWidget.repaint()
            
        self.close()

    def cancel(self):
        self.close()
        
        
