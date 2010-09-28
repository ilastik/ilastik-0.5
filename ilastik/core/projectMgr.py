#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

from ilastik.core import dataMgr as dataMgrModule
import numpy
import cPickle as pickle
import h5py
from ilastik.core.utilities import irange, debug
from ilastik.core.overlayMgr import OverlayItem

from vigra import arraytypes as at
from PyQt4 import QtGui

from ilastik.core.volume import DataAccessor,  Volume

from ilastik.core import activeLearning
from ilastik.core import segmentationMgr
from ilastik.core import classifiers
from ilastik.core.modules.Classification import labelMgr, featureMgr, classificationMgr
from ilastik.core import seedMgr
from ilastik.core import objectMgr
from ilastik.core.modules.Classification import classificationMgr
from ilastik.core import backgroundMgr
from ilastik.core import overlayMgr 
from ilastik.core import connectedComponents

from ilastik import core 

ILASTIK_VERSION = 0.5



class Project(object):
    """
    Import/Export for the whole project, including any data, settings, lables etc.
    """
    def __init__(self, name, labeler, description, dataMgr, labelNames=None, labelColors=None):
        if labelNames is None:
            labelNames = []
        if labelColors is None:
            labelColors = {}     
        self.filename = None
        self.useBorderMargin = False
        self.normalizeData = False
        self.drawUpdateInterval = 300
        self.rgbData = True
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataMgr = dataMgr
        self.labelNames = labelNames
        self.labelColors = labelColors
        self.trainingMatrix = None
        self.trainingLabels = None
        self.trainingFeatureNames = None
        self.featureMgr = featureMgr.FeatureMgr(self.dataMgr)
        
        
        classificationMgr.ClassificationModuleMgr(self.dataMgr, self.featureMgr)
            
        self.classificationMgr = self.dataMgr.properties["Classification"]["classificationMgr"]
        
        self.labelMgr = labelMgr.LabelMgr(self.dataMgr, self.classificationMgr)
        self.seedMgr = seedMgr.SeedMgr(self.dataMgr)
        self.objectMgr = objectMgr.ObjectMgr(self.dataMgr)
        self.backgroundMgr = backgroundMgr.BackgroundMgr(self.dataMgr)
        self.classifier = classifiers.classifierRandomForest.ClassifierRandomForest
        self.segmentor = core.segmentors.segmentorClasses[0]()
        self.connector = connectedComponents.ConnectedComponents()
 
    def saveToDisk(self, fileName = None):
        """ Save the whole project includeing data, feautues, labels and settings to 
        and hdf5 file with ending ilp """
        try:
            if fileName is not None:
                self.filename = fileName
            else:
                fileName = self.filename
                
            fileHandle = h5py.File(fileName,'w')
            
            fileHandle.create_dataset('IlastikVersion', data=ILASTIK_VERSION)
            
            # get project settings
            projectG = fileHandle.create_group('Project') 
            dataSetG = fileHandle.create_group('DataSets') 
    
            projectG.create_dataset('Name', data=str(self.name))
            projectG.create_dataset('Labeler', data=str(self.labeler))
            projectG.create_dataset('Description', data=str(self.description))
                
            featureG = projectG.create_group('FeatureSelection')
            
            try:
                self.featureMgr.exportFeatureItems(featureG)
            except:
                print 'saveToDisk(): No features where selected: '
                
                
            # get number of images
            
            # save raw data and labels
            for k, item in enumerate(self.dataMgr):
                # create group for dataItem
                dk = dataSetG.create_group('dataItem%02d' % k)
                dk.attrs["fileName"] = str(item.fileName)
                dk.attrs["_name"] = str(item._name)
                # save raw data
                item._dataVol.serialize(dk)
                if item._prediction is not None:
                    item._prediction.serialize(dk, '_prediction' )
    
    
            # Save to hdf5 file
            fileHandle.close()
            self.dataMgr.exportClassifiers(fileName,'Project/')
        except:
            return False
        
        return True
    
    @staticmethod
    def loadFromDisk(fileName, featureCache):
        fileHandle = h5py.File(fileName,'r')
        # p = pickle.load(fileHandle)
        
        # extract basic project settings
        projectG = fileHandle['Project']
        name = projectG['Name'].value
        labeler = projectG['Labeler'].value 
        description = projectG['Description'].value
        # init dataMgr 
        
        n = len(fileHandle['DataSets'])
        dataMgr = dataMgrModule.DataMgr(featureCache);
        
        for name in fileHandle['DataSets']:
            activeItem = dataMgrModule.DataItemImage(fileHandle['DataSets'][name].attrs['Name'])
            activeItem.deserialize(fileHandle['DataSets'][name])
            #dataVol = Volume.deserialize(activeItem, fileHandle['DataSets'][name])
            #activeItem._dataVol = dataVol
            activeItem.fileName = fileHandle['DataSets'][name].attrs['fileName']

            activeItem.updateOverlays()
                            
            dataMgr.append(activeItem,alreadyLoaded=True)

               
        fileHandle.close()
        
        
        project = Project( name, labeler, description, dataMgr)
        project.filename = fileName
        # print "Project %s loaded from %s " % (p.name, fileName)
        return project

    def deleteFeatureOverlays(self):
        for index2,  di in enumerate(self.dataMgr):
            keys = di.overlayMgr.keys()
            for k in keys:
                if k.startswith("Classification/Features/"):
                    di.overlayMgr.remove(k)
    
    
    def createFeatureOverlays(self):
        for index,  feature in enumerate(self.featureMgr.featureItems):
            offset = self.featureMgr.featureOffsets[index]
            size = self.featureMgr.featureSizes[index]

            for index2,  di in enumerate(self.dataMgr):
                #create Feature Overlays
                for c in range(0,size):
                    rawdata = di.properties["Classification"]["featureM"][:, :, :, :, offset+c:offset+c+1]
                    #TODO: the min/max stuff here is slow !!!
                    #parallelize ??
                    min = numpy.min(rawdata)
                    max = numpy.max(rawdata)
                    data = DataAccessor(rawdata,  channels = True,  autoRgb = False)
                    
                    ov = OverlayItem(data, color = QtGui.QColor(255, 0, 0), alpha = 1.0,  autoAdd = False, autoVisible = False)
                    ov.min = min
                    ov.max = max
                    di.overlayMgr[ feature.getKey(c)] = ov
        
  

