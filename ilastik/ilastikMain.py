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

import sys
import os
from PyQt4 import QtCore, QtGui, uic

#force QT4 toolkit for the enthought traits UI
os.environ['ETS_TOOLKIT'] = 'qt4'

import vigra
from vigra import arraytypes as at


import threading
import traceback
import numpy
import time

import ilastik.gui
from ilastik.gui.segmentationWeightSelectionDlg import SegmentationWeightSelectionDlg
from ilastik.core import version, dataMgr, projectMgr, featureMgr, classificationMgr, segmentationMgr, activeLearning, onlineClassifcator, dataImpex
from ilastik.gui import ctrlRibbon, stackloader, fileloader, batchProcess
from ilastik.gui.featureDlg import FeatureDlg
from Queue import Queue as queue
from collections import deque
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.core.utilities import irange, debug
from ilastik.gui.classifierSelectionDialog import ClassifierSelectionDlg
from ilastik.gui.segmentorSelectionDlg import SegmentorSelectionDlg
from ilastik.gui.ribbons.ribbonBase import IlastikTabBase
from ilastik.gui.projectDialog import ProjectDlg
import copy
import h5py

from OpenGL.GL import *

from PyQt4 import QtCore, QtGui, QtOpenGL
import getopt

from ilastik.gui import volumeeditor as ve
from ilastik.gui.shortcutmanager import *

from ilastik.gui.labelWidget import LabelListWidget
from ilastik.gui.seedWidget import SeedListWidget
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor,  Volume


from ilastik import core
import core.segmentors

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#bad bad bad
#LAST_DIRECTORY = os.path.expanduser("~")




class MainWindow(QtGui.QMainWindow):
    #global LAST_DIRECTORY
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
            self.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
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
        for item in self.project.dataMgr:
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

        self.activeImage = number
        self.project.dataMgr.activeImage = number
        
        self.destroyImageWindows()

        self.createImageWindows( self.project.dataMgr[number].dataVol)
        
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
        from ilastik.gui.ribbons.standardRibbons import ProjectTab
        
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.IlastikTabWidget(self.ribbonToolbar)
        
        self.ribbonToolbar.addWidget(self.ribbon)
        
        self.ribbonsTabs = IlastikTabBase.__subclasses__()

        for tab in self.ribbonsTabs:
            self.ribbon.addTab(tab(self), tab.name)
        
   
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
  
        self.ribbon.setCurrentIndex (0)
        self.connect(self.ribbon,QtCore.SIGNAL("currentChanged(int)"),self.tabChanged)


    def tabChanged(self,  index):
        """
        update the overlayWidget of the volumeEditor and switch the history
        between seeds and labels, also make sure the 
        seed/label widget has a reference to the overlay in the overlayWidget
        they correspond to.
        """
        
        self.ribbon.widget(index).on_activation()
        
        if self.ribbon.tabText(index) == "Segmentation":
            if self.labelWidget.history != self.project.dataMgr[self.activeImage].dataVol.seeds.history:
                self.project.dataMgr[self.activeImage].dataVol.labels.history = self.labelWidget.history
                
            if self.project.dataMgr[self.activeImage].dataVol.seeds.history is not None:
                self.labelWidget.history = self.project.dataMgr[self.activeImage].dataVol.seeds.history
            
            self.labelWidget.history.volumeEditor = self.labelWidget

            overlayWidget = OverlayWidget(self.labelWidget, self.project.dataMgr[self.activeImage].overlayMgr,  self.project.dataMgr[self.activeImage].dataVol.seedOverlays)
            self.labelWidget.setOverlayWidget(overlayWidget)
            
            #create SeedsOverlay
            ov = OverlayItem(self.project.dataMgr[self.activeImage].dataVol.seeds.data, color = 0, alpha = 1.0, colorTable = self.project.dataMgr[self.activeImage].dataVol.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
            self.project.dataMgr[self.activeImage].overlayMgr["Segmentation/Seeds"] = ov
            ov = self.project.dataMgr[self.activeImage].overlayMgr["Segmentation/Seeds"]

            self.labelWidget.setLabelWidget(SeedListWidget(self.project.seedMgr,  self.project.dataMgr[self.activeImage].dataVol.seeds,  self.labelWidget,  ov))
            
            
        elif self.labelWidget is not None:
            if self.labelWidget.history != self.project.dataMgr[self.activeImage].dataVol.labels.history:
                self.project.dataMgr[self.activeImage].dataVol.seeds.history = self.labelWidget.history
            
            if self.project.dataMgr[self.activeImage].dataVol.labels.history is not None:
                self.labelWidget.history = self.project.dataMgr[self.activeImage].dataVol.labels.history
            self.labelWidget.history.volumeEditor = self.labelWidget
            
            overlayWidget = OverlayWidget(self.labelWidget, self.project.dataMgr[self.activeImage].overlayMgr,  self.project.dataMgr[self.activeImage].dataVol.labelOverlays)
            self.labelWidget.setOverlayWidget(overlayWidget)
            
            #create LabelOverlay
            ov = OverlayItem(self.project.dataMgr[self.activeImage].dataVol.labels.data, color = 0, alpha = 1.0, colorTable = self.project.dataMgr[self.activeImage].dataVol.labels.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
            self.project.dataMgr[self.activeImage].overlayMgr["Classification/Labels"] = ov
            ov = self.project.dataMgr[self.activeImage].overlayMgr["Classification/Labels"]
            
            self.labelWidget.setLabelWidget(LabelListWidget(self.project.labelMgr,  self.project.dataMgr[self.activeImage].dataVol.labels,  self.labelWidget,  ov))

            
        if self.labelWidget is not None:
            self.labelWidget.repaint()     
            
    def saveProject(self):
        if hasattr(self,'project'):
            if self.project.filename is not None:
                self.project.saveToDisk()
            else:
                self.saveProjectDlg()
            print "saved Project to ", self.project.filename
            
        
    def projectModified(self):
        self.updateFileSelector() #this one also changes the image
        self.project.dataMgr.activeImage = self.activeImage
          
#    def newFeatureDlg(self):
#        self.newFeatureDlg = FeatureDlg(self)
#        self.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
#        self.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
#        self.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
#        self.ribbon.tabDict['Classification'].itemDict['Save Classifier'].setEnabled(False)
        
        
    def initImageWindows(self):
        self.labelDocks = []
        
    def destroyImageWindows(self):
        for dock in self.labelDocks:
            self.removeDockWidget(dock)
        self.labelDocks = []
        if self.labelWidget is not None:
            self.labelWidget.close()
            self.labelWidget.deleteLater()
                
    def createImageWindows(self, dataVol):
        self.labelWidget = ve.VolumeEditor(dataVol, self,  opengl = self.opengl, openglOverview = self.openglOverview)

        if dataVol.labels.history is None:
            dataVol.labels.history = ve.HistoryManager(self.labelWidget)

        if dataVol.seeds.history is None:
            dataVol.seeds.history = ve.HistoryManager(self.labelWidget)

        self.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
        self.labelWidget.normalizeData = self.project.normalizeData
        self.labelWidget.useBorderMargin = self.project.useBorderMargin
        self.labelWidget.setRgbMode(self.project.rgbData)
        
        #setup sub-widgets
        self.labelWidget.setOverlayWidget(OverlayWidget(self.labelWidget, self.project.dataMgr[self.activeImage].overlayMgr,  self.project.dataMgr[self.activeImage].dataVol.labelOverlays))
        #create LabelOverlay
        ov = OverlayItem(self.project.dataMgr[self.activeImage].dataVol.labels.data, color = 0, alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.project.dataMgr[self.activeImage].overlayMgr["Classification/Labels"] = ov
        self.labelWidget.setLabelWidget(LabelListWidget(self.project.labelMgr,  self.project.dataMgr[self.activeImage].dataVol.labels,  self.labelWidget,  ov))
        ov.colorTable = self.labelWidget.labelWidget.colorTab
        
        dock = QtGui.QDockWidget("Ilastik Label Widget", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)

        self.connect(self.labelWidget, QtCore.SIGNAL("labelRemoved(int)"),self.labelRemoved)
        self.connect(self.labelWidget, QtCore.SIGNAL("seedRemoved(int)"),self.seedRemoved)
        
        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

    def labelRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive.updateThreadQueues()


    def seedRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        self.project.dataMgr.removeSeed(number)
        if hasattr(self, "segmentationInteractive"):
            self.segmentatinoInteractive.updateThreadQueues()


    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def featureCompute(self):
        if self.project.featureMgr is not None:
            self.featureComputation = FeatureComputation(self)

    def on_shortcutsDlg(self):
        shortcutManager.showDialog()

#    def on_batchProcess(self):
#        dialog = batchProcess.BatchProcess(self)
#        result = dialog.exec_()
    
#    def on_changeClassifier(self):
#        dialog = ClassifierSelectionDlg(self)
#        self.project.classifier = dialog.exec_()
#        print self.project.classifier

#    def on_changeSegmentor(self):
#        dialog = SegmentorSelectionDlg(self)
#        answer = dialog.exec_()
#        if answer != None:
#            self.project.segmentor = answer
#            self.project.segmentor.setupWeights(self.project.dataMgr[self.activeImage].segmentationWeights)

    def on_segmentationWeights(self):
        
        list = self.project.dataMgr[self.activeImage].overlayMgr.keys()
        selection = QtGui.QInputDialog.getItem(None, "Select Segmentation Weights",  "Weights",  list,  editable = False)
        selection = str(selection[0])
        
        overlay = self.project.dataMgr[self.activeImage].overlayMgr[selection]

        volume = overlay.data[0,:,:,:,0]
        
        print numpy.max(volume),  numpy.min(volume)

        real_weights = numpy.zeros(volume.shape + (3,))        
        
        borderIndicator = QtGui.QInputDialog.getItem(None, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness",  "Gradient"],  editable = False)
        borderIndicator = str(borderIndicator[0])
        
        sigma = 1.0
        normalizePotential = True
        #TODO: this , until now, only supports gray scale and 2D!
        if borderIndicator == "Brightness":
            weights = vigra.filters.gaussianSmoothing(volume[:,:,:].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma)
            weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
            real_weights[:,:,:,0] = weights[:,:,:]
            real_weights[:,:,:,1] = weights[:,:,:]
            real_weights[:,:,:,2] = weights[:,:,:]
        elif borderIndicator == "Darkness":
            weights = vigra.filters.gaussianSmoothing((255 - volume[:,:,:]).swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma)
            weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
            real_weights[:,:,:,0] = weights[:,:,:]
            real_weights[:,:,:,1] = weights[:,:,:]
            real_weights[:,:,:,2] = weights[:,:,:]
        elif borderIndicator == "Gradient":
            weights = numpy.abs(vigra.filters.gaussianGradient(volume[:,:,:].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma))
            weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
            real_weights[:] = weights[:]

        if normalizePotential == True:
            min = numpy.min(real_weights)
            max = numpy.max(real_weights)
            weights = (real_weights - min)*(255.0 / (max - min))
            real_weights[:] = weights[:]

        self.project.segmentor.setupWeights(real_weights)
        self.project.dataMgr[self.activeImage].segmentationWeights = real_weights




    def on_segmentationSegment(self):
        self.segmentationSegment = Segmentation(self)

    def on_classificationTrain(self):
        self.classificationTrain = ClassificationTrain(self)
        
    def on_classificationPredict(self):
        self.classificationPredict = ClassificationPredict(self)
    
    def on_classificationInteractive(self, state):
        if state:
            self.ribbon.getTab('Classification').btnStartLive.setText('Stop Live Prediction')
            self.classificationInteractive = ClassificationInteractive(self)
        else:
            self.classificationInteractive.stop()
            del self.classificationInteractive
            self.ribbon.getTab('Classification').btnStartLive.setText('Start Live Prediction')


    def on_segmentation_border(self):
        pass

    def on_saveClassifier(self, fileName=None):
        
        if not hasattr(self.project.dataMgr,'classifiers'):
            reply = QtGui.QMessageBox.warning(self, 'Error', "No classifiers trained so far. Use Train and Predict to learn classifiers.", QtGui.QMessageBox.Ok)
        classifiers = self.project.dataMgr.classifiers
        
        if len(classifiers) == 0:
            print "no classifiers"
            reply = QtGui.QMessageBox.warning(self, 'Error', "No classifiers trained so far. Use Train and Predict to learn classifiers.", QtGui.QMessageBox.Ok)
        
        if not hasattr(classifiers[0],'serialize'):
            reply = QtGui.QMessageBox.warning(self, 'Error', "The selected classifier is not serializable and cannot be saved to file.", QtGui.QMessageBox.Ok)
            return
        
        if fileName is not None:
            # global LAST_DIRECTORY
            fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", ilastik.gui.LAST_DIRECTORY, "HDF5 Files (*.h5)")
            ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
        
        # Make sure group 'classifiers' exist
        h5file = h5py.File(str(fileName),'w')
        h5file.create_group('classifiers')
        h5file.close()
        
        for i, c in enumerate(classifiers):
            tmp = c.RF.writeHDF5(str(fileName), "classifiers/rf_%03d" % i, True)
            print "Write Random Forest # %03d -> %d" % (i,tmp)
        
        # Export user feature selection
        h5file = h5py.File(str(fileName),'a')
        h5featGrp = h5file.create_group('features')
        
        featureItems = self.project.featureMgr.featureItems
        for k, feat in enumerate(featureItems):
            itemGroup = h5featGrp.create_group('feature_%03d' % k)
            feat.serialize(itemGroup)
        h5file.close()
        
        reply = QtGui.QMessageBox.information(self, 'Sucess', "The classifier and the feature information have be saved to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
        
        
        
        

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Save before Exit?', "Save the Project before quitting the Application", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.saveProject()
            event.accept()
        elif reply == QtGui.QMessageBox.No:
            event.accept()
        else:
            event.ignore()
            




class FeatureComputation(object):
    def __init__(self, parent):
        self.parent = parent
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
            self.parent.project.createFeatureOverlays()

            
    def terminateFeatureProgressBar(self):
        self.parent.statusBar().removeWidget(self.myFeatureProgressBar)
        self.parent.statusBar().hide()
        self.parent.project.dataMgr.buildTrainingMatrix()
        self.parent.project.dataMgr.featureLock.release()
        if hasattr(self.parent, "classificationInteractive"):
            self.parent.classificationInteractive.updateThreadQueues()
            
        #self.parent.ribbon.tabDict['Classification'].itemDict['Select Features'].setEnabled(True)
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        #self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(True)
                    
    def featureShow(self, item):
        pass

class ClassificationTrain(object):
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()
        
    def start(self):
        #process all unaccounted label changes
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
        #self.parent.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(False)
        
        newLabels = self.parent.labelWidget.getPendingLabels()
        if len(newLabels) > 0:
            self.parent.project.dataMgr.updateTrainingMatrix(newLabels)
        
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
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        #self.parent.ribbon.tabDict['Automate'].itemDict['Batchprocess'].setEnabled(True)
        

class ClassificationInteractive(object):
    def __init__(self, parent):
        self.parent = parent
        self.stopped = False
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)

        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('newLabelsPending()'), self.updateThreadQueues)
        self.parent.labelWidget.connect(self.parent.labelWidget, QtCore.SIGNAL('changedSlice(int, int)'), self.updateThreadQueues)

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
        activeItem = self.parent.project.dataMgr[self.parent.activeImage]
        for p_i, descr in enumerate(activeItem.dataVol.labels.descriptions):
            #create Overlay for prediction:
            ov = OverlayItem(descr.prediction, color = QtGui.QColor.fromRgba(long(descr.color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Classification/Prediction/" + descr.name] = ov

        #create Overlay for uncertainty:
        ov = OverlayItem(activeItem.dataVol.uncertainty, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
        self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Classification/Uncertainty"] = ov



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
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        
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
        #self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(False)
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(False)
          
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
                #create Overlay for prediction:
                ov = OverlayItem(activeItem.dataVol.labels.descriptions[p_num-1].prediction,  color = QtGui.QColor.fromRgba(long(activeItem.dataVol.labels.descriptions[p_num-1].color)), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True)
                self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Classification/Prediction/" + activeItem.dataVol.labels.descriptions[p_num-1].name] = ov

            all =  range(len(activeItem.dataVol.labels.descriptions))
            not_predicted = numpy.setdiff1d(all, self.parent.project.dataMgr.classifiers[0].unique_vals - 1)
            for p_i, p_num in enumerate(not_predicted):
                activeItem.dataVol.labels.descriptions[p_num].prediction[:,:,:,:] = 0



            margin = activeLearning.computeEnsembleMargin(activeItem.prediction[:,:,:,:,:])*255.0
            activeItem.dataVol.uncertainty[:,:,:,:] = margin[:,:,:,:]

            #create Overlay for uncertainty:
            ov = OverlayItem(activeItem.dataVol.uncertainty, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
            self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Classification/Uncertainty"] = ov


            self.parent.labelWidget.repaint()
        
    def terminateClassificationProgressBar(self):
        self.parent.statusBar().removeWidget(self.myClassificationProgressBar)
        self.parent.statusBar().hide()
        #self.parent.ribbon.tabDict['Classification'].itemDict['Start Live Prediction'].setEnabled(True)
        #self.parent.ribbon.tabDict['Classification'].itemDict['Train and Predict'].setEnabled(True)
        #self.parent.ribbon.tabDict['Classification'].itemDict['Save Classifier'].setEnabled(True)




class Segmentation(object):

    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()

    def start(self):
        #self.parent.ribbon.tabDict['Segmentation'].itemDict['Segment'].setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        self.segmentation = segmentationMgr.SegmentationThread(self.parent.project.dataMgr, self.parent.project.dataMgr[self.ilastik.activeImage], self.ilastik.project.segmentor)
        numberOfJobs = self.segmentation.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.segmentation.start()
        self.timer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Segmentation... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.segmentation.count
        self.progressBar.setValue(val)
        if not self.segmentation.isRunning():
            print "finalizing segmentation"
            self.timer.stop()
            self.segmentation.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent.activeImage]
        activeItem.dataVol.segmentation = self.segmentation.result

        temp = activeItem.dataVol.segmentation[0, :, :, :, 0]
        
        #create Overlay for segmentation:
        if self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Segmentation/Segmentation"] is None:
            ov = OverlayItem(activeItem.dataVol.segmentation, color = 0, alpha = 1.0, colorTable = self.parent.labelWidget.labelWidget.colorTab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Segmentation/Segmentation"] = ov
        else:
            self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Segmentation/Segmentation"].data = DataAccessor(activeItem.dataVol.segmentation)
        self.ilastik.labelWidget.repaint()


        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        #self.parent.ribbon.tabDict['Segmentation'].itemDict['Segment'].setEnabled(True)


if __name__ == "__main__":
    app = QtGui.QApplication.instance() #(sys.argv)
    #app = QtGui.QApplication(sys.argv)
    mainwindow = MainWindow(sys.argv)
      
    mainwindow.show() 
    app.exec_()
    print "cleaning up..."
    if mainwindow.labelWidget is not None:
        del mainwindow.labelWidget
    del mainwindow


    del core.jobMachine.GLOBAL_WM

    

