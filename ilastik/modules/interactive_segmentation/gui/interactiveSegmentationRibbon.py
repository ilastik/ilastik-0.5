# -*- coding: utf-8 -*-
import numpy, os
import h5py
import time
import copy
import random

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QFileDialog, QLabel

from ilastik.gui.iconMgr import ilastikIcons
from seedWidget import SeedListWidget
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.volumeeditor import DummyLabelWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

from segmentorSelectionDlg import SegmentorSelectionDlg


#*******************************************************************************
# I n l i n e S e t t i n g s W i d g e t                                      *
#*******************************************************************************

class InlineSettingsWidget(QtGui.QWidget):
    def __init__(self, parent=None):
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
            self.ui = None
        if ui is not None:
            self.ui = ui
            self.childWidget.addWidget(self.ui)
            self.ui.setParent(self)
            self.ui.show()

#*******************************************************************************
# I n t e r a c t i v e S e g m e n t a t i o n T a b                          *
#*******************************************************************************

class InteractiveSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Seeded Watershed'
    position = 3
    moduleName = "Interactive_Segmentation"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self.outputPath = os.path.expanduser("~/test-segmentation/")
        self.mapping = dict()
        self.doneBinaryOverlay  = None
        self.doneObjectsOverlay = None
        self.segmentationItemMgr = None
        self.firstInit = True
        
        self._initContent()
        self._initConnects()
        
    def on_imageChanged(self):
        #Finally, initialize the core module   
        if self.segmentationItemMgr is not None:
            self.btnSegment.clicked.disconnect(self.segmentationItemMgr.segment)
        s = self.ilastik._activeImage.Interactive_Segmentation     
        self.segmentationItemMgr = s
        self.connect(s, QtCore.SIGNAL('weightsSetup()'), self.on_setupWeights)
        self.connect(s, QtCore.SIGNAL('newSegmentation()'), self.on_newSegmentation)
        self.connect(s, QtCore.SIGNAL('seedsAvailable(bool)'), self.on_seedsAvailable)
        self.btnSegment.clicked.connect(s.segment)
        self.shortcutSegment = QtGui.QShortcut(QtGui.QKeySequence("s"), self, s.segment, s.segment)
        self.seedOverlay = self.ilastik._activeImage.overlayMgr["Interactive Segmentation/Seeds"]
        self.maybeEnableSegmentButton()
    
    def on_doneOverlaysAvailable(self):
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        bluetable    = [QtGui.qRgb(0, 0, 255) for i in range(256)]
        bluetable[0] = long(0) #transparency
        
        randomColorTable    = [QtGui.qRgb(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for i in range(256)] 
        randomColorTable[0] = long(0) #transparency
        
        self.doneBinaryOverlay = OverlayItem(s.done, color = 0, colorTable=bluetable, alpha = 0.5, autoAdd = True, autoVisible = True, min = 0, max = 255)
        self.ilastik._activeImage.overlayMgr["Interactive Segmentation/Done"] = self.doneBinaryOverlay
        self.doneObjectsOverlay = OverlayItem(s.done, color=0, colorTable=randomColorTable, alpha=0.7, autoAdd=False, autoVisible=False, min = 0, max = 255)
        self.ilastik._activeImage.overlayMgr["Interactive Segmentation/Objects"] = self.doneObjectsOverlay
        
        self.overlayWidget.addOverlayRef(self.doneBinaryOverlay.getRef())
        
    def on_activation(self):
        if self.ilastik.project is None: return
        self.on_imageChanged()

        self.interactionLog = []
        
        self.overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(self.overlayWidget)
        
        s = self.ilastik._activeImage.Interactive_Segmentation

        
        self.seedWidget = SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  
                                         s.seedLabelsVolume,  
                                         self.ilastik.labelWidget,  
                                         self.seedOverlay)
        
        self.ilastik.labelWidget.setLabelWidget(self.seedWidget)
        if self.segmentationItemMgr.firstInit:
            if self.seedWidget.count() == 0:
                self.seedWidget.addLabel("Background", 1, QtGui.QColor(255,0,0))
                self.seedWidget.createLabel() #make at least one object label so that we can start segmenting right away
                self.seedOverlay.displayable3D = True
                self.seedOverlay.backgroundClasses = set([0])
            self.connect(s, QtCore.SIGNAL('weightsSetup()'), self.on_setupWeights)
            self.connect(s, QtCore.SIGNAL('newSegmentation()'), self.on_newSegmentation)
            self.connect(s, QtCore.SIGNAL('seedsAvailable(bool)'), self.on_seedsAvailable)
            self.shortcutSegment = QtGui.QShortcut(QtGui.QKeySequence("s"), self, s.segment, s.segment)
            self.maybeEnableSegmentButton()
            
            self.segmentationItemMgr.firstInit = False
        
        raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
        self.overlayWidget.addOverlayRef(self.seedOverlay.getRef())
        self.overlayWidget.addOverlayRef(raw.getRef())
        
        self.ilastik.labelWidget.interactionLog = self.interactionLog
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget
        
    def on_otherProject(self):
        self.btnChooseWeights.setEnabled(True)

        

    def on_seedsAvailable(self, b):
        self.segmentationItemMgr.seedsAvailable = b
        self.maybeEnableSegmentButton()
        
    def maybeEnableSegmentButton(self):
      if self.segmentationItemMgr.seedsAvailable and self.segmentationItemMgr.weightsSetUp:
          self.btnSegment.setEnabled(True)
          if self.inlineSettings.ui is None:
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings, view="default")
            self.inlineSettings.changeWidget(ui)
      else:
          self.btnSegment.setEnabled(False)
        
    
    def on_deActivation(self):
        if self.ilastik.project is None: return
        self.interactionLog = self.ilastik.labelWidget.interactionLog
        self.ilastik.labelWidget.interactionLog = None
        if self.ilastik.labelWidget._history != self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history:
            self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history

    def _initContent(self):
        self.seedWidget = None
        tl = QtGui.QHBoxLayout()
        #tl.setMargin(0)
        
        self.btnChooseWeights     = TabButton('Choose Input Weights', ilastikIcons.Select)
        self.btnSegment           = TabButton('Segment', ilastikIcons.Play)        
        self.btnSegmentorsOptions = TabButton('Change Segmentor', ilastikIcons.System)
        
        self.only2D = False
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)        

        tl.addStretch()
        self.inlineSettings = InlineSettingsWidget()
        tl.addWidget(self.inlineSettings)
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.btnSegment.setEnabled(False)
        self.btnSegmentorsOptions.setEnabled(False)
        self.btnChooseWeights.setEnabled(False)
        self.setLayout(tl)
        
    def _initConnects(self):
        self.btnChooseWeights.clicked.connect(self.on_btnChooseWeights_clicked)
        self.btnSegmentorsOptions.clicked.connect(self.on_btnSegmentorsOptions_clicked)  
    
    def on_btnChooseWeights_clicked(self):
        #First question: Which overlay?
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        if len(answer) == 0: return #dialog was dismissed
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        overlay = answer[0]
        self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
        volume = overlay._data[0,:,:,:,0]
        
        #Second question: Which border indicator?            
        borderIndicator = QtGui.QInputDialog.getItem(self.ilastik, \
                          "Select Border Indicator",  "Indicator",  \
                          ["Brightness",  "Darkness", "Gradient Magnitude"], \
                          editable = False)
        if not borderIndicator[1]: return #Dialog was dismissed
        
        borderIndicator = str(borderIndicator[0])
        
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(1)

        self.progressBar.setFormat('Calculating weight...')
        statusBar.addWidget(self.progressBar)
        statusBar.show()
        QtGui.qApp.processEvents(QtCore.QEventLoop.WaitForMoreEvents)
        
        # default segmentor
        self.parent.project.dataMgr.Interactive_Segmentation.segmentor = \
            self.ilastik.project.dataMgr.Interactive_Segmentation.segmentorClasses[0]()
            
        #calculate the weights
        #this will call on_setupWeights via a signal/slot connection
        s.calculateWeights(volume, borderIndicator)
        
        
        self.segmentationItemMgr.weightsSetUp = True
        
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.maybeEnableSegmentButton()
        
    def on_setupWeights(self, weights = None):
        self.ilastik.labelWidget.interactionLog = []
        self.btnSegmentorsOptions.setEnabled(True)
        self.segmentationItemMgr.weightsSetUp = True
        self.maybeEnableSegmentButton()
        
    
    def on_newSegmentation(self):
        if type(self.parent.labelWidget.labelWidget) is DummyLabelWidget: return
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        if s.segmentation is None:
            raise RuntimeError('No segmentation!!')
           
        origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
        origColorTable[1] = 255
        
        self.segmentationItemMgr.segmentationOverlay = OverlayItem(s.segmentation, color = 0, alpha = 0.50, colorTable = origColorTable, autoAdd = True, autoVisible = True, linkColorTable = True)
        #this overlay can be shown in 3D
        #the label 0 never occurs, label 1 is assigned to the background  class
        self.segmentationItemMgr.segmentationOverlay.displayable3D = True
        self.segmentationItemMgr.segmentationOverlay.backgroundClasses = set([1])
        self.ilastik._activeImage.overlayMgr["Interactive Segmentation/Segmentation"] =  self.segmentationItemMgr.segmentationOverlay

        #create Overlay for segmentation:
        res = self.localMgr.segmentation
        self.segmentationItemMgr.segmentationOverlay._data = DataAccessor(res)
        origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
        origColorTable[1] = 255            
        self.segmentationItemMgr.segmentationOverlay.colorTable = origColorTable            
            
        if hasattr(self.localMgr, 'borders') and self.localMgr.borders is not None:
            ov = OverlayItem(self.localMgr.borders, color = QtGui.QColor(), alpha = 0.50, autoAdd = True, autoVisible = False, min = 0, max = 1.0)
            self.activeImage.overlayMgr["Interactive Segmentation/Supervoxels"] = ov
        else:
            self.activeImage.overlayMgr.remove("Interactive Segmentation/Supervoxels")
    
        self.parent.labelWidget.repaint()   
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        changed, answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.Interactive_Segmentation.segmentor = answer
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings, view="default")
            self.inlineSettings.changeWidget(ui)
            if changed:
              answer.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].Interactive_Segmentation._segmentationWeights)

            
