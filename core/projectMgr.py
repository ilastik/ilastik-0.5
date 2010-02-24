from core import dataMgr as dataMgrModule
import cPickle as pickle
import h5py
from core.utilities import irange, debug
from vigra import arraytypes as at
from PyQt4 import QtGui

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
    
    def saveToDisk(self, fileName):
        """ Save the whole project includeing data, feautues, labels and settings to 
        and hdf5 file with ending ilp """
        fileHandle = h5py.File(fileName)
        # pickle.dump(self, fileHandle, True)
        
        # get project settings
        projectG = fileHandle.create_group('Project') 
        dataSetG = fileHandle.create_group('DataSets') 

        projectG.create_dataset('Name', data=str(self.name))
        projectG.create_dataset('Labeler', data=str(self.labeler))
        projectG.create_dataset('Description', data=str(self.description))
        projectG.create_dataset('LabelNames', data=map(str,self.labelNames))
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
                predictionIt = dk.create_dataset('prediction', data=prediction.reshape(self.dataMgr[k].shape[0:2] + (-1,)))
                # predictionIt.attrs['classifier'] = 'classifierName'
            
            # save segmentation if available
            if self.dataMgr.segmentation[0] is not None:
                segmentation = self.dataMgr.segmentation[k]
                segmentationIt = dk.create_dataset('segmentation', data=segmentation)
                # segmentationIt.attrs['segmentationOperation'] = 'segmentationOperation'
                
            # save overlayImage if available
            if self.dataMgr[k].overlayImage is not None:
                overlayImage = self.dataMgr[k].overlayImage
                overlayImageIt = dk.create_dataset('overlayImage', data=overlayImage)

        dataSetG.attrs["dataKind"] = self.dataMgr[0].dataKind
        dataSetG.attrs["channelDescription"] = self.dataMgr[0].channelDescription
        dataSetG.attrs["channelUsed"] = self.dataMgr[0].channelUsed
        
        
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
        labelNames = projectG['LabelNames'].value.tolist() 
        labelColors = dict([(k+1,QtGui.QColor(projectG['LabelColors'][k])) for k in range(len(projectG['LabelColors']))])
        
        # init dataMgr 
        n = len(fileHandle['DataSets'])
        dataMgr = dataMgrModule.DataMgr([None for k in range(n)]);
                       
        # add raw data and labels to empty dataMgr                  
        for ind, dataItemValue in irange(fileHandle['DataSets'].values()):
            rawData = at.Image(dataItemValue['rawData'].value)
            labels = at.ScalarImage(dataItemValue['labels'].value)
            originalFileName = dataItemValue.attrs['fileName']
            dataMgr[ind] = dataMgrModule.DataItemImage.initFromArray(rawData, originalFileName)
            dataMgr[ind].labels = labels
            dataMgr[ind].hasLabels = True
            dataMgr[ind].channelDescription = fileHandle['DataSets'].attrs["channelDescription"]
            dataMgr[ind].channelUsed = fileHandle['DataSets'].attrs["channelUsed"]

            # extract features if available
            if 'features' in dataItemValue:
                dataFeatures = []
                for featIT in dataItemValue['features'].values():
                    feature = at.Image(featIT.value)
                    featureName = featIT.attrs['featureName']
                    channelIndex = int(featIT.attrs['channelIndex'])
                    dataFeatures.append((feature, featureName, channelIndex))
                dataMgr.dataFeatures[ind] = dataFeatures
 
            # extract prediction if available
            if 'prediction' in dataItemValue:
                prediction = dataItemValue['prediction'].value
                dataMgr.prediction[ind] = prediction.reshape((prediction.shape[0] * prediction.shape[1] , -1))
        
            # extract segmentaion if available
            if 'segmentation' in dataItemValue:
                segmentation = dataItemValue['segmentation'].value
                dataMgr.segmentation[ind] = segmentation
            
            # load OverlayImage if available
            if 'overlayImage' in dataItemValue:
                overlayImage = at.Image(dataItemValue['overlayImage'].value)
                dataMgr[ind].overlayImage = overlayImage
        
        
        fileHandle.close()
        # print "Project %s loaded from %s " % (p.name, fileName)
        return Project( name, labeler, description, dataMgr, labelNames, labelColors)
    

        
            
#    def setDataMgr(self, dataList):
#        self.dataMgr = dataMagr.dataMagr(dataList)
    