# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 09:33:57 2010

@author: - 
"""

import os, glob
import vigra
import numpy

import numpy
import sys

import vigra
import getopt
import h5py
import glob
import traceback

from PyQt4 import QtCore, QtGui, uic

import sys, gc

import ilastik.gui.volumeeditor as ve

from ilastik.core import dataMgr
from ilastik.gui.iconMgr import ilastikIcons
from ilastik.core.volume import DataAccessor

from ilastik.modules.classification.core import featureMgr
from ilastik.modules.classification.core import classificationMgr
from ilastik.modules.classification.core import classificationMgr

class BatchProcess(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
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

        


    def slotDir(self):
        selection = QtGui.QFileDialog.getOpenFileNames(self, "Select .h5 Files", filter = "HDF5 (*.h5)")
        self.filenames.extend(selection)
        for f in selection:
            self.filesView.addItem(f)
            
    def clearSelection(self):
        self.filenames = []
        self.filesView.clear()

    def slotProcess(self):
        self.process(self.filenames)
    
    
    def printStuff(self, stuff):
        self.logger.insertPlainText(stuff)
        self.logger.ensureCursorVisible()
        self.logger.update()
        self.logger.repaint()
        QtGui.QApplication.instance().processEvents()
                        
    def process(self, fileNames):
        self.logger.clear()
        self.logger.setVisible(True)
  
        #loop over provided images an put them in the hdf5
        z = 0
        allok = True
        for filename in fileNames:
            try:
                self.printStuff("Processing " + str(filename) + "\n")
                
                fr = h5py.File(str(filename), 'r')
                dr = fr["volume/data"]
                mpa = dataMgr.MultiPartDataItemAccessor(DataAccessor(dr), 256, 30)
                

                #save results            
                fw = h5py.File(str(filename) + '_processed.h5', 'w')
                gw = fw.create_group("volume")

                for blockNr in range(mpa.getBlockCount()):
                    
                    self.printStuff("Part " + str(blockNr) + "/" + str(mpa.getBlockCount()) + " " )
                                            
                    dm = dataMgr.DataMgr()
                                    
                    di = mpa.getDataItem(blockNr)
                    dm.append(di, alreadyLoaded = True)
                              
                    fm = dm.Classification.featureMgr      
                    #fm = featureMgr.FeatureMgr(dm)
                    #cm = classificationMgr.ClassificationModuleMgr(dm)
                    fm.setFeatureItems(self.ilastik.project.dataMgr.Classification.featureMgr.featureItems)
    
                    gc.collect()
    
                    fm.prepareCompute(dm)
                    fm.triggerCompute()
                    fm.joinCompute(dm)
    
    
                    dm.module["Classification"]["classificationMgr"].classifiers = self.ilastik.project.dataMgr.module["Classification"]["classificationMgr"].classifiers
                    dm.module["Classification"]["labelDescriptions"] = self.ilastik.project.dataMgr.module["Classification"]["labelDescriptions"]
    
                    classificationPredict = classificationMgr.ClassifierPredictThread(dm)
                    classificationPredict.start()
                    classificationPredict.wait()
                    
                    classificationPredict.generateOverlays()
                    
                    dm[0].serialize(gw)
                    self.printStuff(" done\n")
                                        
                fw.close()
                fr.close()
                
            except Exception, e:
                print "######Exception"
                traceback.print_exc(file=sys.stdout)
                print e
                allok = False
                self.logger.appendPlainText("Error processing file " + filename + ", " + str(e))
                self.logger.appendPlainText("")                
            
            
        if allok:
            self.printStuff("Batch processing finished")            
            self.okButton.setEnabled(True)
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.image
        else:
            return None



       
def test():
    """Text editor demo"""
    import numpy
    app = QtGui.QApplication([""])
    
    dialog = BatchProcess(None)
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
