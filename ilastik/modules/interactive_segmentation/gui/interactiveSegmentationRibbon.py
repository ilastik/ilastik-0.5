# -*- coding: utf-8 -*-
import numpy, vigra, os
import traceback, h5py
import time
import copy
import random

from ilastik.core import dataImpex

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons
from ilastik.modules.connected_components.core.connectedComponentsMgr import ConnectedComponentsModuleMgr, ConnectedComponents
from ilastik.modules.connected_components.gui.guiThread import CC

from seedWidget import SeedListWidget
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

from segmentorSelectionDlg import SegmentorSelectionDlg

#*******************************************************************************
# I n l i n e S e t t i n g s W i d g e t                                      *
#*******************************************************************************

class InlineSettingsWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        # The edit_traits call will generate the widget to embed.
        self.childWidget = QtGui.QHBoxLayout(self)
        self.childWidget.setMargin(0)
        self.childWidget.setSpacing(0)
        
        self.ui = None
        
    def changeWidget(self, ui):
        if self.ui is not None:
            self.ui.close()
            self.childWidget.removeWidget(self.ui)
            del self.ui
        self.ui = None
        if ui is not None:
            self.ui = ui
            self.childWidget.addWidget(self.ui)
            self.ui.setParent(self)

#*******************************************************************************
# I n t e r a c t i v e S e g m e n t a t i o n T a b                          *
#*******************************************************************************

class InteractiveSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Interactive Segmentation'
    position = 3
    moduleName = "Interactive_Segmentation"
    
    outputPath = os.path.expanduser("~/test-segmentation/")
    mapping = dict()
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        self._initContent()
        self._initConnects()
        self.interactionLog = []
        self.defaultSegmentor = False
        
    def on_activation(self):
        if self.ilastik.project is None: return
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        self.connect(s, QtCore.SIGNAL('overlaysChanged()'), self.ilastik.labelWidget.repaint)
        s.init()
        
        #initially add 'Raw Data' overlay
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if "Raw Data" in self.ilastik._activeImage.overlayMgr.keys():
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None: ovs.append(raw.getRef())
        
        self.ilastik.labelWidget.interactionLog = self.interactionLog        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
    
        #add 'Seeds' overlay
        overlayWidget.addOverlayRef(s.seedOverlay.getRef())
        #add 'Done' overlay if it exists
        if s.doneBinaryOverlay is not None:
            overlayWidget.addOverlayRef(s.doneBinaryOverlay.getRef())
        
        self.ilastik.labelWidget.setLabelWidget(SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  s.seedLabelsVolume,  self.ilastik.labelWidget,  s.seedOverlay))
        
        if self.parent.project.dataMgr.Interactive_Segmentation.segmentor is None:
            segmentors = self.parent.project.dataMgr.Interactive_Segmentation.segmentorClasses
            for i, seg in enumerate(segmentors):
                if seg.name == "Supervoxel Segmentation":
                    self.parent.project.dataMgr.Interactive_Segmentation.segmentor = seg()
                    ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget, view='default')
                    self.inlineSettings.changeWidget(ui)
                    self.defaultSegmentor = True
                    break            
            
        """
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
        ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]
        
        if ov is not None and ov_cc is None:
            colorTableCC = OverlayItem.createDefault16ColorColorTable()
            ov_cc = OverlayItem(ov._data, color=0, alpha=0.7, colorTable=colorTableCC, autoAdd=False, autoVisible=False)                    
            self.ilastik._activeImage.overlayMgr["Segmentation/Objects"] = ov_cc
            #ov_cc = self.ilastik._activeImage.overlayMgr["Segmentation/Objects"]
        """

    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.interactionLog = self.ilastik.labelWidget.interactionLog
        self.ilastik.labelWidget.interactionLog = None
        if self.ilastik.labelWidget._history != self.ilastik._activeImage.Interactive_Segmentation.seeds._history:
            self.ilastik._activeImage.Interactive_Segmentation.seeds._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Interactive_Segmentation.seeds._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Interactive_Segmentation.seeds._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
        self.btnChooseDimensions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Using 3D')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        self.btnFinishSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Finish Object')
        self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Change Segmentor')
        
        self.inlineSettings = InlineSettingsWidget(self)
        
        self.only2D = False
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnChooseDimensions.setToolTip('Switch between slice based 2D segmentation and full 3D segmentation\n This is mainly useful for 3D Date with very weak border indicators, where seeds placed in one slice can bleed out badly to other regions')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        
        tl.addWidget(self.btnChooseWeights)
        
        #tl.addWidget(self.btnChooseDimensions)
        tl.addWidget(self.btnSegment)        
        tl.addWidget(self.inlineSettings)
        tl.addWidget(self.btnFinishSegment)
        tl.addStretch()
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.btnSegment.setEnabled(False)
        self.btnFinishSegment.setEnabled(False)
        self.btnChooseDimensions.setEnabled(False)
        self.btnSegmentorsOptions.setEnabled(False)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        self.connect(self.btnFinishSegment, QtCore.SIGNAL('clicked()'), self.on_btnFinishSegment_clicked)
        self.connect(self.btnChooseDimensions, QtCore.SIGNAL('clicked()'), self.on_btnDimensions)
        self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        self.shortcutSegment = QtGui.QShortcut(QtGui.QKeySequence("s"), self, self.on_btnSegment_clicked, self.on_btnSegment_clicked)
        #shortcutManager.register(self.shortcutNextLabel, "Labeling", "Go to next label (cyclic, forward)")
        
    
    def on_btnDimensions(self):
        self.only2D = not self.only2D
        if self.only2D:
            ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]
            if ov is not None:
                zerod = numpy.zeros(ov._data.shape, numpy.uint8)
                ov._data = DataAccessor(zerod)
            self.btnChooseDimensions.setText('Using 2D')
                        
        else:
            self.btnChooseDimensions.setText('Using 3D')
        self.setupWeights()
        
    
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(self.ilastik, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness", "Gradient Magnitude"],  editable = False)
            if borderIndicator[1]:
                borderIndicator = str(borderIndicator[0])
                
                sigma = 1.0
                normalizePotential = True
                #TODO: this , until now, only supports gray scale and 2D!
                if borderIndicator == "Brightness":
                    weights = volume[:,:,:].view(vigra.ScalarVolume)
                elif borderIndicator == "Darkness":
                    weights = (255 - volume[:,:,:]).view(vigra.ScalarVolume)
                elif borderIndicator == "Gradient Magnitude":
                    weights = numpy.ndarray(volume.shape, numpy.float32)
                    if weights.shape[0] == 1:
                        weights[0,:,:] = vigra.filters.gaussianGradientMagnitude((volume[0,:,:]).astype(numpy.float32), 1.0 )
                    else:
                        weights = vigra.filters.gaussianGradientMagnitude((volume[:,:,:]).astype(numpy.float32), 1.0 )
        
                if normalizePotential == True:
                    min = numpy.min(volume)
                    max = numpy.max(volume)
                    print "Weights min/max :", min, max
                    weights = (weights - min)*(255.0 / (max - min))
        
                self.setupWeights(weights)
                self.btnSegmentorsOptions.setEnabled(True)
                self.btnSegment.setEnabled(True)
                self.btnFinishSegment.setEnabled(True)
            

    def setupWeights(self, weights = None):
        self.ilastik.labelWidget.interactionLog = []
        if weights is None:
            weights = self.localMgr._segmentationWeights
        else:
            self.localMgr._segmentationWeights = weights
        if self.globalMgr.segmentor is not None:
            self.globalMgr.segmentor.setupWeights(weights)



    def clearSeeds(self):
        self._seedL = None
        self._seedIndices = None


    def mouseReleaseEvent(self, event):
        """
        mouse button release event
        """
        button = event.button()
        # select an item on which we clicked

    def on_btnFinishSegment_clicked(self):
        (segmentKey, accepted) = QtGui.QInputDialog.getText(self, "Finish object", "Enter object name:")
        segmentKey = str(segmentKey) #convert to native python string
        if not accepted: return #dialog was canceled
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        #make sure the name is unique
        if s.hasSegmentKey(segmentKey):
            msg = QtGui.QMessageBox.critical(self, "Finish object", \
            "an object with name '%s' already exists.\\nPlease choose a different name" % (segmentKey))
            return
        
        s.saveCurrentSegmentsAs(segmentKey)
        
        path = s.outputPath+'/'+str(segmentKey)
        f = open(path + "/interactions.log", "w")
        for l in self.ilastik.labelWidget.interactionLog:
            f.write(l + "\n")
        f.close()
        self.ilastik.labelWidget.interactionLog = []
        
        f = h5py.File(path + "/history.h5", 'w')                        
        self.ilastik.labelWidget._history.serialize(f)
        f.close()

        self.ilastik.labelWidget.repaint()

        
    def on_btnSegment_clicked(self):
        if hasattr(self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor, "bias"):
            bias = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.bias            
            s = "%f: segment(bias) %f" % (time.clock(),bias)
            self.ilastik.labelWidget.interactionLog.append(s)
            
        self.localMgr.segment()

        #ensure that we have a 'Segmentation' overlay which will display the result of the segmentation algorithm
        if self.activeImage.overlayMgr["Segmentation/Segmentation"] is None:
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255
            segmentationOverlay = OverlayItem(self.localMgr.segmentation, color = 0, alpha = 1.0, colorTable = origColorTable, autoAdd = True, autoVisible = True, linkColorTable = True)
            self.activeImage.overlayMgr["Segmentation/Segmentation"] = segmentationOverlay
            self.localMgr.segmentationOverlay = segmentationOverlay #FIXME

        #create Overlay for segmentation:
        res = self.localMgr.segmentation
        self.localMgr.segmentationOverlay._data = DataAccessor(res)
        origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
        origColorTable[1] = 255            
        self.localMgr.segmentationOverlay.colorTable = origColorTable
            
        if self.localMgr.potentials is not None:
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            ov = OverlayItem(self.localMgr.potentials,color = origColorTable[1], alpha = 1.0, autoAdd = True, autoVisible = True, min = 0.0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Potentials"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Potentials")
            
        if self.localMgr.borders is not None:
            #colorTab = []
            #for i in range(256):
            #    color = QtGui.QColor(random.randint(0,255),random.randint(0,255),random.randint(0,255)).rgba()
            #    colorTab.append(color)
                
            ov = OverlayItem(self.localMgr.borders, color = QtGui.QColor(), alpha = 1.0, autoAdd = True, autoVisible = False, min = 0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Supervoxels"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Supervoxels")
            
        self.parent.labelWidget.repaint()
            
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.Interactive_Segmentation.segmentor = answer
            self.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].Interactive_Segmentation._segmentationWeights)
            self.btnSegment.setEnabled(True)
            self.btnFinishSegment.setEnabled(True)
            
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget)

            self.inlineSettings.changeWidget(ui)
            self.defaultSegmentor = False
        elif self.defaultSegmentor is True:
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget)
            self.inlineSettings.changeWidget(ui)
            self.defaultSegmentor = False
            
