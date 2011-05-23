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

import vigra
vigraVersion = vigra.version.split('.')
if int(vigraVersion[0]) < 1 or int(vigraVersion[1]) < 8 or int(vigraVersion[2]) < 0:
    raise RuntimeError("At least vigra version 1.8.0 is required")
print "Using vigra version %s ... ok" % (vigra.version)

import numpy
numpyVersion = numpy.__version__.split('.')
if int(numpyVersion[0]) < 1 or int(numpyVersion[1]) < 3 or int(numpyVersion[2]) < 0:
    raise RuntimeError("At least numpy version 1.3.0 is required")
print "Using numpy version %s ... ok" % (numpy.__version__)

from OpenGL.GL import *
try:
    from OpenGL.GLX import *
#    XInitThreads()
except:
    pass

import sys
import os
import gc
import platform

from PyQt4 import QtCore, QtOpenGL, QtGui

app = QtGui.QApplication(sys.argv) #(sys.argv

#force QT4 toolkit for the enthought traits UI
os.environ['ETS_TOOLKIT'] = 'qt4'

from ilastik.core import ILASTIK_VERSION
import ilastik.modules

#load core functionality
ilastik.modules.loadModuleCores()

#from ilastik.core import version, dataMgr, projectMgr,  activeLearning, onlineClassifcator, dataImpex, connectedComponentsMgr
#import ilastik.gui
#from ilastik.core import projectMgr, activeLearning

from ilastik.modules.classification.core import featureMgr
from ilastik.core.randomSeed import RandomSeed 

#from ilastik.core import connectedComponentsMgr
#from ilastik.core import projectMgr

from ilastik.gui import volumeeditor as ve
from ilastik.core.dataImpex import DataImpex
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



# Please no import *
from ilastik.gui.shortcutmanager import shortcutManager
import ilastik

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#*******************************************************************************
# R e n d e r C h o i c e D i a l o g                                          *
#*******************************************************************************

class RenderChoiceDialog(QtGui.QDialog):
    def __init__(self):
        #Test for OpenGL Version
        gl2 = False
        w = QtOpenGL.QGLWidget()
        w.setVisible(False)
        w.makeCurrent()
        gl_version =  glGetString(GL_VERSION)
        if gl_version is None:
            gl_version = '0'

        allowChoosingOpenGL = False
        if int(gl_version[0]) >= 2:
            allowChoosingOpenGL = True
        elif int(gl_version[0]) > 0:
            allowChoosingOpenGL = False
        else:
            raise RuntimeError("Absolutely no OpenGL available")

        super(RenderChoiceDialog, self).__init__()
        layout = QtGui.QVBoxLayout(self)
        choicesGroup = QtGui.QButtonGroup(self)
        self.openglChoice   = QtGui.QRadioButton("Open GL")
        self.softwareChoice = QtGui.QRadioButton("Software + OpenGL")
        okButton = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok, QtCore.Qt.Vertical)
        label = QtGui.QLabel("""<b>OpenGL + OpenGL Overview</b> allows
                    for fastest rendering if OpenGL is correctly installed.
                    <br> If visualization is slow or incomplete,
                    try the <b>Software + OpenGL</b> mode.""")

        layout.addWidget(label)
        layout.addWidget(self.openglChoice)
        layout.addWidget(self.softwareChoice)
        layout.addWidget(okButton)
        self.setLayout(layout)

        if platform.system() == 'Darwin':
            allowChoosingOpenGL = False

        if allowChoosingOpenGL:
            self.openglChoice.setChecked(True)
        else:
            self.openglChoice.setEnabled(False)
            self.softwareChoice.setChecked(True)

        QtCore.QObject.connect(okButton, QtCore.SIGNAL("accepted()"), self, QtCore.SLOT("accept()"))
        
    def exec_(self):
        if not (self.openglChoice.isEnabled() and self.softwareChoice.isEnabled()):
            return
        else:
            QtGui.QDialog.exec_(self)

#*******************************************************************************
# M a i n W i n d o w                                                          *
#*******************************************************************************

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

        overlaysToLoad = []

        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ["help", "render=", "project=", "featureCache=", "load-overlays="])
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
                    print '%30s  %s' % ("--load-overlays=[filename,filename...]", "load additional overlays from these files")
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
                elif o in ("--load-overlays"):
                    keys = [x[0] for x in opts]
                    if not "--project" in keys:
                        raise RuntimeError("--load-overlays options is only allowed if --project is passed, too")
                    overlaysToLoad = a.split(',')
                else:
                    assert False, "unhandled option"

        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"

        if self.opengl == None:   #no command line option for opengl was given, ask user interactively
            dlg = RenderChoiceDialog()
            dlg.exec_()

            self.opengl = False
            self.openglOverview = False
            if dlg.openglChoice.isChecked():
                self.opengl = True
                self.openglOverview = True
            elif dlg.softwareChoice.isChecked():
                self.opengl = False
                self.openglOverview = True
            else:
                raise RuntimeError("Unhandled choice in dialog")

        print "* OpenGL:"
        print "  - Using OpenGL for slice views:", self.opengl
        print "  - Using OpenGL for 3D view:    ", self.openglOverview
        
        #if we have OpenGL, a shared QGLWidget is set up,
        self.sharedOpenGLWidget = None
        if self.opengl:
            self.sharedOpenGLWidget = QtOpenGL.QGLWidget()

        self.project = None
        if project != None:
            self.ribbon.getTab('Project').openProject(project)
            #switch to the "classification" tab
            self.ribbon.getTab('Classification').btnClassifierOptions.setEnabled(True)
            self._activeImageNumber = 0
            self.projectModified()

        #in case the user has specified some additional overlays to load from a file, do that
        for overlayFilename in overlaysToLoad:
            print "loading overlay '%s'" % (overlayFilename)
            dataItem = self.labelWidget.ilastik.project.dataMgr[self.labelWidget.ilastik._activeImageNumber]
            ov = DataImpex.importOverlay(dataItem, overlayFilename)
            dataItem.overlayMgr[ov.key] = ov

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
        self.ribbonToolbar.setMovable(False)

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
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(QtGui.QLabel("Select Image:"))
        layout.addWidget(self.fileSelectorList)
        widget.setLayout(layout)
        self.ribbonToolbar.addWidget(widget)
        #self.ribbonToolbar.addWidget(self.fileSelectorList)
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
            moduleName = self.project.dataMgr._currentModuleName = self.ribbon.widget(index).__class__.moduleName

            ribbonWidget = self.ribbon.widget(index)
    
            #for convenience of the module
            ribbonWidget.dataMgr = self.project.dataMgr
            ribbonWidget.activeImage = self.project.dataMgr[self.project.dataMgr._activeImageNumber]
            ribbonWidget.localMgr =  ribbonWidget.activeImage.module[moduleName]
            ribbonWidget.globalMgr = ribbonWidget.dataMgr.module[moduleName]
    
            ribbonWidget.on_activation()

        if self.labelWidget is not None:
            self.labelWidget.repaint()


    def saveProject(self):
        if hasattr(self,'project'):
            if self.project.filename is not None:
                self.project.saveToDisk()
            else:
                fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", ilastik.gui.LAST_DIRECTORY, "Project Files (*.ilp)")
                fn = str(fileName)
                if len(fn) > 4:
                    if fn[-4:] != '.ilp':
                        fn = fn + '.ilp'
                    if self.project.saveToDisk(fn):
                        QtGui.QMessageBox.information(self, 'Success', "The project has been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
                        
                ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fn).path()
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
        gc.collect()
        self.labelWidget = ve.VolumeEditor(dataVol, self,  sharedOpenglWidget = self.sharedOpenGLWidget)

        if self.project.dataMgr._currentModuleName is None:
            self.project.dataMgr._currentModuleName = "Project"

        self.ribbon.widget(self.ribbon.currentTabNumber).on_activation()

        self.labelWidget.drawUpdateInterval = self.project.drawUpdateInterval
        self.labelWidget.normalizeData = self.project.normalizeData
        self.labelWidget.useBorderMargin = self.project.useBorderMargin
        self.labelWidget.setRgbMode(self.project.rgbData)


        dock = QtGui.QDockWidget(self)
        dock.setContentsMargins(0,0,0,0)
        #save space, but makes this dock widget undockable
        #at the moment we do not support undocking anyway, so...
        dock.setTitleBarWidget(QtGui.QWidget())
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        dock.setWidget(self.labelWidget)
        dock.setFeatures(dock.features() & (not QtGui.QDockWidget.DockWidgetClosable))
        self.volumeEditorDock = dock

        self.connect(self.labelWidget, QtCore.SIGNAL("labelRemoved(int)"),self.labelRemoved)

        area = QtCore.Qt.BottomDockWidgetArea
        self.addDockWidget(area, dock)
        self.labelDocks.append(dock)

    def on_otherProject(self):
        for i in range(self.ribbon.count()):
            self.ribbon.widget(i).on_otherProject()

    def labelRemoved(self, number):
        self.ribbon.getTab('Automate').btnBatchProcess.setEnabled(False)
        if hasattr(self, "classificationInteractive"):
            self.classificationInteractive.updateThreadQueues()

    def createFeatures(self):
        self.featureList = featureMgr.ilastikFeatures

    def on_shortcutsDlg(self):
        shortcutManager.showDialog()

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Save before Exit?', "Save the Project before quitting the Application", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.Cancel)
        if reply == QtGui.QMessageBox.Yes:
            self.saveProject()
            event.accept()
            if self.labelWidget.grid:
                self.labelWidget.grid.deleteUndocked()
        elif reply == QtGui.QMessageBox.No:
            event.accept()
            if hasattr(self.labelWidget,'grid') and self.labelWidget.grid:
                self.labelWidget.grid.deleteUndocked()
        else:
            event.ignore()
           

#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    splashImage = QtGui.QPixmap("ilastik/gui/logos/ilastik-splash.png")
    painter = QtGui.QPainter()
    painter.begin(splashImage)
    painter.drawText(QtCore.QPointF(270,110), ilastik.core.readInBuildInfo())
    painter.end()

    splashScreen = QtGui.QSplashScreen(splashImage)
    splashScreen.show()

    app.processEvents();
    ilastik.modules.loadModuleGuis()

    mainwindow = MainWindow(sys.argv)
    mainwindow.setStyleSheet("QSplitter::handle { background-color: #CCCCCC;}")

    mainwindow.show()
    #On OS X, the window has to be raised in order to be visible directly after starting
    #the app
    mainwindow.raise_()
    
    splashScreen.finish(mainwindow)
    
    randomseed = RandomSeed()
    
    app.exec_()
    print "cleaning up..."
    if mainwindow.labelWidget is not None:
        del mainwindow.labelWidget
    del mainwindow
    del randomseed


    del ilastik.core.jobMachine.GLOBAL_WM


