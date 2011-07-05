#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import QFileInfo, Qt, SIGNAL, pyqtSignature
from PyQt4.QtGui import QCheckBox, QColor, QDialog, QErrorMessage, QFileDialog,\
                        QFrame, QHBoxLayout, QHeaderView, QIcon, QLabel, QPixmap,\
                        QPushButton, QSpinBox, QTableWidgetItem, QVBoxLayout,\
                        QWidget
from PyQt4.uic import loadUi

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

class ProjectDlg(QDialog):
    def __init__(self, parent=None, newProject = True):
        QWidget.__init__(self, parent)
        
        self.ilastik = parent
        self.newProject = newProject

        self.labelCounter = 2
        self.columnPos = {}
        self.labelColor = { 1:QColor(Qt.red), 2:QColor(Qt.green), 3:QColor(Qt.yellow), 4:QColor(Qt.blue), 5:QColor(Qt.magenta) , 6:QColor(Qt.darkYellow), 7:QColor(Qt.lightGray) }
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
        loadUi(os.path.join(ilastikPath,"dlgProject.ui"), self) 
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.connect(self.tableWidget, SIGNAL("cellPressed(int, int)"), self.updateThumbnail)
        self.addFile.setIcon(QIcon(ilastikIcons.DoubleArrow))
        self.removeFile.setIcon(QIcon(ilastikIcons.DoubleArrowBack))



    @pyqtSignature("")
    def updateDlg(self, project):
        print "in update Dialog"
        self.project = project
        #self.dataMgr = project.dataMgr        
        self.projectName.setText(project.name)
        self.labeler.setText(project.labeler)
        self.description.setText(project.description)
        
        theFlag = Qt.ItemIsEnabled
        flagON = ~theFlag | theFlag 
        flagOFF = ~theFlag
            
        for d in project.dataMgr:
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            # File _name
            r = QTableWidgetItem(d.fileName)
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
                       
            # Here comes the cool python "checker" use it for if_than_else in lambdas
            checker = lambda x: x and Qt.Checked or Qt.Unchecked
            
            # labels
            r = QTableWidgetItem()
            r.data(Qt.CheckStateRole)
            #TODO: check for label availability
            #r.setCheckState(checker(d._dataVol.labels._data != None))
            
            #r.setFlags(r.flags() & flagOFF);
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
            
        self.oldFiles = rowCount+1
        self.exec_()


    @pyqtSignature("")     
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
            QErrorMessage.qtHandler().showMessage("Different number of files for different channels. Doesn't work.")
            return
        if path is None:
            return
        loaded = False
        try:
            loaded = self.project.loadStack(path, fileList, options) 
        except Exception, e:
            print e
            QErrorMessage.qtHandler().showMessage("Not enough memory, please select a smaller sub-volume. Much smaller, since you may also want to calculate some features...")
        if loaded:   
            # file name
            offsetstr =  '(' + str(options.offsets[0]) + ', ' + str(options.offsets[1]) + ', ' + str(options.offsets[2]) + ')' 
            try:
                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)
            
                r = QTableWidgetItem('Stack at ' + path + ', offsets: ' + offsetstr)
                self.tableWidget.setItem(rowCount, self.columnPos['File'], r)

                # labels
                r = QTableWidgetItem()
                r.data(Qt.CheckStateRole)
                r.setCheckState(Qt.Unchecked)

                self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
                
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
                QErrorMessage.qtHandler().showMessage(str(e))
            
    
    @pyqtSignature("")
    def on_loadFileButton_clicked(self):

        fl = fileloader.FileLoader(self)
        fileList, options = fl.exec_()
        if fileList is None:
            return
        loaded = False
        try:
            self.project.loadFile(fileList, options)
        except Exception, e:
            QErrorMessage.qtHandler().showMessage(str(e))
        for filename in fileList[options.channels[0]]:
            
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            # file name
            r = QTableWidgetItem(filename)
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
            # labels
            r = QTableWidgetItem()
            r.data(Qt.CheckStateRole)
            r.setCheckState(Qt.Checked)
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)


            self.initThumbnail(filename)
            self.tableWidget.setCurrentCell(0, 0)

    @pyqtSignature("")     
    def on_addFile_clicked(self):
        #global LAST_DIRECTORY
        fileNames = QFileDialog.getOpenFileNames(self, "Open Image", ilastik.gui.LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.tiff *.gif *.h5)")
        fileNames.sort()
        loaded = False
        try:
            loaded = self.project.addFile(fileNames)
        except Exception, e:
            QErrorMessage.qtHandler().showMessage(str(e))
        if loaded:
            for file_name in fileNames:
                ilastik.gui.LAST_DIRECTORY = QFileInfo(file_name).path()
                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)

                # file name
                r = QTableWidgetItem(file_name)
                self.tableWidget.setItem(rowCount, self.columnPos['File'], r)
                # labels
                r = QTableWidgetItem()
                r.data(Qt.CheckStateRole)
                r.setCheckState(Qt.Checked)


                self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)

                self.initThumbnail(file_name)
                self.tableWidget.setCurrentCell(0, 0)
                
    @pyqtSignature("")   
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
        thumb = QPixmap(str(file_name))
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
    
    @pyqtSignature("")     
    def on_confirmButtons_accepted(self):
        self.project.name = self.projectName.text()
        self.project.labeler = self.labeler.text()
        self.project.description = self.description.toPlainText()
        gc.collect()
        self.ilastik.project = self.project
        self.accept()

        
    
    @pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        for row in range(self.oldFiles, self.tableWidget.rowCount()):
            fileName = str(self.tableWidget.item(row, self.columnPos['File']).text())
            self.project.removeFile(row)
        self.reject() 


        
#*******************************************************************************
# P r o j e c t S e t t i n g s D l g                                          *
#*******************************************************************************

class ProjectSettingsDlg(QDialog):
    def __init__(self, ilastik = None, project=None):
        QWidget.__init__(self, ilastik)
        
        self.setWindowTitle("Project Options")

        self.project = project
        self.ilastik = ilastik
        
        


        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.drawUpdateIntervalCheckbox = QCheckBox("Train and predict during brush strokes in Interactive Mode")
        self.drawUpdateIntervalCheckbox.setCheckState((self.project.drawUpdateInterval > 0)  * 2)
        self.connect(self.drawUpdateIntervalCheckbox, SIGNAL("stateChanged(int)"), self.toggleUpdateInterval)
        self.layout.addWidget(self.drawUpdateIntervalCheckbox)

        self.drawUpdateIntervalFrame = QFrame()
        tempLayout = QHBoxLayout()
        self.drawUpdateIntervalSpin = QSpinBox()
        self.drawUpdateIntervalSpin.setRange(0,1000)
        self.drawUpdateIntervalSpin.setSuffix("ms")
        self.drawUpdateIntervalSpin.setValue(self.project.drawUpdateInterval)
        tempLayout.addWidget(QLabel(" "))
        tempLayout.addWidget(self.drawUpdateIntervalSpin)
        tempLayout.addStretch()
        self.drawUpdateIntervalFrame.setLayout(tempLayout)
        self.layout.addWidget(self.drawUpdateIntervalFrame)
        if self.project.drawUpdateInterval == 0:
            self.drawUpdateIntervalFrame.setVisible(False)
            self.drawUpdateIntervalSpin.setValue(300)
        
        self.normalizeCheckbox = QCheckBox("Normalize data for display in each slice view separately")
        self.normalizeCheckbox.setCheckState(self.project.normalizeData * 2)
        self.layout.addWidget(self.normalizeCheckbox)

        self.rgbDataCheckbox = QCheckBox("Interpret 3-Channel files as RGB images")
        self.rgbDataCheckbox.setCheckState(self.project.rgbData * 2)
        self.layout.addWidget(self.rgbDataCheckbox)

        self.borderMarginCheckbox = QCheckBox("Show border margin indicator")
        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin * 2)
        self.layout.addWidget(self.borderMarginCheckbox)

        self.fastRepaintCheckbox = QCheckBox("Speed up painting of slice views by tolerating flickering")
        self.fastRepaintCheckbox.setCheckState(self.project.fastRepaint * 2)
        self.layout.addWidget(self.fastRepaintCheckbox)

#        self.borderMarginCheckbox.setCheckState(self.project.useBorderMargin*2)
        self.normalizeCheckbox.setCheckState(self.project.normalizeData*2)

        tempLayout = QHBoxLayout()
        self.cancelButton = QPushButton("Cancel")
        self.connect(self.cancelButton, SIGNAL('clicked()'), self.cancel)
        self.okButton = QPushButton("Ok")
        self.connect(self.okButton, SIGNAL('clicked()'), self.ok)
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
        if self.fastRepaintCheckbox.checkState() == Qt.Checked:
            self.project.fastRepaint = True
        if self.normalizeCheckbox.checkState() == Qt.Checked:
            self.project.normalizeData = True
        if self.borderMarginCheckbox.checkState() == Qt.Checked:
            self.project.useBorderMargin = True
        if self.rgbDataCheckbox.checkState() == Qt.Checked:
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
        
        
