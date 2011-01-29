# -*- coding: utf-8 -*-
import numpy, vigra, os
import traceback, h5py
import time
import copy

from ilastik.core import dataImpex

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


class InteractiveSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Interactive Segmentation'
    position = 3
    moduleName = "Interactive_Segmentation"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        self._initContent()
        self._initConnects()
        self.interactionLog = []
        
    def on_activation(self):
        if self.ilastik.project is None:
            return
        self.ilastik.labelWidget.interactionLog = self.interactionLog
        
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        #create SeedsOverlay
        ov = OverlayItem(self.ilastik._activeImage.Interactive_Segmentation.seeds._data, color = 0, alpha = 1.0, colorTable = self.ilastik._activeImage.Interactive_Segmentation.seeds.getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
        self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"] = ov
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]

        overlayWidget.addOverlayRef(ov.getRef())
        
        self.ilastik.labelWidget.setLabelWidget(SeedListWidget(self.ilastik.project.dataMgr.Interactive_Segmentation.seedMgr,  self.ilastik._activeImage.Interactive_Segmentation.seeds,  self.ilastik.labelWidget,  ov))

        
        
        ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
        if ov is None:
            path = os.path.expanduser("~/test-segmentation/")
            try:
                os.makedirs(path)
            except:
                pass            
            try:
                activeItem = self.ilastik._activeImage
                file_name = path + "done.h5"
                dataImpex.DataImpex.importOverlay(activeItem, file_name)
                
                """
                theDataItem = dataImpex.DataImpex.importDataItem(file_name, None)
                if theDataItem is None:
                    print "No _data item loaded"
                else:
                    if theDataItem.shape[0:-1] == activeItem.shape[0:-1]:
                        data = theDataItem[:,:,:,:,:]
                        ov = OverlayItem(data, color = QtGui.QColor(0,0,255), alpha = 0.5, colorTable = None, autoAdd = True, autoVisible = True, min = 1.0, max = 2.0)
                        activeItem.overlayMgr["Segmentation/Done"] = ov
                    else:
                        print "Cannot add " + theDataItem.fileName + " due to dimensionality mismatch"
                """
            except:
                traceback.print_exc()

    
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
        self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Select Segmentor')
        
        self.inlineSettings = InlineSettingsWidget(self)
        
        self.only2D = False
        
        self.btnChooseWeights.setToolTip('Choose the edge weights for the segmentation task')
        self.btnSegment.setToolTip('Segment the image into foreground/background')
        self.btnChooseDimensions.setToolTip('Switch between slice based 2D segmentation and full 3D segmentation\n This is mainly useful for 3D Date with very weak border indicators, where seeds placed in one slice can bleed out badly to other regions')
        self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegmentorsOptions)
        tl.addWidget(self.btnChooseDimensions)
        tl.addWidget(self.btnSegment)
        tl.addWidget(self.btnFinishSegment)
        tl.addWidget(self.inlineSettings)
        tl.addStretch()
        
        
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
            

    def setupWeights(self, weights = None):
        self.ilastik.labelWidget.interactionLog = []
        if weights is None:
            weights = self.ilastik._activeImage.Interactive_Segmentation._segmentationWeights
        else:
            self.ilastik._activeImage.Interactive_Segmentation._segmentationWeights = weights
        if self.only2D:
            self.ilastik.project.dataMgr.Interactive_Segmentation.segmentors = []
            
            segClass = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.__class__
             
            for z in range(weights.shape[2]):
                seg = segClass()
                w = weights[:,:,z]
                w.shape = w.shape + (1,)
                
                seg.setupWeights(w.view(vigra.ScalarVolume))
                self.ilastik.project.dataMgr.Interactive_Segmentation.segmentors.append(seg)
        else:
            self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.setupWeights(weights)



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
        res = QtGui.QInputDialog.getText(self, "Finish object", "Enter object name:")
        print res
        if res[1] == True:
            path = os.path.expanduser("~/test-segmentation/"+str(res[0]))
            try:
                os.makedirs(path)
            except:
                pass
            ovs = self.ilastik._activeImage.overlayMgr["Segmentation/Segmentation"]
            if ovs is not None:
                dataImpex.DataImpex.exportOverlay(path + "/segmentation", "h5", ovs)
            ovseed = self.ilastik._activeImage.overlayMgr["Segmentation/Seeds"]
            if ovseed is not None:
                dataImpex.DataImpex.exportOverlay(path + "/seeds", "h5", ovseed)
            f = open(path + "/interactions.log", "w")
            for l in self.ilastik.labelWidget.interactionLog:
                f.write(l + "\n")
            f.close()
            self.ilastik.labelWidget.interactionLog = []
            
            if ovs is not None:
                ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
                if ov is None:
                    #create Old Overlays if not there
                    shape = self.ilastik._activeImage.shape
                    data = DataAccessor(numpy.zeros((shape), numpy.uint8))
                    ov = OverlayItem(data, color = QtGui.QColor(0,0,255), alpha = 0.5, autoAdd = True, autoVisible = True, min = 1.0, max = 2.0)
                    self.ilastik._activeImage.overlayMgr["Segmentation/Done"] = ov
                data = ov[0,:,:,:,:]
                seg = ovs[0,:,:,:,:]
                res = numpy.where(seg > 1, seg, data)
                ov[0,:,:,:,:] = res[:]
                #save the current done state
                ov = self.ilastik._activeImage.overlayMgr["Segmentation/Done"]
                dataImpex.DataImpex.exportOverlay(path + "/../done", "h5", ov)
            
            if ovseed is not None:
                ovseed[0,:,:,:,:] = 0
                
            f = h5py.File(path + "/history.h5", 'w')                        
            self.ilastik.labelWidget._history.serialize(f)
            f.close()
            
            
            self.ilastik._activeImage.Interactive_Segmentation.clearSeeds()
            self.ilastik._activeImage.Interactive_Segmentation._buildSeedsWhenNotThere()
            
            self.ilastik.labelWidget.repaint()

        
    def on_btnSegment_clicked(self):
        if hasattr(self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor, "bias"):
            bias = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.bias            
            s = "%f: segment(bias) %f" % (time.clock(),bias)
            self.ilastik.labelWidget.interactionLog.append(s)
            
        if self.only2D:
            self.segmentationSegment = Segmentation2D(self.ilastik)
        else:
            self.segmentationSegment = Segmentation(self.ilastik)

        
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
            
            
            
            
            
            
            
class Segmentation(object):

    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()

    def start(self):
        self.parent.setTabBusy(True)
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
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255
            ov = OverlayItem(activeItem.Interactive_Segmentation.segmentation, color = 0, alpha = 1.0, colorTable = origColorTable, autoAdd = True, autoVisible = True, linkColorTable = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] = ov
        else:
            res = activeItem.Interactive_Segmentation.segmentation
            print "tralalal", res.shape, res.dtype
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]._data = DataAccessor(res)
            origColorTable = copy.deepcopy(self.parent.labelWidget.labelWidget.colorTab)
            origColorTable[1] = 255            
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"].colorTable = origColorTable
        self.ilastik.labelWidget.repaint()
        self.parent.setTabBusy(False)


        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Interactive Segmentation').btnSegment.setEnabled(True)
        
        
class Segmentation2D(object):

    def __init__(self, parent):
        self.parent = parent
        self.ilastik = parent
        self.start()

    def start(self):
        self.parent.setTabBusy(True)
        #self.parent.ribbon.getTab('Interactive Segmentation').btnSegment.setEnabled(False)
        
        self.timer = QtCore.QTimer()
        self.parent.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateProgress)
        zValue = self.ilastik.labelWidget.sliceSelectors[2].value()
        
        dataItem = self.parent.project.dataMgr[self.ilastik._activeImageNumber]
        lvol = dataItem.Interactive_Segmentation.seeds._data[0,:,:,zValue]
        lvol.shape = lvol.shape + (1,)
        
        segmentor = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentors[zValue]
        if hasattr(segmentor, "bias"):
            segmentor.bias = self.ilastik.project.dataMgr.Interactive_Segmentation.segmentor.bias
        lInd = numpy.nonzero(lvol.ravel())
        lValues = lvol.ravel()[lInd]
        lInd = lInd[0]
        segmentation = segmentor.segment(lvol, lValues, lInd)
        
        ov = self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"]
        if ov is None:
            zerod = numpy.zeros(dataItem.shape[0:-1], numpy.uint8)
            ov = OverlayItem(zerod, color = 0, alpha = 1.0, colorTable = self.parent.labelWidget.labelWidget.colorTab, autoAdd = True, autoVisible = True, linkColorTable = True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Segmentation/Segmentation"] = ov
        
        ov[0,:,:,zValue,0] = segmentation[:,:,0,0]
                    
        self.ilastik.labelWidget.repaint()
        self.parent.setTabBusy(False)


        

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


        
    def terminateProgressBar(self):
        self.parent.statusBar().removeWidget(self.progressBar)
        self.parent.statusBar().hide()
        self.parent.ribbon.getTab('Interactive Segmentation').btnSegment.setEnabled(True)                        
