import numpy, vigra, h5py
import random
import code

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore

from ilastik.core.dataMgr import  PropertyMgr
from ilastik.core.overlayMgr import OverlayItem

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.modules.classification.gui.guiThreads import *
from ilastik.modules.classification.gui.labelWidget import LabelListWidget
from ilastik.modules.classification.gui.batchProcess import BatchProcess
from ilastik.modules.classification.gui.featureDlg import FeatureDlg
from ilastik.modules.classification.gui.classifierSelectionDialog import ClassifierSelectionDlg


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
        
        if len(ovs) < 2:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  ovs)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        
        ov = self.ilastik._activeImage.overlayMgr["Classification/Labels"]
        
        overlayWidget.addOverlayRef(ov.getRef())
        
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
        self.parent.newFeatureDlg = FeatureDlg(self.ilastik, preview)

                    
    def on_btnStartLive_clicked(self, state):
        if state:
            self.ilastik.ribbon.getTab('Classification').btnStartLive.setText('Stop Live Prediction')
            self.classificationInteractive = ClassificationInteractive(self.ilastik)
        else:
            self.classificationInteractive.stop()
            del self.classificationInteractive
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
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            return

        try:
            h5file = h5py.File(str(fileName),'a')
            if 'features' in h5file.keys():
                del h5file['features']
            h5featGrp = h5file.create_group('features')
            self.ilastik.project.dataMgr.Classification.featureMgr.exportFeatureItems(h5featGrp)
            h5file.close()
        except RuntimeError as e:
            QtGui.QMessageBox.warning(self, 'Error', str(e), QtGui.QMessageBox.Ok)
            h5file.close()
            return
        
        #if fileName is not None:
            # global LAST_DIRECTORY
            #fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Classifier", ilastik.gui.LAST_DIRECTORY, "HDF5 Files (*.h5)")
            #ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileName).path()
        
        # Make sure group 'classifiers' exist
#        print fileName
#        h5file = h5py.File(str(fileName),'a')
#        h5file.create_group('classifiers')
#        h5file.close()
#        
#        for i, c in enumerate(self.project.dataMgr.classifiers):
#            tmp = c.serialize(str(fileName), "classifiers/rf_%03d" % i)
#            print "Write Random Forest # %03d -> %d" % (i,tmp)
        
        # Export user feature selection
#        h5file = h5py.File(str(fileName),'a')
#        h5featGrp = h5file.create_group('features')
#        
#        featureItems = self.project.featureMgr.featureItems
#        for k, feat in enumerate(featureItems):
#            itemGroup = h5featGrp.create_group('feature_%03d' % k)
#            feat.serialize(itemGroup)
#        h5file.close()

        QtGui.QMessageBox.information(self, 'Success', "The classifier and the feature information have been saved successfully to:\n %s" % str(fileName), QtGui.QMessageBox.Ok)
        
        
    def on_btnClassifierOptions_clicked(self):
        dialog = ClassifierSelectionDlg(self.parent)
        self.parent.project.dataMgr.module["Classification"].classifier = dialog.exec_()