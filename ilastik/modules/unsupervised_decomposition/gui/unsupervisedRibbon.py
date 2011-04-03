from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.unsupervised_decomposition.gui.guiThread import UnsupervisedDecomposition
from ilastik.modules.unsupervised_decomposition.gui.unsupervisedSelectionDlg import UnsupervisedSelectionDlg
import ilastik.gui.volumeeditor as ve

#*******************************************************************************
# U n s u p e r v i s e d T a b                                                *
#*******************************************************************************

class UnsupervisedTab(IlastikTabBase, QtGui.QWidget):
    name = 'Unsupervised Decomposition'
    position = 2
    moduleName = "Unsupervised_Decomposition"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
        self.overlays = None

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
        
        self.btnUnsupervisedOptions.setEnabled(True)     
                
    def on_deActivation(self):
        self.btnDecompose.setEnabled(False)  
            
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
        self.btnChooseOverlays      = TabButton('Select Overlay', ilastikIcons.Select)
        self.btnDecompose           = TabButton('decompose', ilastikIcons.Play)
        self.btnUnsupervisedOptions = TabButton('Unsupervised Decomposition Options', ilastikIcons.System)

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
        else:
            self.btnDecompose.setEnabled(False)         
        
    def on_btnDecompose_clicked(self):
        self.unsDec = UnsupervisedDecomposition(self.ilastik)
        self.unsDec.start(self.overlays)

    def on_btnUnsupervisedOptions_clicked(self):
        dialog = UnsupervisedSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod = answer  
