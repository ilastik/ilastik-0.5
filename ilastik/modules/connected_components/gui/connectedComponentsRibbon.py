from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.connected_components.core.connectedComponentsMgr import BackgroundOverlayItem
#import ilastik.gui.volumeeditor as ve
from backgroundWidget import BackgroundWidget
from guiThread import CC
from labelSelectionForm import LabelSelectionForm


#*******************************************************************************
# C o n n e c t e d C o m p o n e n t s T a b                                  *
#*******************************************************************************

class ConnectedComponentsTab(IlastikTabBase, QtGui.QWidget):
    name = 'Connected Components'
    position = 2
    moduleName = "Connected_Components"
    
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

        self.backgroundLabels = BackgroundWidget(self.ilastik._activeImage.Connected_Components,  self.ilastik._activeImage.Connected_Components.background,  self.ilastik.labelWidget) 
        self.ilastik.labelWidget.setLabelWidget(self.backgroundLabels)
        
        #create ObjectsOverlay
        ov = BackgroundOverlayItem(self.backgroundLabels, self.ilastik._activeImage.Connected_Components.background._data, color = 0, alpha = 1.0, autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Connected Components/Background"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Connected Components/Background"]
        
        self.ilastik.labelWidget.setLabelWidget(self.backgroundLabels)
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.ilastik._activeImage.Connected_Components.background._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Connected_Components.background._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Connected_Components.background._history
            
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
        self.btnInputOverlay = TabButton('Select Overlay', ilastikIcons.Select)
        self.btnCC           = TabButton('CC', ilastikIcons.System)
        self.btnCCBack       = TabButton('CC with background', ilastikIcons.System)
        self.btnFilter       = TabButton('Filter synapses', ilastikIcons.System)
        
        self.btnInputOverlay.setToolTip('Select an overlay for connected components search')
        self.btnCC.setToolTip('Run connected components on the selected overlay')
        self.btnCCBack.setToolTip('Run connected components with background')
        self.btnFilter.setToolTip('Perform synapse filtering and dilation')
        
        self.btnInputOverlay.setEnabled(True)
        self.btnCC.setEnabled(False)
        self.btnCCBack.setEnabled(False)
        self.btnFilter.setEnabled(True)
        
        tl.addWidget(self.btnInputOverlay)
        tl.addWidget(self.btnCC)
        tl.addWidget(self.btnCCBack)
        tl.addStretch()
        tl.addWidget(self.btnFilter)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnInputOverlay, QtCore.SIGNAL('clicked()'), self.on_btnInputOverlay_clicked)
        self.connect(self.btnCC, QtCore.SIGNAL('clicked()'), self.on_btnCC_clicked)
        self.connect(self.btnCCBack, QtCore.SIGNAL('clicked()'), self.on_btnCCBack_clicked)
        self.connect(self.btnFilter, QtCore.SIGNAL('clicked()'), self.on_btnFilter_clicked)
        #self.connect(self.btnCCOptions, QtCore.SIGNAL('clicked()'), self.on_btnCCOptions_clicked)
        
        
    def on_btnInputOverlay_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            ref = answer[0].getRef()
            ref.setAlpha(0.4)
            self.inputOverlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(ref)
            self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.setInputData(answer[0]._data)
            self.parent.labelWidget.repaint()
            self.btnCC.setEnabled(True)
            self.btnCCBack.setEnabled(True)
        
    def on_btnCC_clicked(self):
        self.connComp = CC(self.ilastik)       
        self.connComp.start(None)
        #self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.connect(background = False)
    def on_btnCCBack_clicked(self):
        self.connComp = CC(self.ilastik)
        self.connComp.start(self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.connCompBackgroundClasses)
        self.btnFilter.setEnabled(True)
        #self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.connect(background = True)
        
    def on_btnFilter_clicked(self):
        descriptions =  self.parent.project.dataMgr.module["Classification"]["labelDescriptions"]
        desc_names = []
        for i, d in enumerate(descriptions):
            tempstr = str(i)+" "+d.name
            desc_names.append(tempstr)
        dlg = LabelSelectionForm(self.ilastik, desc_names)
        label, minsize, maxsize = dlg.exec_()
        print label, minsize, maxsize
        # call core function
        self.parent.project.dataMgr.Connected_Components.filterSynapses(self.inputOverlay, label, minsize, maxsize)
        self.ilastik.labelWidget.repaint()
