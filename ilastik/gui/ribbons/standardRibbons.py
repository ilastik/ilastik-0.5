import numpy,vigra
import random
import code

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore
from ilastik.gui.iconMgr import ilastikIcons

import ilastik.gui
from ilastik.gui.projectDialog import ProjectDlg, ProjectSettingsDlg
from ilastik.gui.classifierSelectionDialog import ClassifierSelectionDlg
from ilastik.core import projectMgr
from ilastik.gui.featureDlg import FeatureDlg
from ilastik.gui.segmentorSelectionDlg import SegmentorSelectionDlg
from ilastik.gui.batchProcess import BatchProcess
from ilastik.gui.shortcutmanager import shortcutManager
import ilastik.core.overlays
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.core.overlayMgr import OverlayItem
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui import volumeeditor as ve
from ilastik.core.volume import DataAccessor
from ilastik.gui.labelWidget import LabelListWidget
from ilastik.gui.seedWidget import SeedListWidget
from ilastik.gui.objectWidget import ObjectListWidget
from ilastik.gui.backgroundWidget import BackgroundWidget


import gc, weakref

class ProjectTab(IlastikTabBase, QtGui.QWidget):
    name = 'Project'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.projectOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.projectOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
    
    def on_deActivation(self):
        if self.ilastik.labelWidget is not None:
            if self.ilastik.labelWidget._history != self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history:
                self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history = self.ilastik.labelWidget._history
    
            if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history is not None:
                self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history

        
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
            self.parent._activeImage = 0
            
    def on_btnSave_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Project", ilastik.gui.LAST_DIRECTORY, "Project Files (*.ilp)")
        fn = str(fileName)
        if len(fn) > 4:
            if fn[-4:] != '.ilp':
                fn = fn + '.ilp'
            self.parent.project.saveToDisk(fn)
            ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fn).path()
    
    def on_btnOpen_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Project", ilastik.gui.LAST_DIRECTORY, "Project Files (*.ilp)")
        if str(fileName) != "":
            labelWidget = None
            if self.parent.project is not None:
                if len(self.parent.project.dataMgr) > self.parent._activeImage:
                    labelWidget = weakref.ref(self.parent.project.dataMgr[self.parent._activeImage])#.featureBlockAccessor)
            self.parent.project = projectMgr.Project.loadFromDisk(str(fileName), self.parent.featureCache)
            self.btnSave.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnOptions.setEnabled(True)
            self.parent._activeImage = 0
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
        tmp = ProjectSettingsDlg(self, self.parent.project)
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
            ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.projectOverlays
            if len(ovs) == 0:
                raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
                if raw is not None:
                    ovs.append(raw.getRef())
            
            self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
    
            overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.projectOverlays)
            self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
            
            self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
            
            
            self.volumeEditorVisible = self.ilastik.volumeEditorDock.isVisible()
            self.ilastik.volumeEditorDock.setVisible(False)
            
            if self.consoleWidget is None:
                locals = {}
                locals["activeImage"] = self.ilastik.project.dataMgr[self.ilastik._activeImage]
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
            if self.ilastik.labelWidget is not None:
                if self.ilastik.labelWidget._history != self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history:
                    self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history = self.ilastik.labelWidget._history
        
                if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history is not None:
                    self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history
            
        def _initContent(self):
            pass
        
        def _initConnects(self):
            pass
except:
    pass    


        
class ClassificationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Classification'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labelOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labelOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        #create LabelOverlay
        ov = OverlayItem(self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._data, color = 0, alpha = 1.0, colorTable = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Classification/Labels"] = ov
        ov = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Classification/Labels"]
        
        self.ilastik.labelWidget.setLabelWidget(LabelListWidget(self.ilastik.project.labelMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels,  self.ilastik.labelWidget,  ov))
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        if hasattr(self.parent, "classificationInteractive"):
            self.btnStartLive.click()
        if self.ilastik.labelWidget._history != self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history:
            self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history = self.ilastik.labelWidget._history

        if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history is not None:
            self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.labels._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
     
        self.btnSelectFeatures = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Select Features')
        self.btnStartLive = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Start Live Prediction')
        self.btnStartLive.setCheckable(True)
        self.btnTrainPredict = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Train and Predict')
        self.btnExportClassifier = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Export Classifier')
        self.btnClassifierOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Classifier Options')
        
        self.btnSelectFeatures.setToolTip('Select and compute features')
        self.btnStartLive.setToolTip('Toggle interactive prediction of the current image while labeling')
        self.btnTrainPredict.setToolTip('Train and predict all images offline; this step is necessary for automation')
        self.btnExportClassifier.setToolTip('Save current classifier and its feature settings')
        self.btnClassifierOptions.setToolTip('Select a classifier and change its settings')
        
        self.btnSelectFeatures.setEnabled(True)
        self.btnStartLive.setEnabled(False)
        self.btnTrainPredict.setEnabled(False)
        self.btnExportClassifier.setEnabled(False)
        self.btnClassifierOptions.setEnabled(True)
        
        tl.addWidget(self.btnSelectFeatures)
        tl.addWidget(self.btnStartLive)
        tl.addWidget(self.btnTrainPredict)
        tl.addStretch()
        tl.addWidget(self.btnExportClassifier)
        tl.addWidget(self.btnClassifierOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnSelectFeatures, QtCore.SIGNAL('clicked()'), self.on_btnSelectFeatures_clicked)
        self.connect(self.btnStartLive, QtCore.SIGNAL('toggled(bool)'), self.on_btnStartLive_clicked)
        self.connect(self.btnTrainPredict, QtCore.SIGNAL('clicked()'), self.on_btnTrainPredict_clicked)
        self.connect(self.btnExportClassifier, QtCore.SIGNAL('clicked()'), self.on_btnExportClassifier_clicked)
        self.connect(self.btnClassifierOptions, QtCore.SIGNAL('clicked()'), self.on_btnClassifierOptions_clicked)
        
    def on_btnSelectFeatures_clicked(self):
        preview = self.parent.project.dataMgr[0]._dataVol._data[0,0,:,:,0:3]
        self.parent.newFeatureDlg = FeatureDlg(self.parent, preview)
        
    def on_btnStartLive_clicked(self, state):
        self.parent.on_classificationInteractive(state)
        
    def on_btnTrainPredict_clicked(self):
        self.parent.on_classificationTrain()
        
    def on_btnExportClassifier_clicked(self):
        self.parent.on_exportClassifier()
        
    def on_btnClassifierOptions_clicked(self):
        dialog = ClassifierSelectionDlg(self.parent)
        self.parent.project.classifier = dialog.exec_()

class AutoSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Auto Segmentation'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        self.weights = None
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.autosegOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.autosegOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
    
    def on_deActivation(self):
        pass
    
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Border Indicator')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        #self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Segmentors Options')
        
        self.btnChooseWeights.setToolTip('Choose the border indicator for the segmentation task')
        self.btnSegment.setToolTip('Segment the image')
        #self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        #tl.addWidget(self.btnSegmentorsOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        #self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            print numpy.max(volume),  numpy.min(volume)
    
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(None, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness"],  editable = False)
            borderIndicator = str(borderIndicator[0])
            
            sigma = 1.0
            normalizePotential = True
            #TODO: this , until now, only supports gray scale and 2D!
            if borderIndicator == "Brightness":
                weights = volume[:,:,:]
            elif borderIndicator == "Darkness":
                weights = (255 - volume[:,:,:])
    
            if normalizePotential == True:
                min = numpy.min(weights)
                max = numpy.max(weights)
                weights = (weights - min)*(255.0 / (max - min))
                #real_weights[:] = weights[:]

            data = numpy.ndarray(weights.shape, 'float32')
            data[:] = weights[:]
                    
            self.weights = data
                
        
    def on_btnSegment_clicked(self):
        
        if self.weights is not None:
            res = numpy.ndarray((1,) + self.weights.shape + (1,), 'int32')
            if self.weights.shape[0] > 1:
                data = self.weights.view(vigra.ScalarVolume)
                res[0,:,:,:,0] = vigra.analysis.watersheds(data, neighborhood = 6)[0]
            else:
                data = self.weights[0,:,:].view(vigra.ScalarImage)
                res[0,0,:,:,0] = vigra.analysis.watersheds(data, neighborhood = 4)[0]
            
            colortable = []
            for i in range(256):
                color = QtGui.QColor(random.randint(0,255),random.randint(0,255),random.randint(0,255))
                colortable.append(color.rgba())
            
            #create Overlay for segmentation:
            if self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Auto Segmentation/Segmentation"] is None:
                ov = OverlayItem(res, color = 0, alpha = 1.0, colorTable = colortable, autoAdd = True, autoVisible = True)
                self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Auto Segmentation/Segmentation"] = ov
            else:
                self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Auto Segmentation/Segmentation"]._data = DataAccessor(res)
            self.parent.labelWidget.repaint()
        
    def on_btnSegmentorsOptions_clicked(self):
        pass
        #dialog = AutoSegmentorSelectionDlg(self.parent)
        #answer = dialog.exec_()
        #if answer != None:
        #    self.parent.project.autoSegmentor = answer
        #    self.parent.project.autoSegmentor.setupWeights(self.parent.project.dataMgr[self.parent._activeImage].autoSegmentationWeights)


        
class SegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Segmentation'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seedOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seedOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        #create SeedsOverlay
        ov = OverlayItem(self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds._data, color = 0, alpha = 1.0, colorTable = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Segmentation/Seeds"] = ov
        ov = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Segmentation/Seeds"]

        self.ilastik.labelWidget.setLabelWidget(SeedListWidget(self.ilastik.project.seedMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds,  self.ilastik.labelWidget,  ov))


    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        if self.ilastik.labelWidget._history != self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds._history:
            self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds._history = self.ilastik.labelWidget._history
        
        if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds._history is not None:
            self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        self.btnSegment.setEnabled(False)
        self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Segmentors Options')
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            print numpy.max(volume),  numpy.min(volume)
    
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(None, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness"],  editable = False)
            borderIndicator = str(borderIndicator[0])
            
            sigma = 1.0
            normalizePotential = True
            #TODO: this , until now, only supports gray scale and 2D!
            if borderIndicator == "Brightness":
                weights = volume[:,:,:].view(vigra.ScalarVolume)
                #weights = vigra.filters.gaussianSmoothing(volume[:,:,:].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma)
                #weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
                #real_weights[:,:,:,0] = weights[:,:,:]
                #eal_weights[:,:,:,1] = weights[:,:,:]
                #real_weights[:,:,:,2] = weights[:,:,:]
            elif borderIndicator == "Darkness":
                weights = (255 - volume[:,:,:]).view(vigra.ScalarVolume)
                #weights = vigra.filters.gaussianSmoothing((255 - volume[:,:,:]).swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma)
                #weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
                #real_weights[:,:,:,0] = weights[:,:,:]
                #real_weights[:,:,:,1] = weights[:,:,:]
                #real_weights[:,:,:,2] = weights[:,:,:]
            elif borderIndicator == "Gradient":
                weights = vigra.filters.gaussianGradientMagnitude(volume[:,:,:].swapaxes(0,2).astype('float32').view(vigra.ScalarVolume), sigma)
                weights = weights.swapaxes(0,2).view(vigra.ScalarVolume)
                #real_weights[:] = weights[:]
    
            if normalizePotential == True:
                min = numpy.min(weights)
                max = numpy.max(weights)
                weights = (weights - min)*(255.0 / (max - min))
                #real_weights[:] = weights[:]
    
            self.ilastik.project.segmentor.setupWeights(weights)
            self.ilastik.project.dataMgr[self.ilastik._activeImage]._segmentationWeights = weights
            self.btnSegment.setEnabled(True)
        
    def on_btnSegment_clicked(self):
        self.parent.on_segmentationSegment()
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.segmentor = answer
            self.parent.project.segmentor.setupWeights(self.parent.project.dataMgr[self.parent._activeImage]._segmentationWeights)

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
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.backgroundOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.backgroundOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        
        #create background overlay
        ov = OverlayItem(self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background._data, color=0, alpha=1.0, colorTable = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background.getColorTab(), autoAdd = True, autoVisible = True, linkColorTable = True)
        self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Connected Components/Background"] = ov
        ov = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Connected Components/Background"]
        
        self.ilastik.labelWidget.setLabelWidget(BackgroundWidget(self.ilastik.project.backgroundMgr, self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background, self.ilastik.labelWidget, ov))    
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background._history = self.ilastik.labelWidget._history

        if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background._history is not None:
            self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.background._history
        
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
        
    
class ObjectsTab(IlastikTabBase, QtGui.QWidget):
    name = 'Objects'
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objectOverlays
        if len(ovs) == 0:
            raw = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())        
        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objectOverlays)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        
        #create ObjectsOverlay
        ov = OverlayItem(self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objects._data, color = 0, alpha = 1.0, colorTable = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Objects/Selection"] = ov
        ov = self.ilastik.project.dataMgr[self.ilastik._activeImage].overlayMgr["Objects/Selection"]
        
        self.ilastik.labelWidget.setLabelWidget(ObjectListWidget(self.ilastik.project.objectMgr,  self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objects,  self.ilastik.labelWidget,  ov))
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objects._history = self.ilastik.labelWidget._history
        
        if self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objects._history is not None:
            self.ilastik.labelWidget._history = self.ilastik.project.dataMgr[self.ilastik._activeImage]._dataVol.objects._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Select overlay')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'3D')
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.parent,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            import ilastik.core.overlays.selectionOverlay
            if self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Objects/Selection Result"] is None:
                ov = ilastik.core.overlays.selectionOverlay.SelectionOverlay(answer[0]._data, color = long(QtGui.QColor(0,255,255).rgba()))
                self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Objects/Selection Result"] = ov
                ov = self.parent.project.dataMgr[self.parent._activeImage].overlayMgr["Objects/Selection Result"]
            
            ref = answer[0].getRef()
            ref.setAlpha(0.4)
            self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
            
            self.parent.project.objectMgr.setInputData(answer[0]._data)
                
            self.parent.labelWidget.repaint()

    def on_btnSegment_clicked(self):
        pass
                    


            
class AutomateTab(IlastikTabBase, QtGui.QWidget):
    name = 'Automate'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
    
    def on_activation(self):
        pass
                        
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        
        tl = QtGui.QHBoxLayout()      
        self.btnBatchProcess = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Batch Process')
       
        self.btnBatchProcess.setToolTip('Select and batch predict files with the currently trained classifier')
        tl.addWidget(self.btnBatchProcess)
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnBatchProcess, QtCore.SIGNAL('clicked()'), self.on_btnBatchProcess_clicked)
        
    def on_btnBatchProcess_clicked(self): 
        dialog = BatchProcess(self.parent)
        dialog.exec_()
        
class HelpTab(IlastikTabBase, QtGui.QWidget):
    name = 'Help'
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        print 'Changed to Tab: ', self.__class__.name
       
    def on_deActivation(self):
        print 'Left Tab ', self.__class__.name
        
    def _initContent(self):

        tl = QtGui.QHBoxLayout()      
        self.btnShortcuts = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Help),'Shortcuts')
      
        self.btnShortcuts.setToolTip('Show a list of ilastik shortcuts')
        
        tl.addWidget(self.btnShortcuts)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        
    def _initConnects(self):
        self.connect(self.btnShortcuts, QtCore.SIGNAL('clicked()'), self.on_btnShortcuts_clicked)
        
    def on_btnShortcuts_clicked(self):
        shortcutManager.showDialog()
        
        
    
    
    
