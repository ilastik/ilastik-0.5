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

import sys
sys.path.append( os.path.join(os.getcwd(), '..') )

import volumeeditor as ve

from core import dataMgr, featureMgr
from core import classificationMgr as cm

class BatchProcess(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self)
        self.filenames = []
        self.ilastik = parent
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.filesView = QtGui.QListWidget()
        self.filesView.setMinimumHeight(300)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        self.layout.addWidget(self.pathButton)
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

        if self.ilastik.featureCache is not None:
            if 'tempF_batch' in self.ilastik.featureCache.keys():
                grp = self.ilastik.featureCache['tempF_batch']
            else:
                grp = self.ilastik.featureCache.create_group('tempF_batch')
        else:
            grp = None

        self.dataMgr = dataMgr.DataMgr(grp)
        self.dataMgr.channels = self.ilastik.project.dataMgr.channels
        


    def slotDir(self):
        self.filenames = QtGui.QFileDialog.getOpenFileNames(self, "Image Files")
        self.filesView.clear()
        for f in self.filenames:
            self.filesView.addItem(f)

    def slotProcess(self):
        self.process(self.filenames)
    
    def process(self, fileNames):
        self.logger.clear()
        self.logger.setVisible(True)
  
        #loop over provided images an put them in the hdf5
        z = 0
        allok = True
        for filename in fileNames:
            try:
                filename = str(filename)
                di = dataMgr.DataItemImage(filename)
                di.loadData()
                self.dataMgr.append(di)

                fm = featureMgr.FeatureMgr(self.dataMgr, self.ilastik.project.featureMgr.featureItems)

                fm.prepareCompute(self.dataMgr)
                fm.triggerCompute()
                fm.joinCompute(self.dataMgr)


                self.dataMgr.classifiers = self.ilastik.project.dataMgr.classifiers

                classificationPredict = cm.ClassifierPredictThread(self.dataMgr)
                classificationPredict.start()
                classificationPredict.wait()
  
                #save results
            
                f = h5py.File(filename + '_processed.h5', 'w')
                g = f.create_group("volume")
                self.dataMgr[0].dataVol.labels = ve.VolumeLabels(ve.DataAccessor(numpy.zeros((self.dataMgr[0].dataVol.data.shape[0:4]),'uint8')))
                self.dataMgr[0].dataVol.labels.descriptions = self.ilastik.project.dataMgr[0].dataVol.labels.descriptions
                self.dataMgr[0].dataVol.serialize(g)
                self.dataMgr[0].prediction.serialize(g, 'prediction')
                f.close()
                self.logger.insertPlainText(".")
            except Exception, e:
                print "######Exception"
                traceback.print_exc(file=sys.stdout)
                print e
                allok = False
                self.logger.appendPlainText("Error processing file " + filename + ", " + str(e))
                self.logger.appendPlainText("")                
            
            self.dataMgr.clearDataList()
            #self.logger.update()
            self.logger.repaint()
            
        if allok:
            self.logger.appendPlainText("Batch processing finished")            
            self.okButton.setEnabled(True)
        
    def exec_(self):
        if super(BatchProcess, self).exec_() == QtGui.QDialog.Accepted:
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
