# -*- coding: utf-8 -*-
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore

import ilastik.gui
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.object_picking.core.objectModuleMgr import ObjectOverlayItem
from objectWidget import ObjectListWidget

#*******************************************************************************
# O b j e c t s T a b                                                          *
#*******************************************************************************

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

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.objectLabels = ObjectListWidget(self.ilastik._activeImage.Object_Picking,  self.ilastik._activeImage.Object_Picking.objects,  self.ilastik.labelWidget) 
        self.ilastik.labelWidget.setLabelWidget(self.objectLabels)
        
        #create ObjectsOverlay
        ov = ObjectOverlayItem(self.objectLabels, self.ilastik._activeImage.Object_Picking.objects._data, color = 0, alpha = 1.0, autoAdd = True, autoVisible = True,  linkColorTable = True)
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
        tl.setMargin(0)
        
        self.btnChooseOverlay = TabButton('Select overlay', ilastikIcons.Select)
        self.btn3D            = TabButton('3D', ilastikIcons.Play)
        self.btnReport        = TabButton('Generate report', ilastikIcons.Play)
        self.btnSelectAll     = TabButton('Select all', ilastikIcons.Select)
        self.btnClearAll      = TabButton('Clear all', ilastikIcons.Select)
        
        self.btnChooseOverlay.setToolTip('Choose the overlay with objects')
        self.btn3D.setToolTip('Display the currently selected objects in 3D')
        self.btnReport.setToolTip('Generate a report for all currently selected objects')
        
        self.btnSelectAll.setToolTip('Select all the objects')
        self.btnClearAll.setToolTip('Clear selection')
        
        tl.addWidget(self.btnChooseOverlay)
        tl.addWidget(self.btn3D)
        tl.addWidget(self.btnReport)
        tl.addStretch()
        tl.addWidget(self.btnSelectAll)
        tl.addWidget(self.btnClearAll)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseOverlay, QtCore.SIGNAL('clicked()'), self.on_btnChooseOverlay_clicked)
        self.connect(self.btn3D, QtCore.SIGNAL('clicked()'), self.on_btn3D_clicked)
        self.connect(self.btnReport, QtCore.SIGNAL('clicked()'), self.on_btnReport_clicked)
        self.connect(self.btnSelectAll, QtCore.SIGNAL('clicked()'), self.on_btnSelectAll_clicked)
        self.connect(self.btnClearAll, QtCore.SIGNAL('clicked()'), self.on_btnClearAll_clicked)
        
    def on_btnChooseOverlay_clicked(self):
        dlg = OverlaySelectionDialog(self.parent,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            import ilastik.core.overlays.selectionOverlay
            if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"] is None:
                ov = ilastik.core.overlays.selectionOverlay.SelectionOverlay(answer[0]._data, color = long(QtGui.QColor(0,255,255).rgba()))
                ov.displayable3D = True
                ov.backgroundClasses = set([0])
                ov.smooth3D = True
                
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"] = ov
                ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Objects/Selection Result"]
            
            ref = answer[0].getRef()
            ref.setAlpha(0.4)
            self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
            
            self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Object_Picking.setInputData(answer[0]._data)
                
            self.parent.labelWidget.repaint()

    def on_btn3D_clicked(self):
        pass

    def on_btnSelectAll_clicked(self):
        self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Object_Picking.selectAll()

    def on_btnClearAll_clicked(self):
        self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Object_Picking.clearAll()

    def on_btnReport_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Report", ilastik.gui.LAST_DIRECTORY, "Reports (*.html)")
        fn = str(QtCore.QDir.convertSeparators(fileName))
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fn).path()
        self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Object_Picking.generateReport(fn)
