import numpy

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.modules.connected_components.core.connectedComponentsMgr import BackgroundOverlayItem
from ilastik.modules.connected_components.core.synapseDetectionFilter import SynapseFilterAndSegmentor 
from ilastik.core.volume import DataAccessor
#import ilastik.gui.volumeeditor as ve
from backgroundWidget import BackgroundWidget
from guiThread import CC
from labelSelectionForm import LabelSelectionForm
from ilastik.core import overlayMgr


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
        
        self.btnInputOverlay = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Select Overlay')
        self.btnCC = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'CC')
        self.btnCCBack = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System), 'CC with background')
        self.btnFilter = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System), 'Filter synapses')
        self.btnCCOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System), 'Options')
        
        self.btnInputOverlay.setToolTip('Select an overlay for connected components search')
        self.btnCC.setToolTip('Run connected components on the selected overlay')
        self.btnCCBack.setToolTip('Run connected components with background')
        self.btnFilter.setToolTip('Perform magic synapse filtering and dilation')
        self.btnCCOptions.setToolTip('Set options')
        
        self.btnInputOverlay.setEnabled(True)
        self.btnCC.setEnabled(False)
        self.btnCCBack.setEnabled(False)
        self.btnFilter.setEnabled(False)
        self.btnCCOptions.setEnabled(True)
        
        tl.addWidget(self.btnInputOverlay)
        tl.addWidget(self.btnCC)
        tl.addWidget(self.btnCCBack)
        tl.addStretch()
        tl.addWidget(self.btnFilter)
        tl.addWidget(self.btnCCOptions)
        
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
        #This is a special function to filter synapses. First, it finds the sizes of labeled objects
        #and throws away everything <0.1 of the smallest labeled object or >10 of the largest labeled
        #object. Then, it assumes that the input overlay
        #is a threhsold overlay and computes it for equal probabilities, and then dilates the
        #the current connected components to the size of their counterparts in the equal 
        #probability connected components.
        
        #FIXME: This function is very specific and is only put here until ilastik 0.6 allows 
        #to make it into a special workflow. Remove as soon as possible!
        
        descriptions =  self.parent.project.dataMgr.module["Classification"]["labelDescriptions"]
        desc_names = []
        for i, d in enumerate(descriptions):
            tempstr = str(i)+" "+d.name
            desc_names.append(tempstr)
        dlg = LabelSelectionForm(self.ilastik, desc_names)
        label = dlg.exec_()
        print label
        parts = label.split(" ")
        labelnum = int(parts[0])
        labelname = parts[1]
        thres = self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].Connected_Components.inputData
        cc = self.parent.project.dataMgr[self.parent.project.dataMgr._activeImageNumber].overlayMgr["Connected Components/CC Results"]
        if thres is None:
            print "no threshold overlay"
            return
        if cc is None:
            print "No cc overlay"
            return
        sfad = SynapseFilterAndSegmentor(self.parent, labelnum, cc, self.inputOverlay)
        objs_user, goodsizes = sfad.computeSizes()
        objs_ref = sfad.computeReferenceObjects()
        goodsizes = [s for s in goodsizes if s>100]
        
        mingoodsize = min(goodsizes)
        maxgoodsize = max(goodsizes)
        objs_final = sfad.filterObjects(objs_user, objs_ref, mingoodsize, maxgoodsize)
        #create a new, filtered overlay:
        result = numpy.zeros(cc.shape, dtype = 'int32')
        objcounter = 1
        for iobj in objs_final:
            for i in range(len(iobj[0])):
                result[0, iobj[0][i], iobj[1][i], iobj[2][i], 0] = int(objcounter)
            objcounter = objcounter +1
        
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Filtered"] is None:
            #colortab = [QtGui.qRgb(i, i, i) for i in range(256)]
            colortab = CC.makeColorTab()
            ov = overlayMgr.OverlayItem(result, color = QtGui.QColor(255, 0, 0), alpha = 1.0, colorTable = colortab, autoAdd = True, autoVisible = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Filtered"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Connected Components/CC Filtered"]._data = DataAccessor(result)
        self.ilastik.labelWidget.repaint()
