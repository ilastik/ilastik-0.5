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
from ilastik.core import ILASTIK_VERSION
import traceback

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py
from ilastik.core import dataImpex
import os.path, sys

#*******************************************************************************
# P r o j e c t                                                                *
#*******************************************************************************

class Project(object):
    """
    Import/Export for the whole project, including any data, settings, labels etc.
    """
    def __init__(self, name, labeler, description, dataMgr=None, labelNames=None, labelColors=None):
        if labelNames is None:
            labelNames = []
        if labelColors is None:
            labelColors = {}     
        self.filename = None
        self.fastRepaint = True
        self.useBorderMargin = False
        self.normalizeData = False
        self.drawUpdateInterval = 300
        self.rgbData = True
        self.name = name
        self.labeler = labeler
        self.description = description
        if dataMgr is not None:
            self.dataMgr = dataMgr
        else:
            self.dataMgr = dataMgrModule.DataMgr()
            
        self.labelNames = labelNames
        self.labelColors = labelColors
        self.trainingMatrix = None
        self.trainingLabels = None
        self.trainingFeatureNames = None
        
 
    def saveToDisk(self, fileName = None):
        """ Save the whole project including data, features, labels and settings to 
        and hdf5 file with ending ilp """
        try:
            if fileName is not None:
                self.filename = fileName
            else:
                fileName = self.filename
                
            fileHandle = h5py.File(fileName,'w')
            
            fileHandle.create_dataset('ilastikVersion', data=ILASTIK_VERSION)

            projectG = fileHandle.create_group('Project') 
            dataSetG = fileHandle.create_group('DataSets')             
            
            projectG.create_dataset('Name', data=str(self.name))
            projectG.create_dataset('Labeler', data=str(self.labeler))
            projectG.create_dataset('Description', data=str(self.description))
                
            self.dataMgr.serialize(projectG, dataSetG)
            # Save to hdf5 file
            fileHandle.close()
            
            #TODO, integrate somehow into serialization scheme
            if self.dataMgr.module["Classification"] is not None:
                self.dataMgr.module["Classification"].exportClassifiers(fileName,'Project/')
            
        except Exception as e:
            print e.message
            traceback.print_exc()
            return False
        return True
    
    @staticmethod
    def loadFromDisk(fileName, featureCache):
        fileHandle = h5py.File(fileName,'r')
        # p = pickle.load(fileHandle)
        
        # extract basic project settings
        projectG = fileHandle['Project']
        dataG = fileHandle['DataSets']
        name = projectG['Name'].value
        labeler = projectG['Labeler'].value 
        description = projectG['Description'].value
        # init dataMgr 
        
        n = len(dataG)
        
        dataMgr = dataMgrModule.DataMgr.deserialize(projectG, dataG)

        
        project = Project( name, labeler, description, dataMgr)
        project.filename = fileName
        
        fileHandle.close()
        return project
        
    def loadStack(self, path, fileList, options):
        #TODO: maybe get rid of path later on
        
        try:
            theDataItem = dataImpex.DataImpex.importDataItem(fileList, options)
        except MemoryError:
            raise MemoryError
        if theDataItem is not None:   
            # file name
            dirname = os.path.basename(os.path.dirname(path))
            offsetstr =  '(' + str(options.offsets[0]) + ', ' + str(options.offsets[1]) + ', ' + str(options.offsets[2]) + ')'
            theDataItem._name = dirname + ' ' + offsetstr
            theDataItem.fileName = path   
            try:
                self.dataMgr.append(theDataItem, True)
                self.dataMgr._dataItemsLoaded[-1] = True

                theDataItem._hasLabels = True
                theDataItem._isTraining = True
                theDataItem._isTesting = True
                
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
                raise e
        return True

    def loadFile(self, fileList, options):
        itemList = []
        try:
            itemList = dataImpex.DataImpex.importDataItems(fileList, options)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print e
            raise e
        for index, item in enumerate(itemList):
            self.dataMgr.append(item, True)
        return True
            
    def addFile(self, fileList):
        fileList = sorted(fileList)
        for file_name in fileList:
            try:
                file_name = str(file_name)
                theDataItem = dataImpex.DataImpex.importDataItem(file_name, None)
                self.dataMgr.append(theDataItem, True)
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
                raise e
        return True
    
    def removeFile(self, fileIndex):
        self.dataMgr.remove(fileIndex)
        
