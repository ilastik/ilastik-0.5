import numpy, vigra, h5py
import random
import code

import ilastik.gui
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase
from PyQt4 import QtGui, QtCore

from ilastik.core.dataMgr import  PropertyMgr
from ilastik.core.overlayMgr import OverlayItem, OverlayReferenceMgr


from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.iconMgr import ilastikIcons

from ilastik.modules.classification.gui import *
from ilastik.modules.cells_module.core.cellsBatchMgr import BatchProcessingManager
from ilastik.gui import volumeeditor as ve

class AutomatedCellsTab(IlastikTabBase, QtGui.QWidget):
    name = 'Automated Cells Counting'
    position = 42
    moduleName = "Automated Cells Counting"
    
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
        self.btnSelectClassfierGyrus=QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Find),'Select Classifier Gyrus')
        self.btnSelectClassfierCells=QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Find),'Select Classifier Cells')
        self.btnSelectClassfierDcx=QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Find),'Select Classifier Dcx')
        
        self.btnBatchProcess = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Play),'Batch Process')
        
        
        self.btnSelectClassfierGyrus.setToolTip('Select the classifier to be used to segment the Gyrus in the batch process')
        self.btnBatchProcess.setToolTip('Choose the file to process')
        self.btnSelectClassfierCells.setToolTip('Select the classifier to be used to segment the Cells in the batch process')
        self.btnSelectClassfierDcx.setToolTip('Select the classifier to be used to decide weather a cell is positive')
        
        tl.addWidget(self.btnSelectClassfierGyrus)
        tl.addWidget(self.btnSelectClassfierCells)
        tl.addWidget(self.btnSelectClassfierDcx)
        tl.addWidget(self.btnBatchProcess)
        
        
        tl.addStretch()
        
        self.setLayout(tl)
        
    def _initConnects(self):
        self.connect(self.btnBatchProcess, QtCore.SIGNAL('clicked()'), self.on_btnBatchProcess_clicked)
        self.connect(self.btnSelectClassfierGyrus, QtCore.SIGNAL('clicked()'), self.on_btnSelectClassifierGyrus_clicked)
        self.connect(self.btnSelectClassfierCells, QtCore.SIGNAL('clicked()'), self.on_btnSelectClassifierCells_clicked)
        self.connect(self.btnSelectClassfierDcx, QtCore.SIGNAL('clicked()'), self.on_btnSelectClassifierDcx_clicked)
    
    def on_btnSelectClassifierDcx_clicked(self):
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        
        
        self.fileNameToClassifierDcx= str(fileNameToClassifier)   
        
    def on_btnBatchProcess_clicked(self): 
        
        dialog = BatchProcessDialog(self.parent,self.fileNameToClassifierGyrus,self.fileNameToClassifierCells,self.fileNameToClassifierDcx)
        dialog.exec_()
        print "Select before a classifier!!"
             
    def on_btnSelectClassifierGyrus_clicked(self):
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        
        
        self.fileNameToClassifierGyrus = str(fileNameToClassifier)
   
    def on_btnSelectClassifierCells_clicked(self):
        path = ilastik.gui.LAST_DIRECTORY
        fileNameToClassifier = QtGui.QFileDialog.getOpenFileName(self, "", path)
        ilastik.gui.LAST_DIRECTORY = QtCore.QFileInfo(fileNameToClassifier).path()
        
        
        self.fileNameToClassifierCells = str(fileNameToClassifier)
        print self.fileNameToClassifierCells


class BatchProcessDialog(QtGui.QDialog):
    def __init__(self, parent=None,fileNameToClassifierGyrus=None,fileNameToClassfierCells=None, fileNameToClassifierDcx=None):
        
        #print fileNameToClassfierCells
        #print fileNameToClassifierGyrus
        
        self.fileNameToClassifierGyrus = fileNameToClassifierGyrus
        self.fileNameToClassifierCells = fileNameToClassfierCells
        self.fileNameToClassifierDcx=fileNameToClassifierDcx
        
        if self.isPrecondition():   
            
            QtGui.QWidget.__init__(self, parent)
            self.setWindowTitle("Batch Process")
            self.filenames = []
            self.ilastik = parent
            self.setMinimumWidth(400)
            self.layout = QtGui.QVBoxLayout()
            self.setLayout(self.layout)
        
            self.filesView = QtGui.QListWidget()
            self.filesView.setMinimumHeight(300)
        
            self.pathButton = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.AddSel), "Add to selection")
            self.clearSelectionBtn = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.RemSel), "Clear all")
        
        
            self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
            self.connect(self.clearSelectionBtn, QtCore.SIGNAL('clicked()'), self.clearSelection)
        
            tempLayout = QtGui.QHBoxLayout()
        
            tempLayout.addWidget(self.pathButton)
            tempLayout.addWidget(self.clearSelectionBtn)
            tempLayout.addStretch()
        
            self.layout.addLayout(tempLayout)
            self.layout.addWidget(self.filesView)
        
        
            tempLayout = QtGui.QHBoxLayout()
            self.cancelButton = QtGui.QPushButton("Cancel")
            self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
            
            self.okButton = QtGui.QPushButton("Ok")
            self.okButton.setEnabled(False)
            self.connect(self.okButton, QtCore.SIGNAL('clicked()'), self.accept)
            
            self.loadButton = QtGui.QPushButton("Process")
            self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotProcess)
            self.loadButton.setEnabled(False)
            
            tempLayout.addStretch()
            tempLayout.addWidget(self.cancelButton)
            tempLayout.addWidget(self.okButton)
            tempLayout.addWidget(self.loadButton)
            self.layout.addStretch()
            self.layout.addLayout(tempLayout)
        
        
            self.logger = QtGui.QPlainTextEdit()
            self.logger.setVisible(False)
            self.layout.addWidget(self.logger)        
            self.image = None
        else:
            print "select valid classifiers: "
            
            print self.fileNameToClassifierCells
            print self.fileNameToClassifierGyrus
            print self.fileNameToClassifierDcx
    
    def isPrecondition(self):
        
        return self.fileNameToClassifierGyrus!=None and self.fileNameToClassifierDcx!=None and self.fileNameToClassifierCells !=None
        


    def slotDir(self):
        selection = QtGui.QFileDialog.getOpenFileNames(self, "Select .h5", filter = "HDF5 (*.h5)")
        self.filenames.extend(selection)
        for f in selection:
            self.filesView.addItem(f)
            
        if self.filesView != None:
            self.loadButton.setEnabled(True)
          
    def clearSelection(self):
        self.filenames = []
        self.filesView.clear()

    def slotProcess(self):
        self.okButton.setEnabled(True)
        self.process(self.filenames)
        
        
    
    def printStuff(self, stuff):
        self.logger.insertPlainText(stuff)
        self.logger.ensureCursorVisible()
        self.logger.update()
        self.logger.repaint()
        QtGui.QApplication.instance().processEvents()
                        
    def process(self, fileNames):
        print fileNames
        manager=BatchProcessingManager(fileNames,str(self.fileNameToClassifierGyrus),str(self.fileNameToClassifierCells),str(self.fileNameToClassifierDcx))
        
        manager.Start()
        self.okButton.setEnabled(True)
        print "BATCH PROCESS FINISHED!!!"
        self.clearSelection()
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.image
        else:
            return None