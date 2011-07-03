#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QApplication, QCheckBox, QDialog, QFileDialog,\
                        QHBoxLayout, QIcon, QLineEdit, QListWidget,\
                        QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

from ilastik.modules.classification.core.batchProcess import BatchOptions, BatchProcessCore
from ilastik.gui.iconMgr import ilastikIcons

#*******************************************************************************
# B a t c h P r o c e s s                                                      *
#*******************************************************************************

class BatchProcess(QDialog):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setWindowTitle("Batch Process")
        self.filenames = []
        self.ilastik = parent
        self.setMinimumWidth(400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.filesView = QListWidget()
        self.filesView.setMinimumHeight(300)
        
        self.outputDir = QLineEdit("")
        self.writeSegmentation = QCheckBox("Write segmentation")
        self.writeFeatures = QCheckBox("Write features")
        
        self.writeSegmentation.setEnabled(False)
        self.writeFeatures.setEnabled(False)
        
        # Oli TODO: implement these options 
        self.writeSegmentation.setVisible(False)
        self.writeFeatures.setVisible(False)
        
        self.serializeProcessing = QCheckBox("Blockwise processing (saves memory)")
        self.serializeProcessing.setCheckState(False)
        
        self.pathButton = QPushButton(QIcon(ilastikIcons.AddSel), "Add to selection")
        self.removeButton = QPushButton(QIcon(ilastikIcons.RemSel), "Remove from selection")
        self.clearSelectionBtn = QPushButton("Clear all")
        
        
        self.connect(self.pathButton, SIGNAL('clicked()'), self.slotDir)
        self.connect(self.removeButton, SIGNAL('clicked()'), self.removeSelectedEntry)
        self.connect(self.clearSelectionBtn, SIGNAL('clicked()'), self.clearSelection)
        
        tempLayout = QHBoxLayout()
        
        tempLayout.addWidget(self.pathButton)
        tempLayout.addWidget(self.removeButton)
        tempLayout.addWidget(self.clearSelectionBtn)
        tempLayout.addStretch()
        
        self.layout.addLayout(tempLayout)
        self.layout.addWidget(self.filesView)
        self.layout.addWidget(self.writeFeatures)
        self.layout.addWidget(self.writeSegmentation)
        self.layout.addWidget(self.serializeProcessing)


        tempLayout = QHBoxLayout()
        self.cancelButton = QPushButton("Cancel")
        self.connect(self.cancelButton, SIGNAL('clicked()'), self.reject)
        self.okButton = QPushButton("Ok")
        self.okButton.setEnabled(False)
        self.connect(self.okButton, SIGNAL('clicked()'), self.accept)
        self.loadButton = QPushButton("Process")
        self.connect(self.loadButton, SIGNAL('clicked()'), self.slotProcess)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.okButton)
        tempLayout.addWidget(self.loadButton)
        self.layout.addStretch()
        self.layout.addLayout(tempLayout)
        
        
        self.logger = QPlainTextEdit()
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
        selection = QFileDialog.getOpenFileNames(self, "Select .h5 or image Files", filter = "HDF5 (*.h5);; Images (*.jpg *.tiff *.tif *.png *.jpeg)")
        
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
        QApplication.instance().processEvents()
                        
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
        if QDialog.exec_(self) == QDialog.Accepted:
            return  self.image
        else:
            return None



       
def test():
    """Text editor demo"""
    app = QApplication([""])
    
    dialog = BatchProcess(None)
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()
