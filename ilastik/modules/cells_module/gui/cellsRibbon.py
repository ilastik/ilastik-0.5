from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton
from PyQt4 import QtGui, QtCore
import numpy
import random
import vigra


import ilastik.gui
from ilastik.gui.iconMgr import ilastikIcons
import ilastik.gui.volumeeditor as ve
from ilastik.gui.overlayWidget import OverlayWidget




#TODO SPLIT INTO THREE PARTS
from ilastik.modules.cells_module.core.channelsjobs.cellsMgrDapy import GyrusSegmentation
from ilastik.modules.cells_module.core.channelsjobs.cellsMgrBrdU import BrdUSegmentation
from ilastik.modules.cells_module.core.channelsjobs.cellsMgrDcX import DcxSegmentation



from ilastik.core.overlayMgr import OverlayItem
from ilastik.core.volume import DataAccessor

import csv


class CellsCountingTab(IlastikTabBase, QtGui.QWidget):
    name = 'Cells Counting'  #the name of your ribbon
    position = 41    #the position in the tabbar
    moduleName = "cells"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        """
        you can create some default overlays here 
        or set up your own labelWidget for the VolumeEditor
        that can handle user given pixel labels in any
        way
        """
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                        
        self.ilastik.labelWidget._history.volumeEditor = self.ilastik.labelWidget

        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
        
        
        """Add standard overlays"""
        
        weights=self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 1].astype(numpy.uint8)
        ov = OverlayItem(self.parent._activeImage, weights, color=QtGui.QColor(255,0,0), alpha=1.0, colorTable=[QtGui.qRgb(i, i, i) for i in range(256)], autoAdd=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr['cells/BrdU Channel'] = ov
        
        weights=self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 0].astype(numpy.uint8)
        ov = OverlayItem(self.parent._activeImage, weights, color=QtGui.QColor(255,0,0), alpha=1.0, colorTable=[QtGui.qRgb(i, i, i) for i in range(256)], autoAdd=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr['cells/Dapi Channel'] = ov
        
        weights=self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 2].astype(numpy.uint8)
        ov = OverlayItem(self.parent._activeImage, weights, color=QtGui.QColor(255,0,0), alpha=1.0, colorTable=[QtGui.qRgb(i, i, i) for i in range(256)], autoAdd=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr['cells/Dcx Channel'] = ov
        
        self.use3D=True
    def on_deActivation(self):
        print 'Left Tab ', self.__class__.name
        
    def _initContent(self):

        tl = QtGui.QHBoxLayout()      
        self.btnDapi = TabButton('Dapi Channel',QtGui.QIcon(ilastikIcons.Cut),)
        self.btnBrdU  = TabButton('BrdU Channel',QtGui.QIcon(ilastikIcons.Cut),)
        self.btnDcx  = TabButton('Dcx Channel',QtGui.QIcon(ilastikIcons.Cut),)
        self.btnExport  = TabButton('Export Results',QtGui.QIcon(ilastikIcons.Cut),)    
      
      
        self.btnDapi.setToolTip('Segment the Gyrus')
        self.btnBrdU.setToolTip('find interesting cells')
        self.btnDcx.setToolTip('find positive cells')
        self.btnExport.setToolTip('export Results')
        
        
        tl.addWidget(self.btnDapi)
        tl.addWidget(self.btnBrdU)
        tl.addWidget(self.btnDcx)
        tl.addWidget(self.btnExport)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        self.btnDimSelect = TabButton('Distance 3D',QtGui.QIcon(ilastikIcons.Cut),)
        
        tl.addWidget(self.btnDimSelect)       
        
        
    def _initConnects(self):
        self.connect(self.btnDapi, QtCore.SIGNAL('clicked()'), self.on_btnDapi_clicked)
        self.connect(self.btnBrdU, QtCore.SIGNAL('clicked()'), self.on_btnBrdU_clicked)
        self.connect(self.btnDcx, QtCore.SIGNAL('clicked()'), self.on_btnDcx_clicked)
        self.connect(self.btnExport, QtCore.SIGNAL('clicked()'), self.on_btnExport_clicked)
        self.connect(self.btnDimSelect,QtCore.SIGNAL('clicked()'), self.on_btnDimSelect_clicked)

#############################################################################################################        
    
    def on_btnDimSelect_clicked(self):
        
        if self.use3D==True:
            self.btnDimSelect.setText("Distance 2D")
            self.use3D=False
        else:
            self.use3D=True
            self.btnDimSelect.setText("Distance 3D")
        
#############################################################################################################    
    
    
    
    def on_btnDapi_clicked(self):
        #self.weights = self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 0]
        #self.weights = self.weights.astype(numpy.float32)
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        fileNameToClassifier = str(fileNameToClassifier)
         
        self.Gyrus = GyrusSegmentation(self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 0].astype(numpy.float32),self.use3D,fileNameToClassifier)
       
        """sets the overlay"""       
        
        """interior"""
        """prepare the color table for the overlay"""
        colortable = [0]
        color = QtGui.QColor(255,0,0)
        colortable.append(color.rgba())
        
        
        ov = OverlayItem(self.parent._activeImage, self.Gyrus.res.astype(numpy.uint8),colorTable=colortable, autoAdd=True, autoVisible=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["cells/interior"] = ov
        
        """gyrus"""
        colortable = [0]
        color = QtGui.QColor(0,255,0)
        colortable.append(color.rgba())
        
        ov = OverlayItem(self.parent._activeImage, self.Gyrus.segmented.astype(numpy.uint8),colorTable=colortable, autoAdd=True, autoVisible=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["cells/Gyrus"] = ov
        """distance transform"""
        ov = OverlayItem(self.parent._activeImage, self.Gyrus.distanceTransformed,color= QtGui.QColor(0,0,255).rgba())
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["cells/Distance Transform"] = ov

###################################################################################       
    def on_btnBrdU_clicked(self):
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        
        fileNameToClassifier = str(fileNameToClassifier)
        
        
        self.Cells=BrdUSegmentation(self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 1],fileNameToClassifier,self.Gyrus.segmented+self.Gyrus.res)
        
        
        
        
        
        
        self.makeOverlay("cells/Segmented Cells", self.Cells.segmented.astype(numpy.uint8))
   
   
   
        

    

       
       
       
################################################################################################################       
    def on_btnDcx_clicked(self):
        
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        
        fileNameToClassifier = str(fileNameToClassifier)
                
        colortable = [0]
        color = QtGui.QColor(0,0,255)
        colortable.append(color.rgba())
        
        self.Dcx=DcxSegmentation(self.Cells.DictPositions,self.ilastik.project.dataMgr[0]._dataVol._data[0, :, :, :, 2],fileNameToClassifier)
        
        ov = OverlayItem(self.parent._activeImage, self.Dcx.segmented.astype(numpy.uint8),colorTable=colortable, autoAdd=True, autoVisible=True)
        self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr["cells/Dcx positive"] = ov
        
         
    
    
    def on_btnExport_clicked(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Export Results", filter =  "csv Files (*.csv)")
        self.ExportResults(fileName)
        print "Results Saved to: " + fileName    

####################################################################################################################       
    
    def ExportResults(self,fileName):
        
        f=open(fileName,'wb')
        
        self.Header=['cell id','Z_center','Distance from Interior','Cell Volume',
                     'Cell Average BrdU Intensity','Cell Average Dcx Intensity',
                     'Positive to Dcx',
                     'Gyrus Volume','Gyrus Area',
                     "Interior Volume", "Interior Area",
                     'AI Slice in Dapy channel','AI Slice in BrdU channel','AI Slice in Dcx channel']
        
        try:
            writer = csv.writer(f,delimiter=',')
            writer.writerow(self.Header)
            for k in self.Cells.DictCenters.iterkeys():
                x=self.Cells.DictCenters[k][0]
                y=self.Cells.DictCenters[k][1]
                z=self.Cells.DictCenters[k][2]
                
                row =[k,z,self.Gyrus.distanceTransformed[x][y][z],len(self.Cells.DictPositions[k][0]),
                      self.Cells.DictIntBrdU[k],self.Dcx.DictIntDcX[k],
                      self.Dcx.dictPositiveCells[k],
                      self.Gyrus.GyrusVolume,self.Gyrus.GyrusArea[z],
                      self.Gyrus.InteriorVolume,self.Gyrus.InteriorArea[z],
                      self.Gyrus.averageIntSlice[z],self.Cells.averageIntSlice[z],self.Dcx.averageIntSlice[z]]
                writer.writerow(row)
        finally:
            f.close()
        

        

    
 
        
################################################################################################       
    
    def makeOverlay(self, name, data, transparentValues=(0,)):
   
        colortable = []
        for i in range(256):
            color = QtGui.QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            colortable.append(color.rgba())
            
        for k in transparentValues:
            colortable[k] = QtCore.Qt.transparent
        #create Overlay for segmentation:
        if self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr[name] is None:
            ov = OverlayItem(self.parent._activeImage, data, color=0, alpha=1.0, colorTable=colortable, autoAdd=True, autoVisible=True)
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr[name] = ov
        else:
            self.parent.project.dataMgr[self.parent._activeImageNumber].overlayMgr[name]._data = DataAccessor(data)
    
    
    
    

