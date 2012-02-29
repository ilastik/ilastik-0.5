# -*- coding: utf-8 -*-
import numpy, os
import h5py
import time
import copy
import random

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QFileDialog

from ilastik.gui.iconMgr import ilastikIcons
from seedWidget import SeedListWidget
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.volumeeditor import DummyLabelWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

from segmentorSelectionDlg import SegmentorSelectionDlg

from ilastik.modules.interactive_segmentation.core import startupOutputPath

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
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self.outputPath = os.path.expanduser("~/test-segmentation/")
        self.mapping = dict()
        self.doneBinaryOverlay  = None
        self.doneObjectsOverlay = None
        
        self.weightsSetUp   = False
        self.seedsAvailable = False
        self.firstInit = True
        
        self._initContent()
        self._initConnects()
    
    def on_doneOverlaysAvailable(self):
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        bluetable    = [QtGui.qRgb(0, 0, 255) for i in range(256)]
        bluetable[0] = long(0) #transparency
        
        randomColorTable    = [QtGui.qRgb(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for i in range(256)] 
        randomColorTable[0] = long(0) #transparency
        
        self.doneBinaryOverlay = OverlayItem(s.done, color = 0, colorTable=bluetable, alpha = 0.5, autoAdd = True, autoVisible = True, min = 0, max = 255)
        self.ilastik._activeImage.overlayMgr["Segmentation/Done"] = self.doneBinaryOverlay
        self.doneObjectsOverlay = OverlayItem(s.done, color=0, colorTable=randomColorTable, alpha=0.7, autoAdd=False, autoVisible=False, min = 0, max = 255)
        self.ilastik._activeImage.overlayMgr["Segmentation/Objects"] = self.doneObjectsOverlay
        
        self.overlayWidget.addOverlayRef(self.doneBinaryOverlay.getRef())
        
    def on_activation(self):
        if self.ilastik.project is None: return

        self.interactionLog = []
        
        self.overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(self.overlayWidget)
        
        
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        #add 'Seeds' overlay
        self.seedOverlay = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]
        
        self.seedWidget = SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  
                                         s.seedLabelsVolume,  
                                         self.ilastik.labelWidget,  
                                         self.seedOverlay)
        
        self.ilastik.labelWidget.setLabelWidget(self.seedWidget)
        if self.firstInit:
            self.seedWidget.addLabel("Background", 1, QtGui.QColor(255,0,0))
            self.seedWidget.createLabel() #make at least one object label so that we can start segmenting right away
            self.seedOverlay.displayable3D = True
            self.seedOverlay.backgroundClasses = set([0])
            self.seedOverlay.smooth3D = False
        
        raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
        self.overlayWidget.addOverlayRef(raw.getRef())
        self.overlayWidget.addOverlayRef(self.seedOverlay.getRef())
        
        self.ilastik.labelWidget.interactionLog = self.interactionLog
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        #Finally, initialize the core module        
        s = self.ilastik._activeImage.Interactive_Segmentation
        self.connect(s, QtCore.SIGNAL('overlaysChanged()'), self.on_overlaysChanged)
        self.connect(s, QtCore.SIGNAL('doneOverlaysAvailable()'), self.on_doneOverlaysAvailable)
        self.connect(s, QtCore.SIGNAL('weightsSetup()'), self.on_setupWeights)
        self.connect(s, QtCore.SIGNAL('newSegmentation()'), self.on_newSegmentation)
        self.connect(s, QtCore.SIGNAL('numColorsNeeded(int)'), self.on_numColorsNeeded)
        self.connect(s, QtCore.SIGNAL('seedsAvailable(bool)'), self.on_seedsAvailable)
        self.btnSegment.clicked.connect(s.segment)
        self.shortcutSegment = QtGui.QShortcut(QtGui.QKeySequence("s"), self, s.segment, s.segment)

        self.segmentorInit()
   
    def segmentorInit(self):

        self.btnChooseWeights.setEnabled(True)
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(1)

        self.progressBar.setFormat(' Initializing...')
        statusBar.addWidget(self.progressBar)
        statusBar.show()
        QtGui.qApp.processEvents(QtCore.QEventLoop.WaitForMoreEvents)

        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()

        self.firstInit = False
        self.maybeEnableSegmentButton()

    def on_seedsAvailable(self, b):
        self.seedsAvailable = b
        self.maybeEnableSegmentButton()
        
    def maybeEnableSegmentButton(self):
        self.btnSegment.setEnabled(self.seedsAvailable and self.weightsSetUp)

    def on_numColorsNeeded(self, numColors):
        """make sure that there are enough label colors.
           numColors refers to the _total_ number of colors,
           including the background. Note that the background label color
           is always present."""
        
        if self.seedWidget.count() >= numColors: return
        
        for _ in range(numColors-self.seedWidget.count()):
            self.seedWidget.createLabel()
    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        self.interactionLog = self.ilastik.labelWidget.interactionLog
        self.ilastik.labelWidget.interactionLog = None
        if self.ilastik.labelWidget._history != self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history:
            self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Interactive_Segmentation.seedLabelsVolume._history

        
    def _initContent(self):
        self.seedWidget = None
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
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
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.btnSegment.setEnabled(False)
        self.btnSegmentorsOptions.setEnabled(False)
        self.btnChooseWeights.setEnabled(False)
        self.setLayout(tl)
        
    def _initConnects(self):
        self.btnChooseWeights.clicked.connect(self.on_btnChooseWeights_clicked)
        self.btnSegmentorsOptions.clicked.connect(self.on_btnSegmentorsOptions_clicked)
    
    def on_btnChooseDir_clicked(self):
        startupOutputPath = str(QFileDialog.getExistingDirectory(None, "Select empty directory to store segmentations in"))
        if startupOutputPath is not None:
            s = self.ilastik._activeImage.Interactive_Segmentation
            s.outputPath = startupOutputPath
            self.segmentorInit()
            self.btnChooseDir.setEnabled(False)
     
    def on_btnRebuildDone_toggled(self, toggled):
        s = self.ilastik._activeImage.Interactive_Segmentation
        s.setRebuildDonePolicy(toggled)
    
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
        
        
        
        
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.maybeEnableSegmentButton()
        
    def on_setupWeights(self, weights = None):
        self.ilastik.labelWidget.interactionLog = []
        self.btnSegmentorsOptions.setEnabled(True)
        self.weightsSetUp = True
        self.maybeEnableSegmentButton()
        
    def clearSeeds(self):
        self._seedL = None
        self._seedIndices = None


    def mouseReleaseEvent(self, event):
        """
        mouse button release event
        """
        button = event.button()
        # select an item on which we clicked

    def on_btnSave_clicked(self):
        s = self.ilastik._activeImage.Interactive_Segmentation
        s.saveCurrentSegment()

    def on_btnSaveAs_clicked(self):
        (segmentKey, accepted) = QtGui.QInputDialog.getText(self, "Finish object", "Enter object name:")
        segmentKey = str(segmentKey) #convert to native python string
        if not accepted: return #dialog was canceled
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        #make sure the name is unique
        if s.hasSegmentsKey(segmentKey):
            msg = QtGui.QMessageBox.critical(self, "Finish object", \
            "An object with name '%s' already exists. Please choose a different name" % (segmentKey))
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
    
    def on_overlaysChanged(self):
        if type(self.parent.labelWidget.labelWidget) is DummyLabelWidget: return
        
        s = self.ilastik._activeImage.Interactive_Segmentation
        
        if s.segmentation is None:
            #the segmentation has been cleared, remove overlay
            self.activeImage.overlayMgr.remove("Segmentation/Segmentation")
            self.segmentationOverlay = None
        elif self.activeImage.overlayMgr["Segmentation/Segmentation"] is None:
            #ensure that we have a 'Segmentation' overlay which will display the result of the segmentation algorithm
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255
            
            self.segmentationOverlay = OverlayItem(self.localMgr.segmentation, color = 0, alpha = 1.0, colorTable = origColorTable, autoAdd = True, autoVisible = True, linkColorTable = True)
            #this overlay can be shown in 3D
            #the label 0 never occurs, label 1 is assigned to the background  class
            self.segmentationOverlay.displayable3D = True
            self.segmentationOverlay.backgroundClasses = set([1])
            self.activeImage.overlayMgr["Segmentation/Segmentation"] = self.segmentationOverlay

        if s.segmentation is not None:
            #create Overlay for segmentation:
            res = self.localMgr.segmentation
            self.segmentationOverlay._data = DataAccessor(res)
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255            
            self.segmentationOverlay.colorTable = origColorTable
            
        if self.localMgr.potentials is not None:
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            ov = OverlayItem(self.localMgr.potentials,color = origColorTable[1], alpha = 1.0, autoAdd = True, autoVisible = True, min = 0.0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Potentials"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Potentials")
            
        if hasattr(self.localMgr, 'borders') and self.localMgr.borders is not None:
            ov = OverlayItem(self.localMgr.borders, color = QtGui.QColor(), alpha = 1.0, autoAdd = True, autoVisible = False, min = 0, max = 1.0)
            self.activeImage.overlayMgr["Segmentation/Supervoxels"] = ov
        else:
            self.activeImage.overlayMgr.remove("Segmentation/Supervoxels")
    
        self.parent.labelWidget.repaint()
    
    def on_newSegmentation(self):
        if hasattr(self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor, "bias"):
            bias = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.bias            
            s = "%f: segment(bias) %f" % (time.clock(),bias)
            self.ilastik.labelWidget.interactionLog.append(s)
        self.on_overlaysChanged()    
        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            self.parent.project.dataMgr.Interactive_Segmentation.segmentor = answer
            self.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].Interactive_Segmentation._segmentationWeights)
            ui = self.parent.project.dataMgr.Interactive_Segmentation.segmentor.getInlineSettingsWidget(self.inlineSettings.childWidget)
            self.inlineSettings.changeWidget(ui)

            
