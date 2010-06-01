#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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


# profile with python -m cProfile ilastikMain.py
# python -m cProfile -o profiling.prf  ilastikMain.py
# import pstats
# p = pstats.StaPATHts('fooprof')
# p.sort_statsf('time').reverse_order().print_stats()
# possible sort order: "stdname" "calls" "time" "cumulative". more in p.sort_arg_dic

import vigra
from vigra import arraytypes as at

import sys
import os

import threading 
import numpy
import time
from PyQt4 import QtCore, QtGui, uic
from core import version, dataMgr, projectMgr, featureMgr, classificationMgr, segmentationMgr, activeLearning, onlineClassifcator
from gui import ctrlRibbon, stackloader, batchProcess
from Queue import Queue as queue
from collections import deque
from gui.iconMgr import ilastikIcons
from core.utilities import irange, debug
from core import jobMachine
import copy
import h5py

from OpenGL.GL import *

from PyQt4 import QtCore, QtGui, QtOpenGL
import getopt

from gui import volumeeditor as ve


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setGeometry(50, 50, 800, 600)
        self.iconPath = '../../icons/32x32/'
        
        #self.setWindowTitle("Ilastik rev: " + version.getIlastikVersion())
        self.setWindowIcon(QtGui.QIcon(ilastikIcons.Python))

        self.activeImageLock = threading.Semaphore(1) #prevent chaning of activeImage during thread stuff
        
        self.labelWidget = None
        self.activeImage = 0
        
        self.createRibbons()
        self.initImageWindows()

        self.createFeatures()
              
        self.classificationProcess = None
        self.classificationOnline = None
        
        self.featureCache = None
        self.opengl = None
        project = None        
        
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ["help", "render=", "project=", "featureCache="])
            for o, a in opts:
                if o == "-v":
                    verbose = True
                elif o in ("--help"):
                    print '%30s  %s' % ("--help", "print help on command line options")
                    print '%30s  %s' % ("--render=[s,s_gl,gl_gl]", "chose slice renderer:")
                    print '%30s  %s' % ("s", "software without 3d overview")
                    print '%30s  %s' % ("s_gl", "software with opengl 3d overview")
                    print '%30s  %s' % ("gl_gl", "opengl with opengl 3d overview")
                    print '%30s  %s' % ("--project=[filename]", "open specified project file")
                    print '%30s  %s' % ("--featureCache=[filename]", "use specified file for caching of features")
                elif o in ("--render"):
                    if a == 's':
                        self.opengl = False
                        self.openglOverview = False
                    elif a == 's_gl':
                        self.opengl = False
                        self.openglOverview = True
                    elif a == 'gl_gl':
                        self.opengl = True
                        self.openglOverview = True
                    else:
                        print "invalid --render option"
                        sys.exit()                                         
                elif o in ("--project"):
                    project = a
                elif o in ("--featureCache"):
                    self.featureCache = a
                else:
                    assert False, "unhandled option"
            
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
                

        if self.opengl == None:   #no command line option for opengl was given, ask user interactively
            #test for opengl version
            gl2 = False
            w = QtOpenGL.QGLWidget()
            w.setVisible(False)
            w.makeCurrent()
            gl_version =  glGetString(GL_VERSION)
            if gl_version is None:
                gl_version = '0'
            del w
            
            if int(gl_version[0]) >= 2:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', "choose render method", ['OpenGL + OpenGL Overview', 'Software without Overview', 'Software + OpenGL Overview'], 0, False)
            elif int(gl_version[0]) > 0:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', "choose render method", ['Software without Overview', 'Software + OpenGL Overview'], 0, False)
            else:
                dl = []
                dl.append("")
                
            self.opengl = False
            self.openglOverview = False
            if dl[0] == "OpenGL + OpenGL Overview":
                self.opengl = True
                self.openglOverview = True
            elif dl[0] == "Software + OpenGL Overview":
                self.opengl = False
                self.openglOverview = True

        if project != None:
            self.project = projectMgr.Project.loadFromDisk(project, self.featureCache)
            self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
            self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
            self.activeImage = 0
            self.projectModified()
        
        self.shortcutSave = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.saveProject, self.saveProject) 

        
                
    def updateFileSelector(self):
        self.fileSelectorList.clear()
        for index, item in enumerate(self.project.dataMgr):
            self.fileSelectorList.addItem(item.Name)
            if index == self.activeImage:
                self.fileSelectorList.setCurrentIndex(index)
    
    def changeImage(self, number):
        if hasattr(self, "classificationInteractive"):
            self.labelWidget.disconnect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
        self.activeImageLock.acquire()
        if self.labelWidget is not None:
            self.labelWidget.history.volumeEditor = None
        if number != self.activeImage:
            self.project.dataMgr[self.activeImage].history = self.labelWidget.history
        self.activeImage = number
        self.destroyImageWindows()
        self.createImageWindows( self.project.dataMgr[number].dataVol)
        if self.project.dataMgr[self.activeImage].history is not None:
            self.labelWidget.history = self.project.dataMgr[self.activeImage].history
            self.labelWidget.history.volumeEditor = self.labelWidget
        
        self.updateLabelWidgetOverlays()
        self.labelWidget.repaint() #for overlays
        self.activeImageLock.release()
        if hasattr(self, "classificationInteractive"):
            self.labelWidget.connect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
            self.classificationInteractive.updateThreadQueues()
            
    def historyUndo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyUndo
        
    def historyRedo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyRedo
    
    def createRibbons(self):                     
      
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.Ribbon(self.ribbonToolbar)
        for ribbon_name, ribbon_group in ctrlRibbon.createRibbons().items():
            tabs = ribbon_group.makeTab()   
            self.ribbon.addTab(tabs, ribbon_group.name)
        self.ribbonToolbar.addWidget(self.ribbon)
        
        
        self.fileSelectorList = QtGui.QComboBox()
        widget = QtGui.QWidget()
        self.fileSelectorList.setMinimumWidth(140)
        self.fileSelectorList.setMaximumWidth(240)
        self.fileSelectorList.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("Select Image:"))
        layout.addWidget(self.fileSelectorList)
        widget.setLayout(layout)
        self.ribbonToolbar.addWidget(widget)
        self.fileSelectorList.connect(self.fileSelectorList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeImage)
                
        # Wee, this is really ugly... anybody have better ideas for connecting 
        # the signals. This way has no future and is just a workaround
        
        self.connect(self.ribbon.tabDict['Projects'].itemDict['New'], QtCore.SIGNAL('clicked()'), self.newProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Save'], QtCore.SIGNAL('clicked()'), self.saveProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Open'], QtCore.SIGNAL('clicked()'), self.loadProjectDlg)
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Edit'], QtCore.SIGNAL('clicked()'), self.editProjectDlg)
        self.connect(self.ribbon.tabDict['Features'].itemDict['Select'], QtCore.SIGNAL('clicked()'), self.newFeatureDlg)
        self.connect(self.ribbon.tabDict['Features'].itemDict['Compute'], QtCore.SIGNAL('clicked()'), self.featureCompute)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Train'], QtCore.SIGNAL('clicked()'), self.on_classificationTrain)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Predict'], QtCore.SIGNAL('clicked()'), self.on_classificationPredict)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Interactive'], QtCore.SIGNAL('clicked(bool)'), self.on_classificationInteractive)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Batchprocess'], QtCore.SIGNAL('clicked(bool)'), self.on_batchProcess)
        #self.connect(self.ribbon.tabDict['Classification'].itemDict['Online'], QtCore.SIGNAL('clicked(bool)'), self.on_classificationOnline)
        #TODO: reenable segmentation
        #self.connect(self.ribbon.tabDict['Segmentation'].itemDict['Segment'], QtCore.SIGNAL('clicked(bool)'), self.on_segmentation)
        
        
        #TODO: reenable online classification sometime 
#        # Make menu for online Classification
#        btnOnlineToggle = self.ribbon.tabDict['Classification'].itemDict['Online']
#        btnOnlineToggle.myMenu = QtGui.QMenu();
#        btnOnlineToggle.onlineRfAction = btnOnlineToggle.myMenu.addAction('Online RF')
#        btnOnlineToggle.onlineSVMAction = btnOnlineToggle.myMenu.addAction('Online SVM')
#        btnOnlineToggle.onlineStopAction = btnOnlineToggle.myMenu.addAction('Stop')
#        btnOnlineToggle.onlineStopAction.setEnabled(False)
#        btnOnlineToggle.setMenu(btnOnlineToggle.myMenu)
        
#        # Connect online classification Actions to slots
#        self.connect(btnOnlineToggle.onlineRfAction, QtCore.SIGNAL('triggered()'), lambda : self.on_classificationOnline('online RF'))
#        self.connect(btnOnlineToggle.onlineSVMAction, QtCore.SIGNAL('triggered()'), lambda : self.on_classificationOnline('online laSvm'))
#        self.connect(btnOnlineToggle.onlineStopAction, QtCore.SIGNAL('triggered()'), lambda : self.on_classificationOnline('stop'))
        
        # make Label and View Tab invisible (this tabs are not helpful so far)
        self.ribbon.removeTab(1)
        self.ribbon.removeTab(1)
              
        
        self.connect(self.ribbon.tabDict['Export'].itemDict['Export'], QtCore.SIGNAL('clicked()'), self.export2Hdf5)
        
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(False)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(False)
        self.ribbon.tabDict['Features'].itemDict['Select'].setEnabled(False)        
        self.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Interactive'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Batchprocess'].setEnabled(False)        
        self.ribbon.tabDict['Export'].itemDict['Export'].setEnabled(False)        
        
        #self.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(False)
        #self.ribbon.tabDict['Classification'].itemDict['Compute'].setEnabled(False)
        
        self.ribbon.setCurrentIndex (0)
          
    def newProjectDlg(self):
        self.projectDlg = ProjectDlg(self)
    
    def saveProjectDlg(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", ".", "Project Files (*.ilp)")
        fn = str(fileName)
        if len(fn) > 4:
            if fn[-4:] != '.ilp':
                fn = fn + '.ilp'
            self.project.saveToDisk(fn)
            

                
            
    def saveProject(self):
        if hasattr(self,'project'):
            if self.project.filename is not None:
                self.project.saveToDisk()
            else:
                self.saveProjectDlg()
            print "saved Project to ", self.project.filename
        
    def loadProjectDlg(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Project", ".", "Project Files (*.ilp)")
        self.project = projectMgr.Project.loadFromDisk(str(fileName), self.featureCache)
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        if hasattr(self, 'projectDlg'):
            del self.projectDlg
        self.activeImage = 0
        self.projectModified() 
        
    def editProjectDlg(self):
        self.projectDlg = ProjectDlg(self, False)
        self.projectDlg.updateDlg(self.project)
        self.projectModified()
            
        
    def projectModified(self):
        self.updateFileSelector() #this one also changes the image
        self.changeImage(self.activeImage)
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        self.ribbon.tabDict['Features'].itemDict['Select'].setEnabled(True)
        
        
    def updateLabelWidgetOverlays(self):
        #TODO: this whole method is so ugly, it should be forbidden !
        
        activeItem = self.project.dataMgr[self.activeImage]
        self.labelWidget.overlayView.clearOverlays()

        for imageIndex, imageItem in  enumerate(self.project.dataMgr):           
            if imageIndex != self.activeImage:
                if imageItem.dataVol.labels is None:
                    imageItem.dataVol.labels = ve.VolumeLabels(ve.DataAccessor(numpy.zeros((imageItem.dataVol.data.shape[0:4]),'uint8')))
                else:
                    for ii, itemii in enumerate(activeItem.dataVol.labels.descriptions):
                        if ii < len(imageItem.dataVol.labels.descriptions):
                            if not (imageItem.dataVol.labels.descriptions[ii] ==  itemii):
                                imageItem.dataVol.labels.descriptions[ii] = itemii.clone()
                                imageItem.dataVol.labels.descriptions[ii].prediction = None
                        else:
                            imageItem.dataVol.labels.descriptions.append(itemii.clone())
                            imageItem.dataVol.labels.descriptions[ii].prediction = None
            else:
                if imageItem.dataVol.labels.data is None:
                    imageItem.dataVol.labels.data = ve.DataAccessor(numpy.zeros((imageItem.dataVol.data.shape[0:4]),'uint8'))

        for imageIndex, imageItem in  enumerate(self.project.dataMgr):            
            for p_i, item in enumerate(imageItem.dataVol.labels.descriptions):
                if item.prediction is None:
                   item.prediction = numpy.zeros(imageItem.dataVol.data.shape[0:-1],'uint8')
                if imageIndex == self.activeImage:
                    color = QtGui.QColor.fromRgb(long(item.color))
                    self.labelWidget.addOverlay(True, item.prediction, item.name, color, 0.4)
            
            if imageItem.dataVol.uncertainty is None:
                imageItem.dataVol.uncertainty = numpy.zeros( imageItem.dataVol.data.shape[0:-1] ,'uint8')

            if imageIndex == self.activeImage: 
                self.labelWidget.addOverlay(False, activeItem.dataVol.uncertainty, "Uncertainty", QtGui.QColor(255,0,0), 0.9)
            
            if imageItem.dataVol.segmentation is None:
                imageItem.dataVol.segmentation = numpy.zeros(imageItem.dataVol.data.shape[0:-1],'uint8')

            if imageIndex == self.activeImage:
                self.labelWidget.addOverlay(False, activeItem.dataVol.segmentation, "Segmentation", QtGui.QColor(255,126,255), 1.0, self.labelWidget.labelView.colorTab)
       
        
    def newFeatureDlg(self):
        self.newFeatureDlg = FeatureDlg(self)
        self.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(True)
        self.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Interactive'].setEnabled(False)        
        self.ribbon.tabDict['Classification'].itemDict['Batchprocess'].setEnabled(False)        
        
        
    def newEditChannelsDlg(self):
        self.editChannelsDlg = editChannelsDlg(self)
        
    def initImageWindows(self):
        self.labelDocks = []
        
    def destroyImageWindows(self):
        for dock in self.labelDocks:
            self.removeDockWidget(dock)
        self.labelDocks = []
        if self.labelWidget is not None:
            self.labelWidget.cleanup()
            self.labelWidget.close()
            del self.labelWidget
                
    def createImageWindows(self, dataVol):
        self.labelWidget = ve.VolumeEditor(dataVol, embedded = True, opengl = self.opengl, openglOverview = self.openglOverview, parent = self)
        self.connect(self.labelWidget.labelView, QtCore.SIGNAL("labelPropertiesChanged()"),self.updateLabelWidgetOverlays)
                
        dock = QtGui.QDockWidget("Ilastik Label Widget", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)

        
        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)
        
    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        if self.project.featureMgr is not None:
            self.featureComputation = FeatureComputation(self)
#

    def on_batchProcess(self):
        dialog = batchProcess.BatchProcess(self)
        result = dialog.exec_()
    
    def on_classificationTrain(self):
        self.classificationTrain = ClassificationTrain(self)
        
    def on_classificationPredict(self):
        self.classificationPredict = ClassificationPredict(self)
    
    def on_classificationInteractive(self, state):
        if state:
            self.classificationInteractive = ClassificationInteractive(self)
        else:
            self.classificationInteractive.stop()
    
    def export2Hdf5(self):
        if not hasattr(self.project.dataMgr,'classifiers'):
            return
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", ".", "HDF5 FIles (*.h5)")
        print fileName
        #self.labelWidget.updateLabelsOfDataItems(self.project.dataMgr)
        #self.project.dataMgr.export2Hdf5(str(fileName))
        
        rfs = self.project.dataMgr.classifiers
        
        for i,rf in enumerate(rfs):
            tmp = rf.classifier.writeHDF5(str(fileName), "rf_%03d" % i, True)
            print "Write Random Forest # %03d -> %d" % (i,tmp)
        print "Done"
            
        
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
            print "edit Project"
        else:
            self.dataMgr = dataMgr.DataMgr(self.ilastik.featureCache)
            self.project = self.ilastik.project = projectMgr.Project(str(projectName.text()), str(labeler.text()), str(description.toPlainText()) , self.dataMgr)
            print "new Project"
                    
    def initDlg(self):
        uic.loadUi('gui/dlgProject.ui', self) 
        self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.connect(self.tableWidget, QtCore.SIGNAL("cellPressed(int, int)"), self.updateThumbnail)
        #self.on_cmbLabelName_currentIndexChanged(0)
        self.show()
        



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
        imageData = sl.exec_()
        
        if imageData is not None:   
                
            theDataItem = dataMgr.DataItemImage.initFromArray(imageData, "Image Stack")
            self.dataMgr.append(theDataItem)
            self.dataMgr.dataItemsLoaded[-1] = True
                       
            theDataItem.hasLabels = True
            theDataItem.isTraining = True
            theDataItem.isTesting = True
                    
            self.ilastik.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
            self.ilastik.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
            
            rowCount = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowCount)
            
            theFlag = QtCore.Qt.ItemIsEnabled
            flagON = ~theFlag | theFlag 
            flagOFF = ~theFlag
            
            # file name
            r = QtGui.QTableWidgetItem('Stack' + str(rowCount))
            self.tableWidget.setItem(rowCount, self.columnPos['File'], r)

                      
            # labels
            r = QtGui.QTableWidgetItem()
            r.data(QtCore.Qt.CheckStateRole)
            r.setCheckState(QtCore.Qt.Unchecked)
            
            self.tableWidget.setItem(rowCount, self.columnPos['Labels'], r)
            
                        
    @QtCore.pyqtSignature("")     
    def on_addFile_clicked(self):
        
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", ".", "Image Files (*.png *.jpg *.bmp *.tif *.gif *.h5)")
        fileNames.sort()
        if fileNames:
            for file_name in fileNames:
                file_name = str(file_name)
                
                theDataItem = dataMgr.DataItemImage(file_name)
                self.dataMgr.append(theDataItem)                
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
                theDataItem.dataVol.labels = None
                
            contained = False
            for pr in theDataItem.projects:
                if pr == self.parent.project:
                    contained = true
            if not contained:
                theDataItem.projects.append(self.parent.project)
        
        self.parent.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.parent.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        
        self.parent.activeImage = 0
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
        
        uic.loadUi('gui/dlgFeature.ui', self) 
        for featureItem in self.parent.featureList:
            self.featureList.insertItem(self.featureList.count() + 1, QtCore.QString(featureItem.__str__()))        
        
        for k, groupName in irange(featureMgr.ilastikFeatureGroups.groupNames):
            rc = self.featureTable.rowCount()
            self.featureTable.insertRow(rc)
        self.featureTable.setVerticalHeaderLabels(featureMgr.ilastikFeatureGroups.groupNames)
       
        
        for k, scaleName in irange(featureMgr.ilastikFeatureGroups.groupScaleNames):
            rc = self.featureTable.columnCount()
            self.featureTable.insertColumn(rc)
        self.featureTable.setHorizontalHeaderLabels(featureMgr.ilastikFeatureGroups.groupScaleNames)
        
        #self.featureTable.resizeRowsToContents()
        #self.featureTable.resizeColumnsToContents()
        for c in range(self.featureTable.columnCount()):
            self.featureTable.horizontalHeader().resizeSection(c, 54)#(0, QtGui.QHeaderView.Stretch)

        #self.featureTable.verticalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.featureTable.setShowGrid(False)
        
        
        for r in range(self.featureTable.rowCount()):
            for c in range(self.featureTable.columnCount()):
                item = QtGui.QTableWidgetItem()
                if featureMgr.ilastikFeatureGroups.selection[r][c]:
                    item.setIcon(QtGui.QIcon(ilastikIcons.Preferences))
                self.featureTable.setItem(r, c, item)
        self.setStyleSheet("selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0.5, y2: 0.5, stop: 0 #BBBBDD, stop: 1 white)")
        self.show()
    
    def on_featureTable_itemSelectionChanged(self):  
        sel = self.featureTable.selectedItems()
        sel_flag = False
        for i in sel:
            if i.icon().isNull():
                sel_flag = True
        
        if sel_flag:
            for i in sel:
                icon = QtGui.QIcon(ilastikIcons.Preferences)
                i.setIcon(icon)
                featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = True  
                           
        else:
            for i in sel:
                icon = QtGui.QIcon()
                i.setIcon(icon)   
                featureMgr.ilastikFeatureGroups.selection[i.row()][i.column()] = False     
                
        self.computeMemoryRequirement(featureMgr.ilastikFeatureGroups.createList())
        
    @QtCore.pyqtSignature("")     
    def on_confirmButtons_accepted(self):  
        self.parent.project.featureMgr = featureMgr.FeatureMgr(self.parent.project.dataMgr)

        featureSelectionList = featureMgr.ilastikFeatureGroups.createList()
        self.parent.project.featureMgr.setFeatureItems(featureSelectionList)
        self.computeMemoryRequirement(featureSelectionList)
        self.close()
        
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()
        
    def computeMemoryRequirement(self, featureSelectionList):
        if featureSelectionList != []:
            dataMgr = self.parent.project.dataMgr
            if dataMgr[0].dataVol.data.shape[1] > 1:
                #3D
                dimSel = 1
            else:
                #2D
                dimSel = 0
                
            numOfChannels = dataMgr[0].dataVol.data.shape[-1]
            numOfEffectiveFeatures = reduce(lambda x,y: x +y, [k.numOfOutputs[dimSel] for k in featureSelectionList]) * numOfChannels
            numOfPixels = numpy.sum([ numpy.prod(dataItem.dataVol.data.shape[:-1]) for dataItem in dataMgr ])
            # 7 bytes per pixel overhead
            memoryReq = numOfPixels * (7 + numOfEffectiveFeatures*4.0) /1024.0**2
            print "Total feature vector length is %d with aprox. memory demand of %8.2f MB" % (numOfEffectiveFeatures, memoryReq)
        else:
            print "No features selected"
        # return memoryReq

class FeatureComputation(object):
    def __init__(self, parent):
        self.parent = parent
        self.parent.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(False)
        self.parent.ribbon.tabDict['Features'].itemDict['Select'].setEnabled(False)
        self.featureCompute()
        
        
    
    def featureCompute(self):
        self.parent.project.dataMgr.featureLock.acquire()
        self.myTimer = QtCore.QTimer()
        self.parent.connect(self.myTimer, QtCore.SIGNAL("timeout()"), self.updateFeatureProgress)
        self.parent.project.dataMgr.clearFeaturesAndTraining()
        numberOfJobs = self.parent.project.featureMgr.prepareCompute(self.parent.project.dataMgr)   
        self.initFeatureProgress(numberOfJobs)
        self.parent.project.featureMgr.triggerCompute()
        self.myTimer.start(200)
        
    def initFeatureProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myFeatureProgressBar = QtGui.QProgressBar()
        self.myFeatureProgressBar.setMinimum(0)
        self.myFeatureProgressBar.setMaximum(numberOfJobs)
        self.myFeatureProgressBar.setFormat(' Features... %p%')
        statusBar.addWidget(self.myFeatureProgressBar)
        statusBar.show()
    
    def updateFeatureProgress(self):
        val = self.parent.project.featureMgr.getCount() 
        self.myFeatureProgressBar.setValue(val)
        if not self.parent.project.featureMgr.featureProcess.is_alive():
            self.myTimer.stop()
            self.terminateFeatureProgressBar()
            self.parent.project.featureMgr.joinCompute(self.parent.project.dataMgr)
            
            
    def terminateFeatureProgressBar(self):
        self.parent.statusBar().removeWidget(self.myFeatureProgressBar)
        self.parent.statusBar().hide()
        self.parent.project.dataMgr.buildTrainingMatrix()
        self.parent.project.dataMgr.featureLock.release()
        if hasattr(self.parent, "classificationInteractive"):
            self.parent.classificationInteractive.updateThreadQueues()
            
        self.parent.ribbon.tabDict['Features'].itemDict['Select'].setEnabled(True)            
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(True)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Interactive'].setEnabled(True)        
                    
    def featureShow(self, item):
        pass

class ClassificationTrain(object):
    def __init__(self, parent):
        self.parent = parent
        self.start()
        
    def start(self):
        #process all unaccounted label changes
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(False)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(False)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Batchprocess'].setEnabled(False)        
        
        newLabels = self.parent.labelWidget.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.updateTrainingMatrix(self.parent.activeImage, newLabels)
        
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
        numberOfJobs = 10                 
        self.initClassificationProgress(numberOfJobs)
        
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, self.parent.project.dataMgr)
        self.classificationProcess.start()
        self.classificationTimer.start(500) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Training... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationProcess.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationProcess.isRunning():
            self.classificationTimer.stop()
            self.classificationProcess.wait()
            self.finalize()
            self.terminateClassificationProgressBar()
            
    def finalize(self):
        pass
                      
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(True)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(True)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Batchprocess'].setEnabled(True)        
        

class ClassificationInteractive(object):
    def __init__(self, parent):
        self.parent = parent
        self.stopped = False
        self.trainingQueue = deque(maxlen=1)
        self.predictionQueue = deque(maxlen=1)
        self.resultQueue = deque(maxlen=3)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(False)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(False)

        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.updateThreadQueues)
        self.temp_cnt = 0
        self.start()
    
    def updateThreadQueues(self):
        if self.classificationInteractive is not None:
            self.myInteractionProgressBar.setVisible(True)
            self.classificationInteractive.dataPending.set()

    def updateLabelWidget(self):
        try:
            self.myInteractionProgressBar.setVisible(False)
            self.parent.labelWidget.repaint()                    
        except IndexError:
            pass
                


    def initInteractiveProgressBar(self):
        statusBar = self.parent.statusBar()
        self.myInteractionProgressBar = QtGui.QProgressBar()
        self.myInteractionProgressBar.setVisible(False)
        self.myInteractionProgressBar.setMinimum(0)
        self.myInteractionProgressBar.setMaximum(0)
        statusBar.addWidget(self.myInteractionProgressBar)
        statusBar.show()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myInteractionProgressBar)
        self.parent.statusBar().hide()
        
    def start(self):
               
        self.initInteractiveProgressBar()
        self.classificationInteractive = classificationMgr.ClassifierInteractiveThread(self.parent, self.trainingQueue, self.predictionQueue, self.resultQueue)

        self.parent.connect(self.classificationInteractive, QtCore.SIGNAL("resultsPending()"), self.updateLabelWidget)      
    
               
        self.classificationInteractive.start()
        self.updateThreadQueues()
        
        
    def stop(self):
        self.classificationInteractive.stopped = True

        self.classificationInteractive.dataPending.set() #wake up thread one last time before his death
        self.classificationInteractive.wait()
        self.finalize()
        
        self.terminateClassificationProgressBar()
    
    def finalize(self):
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(True)
        if len(self.parent.project.dataMgr.classifiers)>0:
            self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(True)
        
        self.parent.project.dataMgr.classifiers = list(self.classificationInteractive.classifiers)
        self.classificationInteractive =  None
        
#class ClassificationOnline(object):
#    def __init__(self, parent):
#        print "Online Classification initialized"
#        self.parent = parent
#        
#        self.OnlineThread = None
#        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending'), self.updateTrainingData)
#        self.parent.connect(self.parent, QtCore.SIGNAL('newPredictionsPending'), self.updatePredictionData)
#
#    def __del__(self):
#        self.parent.labelWidget.disconnect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending'))
#        self.parent.disconnect(self.parent,self.QtCore.SIGNAL('newPredictionsPending'))
#        
#    def start(self,name):
#        print "Online Classification starting"
#
#        #self.parent.generateTrainingData()
#        
#        features = self.parent.project.trainingMatrix
#        labels = self.parent.project.trainingLabels  
#
#        self.parent.labelWidget.labelForImage[0].DrawManagers[0].createBrushQueue('onlineLearning')
#        predictionList = self.parent.project.dataMgr.buildFeatureMatrix()
#        ids = numpy.zeros((len(labels),)).astype(numpy.int32)
#
#        self.OnlineThread = classificationMgr.ClassifierOnlineThread(name, features, labels.astype(numpy.int32), ids, predictionList, self.predictionUpdatedCallBack)
#        self.OnlineThread.start()
#        
#    def stop(self):
#        print "Online Classification stopped"
#        self.OnlineThread.stopped = True
#        self.OnlineThread.commandQueue.put((None, None, None, 'stop'))
#        print "Joining thread"
#        self.OnlineThread.wait()
#        print "Thread stopped"
#        self.OnlineThread = None
#        self.parent.labelWidget.labelForImage[0].DrawManagers[0].deleteBrushQueue('onlineLearning')
#    
#    def predictionUpdatedCallBack(self):
#        self.parent.emit(QtCore.SIGNAL('newPredictionsPending'))
#
#    def updatePredictionData(self):
#        print "Updating prediction data"
#        tic = time.time()
#        if self.OnlineThread == None:
#            return
#        new_pred=self.OnlineThread.predictions[self.parent.labelWidget.activeImage].pop()
#        #self.preds=numpy.zeros((new_pred.shape[0],2))
#        #for i in xrange(len(new_pred)):
#        #    self.preds[i,0]=1.0-new_pred[i]
#        #    self.preds[i,1]=new_pred[i]
#        print new_pred.shape
#
#        tmp = {}
#        print new_pred.shape
#        tmp[self.parent.labelWidget.activeImage] = new_pred
#        self.parent.labelWidget.OverlayMgr.updatePredictionsPixmaps(tmp)
#        self.parent.labelWidget.OverlayMgr.setOverlayState('Prediction')
#        
#        
#        print "Done updating prediction data: %f secs" % (time.time() - tic)
#        #self.parent.labelWidget.OverlayMgr.showOverlayPixmapByState()
#        
#    
#    def updateTrainingData(self):
#        active_image=self.parent.labelWidget.activeImage
#        print active_image
#        Labels=self.parent.labelWidget.labelForImage[active_image].DrawManagers[0].labelmngr.labelArray
#        queue=self.parent.labelWidget.labelForImage[active_image].DrawManagers[0].BrushQueues['onlineLearning']
#
#        #TODO: make as many as there are images
#        labelArrays=[numpy.array([0])] * (active_image+1)
#
#        while(True):
#            labelArrays[active_image]=numpy.zeros(Labels.shape,Labels.dtype)
#            try:
#                step=queue.pop()
#            except IndexError:
#                break
#            #decompose step, start by removing data
#            remove_data=[]
#
#            for i in xrange(len(step.oldValues)):
#                if step.oldValues[i]!=0 or step.isUndo:
#                    remove_data.append(step.positions[i])
#            remove_data=numpy.array(remove_data).astype(numpy.float32)
#            self.OnlineThread.commandQueue.put((None,None,remove_data,'remove'))
#
#            #add new data
#            add_indexes=[]
#            for i in xrange(len(step.oldValues)):
#                if (not step.isUndo and step.newLabel!=0) or (step.isUndo and step.oldValues[i]!=0): 
#                    add_indexes.append(step.positions[i])
#                    labelArrays[active_image][step.positions[i]]=Labels[step.positions[i]]
#            #create the new features
#            #self.parent.generateTrainingData(labelArrays)
#            add_indexes=numpy.array(add_indexes)
#
#            print "*************************************"
#            print "************* SENDING ***************"
#            print "*************************************"
#            self.OnlineThread.commandQueue.put((self.parent.project.trainingMatrix,
#                                                self.parent.project.trainingLabels.astype(numpy.int32),
#                                                numpy.array(add_indexes).astype(numpy.int32),'learn'))
        
    
class ClassificationPredict(object):
    def __init__(self, parent):
        self.parent = parent
        self.start()
    
    def start(self):       
        self.parent.ribbon.tabDict['Classification'].itemDict['Interactive'].setEnabled(False)        
        self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(False)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(False)
          
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
                    
        self.classificationPredict = classificationMgr.ClassifierPredictThread(self.parent.project.dataMgr)
        numberOfJobs = self.classificationPredict.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.classificationPredict.start()
        self.classificationTimer.start(200) 

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.myClassificationProgressBar = QtGui.QProgressBar()
        self.myClassificationProgressBar.setMinimum(0)
        self.myClassificationProgressBar.setMaximum(numberOfJobs)
        self.myClassificationProgressBar.setFormat(' Prediction... %p%')
        statusBar.addWidget(self.myClassificationProgressBar)
        statusBar.show()
    
    def updateClassificationProgress(self):
        val = self.classificationPredict.count
        self.myClassificationProgressBar.setValue(val)
        if not self.classificationPredict.isRunning():
            self.classificationTimer.stop()

            self.classificationPredict.wait()
            self.finalize()           
            self.terminateClassificationProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent.activeImage]
        if activeItem.prediction is not None:
            print activeItem.prediction.shape
            for p_i, item in enumerate(activeItem.dataVol.labels.descriptions):
                print ":", item.prediction.shape
                item.prediction[:,:,:,:] = (activeItem.prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)

            margin = activeLearning.computeEnsembleMargin(activeItem.prediction[:,:,:,:,:])*255.0
            activeItem.dataVol.uncertainty[:,:,:,:] = margin[:,:,:,:]
            seg = segmentationMgr.LocallyDominantSegmentation(activeItem.prediction[:,:,:,:,:], 1.0)
            activeItem.dataVol.segmentation[:,:,:,:] = seg[:,:,:,:]

            self.parent.labelWidget.repaint()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Classification'].itemDict['Predict'].setEnabled(True)  
        self.parent.ribbon.tabDict['Classification'].itemDict['Interactive'].setEnabled(True)  
        self.parent.ribbon.tabDict['Classification'].itemDict['Train'].setEnabled(True)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow(sys.argv)
      
    mainwindow.show() 
    app.exec_()
    print "cleaning up..."
    if mainwindow.labelWidget is not None:
        del mainwindow.labelWidget
    del mainwindow
    del jobMachine.GLOBAL_WM
    

