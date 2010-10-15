# -*- coding: utf-8 -*-
import numpy, vigra
import random

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlaySelectionDlg import OverlaySelectionDialog
from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor
import ilastik.gui.volumeeditor as ve
                    
class AutoSegmentationTab(IlastikTabBase, QtGui.QWidget):
    name = 'Auto Segmentation'
    position = 2
    moduleName = "Automatic_Segmentation"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        self.weights = None
        
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
    
    def on_deActivation(self):
        pass
    
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        
        self.btnChooseWeights = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Select),'Choose Border Indicator')
        self.btnSegment = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Segment')
        #self.btnSegmentorsOptions = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.System),'Segmentors Options')
        
        self.btnChooseWeights.setToolTip('Choose the border indicator for the segmentation task')
        self.btnSegment.setToolTip('Segment the image')
        #self.btnSegmentorsOptions.setToolTip('Select a segmentation plugin and change settings')
        
        tl.addWidget(self.btnChooseWeights)
        tl.addWidget(self.btnSegment)
        tl.addStretch()
        #tl.addWidget(self.btnSegmentorsOptions)
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnChooseWeights, QtCore.SIGNAL('clicked()'), self.on_btnChooseWeights_clicked)
        self.connect(self.btnSegment, QtCore.SIGNAL('clicked()'), self.on_btnSegment_clicked)
        #self.connect(self.btnSegmentorsOptions, QtCore.SIGNAL('clicked()'), self.on_btnSegmentorsOptions_clicked)
        
        
    def on_btnChooseWeights_clicked(self):
        dlg = OverlaySelectionDialog(self.ilastik,  singleSelection = True)
        answer = dlg.exec_()
        
        if len(answer) > 0:
            overlay = answer[0]
            self.parent.labelWidget.overlayWidget.addOverlayRef(overlay.getRef())
            
            volume = overlay._data[0,:,:,:,0]
            
            print numpy.max(volume),  numpy.min(volume)
    
            #real_weights = numpy.zeros(volume.shape + (3,))        
            
            borderIndicator = QtGui.QInputDialog.getItem(self.ilastik, "Select Border Indicator",  "Indicator",  ["Brightness",  "Darkness"],  editable = False)
            borderIndicator = str(borderIndicator[0])
            
            sigma = 1.0
            normalizePotential = True
            #TODO: this , until now, only supports gray scale and 2D!
            if borderIndicator == "Brightness":
                weights = volume[:,:,:]
            elif borderIndicator == "Darkness":
                weights = (255 - volume[:,:,:])
    
            if normalizePotential == True:
                min = numpy.min(weights)
                max = numpy.max(weights)
                weights = (weights - min)*(255.0 / (max - min))
                #real_weights[:] = weights[:]

            data = numpy.ndarray(weights.shape, 'float32')
            data[:] = weights[:]
                    
            self.weights = data
                
        
    def on_btnSegment_clicked(self):
        
        if self.weights is not None:
            res = numpy.ndarray((1,) + self.weights.shape + (1,), 'int32')
            if self.weights.shape[0] > 1:
                data = self.weights.view(vigra.ScalarVolume)
                res[0,:,:,:,0] = vigra.analysis.watersheds(data, neighborhood = 6)[0]
            else:
                data = self.weights[0,:,:].view(vigra.ScalarImage)
                res[0,0,:,:,0] = vigra.analysis.watersheds(data, neighborhood = 4)[0]
            
            colortable = []
            for i in range(256):
                color = QtGui.QColor(random.randint(0,255),random.randint(0,255),random.randint(0,255))
                colortable.append(color.rgba())
            
            #create Overlay for segmentation:
            if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"] is None:
                ov = OverlayItem(self.parent._activeImage, res, color = 0, alpha = 1.0, colorTable = colortable, autoAdd = True, autoVisible = True)
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"] = ov
            else:
                self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["Auto Segmentation/Segmentation"]._data = DataAccessor(res)
            self.parent.labelWidget.repaint()
        
    def on_btnSegmentorsOptions_clicked(self):
        pass
        #dialog = AutoSegmentorSelectionDlg(self.parent)
        #answer = dialog.exec_()
        #if answer != None:
        #    self.parent.project.autoSegmentor = answer
        #    self.parent.project.autoSegmentor.setupWeights(self.parent.project.dataMgr[self.parent._activeImageNumber].autoSegmentationWeights)

