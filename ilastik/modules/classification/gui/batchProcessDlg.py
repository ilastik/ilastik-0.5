# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:33:57 2010

@author: - 
"""

import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

from PyQt4 import QtCore, QtGui

from ilastik.modules.classification.core.batchProcess import BatchOptions, BatchProcessCore
from ilastik.gui.iconMgr import ilastikIcons

#*******************************************************************************
# B a t c h P r o c e s s                                                      *
#*******************************************************************************

class BatchProcess(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle("Batch Process")
        self.filenames = []
        self.ilastik = parent
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.filesView = QtGui.QListWidget()
        self.filesView.setMinimumHeight(300)
        
        self.outputDir = QtGui.QLineEdit("")
        self.writeSegmentation = QtGui.QCheckBox("Write segmentation")
        self.writeFeatures = QtGui.QCheckBox("Write features")
        
        self.writeSegmentation.setEnabled(False)
        self.writeFeatures.setEnabled(False)
        
        # Oli TODO: implement these options 
        self.writeSegmentation.setVisible(False)
        self.writeFeatures.setVisible(False)
        
        self.serializeProcessing = QtGui.QCheckBox("Blockwise processing (saves memory)")
        self.serializeProcessing.setCheckState(False)
        
        self.pathButton = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.AddSel), "Add to selection")
        self.removeButton = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.RemSel), "Remove from selection")
        self.clearSelectionBtn = QtGui.QPushButton("Clear all")
        
        
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        self.connect(self.removeButton, QtCore.SIGNAL('clicked()'), self.removeSelectedEntry)
        self.connect(self.clearSelectionBtn, QtCore.SIGNAL('clicked()'), self.clearSelection)
        
        tempLayout = QtGui.QHBoxLayout()
        
        tempLayout.addWidget(self.pathButton)
        tempLayout.addWidget(self.removeButton)
        tempLayout.addWidget(self.clearSelectionBtn)
        tempLayout.addStretch()
        
        self.layout.addLayout(tempLayout)
        self.layout.addWidget(self.filesView)
        self.layout.addWidget(self.writeFeatures)
        self.layout.addWidget(self.writeSegmentation)
        self.layout.addWidget(self.serializeProcessing)


        tempLayout = QtGui.QHBoxLayout()
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        self.okButton = QtGui.QPushButton("Ok")
        self.okButton.setEnabled(False)
        self.connect(self.okButton, QtCore.SIGNAL('clicked()'), self.accept)
        self.loadButton = QtGui.QPushButton("Process")
        self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotProcess)
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

        
    def removeSelectedEntry(self):
        itemIndex = self.filesView.currentRow()
        if itemIndex >= 0:
            dummy = self.filesView.takeItem(itemIndex)
            del dummy
            del self.filenames[itemIndex]
        for a in self.filenames:
            print a
        
        

    def slotDir(self):
        selection = QtGui.QFileDialog.getOpenFileNames(self, "Select .h5 or image Files", filter = "HDF5 (*.h5);; Images (*.jpg *.tiff *.tif *.png *.jpeg)")
        
        for s in selection:
            self.filenames.append(str(s))
            
        for f in selection:
            self.filesView.addItem(f)
            
    def clearSelection(self):
        self.filenames = []
        self.filesView.clear()

    def slotProcess(self):
        outputDir = os.path.split(str(self.filenames[0]))[0]
        descr = self.ilastik.project.dataMgr.module["Classification"]["labelDescriptions"]

        bo = BatchOptions(outputDir, 'gui-mode-no-file-name-needed', self.filenames, descr)
        bo.writeFeatures = self.writeFeatures.isChecked()
        bo.writeSegmentation = self.writeSegmentation.isChecked()
        bo.serializeProcessing = self.serializeProcessing.isChecked()
        self.process(bo)
    
    
    def printStuff(self, stuff):
        self.logger.insertPlainText(stuff)
        self.logger.ensureCursorVisible()
        self.logger.update()
        self.logger.repaint()
        QtGui.QApplication.instance().processEvents()
                        
    def process(self, batchOptions):
        self.logger.clear()
        self.logger.setVisible(True)
        
        classifiers = self.ilastik.project.dataMgr.module["Classification"]["classificationMgr"].classifiers
        featureList = self.ilastik.project.dataMgr.Classification.featureMgr.featureItems
        batchOptions.setFeaturesAndClassifier(classifiers, featureList)
        batchProcess = BatchProcessCore(batchOptions)
        for i in batchProcess.process():
            self.printStuff("Finished: " + str(i) + "\n")
        self.okButton.setEnabled(True)

    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.image
        else:
            return None



       
def test():
    """Text editor demo"""
    app = QtGui.QApplication([""])
    
    dialog = BatchProcess(None)
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()
