from core import dataMgr
import cPickle as pickle
import h5py
from core.utilities import irange, debug

class Project(object):
    def __init__(self, name, labeler, description, dataMgr):
        self.name = name
        self.labeler = labeler
        self.description = description
        self.dataMgr = dataMgr
        self.labelNames = []
        self.labelColors = {}
        self.trainingMatrix = None
        self.trainingLabels = None
        self.trainingFeatureNames = None
    
    def saveToDisk(self, fileName):
        """ Save the whole project includeing data, feautues, labels and settings to 
        and hdf5 file with ending ilp """
        fileHandle = h5py.File(fileName)
        # pickle.dump(self, fileHandle, True)
        
        # get project settings
        projectG = fileHandle.create_group('Project') 
        dataSetG = fileHandle.create_group('DataSets') 

        projectG.create_dataset('Name', data=self.name)
        projectG.create_dataset('Labeler', data=self.labeler)
        projectG.create_dataset('Description', data=self.description)
        projectG.create_dataset('LabelNames', data=self.labelNames)
        projectG.create_dataset('LabelColors', data=[int(k.rgba()) for k in self.labelColors.values()])
        
        # get number of images
        n = len(self.dataMgr)
        
        # save raw data and labels
        for k in range(n):
            # create group for dataItem
            dk = dataSetG.create_group('dataItem%02d' % k)
            dk.attrs["fileName"] = str(self.dataMgr[k].fileName)
            # save raw data
            dataIt = dk.create_dataset('rawData', data=self.dataMgr[k].data)
            dataIt.attrs["dataKind"] = self.dataMgr[k].dataKind
            # save raw labels
            labelIt = dk.create_dataset('labels', data=self.dataMgr[k].labels)
        
            # save features if available
            if self.dataMgr.dataFeatures:
                feaureG = dk.create_group('features')
                for fCnt, (feature, featureName, channelIndex) in irange(self.dataMgr.dataFeatures[k]):
                    featureIT = feaureG.create_dataset('feature%03d' % fCnt,data=feature)
                    featureIT.attrs['featureName'] = featureName
                    featureIT.attrs['channelIndex'] = channelIndex

            # save prediction if available
            if self.dataMgr.prediction[0] is not None:
                prediction = self.dataMgr.prediction[k]
                predictionIt = dk.create_dataset('prediction',data=prediction.reshape(self.dataMgr[k].shape[0:2] + (-1,)))
                # predictionIt.attrs['classifier'] = 'classifierName'
            
            # save segmentation if available
            if self.dataMgr.segmentation[0] is not None:
                segmentation = self.dataMgr.segmentation[k]
                segmentationIt = dk.create_dataset('segmentation',data=segmentation)
                # segmentationIt.attrs['segmentationOperation'] = 'segmentationOperation'

        dataSetG.attrs["dataKind"] = self.dataMgr[0].dataKind
        
        # Save to hdf5 file
        fileHandle.close()
        print "Project %s saved to %s " % (self.name, fileName)
    
    @staticmethod
    def loadFromDisk(fileName):
        fileHandle = open(fileName,'rb')
        p = pickle.load(fileHandle)
        fileHandle.close()
        print "Project %s loaded from %s " % (p.name, fileName)
        return p
    

        
            
#    def setDataMgr(self, dataList):
#        self.dataMgr = dataMagr.dataMagr(dataList)
    