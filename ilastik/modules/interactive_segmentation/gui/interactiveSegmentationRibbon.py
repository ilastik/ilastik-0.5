# -*- coding: utf-8 -*-
import numpy, vigra


from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons


from seedWidget import SeedListWidget
from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

from segmentorSelectionDlg import SegmentorSelectionDlg

from ilastik.modules.interactive_segmentation.core.segmentationMgr import SegmentationThread

class InteractiveSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Interactive Segmentation'
    position = 2
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        ovs = self.ilastik._activeImage.Interactive_Segmentation.overlays
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik._activeImage.overlayMgr,  ovs)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        #create SeedsOverlay
        ov = OverlayItem(self.ilastik._activeImage.Interactive_Segmentation.seeds._data, color = 0, alpha = 1.0, colorTable = self.ilastik._activeImage.Interactive_Segmentation.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]

        overlayWidget.addOverlayRef(ov.getRef())
        
        self.ilastik.labelWidget.setLabelWidget(SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  self.ilastik._activeImage.Interactive_Segmentation.seeds,  self.ilastik.labelWidget,  ov))

        self.btnSegmentorsOptions.setEnabled(True)     

    
    def on_deActivation(self):
        if self.ilastik.project is None:
            return
        if self.ilastik.labelWidget._history != self.ilastik._activeImage.Interactive_Segmentation.seeds._history:
            self.ilastik._activeImage.Interactive_Segmentation.seeds._history = self.ilastik.labelWidget._history
        
        if self.ilastik._activeImage.Interactive_Segmentation.seeds._history is not None:
            self.ilastik.labelWidget._history = self.ilastik._activeImage.Interactive_Segmentation.seeds._history
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Weights')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Segmentors Options')
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        tl.addWidget(self.btnSegmentorsOptions)
        
        self.btnSegment.setEnabled(False)
        self.btnSegmentorsOptions.setEnabled(False)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(None, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness"],  editable = False)
            borderIndicator = str(borderIndicator[0])
            
            sigma = 1.0
            normalizePotential = True
            #TODO: this , until now, only supports gray scale and 2D!
            if borderIndicator == "Brightness":
                weights = volume[:,:,:].view(vigra.ScalarVolume)
            elif borderIndicator == "Darkness":
                weights = (255 - volume[:,:,:]).view(vigra.ScalarVolume)
    
            if normalizePotential == True:
                min = numpy.min(volume)
                max = numpy.max(volume)
                print "Weights min/max :", min, max
                weights = (weights - min)*(255.0 / (max - min))
    
            self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.setupWeights(weights)
            self.ilastik._activeImage.Interactive_Segmentation._segmentationWeights = weights
            self.btnSegment.setEnabled(True)

    def clearSeeds(self):
        self._seedL = None
        self._seedIndices = None

        
    def on_btnSegment_clicked(self):
        self.segmentationSegment = Segmentation(self.ilastik)

        
    def on_btnSegmentorsOptions_clicked(self):
        dialog = SegmentorSelectionDlg(self.parent)
        answer = dialog.exec_()
        if answer != None:
            segmentor = self.parent.project.dataMgr.Interactive_Segmentation.segmentor = answer
            segmentor.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].Interactive_Segmentation._segmentationWeights)
            
            
            
            
            
class Segmentation(object):

    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()

    def start(self):
        self.parent.ribbon.getTab('Interactive Segmentation').btnSegment.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)

        self.segmentation = SegmentationThread(self.parent.project.dataMgr, self.parent.project.dataMgr[self.ilastik._activeImageNumber], self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor)
        numberOfJobs = self.segmentation.numberOfJobs
        self.initClassificationProgress(numberOfJobs)
        self.segmentation.start()
        self.timer.start(200)

    def initClassificationProgress(self, numberOfJobs):
        statusBar = self.parent.statusBar()
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(numberOfJobs)
        self.progressBar.setFormat(' Segmentation... %p%')
        statusBar.addWidget(self.progressBar)
        statusBar.show()

    def updateProgress(self):
        val = self.segmentation.count
        self.progressBar.setValue(val)
        if not self.segmentation.isRunning():
            print "finalizing segmentation"
            self.timer.stop()
            self.segmentation.wait()
            self.finalize()
            self.terminateProgressBar()

    def finalize(self):
        activeItem = self.parent.project.dataMgr[self.parent._activeImageNumber]
        activeItem.Interactive_Segmentation.segmentation = self.segmentation.result

        #temp = activeItem._dataVol.segmentation[0, :, :, :, 0]
        
        #create Overlay for segmentation:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] is None:
            ov = OverlayItem(activeItem.Interactive_Segmentation.segmentation, color = 0, alpha = 1.0, colorTable = self.parent.labelWidget.labelWidget.colorTab, autoAdd = True, autoVisible = True, linkColorTable = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]._data = DataAccessor(activeItem.Interactive_Segmentation.segmentation)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"].colorTable = self.parent.labelWidget.labelWidget.colorTab
        self.ilastik.labelWidget.repaint()


        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Interactive Segmentation').btnSegment.setEnabled(True)            
