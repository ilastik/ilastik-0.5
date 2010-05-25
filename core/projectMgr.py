from core import dataMgr as dataMgrModule
import numpy
import cPickle as pickle
import h5py
from core.utilities import irange, debug

from vigra import arraytypes as at
from PyQt4 import QtGui

from gui.volumeeditor import DataAccessor as DataAccessor
from gui.volumeeditor import Volume as Volume

from core import activeLearning
from core import segmentationMgr

class Project(object):
    """
    Import/Export for the whole project, including any data, settings, lables etc.
    """
    def __init__(self, name, labeler, description, dataMgr, labelNames=None, labelColors=None):
        if labelNames is None:
            labelNames = []
        if labelColors is None:
            labelColors = {}     
            
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataMgr = dataMgr
        self.labelNames = labelNames
        self.labelColors = labelColors
        self.trainingMatrix = None
        self.trainingLabels = None
        self.trainingFeatureNames = None
        self.featureMgr = None
    
    def saveToDisk(self, fileName):
        """ Save the whole project includeing data, feautues, labels and settings to 
        and hdf5 file with ending ilp """
        fileHandle = h5py.File(fileName,'w')
        # pickle.dump(self, fileHandle, True)
        
        # get project settings
        projectG = fileHandle.create_group('Project') 
        dataSetG = fileHandle.create_group('DataSets') 

        projectG.create_dataset('Name', data=str(self.name))
        projectG.create_dataset('Labeler', data=str(self.labeler))
        projectG.create_dataset('Description', data=str(self.description))
                
        # get number of images
        n = len(self.dataMgr)
        
        # save raw data and labels
        for k, item in enumerate(self.dataMgr):
            # create group for dataItem
            dk = dataSetG.create_group('dataItem%02d' % k)
            dk.attrs["fileName"] = str(item.fileName)
            dk.attrs["Name"] = str(item.Name)
            # save raw data
            item.dataVol.serialize(dk)
            if item.prediction is not None:
                item.prediction.serialize(dk, 'prediction' )
            
        
        
        # Save to hdf5 file
        fileHandle.close()
        print "Project %s saved to %s " % (self.name, fileName)
    
    @staticmethod
    def loadFromDisk(fileName):
        fileHandle = h5py.File(fileName,'r')
        # p = pickle.load(fileHandle)
        
        # extract basic project settings
        projectG = fileHandle['Project']
        name = projectG['Name'].value
        labeler = projectG['Labeler'].value 
        description = projectG['Description'].value
        # init dataMgr 
        
        n = len(fileHandle['DataSets'])
        dataMgr = dataMgrModule.DataMgr();
        
        for name in fileHandle['DataSets']:
            dataVol = Volume.deserialize(fileHandle['DataSets'][name])
            activeItem = dataMgrModule.DataItemImage(fileHandle['DataSets'][name].attrs['Name'])
            activeItem.dataVol = dataVol
            if 'prediction' in fileHandle['DataSets'][name].keys():
                prediction = DataAccessor.deserialize(fileHandle['DataSets'][name], 'prediction' )
                activeItem.prediction = prediction
                for p_i, item in enumerate(activeItem.dataVol.labels.descriptions):
                    item.prediction = (activeItem.prediction[:,:,:,:,p_i] * 255).astype(numpy.uint8)
    
                margin = activeLearning.computeEnsembleMargin(activeItem.prediction[:,:,:,:,:])*255.0
                activeItem.dataVol.uncertainty = margin[:,:,:,:]
                seg = segmentationMgr.LocallyDominantSegmentation(activeItem.prediction[:,:,:,:,:], 1.0)
                activeItem.dataVol.segmentation = seg[:,:,:,:]

            dataMgr.append(activeItem,alreadyLoaded=True)

               
        fileHandle.close()
        # print "Project %s loaded from %s " % (p.name, fileName)
        return Project( name, labeler, description, dataMgr)
    
