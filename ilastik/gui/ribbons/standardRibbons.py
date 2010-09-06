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

class ProjectTab(IlastikTabBase, QtGui.QWidget):
    name = 'Project'
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
            self.parent.activeImage = 0
            
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
            self.parent.project = projectMgr.Project.loadFromDisk(str(fileName), self.parent.featureCache)
            self.btnSave.setEnabled(True)
            self.btnEdit.setEnabled(True)
            self.btnOptions.setEnabled(True)
            self.parent.activeImage = 0
            self.parent.changeImage(0)
            
            ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
   
    def on_btnEdit_clicked(self):
        self.parent.pareprojectDlg = ProjectDlg(self, False)
        self.parentprojectDlg.updateDlg(self.project)
        self.parent.projectModified()
        
    def on_btnOptions_clicked(self):
        tmp = ProjectSettingsDlg(self, self.parent.project)
        tmp.exec_()
        
class ClassificationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Classification'
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
        preview = self.parent.project.dataMgr[0].dataVol.data[0,0,:,:,0:3]
        self.parent.newFeatureDlg = FeatureDlg(self.parent, preview)
        
    def on_btnStartLive_clicked(self, state):
        self.parent.on_classificationInteractive(state)
        
    def on_btnTrainPredict_clicked(self):
        self.parent.on_classificationTrain()
        
    def on_btnExportClassifier_clicked(self):
        self.parent.on_saveClassifier()
        
    def on_btnClassifierOptions_clicked(self):
        dialog = ClassifierSelectionDlg(self.parent)
        self.parent.project.classifier = dialog.exec_()
        
class SegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Segmentation'
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
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
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
        self.parent.on_segmentationWeights()
        
    def on_btnSegment_clicked(self):
        self.parent.on_segmentationSegment()
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.segmentor = answer
            self.parent.project.segmentor.setupWeights(self.project.dataMgr[self.activeImage].segmentationWeights)


class ObjectsTab(IlastikTabBase, QtGui.QWidget):
    name = 'Objects'
    
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
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
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
            ov = ilastik.core.overlays.selectionOverlay.SelectionOverlay(answer[0].data, color = long(QtGui.QColor(0,255,255).rgba()))
            self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Objects/Selection Result"] = ov
            ov = self.parent.project.dataMgr[self.parent.activeImage].overlayMgr["Objects/Selection Result"]
            
            ref = answer[0].getRef()
            ref.setAlpha(0.4)
            self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
            
            self.parent.project.objectMgr.setInputData(answer[0].data)
                
            self.parent.labelWidget.repaint()

    def on_btnSegment_clicked(self):
        pass
                    

class ConnectedComponentsTab(IlastikTabBase, QtGui.QWidget):
    name = "Connected Components"
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
        self.parent.on_objectProcSelect()
        self.btnCC.setEnabled(True)
        self.btnCCBack.setEnabled(True)
        
    def on_btnCC_clicked(self):
        self.parent.connComp.start(False)
        
    def on_btnCCBack_clicked(self):
        self.parent.connComp.start(True)
        
    

            
class AutomateTab(IlastikTabBase, QtGui.QWidget):
    name = 'Automate'
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
        
    def _initConnects(self):
        self.connect(self.btnShortcuts, QtCore.SIGNAL('clicked()'), self.on_btnShortcuts_clicked)
        
    def on_btnShortcuts_clicked(self): 
        shortcutManager.showDialog()
        
        
    
    
    