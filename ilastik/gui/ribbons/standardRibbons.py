# -*- coding: utf-8 -*-
import numpy, vigra
import random
import code

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore
from ilastik.gui.iconMgr import ilastikIcons

import ilastik.gui
from ilastik.gui.projectDialog import ProjectDlg, ProjectSettingsDlg
from ilastik.core import projectMgr

from ilastik.gui.unsupervisedSelectionDlg import UnsupervisedSelectionDlg

from ilastik.gui.shortcutmanager import shortcutManager
import ilastik.core.overlays
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui import volumeeditor as ve


from ilastik.gui.backgroundWidget import BackgroundWidget

import gc, weakref

class ProjectTab(IlastikTabBase, QtGui.QWidget):
    name = 'Project'
    position = 0
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage._dataVol.projectOverlays
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  self.ilastik._activeImage._dataVol.projectOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
    
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnNew = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.New),'New')
        self.btnOpen = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Open),'Open')
        self.btnSave = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Save),'Save')
        self.btnEdit = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Edit),'Edit')
        self.btnOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Edit),'Options')
        
        self.btnNew.setToolTip('Create new project')
        self.btnOpen.setToolTip('Open existing project')
        self.btnSave.setToolTip('Save current project to file')
        self.btnEdit.setToolTip('Edit current project')
        self.btnOptions.setToolTip('Edit ilastik options')
        
        tl.addWidget(self.btnNew)
        tl.addWidget(self.btnOpen)
        tl.addWidget(self.btnSave)
        tl.addWidget(self.btnEdit)
        tl.addStretch()
        tl.addWidget(self.btnOptions)
        
        self.btnSave.setEnabled(False)
        self.btnEdit.setEnabled(False)
        self.btnOptions.setEnabled(False)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnNew, QtCore.SIGNAL('clicked()'), self.on_btnNew_clicked)
        self.connect(self.btnOpen, QtCore.SIGNAL('clicked()'), self.on_btnOpen_clicked)
        self.connect(self.btnSave, QtCore.SIGNAL('clicked()'), self.on_btnSave_clicked)
        self.connect(self.btnEdit, QtCore.SIGNAL('clicked()'), self.on_btnEdit_clicked)
        self.connect(self.btnOptions, QtCore.SIGNAL('clicked()'), self.on_btnOptions_clicked)
        
    # Custom Callbacks
    def on_btnNew_clicked(self):
        self.parent.projectDlg = ProjectDlg(self.parent)
        if self.parent.projectDlg.exec_() == QtGui.QDialog.Accepted:
            self.btnSave.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnOptions.setEnabled(True)
            self.parent.updateFileSelector()
            self.parent._activeImageNumber = 0
            
    def on_btnSave_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", ilastik.gui.LAST_DIRECTORY, "Project Files (*.ilp)")
        fn = str(fileName)
        if len(fn) > 4:
            if fn[-4:] != '.ilp':
                fn = fn + '.ilp'
            if self.parent.project.saveToDisk(fn):
                QtGui.QMessageBox.information(self.parent, 'Success', "The project has been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
                
            ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fn).path()
    
    def on_btnOpen_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Project", ilastik.gui.LAST_DIRECTORY, "Project Files (*.ilp)")
        if str(fileName) != "":
            labelWidget = None
            #if self.parent.project is not None:
            #    if len(self.parent.project.dataMgr) > self.parent._activeImageNumber:
            #        labelWidget = weakref.ref(self.parent.project.dataMgr[self.parent._activeImageNumber])#.featureBlockAccessor)
            self.parent.project = projectMgr.Project.loadFromDisk(str(fileName), self.parent.featureCache)
            self.btnSave.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnOptions.setEnabled(True)
            self.parent.changeImage(0)
            
            ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
            gc.collect()
            if labelWidget is not None:
                if labelWidget() is not None:
                    refs =  gc.get_referrers(labelWidget())
                    for i,r in enumerate(refs):
                        print type(r)
                        print "##################################################################"
                        print r
   
    def on_btnEdit_clicked(self):
        self.parent.projectDlg = ProjectDlg(self.parent, False)
        self.parent.projectDlg.updateDlg(self.parent.project)
        self.parent.projectModified()
        
    def on_btnOptions_clicked(self):
        tmp = ProjectSettingsDlg(self.ilastik, self.ilastik.project)
        tmp.exec_()


try:
    from ilastik.gui.shellWidget import SciShell
            
    class ConsoleTab(IlastikTabBase, QtGui.QWidget):
        name = 'Interactive Console'
        def __init__(self, parent=None):
            IlastikTabBase.__init__(self, parent)
            QtGui.QWidget.__init__(self, parent)
            
            self.consoleWidget = None
            
            self._initContent()
            self._initConnects()
            
        def on_activation(self):
            if self.ilastik.project is None:
                return
            ovs = self.ilastik._activeImage._dataVol.projectOverlays
            if len(ovs) == 0:
                raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
                if raw is not None:
                    ovs.append(raw.getRef())
            
            self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
    
            overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  self.ilastik._activeImage._dataVol.projectOverlays)
            self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
            
            self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
            
            
            self.volumeEditorVisible = self.ilastik.volumeEditorDock.isVisible()
            self.ilastik.volumeEditorDock.setVisible(False)
            
            if self.consoleWidget is None:
                locals = {}
                locals["activeImage"] = self.ilastik._activeImage
                locals["dataMgr"] = self.ilastik.project.dataMgr
                self.interpreter = code.InteractiveInterpreter(locals)
                self.consoleWidget = SciShell(self.interpreter)
                
                dock = QtGui.QDockWidget("Ilastik Interactive Console", self.ilastik)
                dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
                dock.setWidget(self.consoleWidget)
                
                self.consoleDock = dock
        
               
                area = QtCore.Qt.BottomDockWidgetArea
                self.ilastik.addDockWidget(area, dock)
            self.consoleDock.setVisible(True)
            self.consoleDock.setFocus()
            self.consoleWidget.multipleRedirection(True)
            
        
        def on_deActivation(self):
            self.consoleWidget.multipleRedirection(False)
            self.consoleWidget.releaseKeyboard()
            self.consoleDock.setVisible(False)
            self.ilastik.volumeEditorDock.setVisible(self.volumeEditorVisible)
            
        def _initContent(self):
            pass
        
        def _initConnects(self):
            pass
except:
    pass    


class UnsupervisedTab(IlastikTabBase, QtGui.QWidget):
    name = 'Unsupervised'
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
        self.overlays = None
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage._dataVol.unsupervisedOverlays
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  self.ilastik._activeImage._dataVol.unsupervisedOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
        self.btnUnsupervisedOptions.setEnabled(True)     
           
    def on_deActivation(self):
        pass
            
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseOverlays = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Select overlay')
        self.btnDecompose = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'decompose')
        self.btnUnsupervisedOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Unsupervised Decomposition Options')

        self.btnDecompose.setEnabled(False)     
        self.btnUnsupervisedOptions.setEnabled(False)     
        
        self.btnChooseOverlays.setToolTip('Choose the overlays for unsupervised decomposition')
        self.btnDecompose.setToolTip('perform unsupervised decomposition')
        self.btnUnsupervisedOptions.setToolTip('select an unsupervised decomposition plugin and change settings')
        
        tl.addWidget(self.btnChooseOverlays)
        tl.addWidget(self.btnDecompose)
        tl.addStretch()
        tl.addWidget(self.btnUnsupervisedOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseOverlays, QtCore.SIGNAL('clicked()'), self.on_btnChooseOverlays_clicked)
        self.connect(self.btnDecompose, QtCore.SIGNAL('clicked()'), self.on_btnDecompose_clicked)
        self.connect(self.btnUnsupervisedOptions, QtCore.SIGNAL('clicked()'), self.on_btnUnsupervisedOptions_clicked)
       
    def on_btnChooseOverlays_clicked(self):
        dlg = OverlaySelectionDialog(self.parent,  singleSelection = False)
        overlays = dlg.exec_()
        
        if len(overlays) > 0:
            self.overlays = overlays
            # add all overlays
            for overlay in overlays:
                ref = overlay.getRef()
                ref.setAlpha(0.4)
                self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
                
            self.parent.labelWidget.repaint()
            self.btnDecompose.setEnabled(True)            

    def on_btnDecompose_clicked(self):
        self.parent.on_unsupervisedDecomposition(self.overlays)

    def on_btnUnsupervisedOptions_clicked(self):
        dialog = UnsupervisedSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.unsupervisedDecomposer = answer
            #self.parent.project.unsupervised.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber]._segmentationWeights)
                    
        

class ConnectedComponentsTab(IlastikTabBase, QtGui.QWidget):
    name = "Connected Components"
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage._dataVol.backgroundOverlays
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  self.ilastik._activeImage._dataVol.backgroundOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        
        #create background overlay
        ov = OverlayItem(self.ilastik._activeImage._dataVol.background._data, color=0, alpha=1.0, colorTable = self.ilastik._activeImage._dataVol.background.getColorTab(), autoAdd = True, autoVisible = True, linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Connected Components/Background"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Connected Components/Background"]
        
        self.ilastik.labelWidget.setLabelWidget(BackgroundWidget(self.ilastik.project.backgroundMgr, self.ilastik._activeImage._dataVol.background, self.ilastik.labelWidget, ov))    
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.ilastik._activeImage._dataVol.background._history = self.ilastik.labelWidget._history

        if self.ilastik._activeImage._dataVol.background._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage._dataVol.background._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnInputOverlay = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Select Overlay')
        self.btnCC = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'CC')
        self.btnCCBack = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System), 'CC with background')
        self.btnCCOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System), 'Options')
        
        self.btnInputOverlay.setToolTip('Select an overlay for connected components search')
        self.btnCC.setToolTip('Run connected componets on the selected overlay')
        self.btnCCBack.setToolTip('Run connected components with background')
        self.btnCCOptions.setToolTip('Set options')
        
        self.btnInputOverlay.setEnabled(True)
        self.btnCC.setEnabled(False)
        self.btnCCBack.setEnabled(False)
        self.btnCCOptions.setEnabled(True)
        
        tl.addWidget(self.btnInputOverlay)
        tl.addWidget(self.btnCC)
        tl.addWidget(self.btnCCBack)
        tl.addStretch()
        tl.addWidget(self.btnCCOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnInputOverlay, QtCore.SIGNAL('clicked()'), self.on_btnInputOverlay_clicked)
        self.connect(self.btnCC, QtCore.SIGNAL('clicked()'), self.on_btnCC_clicked)
        self.connect(self.btnCCBack, QtCore.SIGNAL('clicked()'), self.on_btnCCBack_clicked)
        #self.connect(self.btnCCOptions, QtCore.SIGNAL('clicked()'), self.on_btnCCOptions_clicked)
        
        
    def on_btnInputOverlay_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            print overlay.key
            self.parent.project.dataMgr.connCompBackgroundKey = overlay.key
            
        self.btnCC.setEnabled(True)
        self.btnCCBack.setEnabled(True)
        
    def on_btnCC_clicked(self):
        self.parent.on_connectComponents(background = False)
    def on_btnCCBack_clicked(self):
        self.parent.on_connectComponents(background = True)

        
        
    
    
    
