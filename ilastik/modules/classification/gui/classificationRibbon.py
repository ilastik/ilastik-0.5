import gc

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from ilastik.core.dataMgr import  PropertyMgr

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.modules.classification.gui.guiThreads import *
from ilastik.modules.classification.gui.labelWidget import LabelListWidget
from ilastik.modules.classification.gui.featureDlg import FeatureDlg
from ilastik.modules.classification.gui.classifierSelectionDialog import ClassifierSelectionDlg


#*******************************************************************************
# C l a s s i f i c a t i o n T a b                                            *
#*******************************************************************************

class ClassificationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Classification'
    position = 1
    moduleName = "Classification"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        if self.ilastik._activeImage.module[self.name] is None:
            self.ilastik._activeImage.module[self.name] = PropertyMgr(self.ilastik._activeImage)
        
        ovs = self.ilastik._activeImage.module[self.name].getOverlayRefs()
        
        raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        
        ov = self.ilastik._activeImage.overlayMgr["Classification/Labels"]
        
        overlayWidget.addOverlayRef(ov.getRef())
        overlayWidget.addOverlayRef(raw.getRef())
                
        self.ilastik.labelWidget.setLabelWidget(LabelListWidget(self.ilastik.project.dataMgr.module["Classification"].labelMgr,  self.ilastik.project.dataMgr.module["Classification"]["labelDescriptions"],  self.ilastik.labelWidget,  ov))
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        if hasattr(self.parent, "classificationInteractive"):
            self.btnStartLive.click()
        if self.ilastik.labelWidget is not None and self.ilastik.labelWidget._history != self.ilastik._activeImage.module["Classification"]["labelHistory"]:
            self.ilastik._activeImage.module["Classification"]["labelHistory"] = self.ilastik.labelWidget._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
     
        self.btnSelectFeatures    = TabButton('Select Features', ilastikIcons.Select)
        self.btnStartLive         = TabButton('Start Live Prediction', ilastikIcons.Play)
        self.btnStartLive.setCheckable(True)
        self.btnTrainPredict      = TabButton('Train and Predict', ilastikIcons.System)
        self.btnExportClassifier  = TabButton('Export Classifier', ilastikIcons.Select)
        self.btnClassifierOptions = TabButton('Classifier Options', ilastikIcons.Select)
        
        self.btnSelectFeatures.setToolTip('Select and compute features')
        self.btnStartLive.setToolTip('Toggle interactive prediction of the current image while labeling')
        self.btnTrainPredict.setToolTip('Train and predict all images offline; this step is necessary for automation')
        self.btnExportClassifier.setToolTip('Save current classifier and its feature settings')
        self.btnClassifierOptions.setToolTip('Select a classifier and change its settings')
        
        self.on_otherProject()
        
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
        
    def on_otherProject(self):
        self.btnSelectFeatures.setEnabled(True)
        self.btnStartLive.setEnabled(False)
        self.btnTrainPredict.setEnabled(False)
        self.btnExportClassifier.setEnabled(False)
        self.btnClassifierOptions.setEnabled(True)
        
    def on_btnSelectFeatures_clicked(self):
        preview = self.parent.project.dataMgr[0]._dataVol._data[0,0,:,:,0:3]
        newFeatureDlg = FeatureDlg(self.ilastik, preview)
        answer = newFeatureDlg.exec_()
        if answer == QtGui.QDialog.Accepted:
            self.featureComputation = FeatureComputation(self.ilastik)
        newFeatureDlg.close()
        newFeatureDlg.deleteLater()
        del newFeatureDlg
        gc.collect()
                    
    def on_btnStartLive_clicked(self, state):
        if state:
            self.ilastik.ribbon.getTab('Classification').btnStartLive.setText('Stop Live Prediction')
            self.classificationInteractive = ClassificationInteractive(self.ilastik)
        else:
            self.classificationInteractive.stop()
            self.ilastik.ribbon.getTab('Classification').btnStartLive.setText('Start Live Prediction')
        
    def on_btnTrainPredict_clicked(self):
        self.classificationTrain = ClassificationTrain(self.ilastik)
        self.connect(self.classificationTrain, QtCore.SIGNAL("trainingFinished()"), self.on_trainingFinished)
        
    def on_trainingFinished(self):
        print "Training finished"
        self.classificationPredict = ClassificationPredict(self.ilastik)
        
    def on_btnExportClassifier_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", filter =  "HDF5 Files (*.h5)")
        
        try:
            self.ilastik.project.dataMgr.Classification.exportClassifiers(fileName)
        except (RuntimeError, AttributeError, IOError) as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            return

        try:
            self.ilastik.project.dataMgr.Classification.featureMgr.exportFeatureItems(fileName)
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            return
        
        QtGui.QMessageBox.information(self, 'Success', "The classifier and the feature information have been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
        
        
    def on_btnClassifierOptions_clicked(self):
        dialog = ClassifierSelectionDlg(self.parent)
        self.parent.project.dataMgr.module["Classification"].classifier = dialog.exec_()