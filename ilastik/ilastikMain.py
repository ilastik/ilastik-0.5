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


from OpenGL.GL import *
try:
    from OpenGL.GLX import *
#    XInitThreads()
except:
    pass

import sys
import os

#force QT4 toolkit for the enthought traits UI
os.environ['ETS_TOOLKIT'] = 'qt4'

from ilastik.core import ILASTIK_VERSION
import ilastik.modules

#load core functionality
ilastik.modules.loadModuleCores()

#from ilastik.core import version, dataMgr, projectMgr,  activeLearning, onlineClassifcator, dataImpex, connectedComponentsMgr, unsupervisedMgr
#import ilastik.gui
#from ilastik.core import projectMgr, unsupervisedMgr, activeLearning
from ilastik.core.volume import DataAccessor

from ilastik.modules.classification.core import featureMgr

#from ilastik.core import connectedComponentsMgr
#from ilastik.core import projectMgr

from ilastik.gui import volumeeditor as ve
from ilastik.gui import ctrlRibbon
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
#import ilastik.gui.ribbons.standardRibbons

import threading
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py
import getopt


from PyQt4 import QtCore, QtOpenGL, QtGui

# Please no import *
from ilastik.gui.shortcutmanager import shortcutManager, shortcutManagerDlg, shortcutManager

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        
        QtGui.QMainWindow.__init__(self)
        self.fullScreen = False
        self.setGeometry(50, 50, 800, 600)
        self.setWindowTitle("ilastik " + str(ILASTIK_VERSION))
        self.setWindowIcon(QtGui.QIcon(ilastikIcons.Ilastik))

        self.activeImageLock = threading.Semaphore(1) #prevent chaning of _activeImageNumber during thread stuff
        
        self.previousTabText = ""
        
        self.labelWidget = None
        self._activeImageNumber = 0
        self._activeImage = None
        
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


            help_text = "<b>OpenGL + OpenGL Overview</b> allows for fastest rendering if OpenGL is correctly installed.<br> If visualization is slow or incomplete, try the <b>Software + OpenGL</b> mode."
            if int(gl_version[0]) >= 2:
                dl = QtGui.QInputDialog.getItem(self,'ilastik: Graphics Setup', help_text, ['OpenGL + OpenGL Overview', 'Software + OpenGL Overview'], 0, False)
            elif int(gl_version[0]) > 0:
                dl = QtGui.QInputDialog.getItem(self,'ilastik: Graphics Setup', help_text, ['Software + OpenGL Overview'], 0, False)
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

        self.project = None
        if project != None:
            self.project = projectMgr.Project.loadFromDisk(project, self.featureCache)
            self.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
            self._activeImageNumber = 0
            self.projectModified()
        
        self.shortcutSave = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, self.saveProject, self.saveProject) 
        self.shortcutFullscreen = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+F"), self, self.showFullscreen, self.showFullscreen)
        self.tabChanged(0)
    
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
            self.fileSelectorList.addItem(item._name)
    
    def changeImage(self, number):
        self.fileSelectorList.setEnabled(False)
        
        self.activeImageLock.acquire()
        QtCore.QCoreApplication.processEvents()
        if self.labelWidget is not None:
            self.labelWidget._history.volumeEditor = None


        
        self.destroyImageWindows()
        
        self._activeImageNumber = number
        self._activeImage = self.project.dataMgr[number]
        
        self.project.dataMgr._activeImageNumber = number
        self.project.dataMgr._activeImage = self._activeImage
        
        self.createImageWindows( self.project.dataMgr[number]._dataVol)
        
        self.labelWidget.repaint() #for overlays
        self.activeImageLock.release()
        
        # Notify tabs
        self.ribbon.widget(self.ribbon.currentIndex()).on_activation()        
        self.ribbon.widget(self.ribbon.currentIndex()).on_imageChanged()
        self.fileSelectorList.setEnabled(True)
            
    def historyUndo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyUndo
        
    def historyRedo(self):
        if self.labelWidget is not None:
            self.labelWidget.historyRedo
    
    def createRibbons(self):                        
        self.ribbonToolbar = self.addToolBar("ToolBarForRibbons")
        
        self.ribbon = ctrlRibbon.IlastikTabWidget(self.ribbonToolbar)
        
        self.ribbonToolbar.addWidget(self.ribbon)
        
        self.ribbonsTabs =  sorted(IlastikTabBase.__subclasses__(), key=lambda tab: tab.position)

        for tab in self.ribbonsTabs:
            print "Adding ribbon", tab.name
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

    def setTabBusy(self, state):
        self.fileSelectorList.setEnabled(not state)
        for i in range(self.ribbon.count()):
            enabled = not state
            if i == self.ribbon.currentTabNumber:
                enabled = True
            self.ribbon.setTabEnabled(i, enabled)
        if self.labelWidget is not None:
            self.labelWidget.labelWidget.setEnabled(not state)

    def tabChanged(self,  index):
        """
        update the overlayWidget of the volumeEditor and switch the _history
        between seeds and labels, also make sure the 
        seed/label widget has a reference to the overlay in the overlayWidget
        they correspond to.
        """
        self.ribbon.widget(self.ribbon.currentTabNumber).on_deActivation()
        self.ribbon.currentTabNumber = index
        #change current module name, so that overlays are stored at the right place
        if self.project is not None:
            self.project.dataMgr._currentModuleName = self.ribbon.widget(index).__class__.moduleName 
        self.ribbon.widget(index).on_activation()

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
        
        self.project.dataMgr._activeImageNumber = self._activeImageNumber
        self.project.dataMgr._activeImage = self._activeImage
        
        self._activeImage = self.project.dataMgr[self._activeImageNumber]
     
    def initImageWindows(self):
        self.labelDocks = []
        
    def destroyImageWindows(self):

        if self.labelWidget is not None:
            self.labelWidget.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
            self.labelWidget.cleanUp()
            self.labelWidget.close()
            self.labelWidget.deleteLater()
                    
        self.ribbon.widget(self.ribbon.currentTabNumber).on_deActivation()
        
        for dock in self.labelDocks:
            self.removeDockWidget(dock)
        self.labelDocks = []

        self.volumeEditorDock = None
                
    def createImageWindows(self, dataVol):
        self.labelWidget = ve.VolumeEditor(dataVol, self,  opengl = self.opengl, openglOverview = self.openglOverview)
        
        if self.project.dataMgr._currentModuleName is None:
            self.project.dataMgr._currentModuleName = "Project"
        
        self.ribbon.widget(self.ribbon.currentTabNumber).on_activation()

        self.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
        self.labelWidget.normalizeData = self.project.normalizeData
        self.labelWidget.useBorderMargin = self.project.useBorderMargin
        self.labelWidget.setRgbMode(self.project.rgbData)
        
        
        dock = QtGui.QDockWidget("Ilastik Label Widget", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)
        
        self.volumeEditorDock = dock

        self.connect(self.labelWidget, QtCore.SIGNAL("labelRemoved(int)"),self.labelRemoved)
        
        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

    def labelRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive.updateThreadQueues()

    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures
        
    def on_shortcutsDlg(self):
        shortcutManager.showDialog()

    def on_connectComponents(self, background = False):
        self.connComp = CC(self)
        self.connComp.selection_key = self.project.dataMgr.connCompBackgroundKey
        self.connComp.start(background)

    def on_unsupervisedDecomposition(self, overlays):
        self.unsDec = UnsupervisedDecomposition(self)
        #self.unsDec.selection_key = self.project.dataMgr.connCompBackgroundKey
        self.unsDec.start(overlays)
        
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Save before Exit?', "Save the Project before quitting the Application", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.saveProject()
            event.accept()
        elif reply == QtGui.QMessageBox.No:
            event.accept()
        else:
            event.ignore()
            


class CC(object):
    #Connected components
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        #self.start()

    def start(self, background = False):
        self.parent.ribbon.getTab('Connected Components').btnCC.setEnabled(False)
        self.parent.ribbon.getTab('Connected Components').btnCCBack.setEnabled(False)
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)
        overlay = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr[self.selection_key]
        if background==False:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data)
        else:
            self.cc = connectedComponentsMgr.ConnectedComponentsThread(self.parent.project.dataMgr, overlay._data, self.parent.project.dataMgr.connCompBackgroundClasses)
        numberOfJobs = self.cc.numberOfJobs
        self.initCCProgress(numberOfJobs)
        self.cc.start()
        self.timer.start(200)
        
    def initCCProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Connected Components... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.cc.count
        self.progressBar.setValue(val)
        if not self.cc.isRunning():
            print "finalizing connected components"
            self.timer.stop()
            self.cc.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        #activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        #activeItem._dataVol.cc = self.cc.result

        #temp = activeItem._dataVol.segmentation[0, :, :, :, 0]
        
        #create Overlay for connected components:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"] is None:
            #colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            colortab = self.makeColorTab()
            ov = overlayMgr.OverlayItem(self.parent._activeImage,self.cc.result, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC"]._data = DataAccessor(self.cc.result)
        self.ilastik.labelWidget.repaint()
       
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.tabDict['Connected Components'].btnCC.setEnabled(True)
        self.parent.ribbon.tabDict['Connected Components'].btnCCBack.setEnabled(True)
    
    def makeColorTab(self):
        sublist = []
        sublist.append(QtGui.qRgb(0, 0, 0))
        sublist.append(QtGui.qRgb(255, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 0))
        sublist.append(QtGui.qRgb(0, 255, 0))
        sublist.append(QtGui.qRgb(0, 0, 255))
        
        sublist.append(QtGui.qRgb(255, 255, 0))
        sublist.append(QtGui.qRgb(0, 255, 255))
        sublist.append(QtGui.qRgb(255, 0, 255))
        sublist.append(QtGui.qRgb(255, 105, 180)) #hot pink!
        
        sublist.append(QtGui.qRgb(102, 205, 170)) #dark aquamarine
        sublist.append(QtGui.qRgb(165,  42,  42)) #brown        
        sublist.append(QtGui.qRgb(0, 0, 128)) #navy
        sublist.append(QtGui.qRgb(255, 165, 0)) #orange
        
        sublist.append(QtGui.qRgb(173, 255,  47)) #green-yellow
        sublist.append(QtGui.qRgb(128,0, 128)) #purple
        sublist.append(QtGui.qRgb(192, 192, 192)) #silver
        #sublist.append(QtGui.qRgb(240, 230, 140)) #khaki
        colorlist = []
        for i in range(0, 16):
            colorlist.extend(sublist)
        print len(colorlist)
        return colorlist
    
class UnsupervisedDecomposition(object):
    
    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent

    def start(self, overlays):
        self.parent.ribbon.getTab('Unsupervised').btnDecompose.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        self.ud = unsupervisedMgr.UnsupervisedThread(self.parent.project.dataMgr, overlays, self.parent.project.unsupervisedDecomposer)
        numberOfJobs = self.ud.numberOfJobs
        self.initDecompositionProgress(numberOfJobs)
        self.ud.start()
        self.timer.start(200)

    def initDecompositionProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Unsupervised Decomposition... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.ud.count
        self.progressBar.setValue(val)
        if not self.ud.isRunning():
            self.timer.stop()
            self.ud.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        activeItem._dataVol.unsupervised = self.ud.result

        #create Overlay for unsupervised decomposition:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/pLSA"] is None:
            data = self.ud.result[:,:,:,:,:]
            colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            for o in range(0, data.shape[4]):
                # transform to uint8
                data2 = data[:,:,:,:,o:(o+1)]
                dmin = numpy.min(data2)
                data2 -= dmin
                dmax = numpy.max(data2)
                data2 = 255/dmax*data2
                data2 = data2.astype(numpy.uint8)
                
                ov = OverlayItem(self.parent._activeImage, data2, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/" + self.parent.project.unsupervisedDecomposer.shortname + " component %d" % (o+1)] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Unsupervised/" + self.parent.project.unsupervisedDecomposer.shortname]._data = DataAccessor(self.ud.result)
        self.ilastik.labelWidget.repaint()

        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Unsupervised').btnDecompose.setEnabled(True)

        

if __name__ == "__main__":
    app = QtGui.QApplication.instance() #(sys.argv
    
    splashImage = QtGui.QPixmap("logo/ilastik-splash.png")

    splashScreen = QtGui.QSplashScreen(splashImage)
    splashScreen.show();

    app.processEvents();
    ilastik.modules.loadModuleGuis()

    mainwindow = MainWindow(sys.argv)

    
    mainwindow.show() 
    splashScreen.finish(mainwindow)
    app.exec_()
    print "cleaning up..."
    if mainwindow.labelWidget is not None:
        del mainwindow.labelWidget
    del mainwindow



    del ilastik.core.jobMachine.GLOBAL_WM

    

