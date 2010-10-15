# -*- coding: utf-8 -*-
import numpy, vigra
import random

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.object_picking.core.objectModuleMgr import ObjectOverlayItem
from ilastik.core.volume import DataAccessor
import ilastik.gui.volumeeditor as ve
from objectWidget import ObjectListWidget

class ObjectsTab(IlastikTabBase, QtGui.QWidget):
    name = 'Objects'
    moduleName = "Object_Picking"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())        
        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.Object_Picking,  ovs)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.objectLabels = ObjectListWidget(self.ilastik._activeImage.Object_Picking,  self.ilastik._activeImage.Object_Picking.objects,  self.ilastik.labelWidget) 
        self.ilastik.labelWidget.setLabelWidget(self.objectLabels)
        
        #create ObjectsOverlay
        ov = ObjectOverlayItem(self.ilastik._activeImage, self.objectLabels, self.ilastik._activeImage.Object_Picking.objects._data, color = 0, alpha = 1.0, autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Objects/Selection"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Objects/Selection"]
        
        self.ilastik.labelWidget.setLabelWidget(self.objectLabels)
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.ilastik._activeImage.Object_Picking.objects._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Object_Picking.objects._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Object_Picking.objects._history
        
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
            if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"] is None:
                ov = ilastik.core.overlays.selectionOverlay.SelectionOverlay(answer[0]._data, color = long(QtGui.QColor(0,255,255).rgba()))
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"] = ov
                ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"]
            
            ref = answer[0].getRef()
            ref.setAlpha(0.4)
            self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
            
            self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Object_Picking.setInputData(answer[0]._data)
                
            self.parent.labelWidget.repaint()

    def on_btnSegment_clicked(self):
        pass
