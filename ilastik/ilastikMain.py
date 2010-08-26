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

from OpenGL.GL import *
try:
    from OpenGL.GLX import *
    XInitThreads()
except:
    pass

import vigra
from vigra import arraytypes as at

import sys
import os

import threading
import traceback
import numpy
import time
from PyQt4 import QtCore, QtGui, uic

import ilastik
from ilastik.core import version, dataMgr, projectMgr, featureMgr, classificationMgr, segmentationMgr, activeLearning, onlineClassifcator, dataImpex
from ilastik.gui import ctrlRibbon, stackloader, fileloader, batchProcess
from ilastik.gui.featureDlg import FeatureDlg
from Queue import Queue as queue
from collections import deque
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.core.utilities import irange, debug
from ilastik.gui.classifierSelectionDialog import ClassifierSelectionDlg
from ilastik.core import jobMachine
import copy
import h5py

from OpenGL.GL import *

from PyQt4 import QtCore, QtGui, QtOpenGL
import getopt

from ilastik.gui import volumeeditor as ve
from ilastik.gui.shortcutmanager import *

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#bad bad bad
LAST_DIRECTORY = os.path.expanduser("~")

class MainWindow(QtGui.QMainWindow):
    global LAST_DIRECTORY
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.fullScreen = False
        self.setGeometry(50, 50, 800, 600)
        
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
                    self.featureCache = h5py.File(a, 'w')
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

            help_text = "Normally the default option should work for you\nhowever, in some cases it might be beneficial to try to use another rendering method:"
            if int(gl_version[0]) >= 2:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', help_text, ['OpenGL + OpenGL Overview', 'Software + OpenGL Overview', 'Software without Overview'], 0, False)
            elif int(gl_version[0]) > 0:
                dl = QtGui.QInputDialog.getItem(None,'Graphics Setup', help_text, ['Software + OpenGL Overview', 'Software without Overview'], 0, False)
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
            self.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(True)
            self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
            self.ribbon.tabDict['Classification'].itemDict['Classifier Options'].setEnabled(True)
            self.activeImage = 0
            self.projectModified()
        
        self.shortcutSave = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.saveProject, self.saveProject) 
        self.shortcutFullscreen = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+F"), self, self.showFullscreen, self.showFullscreen) 
    
    def showFullscreen(self):
        if self.fullScreen:
            self.showNormal()
        else:
            self.showFullScreen()
        self.fullScreen = not self.fullScreen
                
    def updateFileSelector(self):
        self.fileSelectorList.blockSignals(True)
        self.fileSelectorList.clear()
        self.fileSelectorList.blockSignals(False)
        for index, item in enumerate(self.project.dataMgr):
            self.fileSelectorList.addItem(item.Name)
    
    def changeImage(self, number):
        self.activeImageLock.acquire()
        QtCore.QCoreApplication.processEvents()
        if hasattr(self, "classificationInteractive"):
            #self.labelWidget.disconnect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
            self.classificationInteractive.stop()
            del self.classificationInteractive
            self.classificationInteractive = True
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
            self.classificationInteractive = ClassificationInteractive(self)
            #self.labelWidget.connect(self.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.classificationInteractive.updateThreadQueues)
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
        
        ribbonDict = ctrlRibbon.createRibbons()
        
        for k in range(10):
            for ribbon_group in ribbonDict.values():
                if ribbon_group.position == k:
                    tabs = ribbon_group.makeTab()   
                    self.ribbon.addTab(tabs, ribbon_group.name)
                    print "Add tab", ribbon_group.name
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
        self.connect(self.ribbon.tabDict['Projects'].itemDict['Options'], QtCore.SIGNAL('clicked()'), self.optionsDlg)
        self.connect(self.ribbon.tabDict['Features'].itemDict['Select and Compute'], QtCore.SIGNAL('clicked()'), self.newFeatureDlg)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Train and Predict'], QtCore.SIGNAL('clicked()'), self.on_classificationTrain)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'], QtCore.SIGNAL('clicked(bool)'), self.on_classificationInteractive)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Classifier Options'], QtCore.SIGNAL('clicked(bool)'), self.on_changeClassifier)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Import Classifier'], QtCore.SIGNAL('clicked(bool)'), self.on_importClassifier)
        self.connect(self.ribbon.tabDict['Classification'].itemDict['Export Classifier'], QtCore.SIGNAL('clicked(bool)'), self.on_exportClassifier)
        self.connect(self.ribbon.tabDict['Automate'].itemDict['Batchprocess'], QtCore.SIGNAL('clicked(bool)'), self.on_batchProcess)
        self.connect(self.ribbon.tabDict['Help'].itemDict['Shortcuts'], QtCore.SIGNAL('clicked(bool)'), self.on_shortcutsDlg)
        #self.connect(self.ribbon.tabDict['Classification'].itemDict['Online'], QtCore.SIGNAL('clicked(bool)'), self.on_classificationOnline)

        #self.connect(self.ribbon.tabDict['Segmentation'].itemDict['Segment'], QtCore.SIGNAL('clicked(bool)'), self.on_segmentation)
        #self.connect(self.ribbon.tabDict['Segmentation'].itemDict['BorderSegment'], QtCore.SIGNAL('clicked(bool)'), self.on_segmentation_border)
        
        self.ribbon.tabDict['Classification'].itemDict['Export Classifier'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Classifier Options'].setEnabled(False)
        
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
             
        
#        self.connect(self.ribbon.tabDict['Export'].itemDict['Export'], QtCore.SIGNAL('clicked()'), self.export2Hdf5)
        
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(False)
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setToolTip('Add and Remove files from the current project')
        self.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(False)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(False)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setToolTip('Save the current Project')
        self.ribbon.tabDict['Features'].itemDict['Select and Compute'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setToolTip('Train the RandomForest classifier with the computed features and the provided labels.')
        self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setToolTip('Train the RandomForest classifier while drawing labels and browsing through the file. \nThe currently visible part of the image gets predicted on the fly.')
        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setToolTip('Batchprocess a list of files with the currently trained classifier.\n The processed files and their prediction are stored with the file extension "_processed.h5" ')

#        self.ribbon.tabDict['Export'].itemDict['Export'].setEnabled(False)
        
        #self.ribbon.tabDict['Features'].itemDict['Compute'].setEnabled(False)
        #self.ribbon.tabDict['Classification'].itemDict['Compute'].setEnabled(False)
        
        self.ribbon.setCurrentIndex (0)
          
    def newProjectDlg(self):
        self.projectDlg = ProjectDlg(self)
    
    def saveProjectDlg(self):
        global LAST_DIRECTORY
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", LAST_DIRECTORY, "Project Files (*.ilp)")
        fn = str(fileName)
        if len(fn) > 4:
            if fn[-4:] != '.ilp':
                fn = fn + '.ilp'
            self.project.saveToDisk(fn)
            LAST_DIRECTORY = QtCore.QFileInfo(fn).path()
            

                
            
    def saveProject(self):
        if hasattr(self,'project'):
            if self.project.filename is not None:
                self.project.saveToDisk()
            else:
                self.saveProjectDlg()
            print "saved Project to ", self.project.filename
        
    def loadProjectDlg(self):
        global LAST_DIRECTORY
        print LAST_DIRECTORY
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Project", LAST_DIRECTORY, "Project Files (*.ilp)")
        if str(fileName) != "":
            LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
            self.project = projectMgr.Project.loadFromDisk(str(fileName), self.featureCache)
            self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
            self.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(True)
            self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
            self.ribbon.tabDict['Classification'].itemDict['Classifier Options'].setEnabled(True)
            if hasattr(self, 'projectDlg'):
                self.projectDlg.deleteLater()
            self.activeImage = 0
            self.projectModified()
        
    def editProjectDlg(self):
        self.projectDlg = ProjectDlg(self, False)
        self.projectDlg.updateDlg(self.project)
        self.projectModified()
            
        
    def projectModified(self):
        self.updateFileSelector() #this one also changes the image
        #self.changeImage(self.activeImage)
        self.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(True)
        self.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        self.ribbon.tabDict['Features'].itemDict['Select and Compute'].setEnabled(True)
        
    def optionsDlg(self):
        tmp = ProjectSettingsDlg(self, self.project)
        tmp.exec_()
        
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
        self.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
        self.ribbon.tabDict['Classification'].itemDict['Export Classifier'].setEnabled(False)
        
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
            self.labelWidget.deleteLater()
                
    def createImageWindows(self, dataVol):
        self.labelWidget = ve.VolumeEditor(dataVol, embedded = True, opengl = self.opengl, openglOverview = self.openglOverview, parent = self)
        self.labelWidget.labelView.labelPropertiesChanged_callback = self.updateLabelWidgetOverlays

        self.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
        self.labelWidget.normalizeData = self.project.normalizeData
        self.labelWidget.useBorderMargin = self.project.useBorderMargin
        self.labelWidget.setRgbMode(self.project.rgbData)
        
        #self.connect(self.labelWidget.labelView, QtCore.SIGNAL("labelPropertiesChanged()"),self.updateLabelWidgetOverlays)
        self.connect(self.labelWidget.labelView, QtCore.SIGNAL("labelRemoved(int)"),self.labelRemoved)
                
        dock = QtGui.QDockWidget("Ilastik Label Widget", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)

        
        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

    def labelRemoved(self, number):
        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
        self.project.dataMgr.removeLabel(number)
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive.updateThreadQueues()

    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        if self.project.featureMgr is not None:
            self.featureComputation = FeatureComputation(self)

    def on_shortcutsDlg(self):
        shortcutManager.showDialog()

    def on_batchProcess(self):
        dialog = batchProcess.BatchProcess(self)
        result = dialog.exec_()
    
    def on_changeClassifier(self):
        dialog = ClassifierSelectionDlg(self)
        self.project.classifier = dialog.exec_()
        print self.project.classifier


    def on_classificationTrain(self):
        self.classificationTrain = ClassificationTrain(self)
        
    def on_classificationPredict(self):
        self.classificationPredict = ClassificationPredict(self)
    
    def on_classificationInteractive(self, state):
        if state:
	    self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setText('Stop Live Prediction')
            self.classificationInteractive = ClassificationInteractive(self)
        else:
            self.classificationInteractive.stop()
            del self.classificationInteractive
	    self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setText('Start Live Prediction')



    def on_segmentation(self):
        pass

    def on_segmentation_border(self):
        pass
    
    def on_importClassifier(self):
        global LAST_DIRECTORY
        fileName = str(QtGui.QFileDialog.getOpenFileName(self, "Import Classifier", LAST_DIRECTORY, "Classifier File (*.h5 *.ilc)"))
        
        hf = h5py.File(fileName,'r')
        h5featGrp = hf['features']
        self.project.featureMgr.importFeatureItems(h5featGrp)
        hf.close()
        
        self.project.dataMgr.importClassifiers(fileName)
    
    def on_exportClassifier(self):
        global LAST_DIRECTORY
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", LAST_DIRECTORY, "HDF5 Files (*.h5)")
        LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
        
        try:
            self.project.dataMgr.exportClassifiers(fileName)
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            return

        try:
            h5file = h5py.File(str(fileName),'a')
            h5featGrp = h5file.create_group('features')
            self.project.featureMgr.exportFeatureItems(h5featGrp)
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            h5file.close()
            return
        h5file.close()

        QtGui.QMessageBox.information(self, 'Sucess', "The classifier and the feature information have been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
        
        
        
        

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Save before Exit?', "Save the Project before quitting the Application", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.saveProject()
            event.accept()
        elif reply == QtGui.QMessageBox.No:
            event.accept()
        else:
            event.ignore()
            
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
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(os.path.join(ilastikPath,os.path.join("gui", "dlgProject.ui")), self) 
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
                self.dataMgr.append(theDataItem, True)
                self.dataMgr.dataItemsLoaded[-1] = True

                theDataItem.hasLabels = True
                theDataItem.isTraining = True
                theDataItem.isTesting = True

                self.ilastik.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
                self.ilastik.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(True)

                self.ilastik.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)

                rowCount = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowCount)

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
            print "items returned: ", len(itemList)
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
        global LAST_DIRECTORY
        fileNames = QtGui.QFileDialog.getOpenFileNames(self, "Open Image", LAST_DIRECTORY, "Image Files (*.png *.jpg *.bmp *.tif *.gif *.h5)")
        fileNames.sort()
        if fileNames:
            for file_name in fileNames:
                LAST_DIRECTORY = QtCore.QFileInfo(file_name).path()
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
                theDataItem.dataVol.labels = None
                
            contained = False
            for pr in theDataItem.projects:
                if pr == self.parent.project:
                    contained = true
            if not contained:
                theDataItem.projects.append(self.parent.project)
        
        self.parent.ribbon.tabDict['Projects'].itemDict['Edit'].setEnabled(True)
        self.parent.ribbon.tabDict['Projects'].itemDict['Options'].setEnabled(True)

        self.parent.ribbon.tabDict['Projects'].itemDict['Save'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Classifier Options'].setEnabled(True)
        
        self.parent.activeImage = 0
        self.parent.projectModified()
        self.close()
        
    
    @QtCore.pyqtSignature("")    
    def on_confirmButtons_rejected(self):
        self.close()
        
        


class FeatureComputation(object):
    def __init__(self, parent):
        self.parent = parent
        self.parent.ribbon.tabDict['Features'].itemDict['Select and Compute'].setEnabled(False)
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
        if not self.parent.project.featureMgr.featureProcess.isRunning():
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
            
        self.parent.ribbon.tabDict['Features'].itemDict['Select and Compute'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(True)
                    
    def featureShow(self, item):
        pass

class ClassificationTrain(object):
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()
        
    def start(self):
        #process all unaccounted label changes
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
        self.parent.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
        
        newLabels = self.parent.labelWidget.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.updateTrainingMatrix(self.parent.activeImage, newLabels)
        
        self.classificationTimer = QtCore.QTimer()
        self.parent.connect(self.classificationTimer, QtCore.SIGNAL("timeout()"), self.updateClassificationProgress)      
        numberOfJobs = 10                 
        self.initClassificationProgress(numberOfJobs)
        
        self.classificationProcess = classificationMgr.ClassifierTrainThread(numberOfJobs, self.parent.project.dataMgr, classifier = self.parent.project.classifier)
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
            self.terminateClassificationProgressBar()
            self.finalize()
            
    def finalize(self):
        self.ilastik.on_classificationPredict()
                      
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        self.parent.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(True)
        

class ClassificationInteractive(object):
    def __init__(self, parent):
        self.parent = parent
        self.stopped = False
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)

        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.updateThreadQueues)
        self.parent.labelWidget.connect(self.parent.labelWidget,QtCore.SIGNAL('changedSlice(int, int)'), self.updateThreadQueues)

        self.temp_cnt = 0
        self.start()
    
    def updateThreadQueues(self, a = 0, b = 0):
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
        self.classificationInteractive = classificationMgr.ClassifierInteractiveThread(self.parent, classifier = self.parent.project.classifier)

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
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        
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
        self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
          
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
#            for p_i, item in enumerate(activeItem.dataVol.labels.descriptions):
#                item.prediction[:,:,:,:] = (activeItem.prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)
            for p_i, p_num in enumerate(self.parent.project.dataMgr.classifiers[0].unique_vals):
                activeItem.dataVol.labels.descriptions[p_num-1].prediction[:,:,:,:] = (activeItem.prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)

            all =  range(len(activeItem.dataVol.labels.descriptions))
            not_predicted = numpy.setdiff1d(all, self.parent.project.dataMgr.classifiers[0].unique_vals - 1)
            for p_i, p_num in enumerate(not_predicted):
                activeItem.dataVol.labels.descriptions[p_num].prediction[:,:,:,:] = 0



            margin = activeLearning.computeEnsembleMargin(activeItem.prediction[:,:,:,:,:])*255.0
            activeItem.dataVol.uncertainty[:,:,:,:] = margin[:,:,:,:]
            seg = segmentationMgr.LocallyDominantSegmentation(activeItem.prediction[:,:,:,:,:], 1.0)
            activeItem.dataVol.segmentation[:,:,:,:] = seg[:,:,:,:]

            self.parent.labelWidget.repaint()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        self.parent.ribbon.tabDict['Classification'].itemDict['Export Classifier'].setEnabled(True)

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
    

