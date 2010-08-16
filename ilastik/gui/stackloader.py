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

        #a list of filenames
        #internally, it's a list of lists of filenames
        #for each channel
        self.fileList = []
        self.channels = []

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
        self.multiChannel = QtGui.QCheckBox("MultiChannel Data:")
        self.connect(self.multiChannel, QtCore.SIGNAL("stateChanged(int)"), self.toggleMultiChannel)
        tempLayout.addWidget(self.multiChannel)
        self.layout.addLayout(tempLayout) 
        
        self.multiChannelFrame = QtGui.QFrame()
        tempLayout = QtGui.QVBoxLayout()
        tempLayout1 = QtGui.QHBoxLayout()
        tempLayout1.addWidget(QtGui.QLabel("Enter channel identifiers, e.g. GFP"))
        tempLayout.addLayout(tempLayout1)
        tempLayout2 = QtGui.QHBoxLayout()
        self.redChannelId = QtGui.QLineEdit("")
        self.connect(self.redChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.blueChannelId = QtGui.QLineEdit("")
        self.connect(self.blueChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        self.greenChannelId = QtGui.QLineEdit("")
        self.connect(self.greenChannelId, QtCore.SIGNAL("textChanged(QString)"), self.pathChanged)
        tempLayout2.addWidget(QtGui.QLabel("Red:"))
        tempLayout2.addWidget(self.redChannelId)
        tempLayout2.addWidget(QtGui.QLabel("Blue:"))
        tempLayout2.addWidget(self.blueChannelId)
        tempLayout2.addWidget(QtGui.QLabel("Green:"))
        tempLayout2.addWidget(self.greenChannelId)
        tempLayout.addLayout(tempLayout2)
        self.multiChannelFrame.setLayout(tempLayout)
        self.multiChannelFrame.setVisible(False)
        self.layout.addWidget(self.multiChannelFrame)        

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
        self.layout.addWidget(QtGui.QLabel("Subvolume Offsets:"))
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
        self.previewFiles = QtGui.QCheckBox("Preview or edit file list")
        self.connect(self.previewFiles, QtCore.SIGNAL("stateChanged(int)"), self.togglePreviewFiles)
        tempLayout.addWidget(self.previewFiles)
        self.layout.addLayout(tempLayout)

        self.previewFilesFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.fileListTable = QtGui.QTableWidget()
        #the table will be filled, when the frame is set to visible
        tempLayout.addWidget(self.fileListTable)
        self.previewFilesFrame.setLayout(tempLayout)
        self.previewFilesFrame.setVisible(False)
        self.layout.addWidget(self.previewFilesFrame)


        tempLayout = QtGui.QHBoxLayout()
        self.loadButton = QtGui.QPushButton("Load")
        self.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.slotLoad)
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'), self.reject)
        
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
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

    def toggleMultiChannel(self, int):
	    if self.multiChannel.checkState() == 0:
	        self.multiChannelFrame.setVisible(False)
	    else:
	        self.multiChannelFrame.setVisible(True)

    def togglePreviewFiles(self):
        if self.previewFiles.checkState() == 0:
            self.previewFilesFrame.setVisible(False)
        else:
            self.fillFileTable()
            self.previewFilesFrame.setVisible(True)

    def pathChanged(self, text):
        self.fileList = []
        self.channels = []
        if self.multiChannel.checkState() == 0:
            pathone = str(self.path.text())
            self.fileList.append(sorted(glob.glob(pathone), key=str.lower))
            #self.fileList.append(glob.glob(str(self.path.text())))
            self.channels.append(0)
        else:
            #not all channels have to be filled
            if (len(str(self.redChannelId.text()))>0):
                pathred = str(self.path.text())+"*"+str(self.redChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathred), key=str.lower))
                self.channels.append(0)
            else:
                self.fileList.append([])    
            if (len(str(self.blueChannelId.text()))>0):
                pathblue = str(self.path.text())+"*"+str(self.blueChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathblue), key=str.lower))
                self.channels.append(1)
            else:
                self.fileList.append([])
            if (len(str(self.greenChannelId.text()))>0):
                pathgreen = str(self.path.text())+"*"+str(self.greenChannelId.text())+"*"
                self.fileList.append(sorted(glob.glob(pathgreen), key=str.lower))
                self.channels.append(2)
            else:
                self.fileList.append([])

        self.sizeZ.setValue(len(self.fileList[0]))
        try:
            temp = vigra.impex.readImage(self.fileList[0][0])
            self.sizeX.setValue(temp.shape[0])
            self.sizeY.setValue(temp.shape[1])
            if len(temp.shape) == 3:
                self.rgb = temp.shape[2]
            else:
                self.rgb = 1
        except Exception as e:
            self.sizeZ.setValue(0)
            self.sizeX.setValue(0)
            self.sizeY.setValue(0)


    def slotDir(self):
        path = self.path.text()
        filename = QtGui.QFileDialog.getExistingDirectory(self, "Image Stack Directory", path)
        self.path.setText(filename + "/*")

    def slotFile(self):
        filename= QtGui.QFileDialog.getSaveFileName(self, "Save to File", "*.h5")
        self.file.setText(filename)

    def fillFileTable(self):
        if (len(self.fileList)==0):
            self.fileListTable.setRowCount(1)
            self.fileListTable.setColumnCount(3)
            self.fileListTable.setItem(0, 0, QtGui.QTableWidgetItem(QtCore.QString("file1")))
            self.fileListTable.setItem(0, 1, QtGui.QTableWidgetItem(QtCore.QString("file2")))
            self.fileListTable.setItem(0, 2, QtGui.QTableWidgetItem(QtCore.QString("file3")))
            return
        nfiles = len(self.fileList[0])
        self.fileListTable.setRowCount(nfiles)
        self.fileListTable.setColumnCount(len(self.fileList))
        #it's so ugly... but i don't know how to fill a whole column by list slicing
        if (len(self.fileList)==1):
            #single channel data
            self.fileListTable.setRowCount(len(self.fileList[0]))
            self.fileListTable.setColumnCount(1)       
            for i in range(0, len(self.fileList[0])):
                self.fileListTable.setItem(i, 0, QtGui.QTableWidgetItem(QtCore.QString(self.fileList[0][i])))
        if (len(self.fileList)==3):
            #multichannel data
            nfiles = max([len(self.fileList[0]), len(self.fileList[1]), len(self.fileList[2])])
            self.fileListTable.setRowCount(nfiles)
            self.fileListTable.setColumnCount(3)
            for i in range(0, len(self.fileList[0])):
                self.fileListTable.setItem(i, 0, QtGui.QTableWidgetItem(QtCore.QString(self.fileList[0][i])))
            for i in range(0, len(self.fileList[1])):
                self.fileListTable.setItem(i, 1, QtGui.QTableWidgetItem(QtCore.QString(self.fileList[1][i])))
            for i in range(0, len(self.fileList[2])):
                self.fileListTable.setItem(i, 2, QtGui.QTableWidgetItem(QtCore.QString(self.fileList[2][i])))

    def slotLoad(self):
        if self.multiChannel.checkState() > 0 and len(self.channels)>1:
            if (len(self.fileList[self.channels[0]])!=len(self.fileList[self.channels[1]])) or (len(self.channels)>2 and (len(self.fileList[0])!=len(self.fileList[1]))):
                QtGui.QErrorMessage.qtHandler().showMessage("Chosen channels don't have an equal number of files. Check with Preview files button")
                #should it really reject?
                self.reject()
                return
        
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
        if len(self.channels)>1:
            nch = len(self.channels)
        else:
            nch = self.rgb
        try:
            self.image = numpy.zeros(shape + (nch,), 'float32')
        except Exception, e:
            QtGui.QErrorMessage.qtHandler().showMessage("Not enough Memory, please select a smaller Subvolume. Much smaller !! since you may also want to calculate some features...")
            self.reject()
            return
        
        #loop over provided images an put them in the hdf5
        z = 0
        allok = True
        firstlist = self.fileList[self.channels[0]]
        print len(firstlist)
        img_data2 = None
        img_data3 = None
        for index, filename in enumerate(firstlist):
            if z >= offsets[2] and z < offsets[2] + shape[2]:
                try:
                    print filename
                    img_data = vigra.impex.readImage(filename)
                    
                    if self.rgb > 1:
                        if invert is True:
                            self.image[:,:, z-offsets[2],:] = 255 - img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1],:]
                        else:
                            self.image[:,:,z-offsets[2],:] = img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1],:]
                    else:
                                                  
                        if invert is True:
                            self.image[:,:, z-offsets[2],self.channels[0]] = 255 - img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                            #load other channes if needed
                            if (len(self.channels)>1):
                                img_data2 = vigra.impex.readImage(self.fileList[1][index])
                                self.image[:,:,z-offsets[2],self.channels[1]] = 255 - img_data2[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                            if (len(self.channels)>2):
                                img_data3 = vigra.impex.readImage(self.fileList[2][index])
                                self.image[:,:,z-offsets[2],self.channels[2]] = 255 - img_data3[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                        else:
                            self.image[:,:,z-offsets[2],self.channels[0]] = img_data[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                            #load other channes if needed
                            if (len(self.channels)>1):
                                img_data2 = vigra.impex.readImage(self.fileList[1][index])
                                self.image[:,:,z-offsets[2],self.channels[1]] = img_data2[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
                            if (len(self.channels)>2):
                                img_data3 = vigra.impex.readImage(self.fileList[2][index])
                                self.image[:,:,z-offsets[2],self.channels[2]] = img_data3[offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1]]
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
            self.accept()
        
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
