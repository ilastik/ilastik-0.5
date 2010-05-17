from core import dataMgr as dataMgrModule
import cPickle as pickle
import h5py
from core.utilities import irange, debug

from vigra import arraytypes as at
from PyQt4 import QtGui

from gui.volumeeditor import DataAccessor as DataAccessor
from gui.volumeeditor import Volume as Volume

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
            item = dataMgrModule.DataItemImage(fileHandle['DataSets'][name].attrs['Name'])
            item.dataVol = dataVol
            dataMgr.append(item,alreadyLoaded=True)
        # DataImpex.loadVolumeFromGroup(grp)

               
        fileHandle.close()
        # print "Project %s loaded from %s " % (p.name, fileName)
        return Project( name, labeler, description, dataMgr)
    
