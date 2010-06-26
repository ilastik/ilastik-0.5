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

from PyQt4 import QtCore, QtGui, uic

class StackLoader(QtGui.QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setMinimumWidth(400)
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        tempLayout = QtGui.QHBoxLayout()
        self.path = QtGui.QLineEdit("")
        self.connect(self.path, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.pathButton = QtGui.QPushButton("Select")
        self.connect(self.pathButton, QtCore.SIGNAL('clicked()'), self.slotDir)
        tempLayout.addWidget(self.path)
        tempLayout.addWidget(self.pathButton)
        self.layout.addWidget(QtGui.QLabel("Path to Image Stack:"))
        self.layout.addLayout(tempLayout)


        tempLayout = QtGui.QHBoxLayout()
        self.offsetX = QtGui.QSpinBox()
        self.offsetX.setRange(0,10000)
        self.offsetY = QtGui.QSpinBox()
        self.offsetY.setRange(0,10000)
        self.offsetZ = QtGui.QSpinBox()
        self.offsetZ.setRange(0,10000)
        tempLayout.addWidget( self.offsetX)
        tempLayout.addWidget( self.offsetY)
        tempLayout.addWidget( self.offsetZ)
        self.layout.addWidget(QtGui.QLabel("Sobvolume Offsets:"))
        self.layout.addLayout(tempLayout)
        
        tempLayout = QtGui.QHBoxLayout()
        self.sizeX = QtGui.QSpinBox()
        self.sizeX.setRange(0,10000)
        self.sizeY = QtGui.QSpinBox()
        self.sizeY.setRange(0,10000)
        self.sizeZ = QtGui.QSpinBox()
        self.sizeZ.setRange(0,10000)
        tempLayout.addWidget( self.sizeX)
        tempLayout.addWidget( self.sizeY)
        tempLayout.addWidget( self.sizeZ)
        self.layout.addWidget(QtGui.QLabel("Subvolume Size:"))
        self.layout.addLayout(tempLayout)

        tempLayout = QtGui.QHBoxLayout()
        self.invert = QtGui.QCheckBox("Invert Colors?")
        tempLayout.addWidget(self.invert)
        self.layout.addLayout(tempLayout) 

        tempLayout = QtGui.QHBoxLayout()
        self.grayscale = QtGui.QCheckBox("Convert to Grayscale ?")
        tempLayout.addWidget(self.grayscale)
        self.layout.addLayout(tempLayout) 


        tempLayout = QtGui.QHBoxLayout()
        self.normalize = QtGui.QCheckBox("Normalize Data?")
        tempLayout.addWidget(self.normalize)
        self.layout.addLayout(tempLayout) 


        tempLayout = QtGui.QHBoxLayout()
        self.downsample = QtGui.QCheckBox("Downsample Subvolume to Size:")
        self.connect(self.downsample, QtCore.SIGNAL("stateChanged(int)"), self.toggleDownsample)      
        tempLayout.addWidget(self.downsample)
        self.layout.addLayout(tempLayout)

        self.downsampleFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.downX = QtGui.QSpinBox()
        self.downX.setRange(0,10000)
        self.downY = QtGui.QSpinBox()
        self.downY.setRange(0,10000)
        self.downZ = QtGui.QSpinBox()
        self.downZ.setRange(0,10000)
        tempLayout.addWidget( self.downX)
        tempLayout.addWidget( self.downY)
        tempLayout.addWidget( self.downZ)
        self.downsampleFrame.setLayout(tempLayout)
        self.downsampleFrame.setVisible(False)
        self.layout.addWidget(self.downsampleFrame)
    
        
        tempLayout = QtGui.QHBoxLayout()
        self.alsoSave = QtGui.QCheckBox("also save to Destination File:")
        self.connect(self.alsoSave, QtCore.SIGNAL("stateChanged(int)"), self.toggleAlsoSave)
        tempLayout.addWidget(self.alsoSave)
        self.layout.addLayout(tempLayout) 

        self.alsoSaveFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.fileButton = QtGui.QPushButton("Select")
        self.connect(self.fileButton, QtCore.SIGNAL('clicked()'), self.slotFile)
        self.file = QtGui.QLineEdit("")
        tempLayout.addWidget(self.file)
        tempLayout.addWidget(self.fileButton)
        self.alsoSaveFrame.setLayout(tempLayout)
        self.alsoSaveFrame.setVisible(False)
        self.layout.addWidget(self.alsoSaveFrame)        
        
        
        
        tempLayout = QtGui.QHBoxLayout()
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        self.okButton = QtGui.QPushButton("Ok")
        self.okButton.setEnabled(False)
        self.connect(self.okButton, QtCore.SIGNAL('clicked()'), self.accept)
        self.loadButton = QtGui.QPushButton("Load")
        self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotLoad)
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

    def toggleAlsoSave(self, int):
        if self.alsoSave.checkState() == 0:
            self.alsoSaveFrame.setVisible(False)
        else:
            self.alsoSaveFrame.setVisible(True)
    
    def toggleDownsample(self, int):
        if self.downsample.checkState() == 0:
            self.downsampleFrame.setVisible(False)
        else:
            self.downsampleFrame.setVisible(True)


    def pathChanged(self, text):
        list = glob.glob(str(self.path.text()) )
        self.sizeZ.setValue(len(list))
        temp = vigra.impex.readImage(list[0])
        self.sizeX.setValue(temp.shape[0])
        self.sizeY.setValue(temp.shape[1])
        if len(temp.shape) == 3:
            self.rgb = temp.shape[2]
        else:
            self.rgb = 1


    def slotDir(self):
        path = self.path.text()
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        self.path.setText(filename + "/*")

    def slotFile(self):
        filename= QtGui.QFileDialog.getSaveFileName(self, "Save to File", "*.h5")
        self.file.setText(filename)

    def slotLoad(self):
        offsets = (self.offsetX.value(),self.offsetY.value(),self.offsetZ.value())
        shape = (self.sizeX.value(),self.sizeY.value(),self.sizeZ.value())
        destShape = None
        if self.downsample.checkState() > 0:
            destShape = (self.downX.value(),self.downY.value(),self.downZ.value())
        filename = str(self.file.text())
        if self.alsoSave.checkState() == 0:
            filename = None
        normalize = self.normalize.checkState() > 0
        invert = self.invert.checkState() > 0
        grayscale = self.grayscale.checkState() > 0
        self.load(str(self.path.text()), offsets, shape, destShape, filename, normalize, invert, grayscale)
    
    def load(self, pattern,  offsets, shape, destShape = None, destfile = None, normalize = False, invert = False, makegray = False):
        self.logger.clear()
        self.logger.setVisible(True)

        try:
            self.image = numpy.zeros(shape + (self.rgb,), 'float32')
        except Exception, e:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory, please select a smaller Subvolume. Much smaller !! since you may also want to calculate some features...")
            self.reject()
            return
        
        #loop over provided images an put them in the hdf5
        z = 0
        allok = True
        for filename in sorted(glob.glob(pattern), key = str.lower):
            if z >= offsets[2] and z < offsets[2] + shape[2]:
                try:
                    img_data = vigra.impex.readImage(filename)
                    if self.rgb > 1:
                        if invert is True:
                            self.image[:,:, z-offsets[2],:] = 255 - img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1],:]
                        else:
                            self.image[:,:,z-offsets[2],:] = img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1],:]
                    else:
                        if invert is True:
                            self.image[:,:, z-offsets[2],0] = 255 - img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                        else:
                            self.image[:,:,z-offsets[2],0] = img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                    self.logger.insertPlainText(".")
                except Exception, e:
                    allok = False
                    print e 
                    s = "Error loading file " + filename + "as Slice " + str(z-offsets[2])
                    self.logger.appendPlainText(s)
                    self.logger.appendPlainText("")
                self.logger.repaint()
            z = z + 1
                 
        if destShape is not None:
            result = numpy.zeros(destShape + (self.rgb,), 'float32')
            for i in range(self.rgb):
                cresult = vigra.sampling.resizeVolumeSplineInterpolation(self.image[:,:,:,i].view(vigra.Volume),destShape)
                result[:,:,:,i] = cresult[:,:,:]
            self.image = result
        else:
            destShape = shape
        
        if normalize:
            maximum = numpy.max(self.image)
            minimum = numpy.min(self.image)
            self.image = self.image * (255.0 / (maximum - minimum)) - minimum

        
        if makegray:
            self.image = self.image.view(numpy.ndarray)
            result = numpy.average(self.image, axis = 3)
            self.rgb = 1
            self.image = result.astype('uint8')
            self.image.reshape(self.image.shape + (1,))
        
        self.image = self.image.reshape(1,destShape[0],destShape[1],destShape[2],self.rgb)
        
        try:
            if destfile != None :
                f = h5py.File(destfile, 'w')
                g = f.create_group("volume")        
                g.create_dataset("data",data = self.image)
                f.close()
        except:
            print "######ERROR saving File ", destfile
            
        if allok:
            self.logger.appendPlainText("Slices loaded")            
            self.okButton.setEnabled(True)
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.image
        else:
            return None
       
def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])
    
    dialog = StackLoader()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
