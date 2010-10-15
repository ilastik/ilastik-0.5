import numpy, vigra, h5py
import random
import code

from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore

from ilastik.core.dataMgr import  PropertyMgr
from ilastik.core.overlayMgr import OverlayItem, OverlayReferenceMgr

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.modules.classification.gui import *
from ilastik.modules.classification.gui.batchProcess import BatchProcess


class AutomateTab(IlastikTabBase, QtGui.QWidget):
    name = 'Automate'
    position = 100
    moduleName = "Classification"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
    
    def on_activation(self):
        pass
                        
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        
        tl = QtGui.QHBoxLayout()      
        self.btnBatchProcess = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Batch Process')
       
        self.btnBatchProcess.setToolTip('Select and batch predict files with the currently trained classifier')
        tl.addWidget(self.btnBatchProcess)
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnBatchProcess, QtCore.SIGNAL('clicked()'), self.on_btnBatchProcess_clicked)
        
    def on_btnBatchProcess_clicked(self): 
        dialog = BatchProcess(self.parent)
        dialog.exec_()