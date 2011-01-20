# -*- coding: utf-8 -*-

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore
from ilastik.gui.iconMgr import ilastikIcons

import ilastik.gui
from ilastik.core import projectMgr

from ilastik.gui.unsupervisedSelectionDlg import UnsupervisedSelectionDlg

import ilastik.core.overlays
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.gui import volumeeditor as ve


from ilastik.gui.backgroundWidget import BackgroundWidget




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

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
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
                        
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
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

        
        
    
    
    
