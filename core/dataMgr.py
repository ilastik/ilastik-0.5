# -*- coding: utf-8 -*-
import numpy
import sys
from Queue import Queue as queue
from copy import copy
import os
import threading
import h5py
import h5py as tables # TODO: exchange tables with h5py
from core.utilities import irange, debug, irangeIfTrue

from gui.volumeeditor import DataAccessor as DataAccessor
from gui.volumeeditor import Volume as Volume

import vigra
at = vigra.arraytypes
    

class DataItemBase():
    """
    Data Base class, serves as an interface for the specialized data structures, e.g. images, multispectral, volume etc.  
    """
    #3D: important
    def __init__(self, fileName):
        self.fileName = str(fileName)
        self.Name = os.path.split(self.fileName)[1]
        self.hasLabels = False
        self.isTraining = True
        self.isTesting = False
        self.groupMember = []
        self.projects = []
        
        self.data = None
        self.labels = None
        self.dataKind = None
        self.dataType = []
        self.dataDimensions = 0
        self.thumbnail = None
        self.shape = ()
        self.channelDescription = []
        self.channelUsed = []
        
    def shape(self):
        if self.dataKind in ['rgb', 'multi', 'gray']:
            return self.shape[0:2]
        
    def loadData(self):
        self.data = "This is not an Image..."
    
    def unpackChannels(self):
        if self.dataKind in ['rgb']:
            return [ self.data[:,:,k] for k in range(0,3) ]
        elif self.dataKind in ['multi']:
            return [ self.data[:,:,k] for k in irangeIfTrue(self.channelUsed)]
        elif self.dataKind in ['gray']:
            return [ self.data ]   

class DataItemImage(DataItemBase):
    def __init__(self, fileName):
        DataItemBase.__init__(self, fileName) 
        self.dataDimensions = 2
        self.overlayImage = None
        self.dataVol = None
        self.prediction = None
        self.trainingF = None        
        self.featureM = None
        self.features = [] #features is an array of arrays of arrays etc. like this
                           #feature, channel, time
        
    def loadData(self):
        fBase, fExt = os.path.splitext(self.fileName)
        if fExt == '.oldh5':
            self.data, self.channelDescription, self.labels, self.overlayImage = DataImpex.loadMultispectralData(self.fileName)
        elif fExt == '.h5':
            self.dataVol = DataImpex.loadVolume(self.fileName)  
        else:
            self.data = DataImpex.loadImageData(self.fileName)
            self.labels = None
        #print "Shape after Loading and width",self.data.shape, self.data.width
        if self.dataVol is None:
            dataAcc = DataAccessor(self.data)
            self.dataVol = Volume()
            self.dataVol.data = dataAcc
            self.dataVol.labels = self.labels
        
   
    @classmethod
    def initFromArray(cls, dataArray, originalFileName):
        obj = cls(originalFileName)
        obj.data = dataArray
        obj.extractDataAttributes()
        return obj
        
    def getTrainingMatrixRef(self):
        #TODO: time behaviour should be discussed !
        #also adapt feature computation when doing this(4D??)!
        if self.trainingF is None:
            tempF = []
            tempL = []
    
            tempd =  self.dataVol.labels.data[0, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = self.dataVol.labels.data[0,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                        
            for i_f, it_f in enumerate(self.features): #features
                for i_c, it_c in enumerate(it_f): #channels
                    for i_t, it_t in enumerate(it_c): #time
                        t = it_t.reshape((numpy.prod(it_t.shape[0:3]),it_t.shape[3]))
                        tempF.append(t[indices, :])
            
            self.trainingIndices = indices
            self.trainingL = tempL
            if len(tempF) > 0:
                self.trainingF = numpy.hstack(tempF)
            else:
                self.trainingF = None
        return self.trainingL, self.trainingF, self.trainingIndices
    
    def getTrainingMatrix(self):
        self.getTrainingMatrixRef()
        if self.trainingF is not None:
            return self.trainingL, self.trainingF, self.trainingIndices
        else:
            return None, None, None
            
    def updateTrainingMatrix(self, newLabels):
        #TODO: this method is crazy, make it less crazy
        for nl in newLabels:
            if nl.erasing == False:
                indic =  list(numpy.nonzero(nl.data))
                indic[0] = indic[0] + nl.offsets[0]
                indic[1] += nl.offsets[1]
                indic[2] += nl.offsets[2]
                indic[3] += nl.offsets[3]
                indic[4] += nl.offsets[4]
                
                loopc = 2
                count = 1
                indices = indic[-loopc]*count
                templ = list(self.dataVol.data.shape[1:-1])
                templ.reverse()
                for s in templ:
                    loopc += 1
                    count *= s
                    indices += indic[-loopc]*count
                
                mask = numpy.in1d(self.trainingIndices,indices)
                nonzero = numpy.nonzero(mask)[0]
                if len(nonzero) > 0:
                    self.trainingIndices = numpy.concatenate((numpy.delete(self.trainingIndices,nonzero),indices))
                    tempI = numpy.nonzero(nl.data)
                    tempL = nl.data[tempI]
                    tempL.shape += (1,)
                    temp2 = numpy.delete(self.trainingL,nonzero)
                    temp2.shape += (1,)
                    self.trainingL = numpy.vstack((temp2,tempL))
                    fm = self.getFeatureMatrix()
                    if fm is not None:
                        temp2 = numpy.delete(self.trainingF,nonzero, axis = 0)
                        if len(temp2.shape) == 1:
                            temp2.shape += (1,)
                            fm.shape += (1,)
                        self.trainingF = numpy.vstack((temp2,fm[indices,:]))
                else: #no intersection, just add everything...
                    self.trainingIndices = numpy.hstack((self.trainingIndices,indices))
                    tempI = numpy.nonzero(nl.data)
                    tempL = nl.data[tempI]
                    tempL.shape += (1,)
                    temp2 = self.trainingL
                    self.trainingL = numpy.vstack((temp2,tempL))
                    fm = self.getFeatureMatrix()
                    if fm is not None:
                        temp2 = self.trainingF
                        if len(temp2.shape) == 1:
                            temp2.shape += (1,)
                            fm.shape += (1,)
                        self.trainingF = numpy.vstack((temp2,fm[indices,:]))
            else: #erasing == True
                indic =  list(numpy.nonzero(nl.data))
                indic[0] = indic[0] + nl.offsets[0]
                indic[1] += nl.offsets[1]
                indic[2] += nl.offsets[2]
                indic[3] += nl.offsets[3]
                indic[4] += nl.offsets[4]
                
                loopc = 2
                count = 1
                indices = indic[-loopc]*count
                templ = list(self.dataVol.data.shape[1:-1])
                templ.reverse()
                for s in templ:
                    loopc += 1
                    count *= s
                    indices += indic[-loopc]*count
                
                mask = numpy.in1d(self.trainingIndices,indices) #get intersection
                nonzero = numpy.nonzero(mask)[0]
                if len(nonzero) > 0:
                    self.trainingIndices = numpy.delete(self.trainingIndices,nonzero)
                    self.trainingL  = numpy.delete(self.trainingL,nonzero)
                    self.trainingL.shape += (1,) #needed because numpy.delete is stupid
                    self.trainingF = numpy.delete(self.trainingF,nonzero, axis = 0)
                else: #no intersectoin, in erase mode just pass
                    pass             

            
    def getFeatureMatrixRef(self):
        if self.featureM is None:
            tempM = []
            for i_f, it_f in enumerate(self.features): #features
               for i_c, it_c in enumerate(it_f): #channels
                   for i_t, it_t in enumerate(it_c): #time
                       tempM.append(it_t.reshape(numpy.prod(it_t.shape[0:3]),it_t.shape[3]))

            if len(tempM) > 0:
                self.featureM = numpy.hstack(tempM)
            else:
                self.featureM = None
        return self.featureM      
    
    def getFeatureMatrix(self):
        self.getFeatureMatrixRef()
        if self.featureM is not None:
            return self.featureM
        else:
            return None
        
    def clearFeaturesAndTraining(self):
        self.trainingF = None
        self.trainingL = None
        self.featureM = None
        self.trainingIndices = None
                
    def getFeatureMatrixForViewState(self, vs):
        tempM = []
        for i_f, it_f in enumerate(self.features): #features
           for i_c, it_c in enumerate(it_f): #channels
               for i_t, it_t in enumerate(it_c): #time
                   ttt = []
                   ttt.append(it_t[vs[1],:,:,:].reshape(numpy.prod(it_t.shape[1:3]),it_t.shape[3]))
                   ttt.append(it_t[:,vs[2],:,:].reshape(numpy.prod((it_t.shape[0],it_t.shape[2])),it_t.shape[3]))
                   ttt.append(it_t[:,:,vs[3],:].reshape(numpy.prod(it_t.shape[0:2]),it_t.shape[3]))
                   tempM.append(numpy.vstack(ttt))   

                       
        if len(tempM) > 0:
            featureM = numpy.hstack(tempM)
        else:
            featureM = None
        return featureM              
            
    def unLoadData(self):
        # TODO: delete permanently here for better garbage collection
        self.data = None
        
     
    def serialize(self, h5G):
        self.dataVol.serialize(h5G)
class DataMgr():
    """
    Manages Project structure and associated files, e.g. images volumedata
    """
    #TODO: does not unload data, maybe implement some sort of reference counting if memory scarceness manifests itself
    
    def __init__(self, dataItems=None):
        if dataItems is None:
            dataItems = []            
        self.setDataList(dataItems)
        self.dataFeatures = [None] * len(dataItems)
        self.prediction = [None] * len(dataItems)
        self.segmentation = [None] * len(dataItems)
        self.labels = {}
        self.classifiers = []
        self.featureLock = threading.Semaphore(1) #prevent chaning of activeImage during thread stuff
        
    def setDataList(self, dataItems):
        self.dataItems = dataItems
        self.dataItemsLoaded = [False] * len(dataItems)
        self.segmentation = [None] * len(dataItems)
        self.prediction = [None] * len(dataItems)
        self.uncertainty = [None] * len(dataItems)
        
    def append(self, dataItem):
        self.dataItems.append(dataItem)
        self.dataItemsLoaded.append(False)
        self.segmentation.append(None)
        self.prediction.append(None)
        self.uncertainty.append(None)
        
    
    def buildTrainingMatrix(self):
        trainingF = []
        trainingL = []
        indices = []
        for item in self:
            trainingLabels, trainingFeatures, indic = item.getTrainingMatrixRef()
            if trainingFeatures is not None:
                indices.append(indic)
                trainingL.append(trainingLabels)
                trainingF.append(trainingFeatures)
            
        self.trainingL = trainingL
        self.trainingF = trainingF
        self.trainingIndices = indices     
    
    def getTrainingMatrix(self):
        self.buildTrainingMatrix()
        
        if len(self.trainingF) > 0:
            trainingF = numpy.vstack(self.trainingF)
            trainingL = numpy.vstack(self.trainingL)
        
            return trainingF, trainingL
        else:
            print "######### empty Training Matrix ##########"
            return None, None
        
    
    def updateTrainingMatrix(self, num, newLabels):
        if self.trainingF is None:
            self.buildTrainingMatrix()        
        self[num].updateTrainingMatrix(newLabels)



    def buildFeatureMatrix(self):
        for item in self:
            item.getFeatureMatrix()
                    
    def clearFeaturesAndTraining(self):
        self.trainingF = None
        self.trainingL = None
        self.trainingIndices = None
        
        for index, item in enumerate(self):
            item.clearFeaturesAndTraining()
    
    def getDataList(self):
        return self.dataItems
        
    def dataItemsShapes(self):     
        return map(DataItemBase.shape, self)
        
        
    def __getitem__(self, ind):
        if not self.dataItemsLoaded[ind]:
            self.dataItems[ind].loadData()
            self.dataItemsLoaded[ind] = True
        return self.dataItems[ind]
    
    def __setitem__(self, ind, val):
        self.dataItems[ind] = val
        self.dataItemsLoaded[ind] = True
    
    def getIndexFromFileName(self, fileName):
        for k, dataItem in irange(self.dataItems):
            if fileName == dataItem.fileName:
                return k
        return False
    
    def remove(self, dataItemIndex):
        del self.dataItems[dataItemIndex]
        del self.dataItemsLoaded[dataItemIndex]
        del self.segmentation[dataItemIndex]
        del self.prediction[dataItemIndex]
        del self.uncertainty[dataItemIndex]
    
    def clearDataList(self):
        self.dataItems = []
        self.dataFeatures = []
        self.labels = {}
    
    def __len__(self):
        return len(self.dataItems)
    
    def export2Hdf5(self, fileName):
        for imageIndex, dataFeatures in irange(self.dataFeatures):
            groupName = os.path.split(self[imageIndex].fileName)[-1]
            groupName, dummy = os.path.splitext(groupName)
            F = {}
            F_name = {}
            prefix = 'Channel'
            for feat, f_name, channel_ind in dataFeatures:
                if not F.has_key('%s%03d' % (prefix,channel_ind)):
                    F['%s%03d' % (prefix,channel_ind)] = []
                if not F_name.has_key('%s%03d' % (prefix,channel_ind)):
                    F_name['%s%03d' % (prefix,channel_ind)] = []
                
                if len(feat.shape) == 2:
                    feat.shape = feat.shape +  (1,)
                    
                F['%s%03d' % (prefix,channel_ind)].append(feat)
                F_name['%s%03d' % (prefix,channel_ind)].append(f_name)
                
            F_res = {}
            for f in F:
                F_res[f] = numpy.concatenate(F[f], axis=2)
            
            P = self.prediction[imageIndex]
            if P is not None:
                F_res['Prediction'] = P.reshape(self[imageIndex].shape[0:2] +(-1,))
            
            
            
            L = {}
            L['Labels'] = self[imageIndex].labels
             
                
            DataImpex.exportFeatureLabel2Hdf5(F_res, L, fileName, groupName)
            print "Object saved to disk: %s" % fileName
        
        

class DataImpex(object):
    """
    Data Import/Export class 
    """
    
    @staticmethod
    def loadVolume(fileName):
        h5file = h5py.File(fileName, 'r')
        grp = h5file['volume']
        return Volume.deserialize(grp)
        
    
    @staticmethod
    def loadMultispectralData(fileName):
        h5file = h5py.File(fileName,'r')       
        try:
            if 'data' in h5file.listnames():
                data = at.Image(h5file['data'].value, at.float32)
            else:
                print 'No "data"-field contained in: %s ' % fileName
                return -1
            
            if 'labels' in h5file.listnames():
                labels = at.ScalarImage(h5file['labels'].value, at.uint8)
            else:
                print 'No "labels"-field contained in: %s ' % fileName
                labels = at.ScalarImage(data.shape[0:2], at.uint8)
            
            if 'channelNames' in h5file.listnames():
                channelNames = h5file['channelNames'].value
                channelNames = map(str,channelNames[:,0])
            else:
                print 'No "channelNames"-field contained in: %s ' % fileName
                channelNames = map(str, range(data.shape[2]))
            if 'overlayImage' in h5file.listnames():
                overlayImage = at.Image(h5file['overlayImage'].value)
            else:
                print 'No "overlayImage"-field contained in: %s ' % fileName
                overlayImage = None
                               
        except Exception as e:
            print "Error while reading H5 File %s " % fileName
            print e
        finally:
            h5file.close()
            
        return (data, channelNames, labels, overlayImage)
    
    @staticmethod
    def loadImageData(fileName):
        # I have to do a cast to at.Image which is useless in here, BUT, when i py2exe it,
        # the result of vigra.impex.readImage is numpy.ndarray? I don't know why... (see featureMgr compute)
        data = vigra.impex.readImage(fileName).swapaxes(0,1).view(numpy.ndarray)
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
            #print val.flags
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
            print val.flags
            print '***************'
            val = val.T
            print val.flags
            tmp = h5file.createArray(h5group, key  , val.T,  "Description")
            
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
               
        h5file = h5py.File(fileName,'r')       
        try:
            # Data sets below root are asumed to be data, labels and featureDescriptor
            if 'labels' in h5file.listnames():
                labels = h5file['labels'].value
                res = len(numpy.unique(labels)) - 1
                del labels
            else:
                res = 0
        except Exception as e:
            print "Error while reading H5 File %s " % fileName
            print e
        finally:
            h5file.close()
        return res
    
class channelMgr(object):
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr
        self.compoundChannels = {'rgb':{},'gray':{},'multi':{}}
        
        self.registerCompoundChannels('rgb', 'TrueColor', self.compoundSelectChannelFunctor, [0,1,2]) 
        self.registerCompoundChannels('gray', 'Intensities', self.compoundSelectChannelFunctor, [0,1,2])
        self.registerCompoundChannels('multi', 'Channel:', self.compoundSelectChannelFunctor, 0)
        
    def channelConcatenation(self, dataInd, channelList):
        if self.dataMgr[dataInd].dataKind == 'gray':
            res = self.dataMgr[dataInd].data
        else:
            res = self.dataMgr[dataInd].data[:,:, channelList]
        return res
    
    def getDefaultDisplayImage(self, dataInd):
        if self.dataMgr[dataInd].dataKind == 'gray':
            res = channelConcatenation(self, dataInd, channelList)
        elif self.dataMgr[dataInd].dataKind == 'rgb':
            res = channelConcatenation(self, dataInd, [0,1,2])
        elif self.dataMgr[dataInd].dataKind == 'multi':
            res = channelConcatenation(self, dataInd, [0]) 
        return res 
    
    def registerCompoundChannels(self, dataKind, compoundName, compundFunctor, compundArg):
        self.compoundChannels[dataKind][compoundName] = lambda x,compundArg=compundArg:compundFunctor(x, compundArg)
    
    def compoundSelectChannelFunctor(self, data, selectionList):
        if data.ndim == 3:
            return data[:,:,selectionList]
        else:
            return data
        
        
        
        
    
    
        
        
        
        
        

                    
                    
                    
                
        
        


        
