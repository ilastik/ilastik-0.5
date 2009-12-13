import numpy
import sys
from Queue import Queue as queue
from copy import copy
import os
import tables
from core.utilities import irange, debug

try:
    from vigra import vigranumpycmodule as vm, arraytypes as at
except ImportError:
    try:
        import vigranumpycmodule as vm
    except ImportError:
        sys.exit("vigranumpycmodule not found!")

class DataItemBase():
    def __init__(self, fileName):
        self.fileName = str(fileName)
        self.hasLabels = False
        self.isTraining = True
        self.isTesting = False
        self.groupMember = []
        self.projects = []
        
        self.data = None
        self.labels = []
        self.dataKind = None
        self.dataType = None
        self.dataDimensions = 0
        self.thumbnail = None
        self.shape = ()
        self.channelDescription = []
        
    def shape(self):
        if self.dataKind in ['rgb', 'multi', 'gray']:
            return self.shape[0:2]
        
    def loadData(self):
        self.data = "This is not an Image..."
    
    def unpackChannels(self):
        if self.dataKind in ['rgb']:
            return [ self.data[:,:,k] for k in range(0,3) ]
        elif self.dataKind in ['multi']:
            return [ self.data[:,:,k] for k in range(0, self.data.shape[2]) ]
        elif self.dataKind in ['gray']:
            return [ self.data ]   

class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
        self.dataDimensions = 2
       
    def loadData(self):
        fBase, fExt = os.path.splitext(self.fileName)
        if fExt == '.h5':
            self.data, self.channelDescription, self.labels = DataImpex.loadMultispectralData(self.fileName)
        else:
            self.data = DataImpex.loadImageData(self.fileName)
        #print "Shape after Loading and width",self.data.shape, self.data.width
        self.dataType = self.data.dtype
        self.shape = self.data.shape
        if len(self.data.shape) == 3:
            if self.data.shape[2] == 3:
                self.dataKind = 'rgb'
            elif self.data.shape[2] > 3:
                self.dataKind = 'multi'
        elif len(self.data.shape) == 2:
            self.dataKind = 'gray'
    
            
    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self.data = None
        
class DataItemVolume(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
       
    def loadData(self):
        self.data = vm.readVolume(self.fileName)
        self.dataDimensions = 3
        self.dataType = self.data.dtype
        if len(self.data.shape) == 4:
            if self.data.shape[3] == 3:
                self.dataKind = 'rgb'
            elif self.data.shape[3] > 3:
                self.dataKind = 'multi'
        elif len(self.data.shape) == 3:
            self.dataKind = 'gray'
            
    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self.data = None
    
        
class DataMgr():
    def __init__(self, dataItems=[]):
        self.setDataList(dataItems)
        self.dataFeatures = []
        #self.labels = [None] * len(dataItems)
        self.labels = {}
        self.prediction = [None] * len(dataItems)
        self.dataFeatures = None
        self.segmentation = [None] * len(dataItems)
        
    def setDataList(self, dataItems):
        self.dataItems = dataItems
        self.dataItemsLoaded = [False] * len(dataItems)
        self.segmentation = [None] * len(dataItems)
        
    def dataItemsShapes(self):     
        return map(DataItemBase.shape, self)
        
        
    def __getitem__(self, ind):
        if not self.dataItemsLoaded[ind]:
            self.dataItems[ind].loadData()
            self.dataItemsLoaded[ind] = True
        return self.dataItems[ind]
    
    def clearDataList(self):
        self.dataItems = []
        self.dataFeatures = []
        self.labels = [None] * len(self.dataItems)
    
    def __len__(self):
        return len(self.dataItems)
    
    def buildFeatureMatrix(self):
        self.featureMatrixList = []
        self.featureMatrixList_DataItemIndices = []    
        dataItemNr = 0
        for dataFeatures in self.dataFeatures:
            fTuple = []
            nFeatures = 0
            for features in dataFeatures:
                f = features[0]
                fSize = f.shape[0] * f.shape[1] 
                if len(f.shape) == 2:
                    f = f.reshape(fSize,1)
                else:
                    f = f.reshape(fSize,f.shape[2])    
                fTuple.append(f)
                nFeatures+=1
            if dataItemNr == 0:
                nFeatures_forFirstImage = nFeatures
            if nFeatures == nFeatures_forFirstImage:
                self.featureMatrixList.append( numpy.concatenate(fTuple,axis=1) )
                self.featureMatrixList_DataItemIndices.append(dataItemNr)
            else:
                print "generate feature matrix: nFeatures don't match for data item nr ", dataItemNr
            dataItemNr+=1
        return (self.featureMatrixList, self.featureMatrixList_DataItemIndices)
    
    def updateLabelsOfDataItems(self, labelWidget):
        """ Extract Label Information out of the label Manager and put it to the dataItems attribute"""
        for dataItemIndex, dataItem in irange(self):
            # Check for Labels
            labelArray = labelWidget.labelForImage[dataItemIndex].DrawManagers[0].labelmngr.labelArray
            dataItem.labels = labelArray.reshape(dataItem.shape[0:2])
            
    
    def export2Hdf5(self, fileName, labelWidget):
        self.updateLabelsOfDataItems(labelWidget)
        for imageIndex, dataFeatures in irange(self.dataFeatures):
            groupName = os.path.split(self[imageIndex].fileName[:-3])[-1]
            F = {}
            F_name = {}
            prefix = 'Channel'
            for feat, f_name, channel_ind in dataFeatures:
                if not F.has_key('%s%03d' % (prefix,channel_ind)):
                    F['%s%03d' % (prefix,channel_ind)] = []
                if not F_name.has_key('%s%03d' % (prefix,channel_ind)):
                    F_name['%s%03d' % (prefix,channel_ind)] = []
                
                feat.shape = feat.shape[0], feat.shape[1], 1
                F['%s%03d' % (prefix,channel_ind)].append(feat)
                F_name['%s%03d' % (prefix,channel_ind)].append(f_name)
                
            F_res = {}
            for f in F:
                F_res[f] = numpy.concatenate(F[f], axis=2)
            
            P = self.prediction[imageIndex]
            if P is not None:
                F_res['Prediction'] = P.reshape(self[imageIndex].shape[0:2] +(-1,))
            
            
            
            L = {}
            L['Labels'] = self[imageIndex].labels.T
             
                
            DataImpex.exportFeatureLabel2Hdf5(F_res, L, fileName, groupName)
        
        

class DataImpex(object):
    @staticmethod
    def loadMultispectralData(fileName):
        
        h5file = tables.openFile(fileName,'r')       
        try:
            # Data sets below root are asumed to be data, labels and featureDescriptor
            data = h5file.root.data.read()
            labels = h5file.root.labels.read()
            data = data.swapaxes(1,0)
            labels = at.ScalarImage(labels.T)
            ChannelDescription = h5file.root.featureDescriptor.read()
            ChannelDescription = map(str,ChannelDescription[:,0])
        except Exception as e:
            print "Error while reading H5 File %s " % fileName
            print e
        finally:
            h5file.close()
        return (data.astype(numpy.float32), ChannelDescription, labels.astype(numpy.uint32))
    
    @staticmethod
    def loadImageData(fileName):
        data = vm.readImage(fileName)
        #data = data.swapaxes(0,1)
        return data
    
    @staticmethod    
    def _exportFeatureLabel2Hdf5(features, labels, h5file, h5group):
        try:
            h5group = h5file.createGroup(h5file.root, h5group, 'Some Title')
        except tables.NodeError as ne:
            print ne
            print "_exportFeatureLabel2Hdf5: Overwriting"
            h5file.removeNode(h5file.root, h5group, recursive=True)
            h5group = h5file.createGroup(h5file.root, h5group, 'Some Title')
        
        cnt = 0
        for key in features:
            val = features[key]    
            tmp = h5file.createArray(h5group, key, val, "Description")
            
            tmp._v_attrs.order = cnt
            tmp._v_attrs.type = 'INPUT'
            tmp._v_attrs.scale = 'ORDINAL'
            tmp._v_attrs.domain = 'REAL'
            tmp._v_attrs.dimension = 2
            tmp._v_attrs.missing_label = 0
            cnt += 1
        
        for key in labels:
            val = labels[key]
                
            tmp = h5file.createArray(h5group, key, val, "Description")
            
            tmp._v_attrs.order = cnt
            tmp._v_attrs.type= 'OUTPUT'
            tmp._v_attrs.scale = 'NOMINAL'
            tmp._v_attrs.domain = numpy.array(range(int(val.max())+1))
            tmp._v_attrs.dimension = 2
            tmp._v_attrs.missing_label = 0
            cnt += 1    
            
    @staticmethod
    def exportFeatureLabel2Hdf5(features, labels, hFilename, h5group):
        if os.path.isfile(hFilename):
            mode = 'a'
        else:
            mode = 'w'
        h5file = tables.openFile(hFilename, mode = mode, title = "Ilastik File Version")
        
        try:
            DataImpex._exportFeatureLabel2Hdf5(features, labels, h5file, h5group)
        except Exception as e:
            print e
        finally:
            h5file.close() 
    
    @staticmethod
    def checkForLabels(fileName):
        fileName = str(fileName)
        fBase, fExt = os.path.splitext(fileName)
        if fExt != '.h5':
            return 0
        
        h5file = tables.openFile(fileName,'r')       
        try:
            # Data sets below root are asumed to be data, labels and featureDescriptor
            if hasattr(h5file.root,'labels'):
                res = 1
            else:
                res = 0
        except Exception as e:
            print "Error while reading H5 File %s " % fileName
            print e
        finally:
            h5file.close()
        return res
        
        
        
        
        

                    
                    
                    
                
        
        


        
