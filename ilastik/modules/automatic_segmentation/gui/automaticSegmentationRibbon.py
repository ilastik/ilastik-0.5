# -*- coding: utf-8 -*-
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
import ilastik.gui.volumeeditor as ve
                    
                    
#*******************************************************************************
# A u t o S e g m e n t a t i o n T a b                                        *
#*******************************************************************************

class AutoSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Auto Segmentation'
    position = 2
    moduleName = "Automatic_Segmentation"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        self.weights = None
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
    
    def on_deActivation(self):
        pass
    
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
        self.btnChooseWeights = TabButton('Choose Border Probability Overlay', ilastikIcons.Select)
        self.btnSegment       = TabButton('Segment', ilastikIcons.Play)
        self.btnChooseWeights.setToolTip('Choose the input overlay that contains border probabilities')
        self.btnSegment.setToolTip('Segment the image')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            borderIndicator = QtGui.QInputDialog.getItem(self.ilastik, "Select border indicator type", "Select the border probability type : \n (Normal: bright pixels mean high border probability, Inverted: dark pixels mean high border probability) ",  ["Normal",  "Inverted"],  editable = False)
            borderIndicator = str(borderIndicator[0])
            if borderIndicator == "Normal":
                weights = volume[:,:,:]
            elif borderIndicator == "Inverted":            
                weights = self.parent.project.dataMgr.Automatic_Segmentation.invertPotential(volume)
            weights = self.parent.project.dataMgr.Automatic_Segmentation.normalizePotential(weights)

            self.weights = weights
        
    def on_btnSegment_clicked(self):
        
        if self.weights is not None:
            self.parent.project.dataMgr.Automatic_Segmentation.computeResults(self.weights)
            self.parent.project.dataMgr.Automatic_Segmentation.finalizeResults()
            
            self.parent.labelWidget.repaint()
        
    def on_btnSegmentorsOptions_clicked(self):
        pass

