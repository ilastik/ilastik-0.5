#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

import numpy
import threading 
import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import h5py

from collections import deque

try:
    from PyQt4.QtCore import QThread, SIGNAL
    from PyQt4.QtGui import QColor
    ThreadBase = QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False
    

from ilastik.core import dataMgr as DM
from ilastik.core import activeLearning

from ilastik.core.volume import DataAccessor as DataAccessor, VolumeLabelDescriptionMgr, VolumeLabels
from ilastik.core import jobMachine
from ilastik.core import overlayMgr
import sys, traceback
import classifiers.classifierRandomForest as defaultRF
from ilastik.core.dataMgr import BlockAccessor
from ilastik.core.baseModuleMgr import BaseModuleDataItemMgr, BaseModuleMgr

import featureMgr
import labelMgr

import classifiers

""" Import all classification plugins"""
pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/classifiers')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/othesr files.
            module = __import__('ilastik.modules.classification.core.classifiers.' + module_name)
except Exception, e:
    print e
    traceback.print_exc()
    pass

for i, c in enumerate(classifiers.classifierBase.ClassifierBase.__subclasses__()):
    print "Loaded classifier:", c.name


def interactiveMessagePrint(* args):
    pass
    #print "Thread: ", args[0]

try:
    import vigra
    import vigra.learning
except ImportError:
    sys.exit("vigra module not found!")


def unravelIndices(indices, shape):
    if len(indices.shape) == 1:
        indices.shape = indices.shape + (1,)
    try:
        ti =  numpy.apply_along_axis(numpy.unravel_index, 1, indices , shape)
    except Exception, e:
        print e
        print indices
        print shape
    return ti    


def setintersectionmask(a,b):
    if int(numpy.__version__.split('.')[1])>= 4:
        return numpy.in1d(a,b, assume_unique=True)
    else:
        return numpy.intersect1d(a,b)

#*******************************************************************************
# C l a s s i f i c a t i o n I t e m M o d u l e M g r                        *
#*******************************************************************************

class ClassificationItemModuleMgr(BaseModuleDataItemMgr):
    name = "Classification"
    
    def __init__(self, dataItemImage):
        BaseModuleDataItemMgr.__init__(self, dataItemImage)
        self.dataItemImage = dataItemImage
        self.classificationModuleMgr = None
        
    def setModuleMgr(self, classificationModuleMgr):
        self.classificationModuleMgr = classificationModuleMgr
    
    
    def serialize(self, h5g, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        #for now save the labels and prediction in the old format
        #TODO: change that when we are certain about the new project file format
        vl = VolumeLabels(self.dataItemImage.overlayMgr["Classification/Labels"]._data)
        vl.descriptions = self.classificationModuleMgr.dataMgr.module["Classification"]["labelDescriptions"]
        vl.serialize(h5g, "labels", destbegin, destend, srcbegin, srcend, destshape)

        if len(vl.descriptions) > 0:
            prediction = numpy.zeros(self.dataItemImage.shape[0:-1] + (len(vl.descriptions),), 'float32')
            for d in vl.descriptions:
                if self.dataItemImage.overlayMgr["Classification/Prediction/" + d.name] is not None:
                    prediction[:,:,:,:,d.number-1] = self.dataItemImage.overlayMgr["Classification/Prediction/" + d.name][:,:,:,:,0]
            prediction = DataAccessor(prediction)
            prediction.serialize(h5g, 'prediction', destbegin, destend, srcbegin, srcend, destshape )
        
    def deserialize(self, h5G, offsets = (0,0,0), shape = (0,0,0)):
        labels = VolumeLabels.deserialize(h5G, "labels",offsets, shape)
        self["labels"] = labels
        if 'prediction' in h5G.keys():
            self["prediction"] = DataAccessor.deserialize(h5G, 'prediction', offsets, shape)
        


#*******************************************************************************
# C l a s s i f i c a t i o n M o d u l e M g r                                *
#*******************************************************************************

class ClassificationModuleMgr(BaseModuleMgr):
    name = "Classification"
    
    def __init__(self, dataMgr):
        BaseModuleMgr.__init__(self, dataMgr)
        self.dataMgr = dataMgr
        
        self.featureMgr = featureMgr
        self.classifier = classifiers.classifierRandomForest.ClassifierRandomForest
        if self.dataMgr.module["Classification"] is None:
            self.dataMgr.module["Classification"] = self
        self.classificationMgr = self["classificationMgr"] = ClassificationMgr(self.dataMgr)
        
        if self.dataMgr.module["Classification"]["labelDescriptions"] is None:
            self.dataMgr.module["Classification"]["labelDescriptions"] = VolumeLabelDescriptionMgr()

        for i, im in enumerate(self.dataMgr):
            self.onNewImage(im)
        
        self.labelMgr = labelMgr.LabelMgr(self.dataMgr, self.classificationMgr)      
        self.featureMgr = featureMgr.FeatureMgr(self.dataMgr)

        self.classificationMgr.clearFeaturesAndTraining()
                    
    def onNewImage(self, dataItemImage):
        dataItemImage.Classification.setModuleMgr(self)
        
        #create featureM
        dataItemImage.module["Classification"]["featureM"] = numpy.zeros(dataItemImage.shape[0:-1] + (self.featureMgr.totalFeatureSize,),'float32')
        
        #clear features and training
        self.classificationMgr.clearFeaturesAndTrainingForImage(dataItemImage)
        
        #handle obsolete file formats:
        if dataItemImage.Classification["labels"] is not None:
            labels = dataItemImage.Classification["labels"]
            ov = overlayMgr.OverlayItem(labels._data, alpha = 1.0, colorTable = labels.getColorTab(), autoAdd = True, autoVisible = True, autoAlphaChannel = False, linkColorTable = True)
            dataItemImage.overlayMgr["Classification/Labels"] = ov
            if len(self.dataMgr.module["Classification"]["labelDescriptions"]) == 0: 
                for d in labels.descriptions:
                    self.dataMgr.module["Classification"]["labelDescriptions"].append(d)
            dataItemImage.Classification["labels"]  = None     


        #create LabelOverlay
        if dataItemImage.overlayMgr["Classification/Labels"] is None:
            data = numpy.zeros(dataItemImage.shape[0:-1]+(1,),'uint8')
            ov = overlayMgr.OverlayItem(data, color = 0, alpha = 1.0, colorTable = self.dataMgr.module["Classification"]["labelDescriptions"].getColorTab(), autoAdd = True, autoVisible = True,  linkColorTable = True)
            dataItemImage.overlayMgr["Classification/Labels"] = ov      
        
        #be able to show the labels in 3D
        dataItemImage.overlayMgr["Classification/Labels"].displayable3D = True
        dataItemImage.overlayMgr["Classification/Labels"].backgroundClasses = set([0])
        dataItemImage.overlayMgr["Classification/Labels"].smooth3D = False
        
        #add the raw data
        if dataItemImage.overlayMgr["Raw Data"] is not None:
            dataItemImage.Classification.addOverlayRef(dataItemImage.overlayMgr["Raw Data"].getRef())

                    
        if dataItemImage.Classification["prediction"] is not None:
            prediction = dataItemImage.Classification["prediction"]
            for index, descr in enumerate(self.dataMgr.module["Classification"]["labelDescriptions"]):
                ov = overlayMgr.OverlayItem(DataAccessor(prediction[:,:,:,:,index:index+1], channels = False), color = long(descr.color), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 1.0)
                ov.setColorGetter(descr.getColor, descr)
                dataItemImage.overlayMgr["Classification/Prediction/" + descr.name] = ov
            margin = activeLearning.computeEnsembleMargin(prediction[:,:,:,:,:])
            ov = overlayMgr.OverlayItem(DataAccessor(margin), alpha = 1.0, color = long(65535)<<16, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 1.0)
            dataItemImage.overlayMgr["Classification/Uncertainty"] = ov
            dataItemImage.Classification["prediction"] = None

#        if self._dataVol.uncertainty is not None:
#            #create Overlay for uncertainty:
#            ov = overlayMgr.OverlayItem(self._dataVol.uncertainty, color = QColor(255, 0, 0), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False)
#            self.overlayMgr["Classification/Uncertainty"] = ov        
        
        
        #calculate features for the image
        featureProcess = featureMgr.FeatureThread(self.featureMgr, self.dataMgr, [dataItemImage])        
        featureProcess.start()
        featureProcess.wait()

    def exportClassifiers(self, fileName, pathToGroup='/'):
        if not hasattr(self, 'classificationMgr') or not hasattr(self.classificationMgr, 'classifiers'):
            raise RuntimeError("No classifiers trained so far. Use Train and Predict to learn classifiers.")
        
        if len(self.classificationMgr.classifiers) != 0:      
            h5file = h5py.File(str(fileName),'a')
            h5group = h5file[pathToGroup]
            
            if 'classifiers' in h5group.keys():
                del h5group['classifiers']
                print "Overwrite existing classifiers"
                
            h5group.create_group('classifiers')
            h5file.close()
            
            for i, c in enumerate(self.classificationMgr.classifiers):
                print pathToGroup + "/classifiers/rf_%03d" % i
                c.serialize(str(fileName), pathToGroup + "classifiers/rf_%03d" % i, False)
                print "Write random forest #%03d" % i
                
    @staticmethod    
    def importClassifiers(fileName):
        hf = h5py.File(fileName,'r')
        temp = hf['classifiers'].keys()
        hf.close()
        del hf
        
        classifiers = []
        for cid in temp:
            classifiers.append(defaultRF.ClassifierRandomForest.loadRFfromFile(fileName, 'classifiers/' + cid))   
        return classifiers
          
    def serialize(self, h5G):
        featureG = h5G.create_group('FeatureSelection')        
        try:
            featureG.create_dataset('UserSelection', data=featureMgr.ilastikFeatureGroups.selection)
        except:
            traceback.print_exc()
        
    def deserialize(self, h5G):
        print "ClassificationModuleMgr::deserialize"
        
        #some old file version might not have these keys
        try:
            userSelection = h5G['FeatureSelection']['UserSelection']
            featureMgr.ilastikFeatureGroups.selection = userSelection.value
        except:
            print """Could not find entry FeatureSelection/UserSelection in project file
                     Probably this file is too old. Skipping..."""
          
        classifiers = []
        f = h5G.file
        g = h5G.name + '/classifiers'
        print "  -> looking for classifiers in", g
        if g in f:
            classifiers = f[g].keys()
        
        for cid in classifiers:
            self.classifier.deserialize(f[h5G.name +  '/classifiers/' + cid])
        
#*******************************************************************************
# C l a s s i f i c a t i o n M g r                                            *
#*******************************************************************************

class ClassificationMgr(object):
    def __init__(self, dataMgr):
        self.dataMgr = dataMgr         
        self._trainingVersion = 0
        self._featureVersion = 0
        self.matrixLock = threading.Lock()
        self.classifiers = []
        
        self.classificationModuleMgr = self.dataMgr.module["Classification"]
        

    def getTrainingMforIndForImage(self, ind, dataItemImage):
#                        featureShape = prop["featureM"].shape[0:4]
#                        URI =  unravelIndices(indices, featureShape)
#                        tempfm = prop["featureM"][URI[:,0],URI[:,1],URI[:,2],URI[:,3],:]
#                        tempfm.shape = (tempfm.shape[0],) + (tempfm.shape[1]*tempfm.shape[2],)
        prop = dataItemImage.module["Classification"]
        featureShape = prop["featureM"].shape[0:4]
        URI =  unravelIndices(ind, featureShape)
        if issubclass(prop["featureM"].__class__,numpy.ndarray): 
            trainingF = prop["featureM"][URI[:,0],URI[:,1],URI[:,2],URI[:,3],:]
        else:
            #print ind.shape
            #print prop["featureM"].shape
            trainingF = numpy.zeros((ind.shape[0],) + (prop["featureM"].shape[4],), 'float32')
            for i in range(URI.shape[0]): 
                trainingF[i,:,:] = prop["featureM"][URI[i,0],URI[i,1],URI[i,2],URI[i,3],:]
        return trainingF
        
    def getTrainingMatrixRefForImage(self, dataItemImage):
        prop = dataItemImage.module["Classification"]
        if len(prop["trainingF"]) == 0 and prop["featureM"] is not None:
            tempF = []
            tempL = []
    
            tempd =  dataItemImage.overlayMgr["Classification/Labels"][:, :, :, :, 0].ravel()
            indices = numpy.nonzero(tempd)[0]
            tempL = dataItemImage.overlayMgr["Classification/Labels"][:,:,:,:,0].ravel()[indices]
            tempL.shape += (1,)
                                   
            prop["trainingIndices"] = indices
            prop["trainingL"] = tempL
            if len(indices) > 0:
                prop["trainingF"] = self.getTrainingMforIndForImage(indices, dataItemImage)
            else:
                self.clearFeaturesAndTrainingForImage(dataItemImage)
        return prop["trainingL"], prop["trainingF"], prop["trainingIndices"]
    
    def getTrainingMatrixForImage(self, dataItemImage):
        self.getTrainingMatrixRefForImage(dataItemImage)
        prop = dataItemImage.module["Classification"]
        if len(prop["trainingF"]) != 0:
            return prop["trainingL"], prop["trainingF"], prop["trainingIndices"]
        else:
            return None, None, None

    def updateTrainingMatrixForImage(self, newLabels, dataItemImage):
        """
        This method updates the current training Matrix with new labels.
        newlabels can contain completey new labels, changed labels and deleted labels
        """
        self.matrixLock.acquire()
        prop = dataItemImage.module["Classification"]
        for nl in newLabels:
            try:
                if nl.erasing == False:
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]
                    loopc = 2
                    count = 1
                    indices = indic[-loopc]*count
                    templ = list(dataItemImage.shape[1:-1])
                    templ.reverse()
                    for s in templ:
                        loopc += 1
                        count *= s
                        indices += indic[-loopc]*count

                    if len(indices.shape) == 1:
                        indices.shape = indices.shape + (1,)

                    mask = setintersectionmask(prop["trainingIndices"].ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        tt = numpy.delete(prop["trainingIndices"],nonzero)
                        if len(tt.shape) == 1:
                            tt.shape = tt.shape + (1,)
                        prop["trainingIndices"] = numpy.concatenate((tt,indices))
                        tempI = numpy.nonzero(nl._data)
                        tempL = nl._data[tempI]
                        tempL.shape += (1,)
                        temp2 = numpy.delete(prop["trainingL"],nonzero)
                        temp2.shape += (1,)
                        prop["trainingL"] = numpy.vstack((temp2,tempL))


                        temp2 = numpy.delete(prop["trainingF"],nonzero, axis = 0)

                        if prop["featureM"] is not None and len(indices) > 0:
                            tempfm = self.getTrainingMforIndForImage(indices, dataItemImage)

                            if len(temp2.shape) == 1:
                                temp2.shape += (1,)

                            prop["trainingF"] = numpy.vstack((temp2,tempfm))
                        else:
                            prop["trainingF"] = temp2

                    elif indices.shape[0] > 0: #no intersection, just add everything...
                        if len(prop["trainingIndices"].shape) == 1:
                            prop["trainingIndices"].shape = prop["trainingIndices"].shape + (1,)
                        prop["trainingIndices"] = numpy.concatenate((prop["trainingIndices"],indices))

                        tempI = numpy.nonzero(nl._data)
                        tempL = nl._data[tempI]
                        tempL.shape += (1,)
                        temp2 = prop["trainingL"]
                        prop["trainingL"] = numpy.vstack((temp2,tempL))

                        if prop["featureM"] is not None and len(indices) > 0:
                            if prop["trainingF"] is not None:
                                tempfm = self.getTrainingMforIndForImage(indices, dataItemImage)
                                if len(prop["trainingF"].shape) == 1:
                                    prop["trainingF"].shape = (0,tempfm.shape[1])
                                #print tempfm.shape, prop["trainingF"].shape 
                                prop["trainingF"] = numpy.vstack((prop["trainingF"],tempfm))
                            else:
                                prop["trainingF"] = self.getTrainingMforIndForImage(indices, dataItemImage)

                else: #erasing == True
                    indic =  list(numpy.nonzero(nl._data))
                    indic[0] = indic[0] + nl.offsets[0]
                    indic[1] += nl.offsets[1]
                    indic[2] += nl.offsets[2]
                    indic[3] += nl.offsets[3]
                    indic[4] += nl.offsets[4]

                    loopc = 2
                    count = 1
                    indices = indic[-loopc]*count
                    templ = list(dataItemImage.shape[1:-1])
                    templ.reverse()
                    for s in templ:
                        loopc += 1
                        count *= s
                        indices += indic[-loopc]*count

                    mask = setintersectionmask(prop["trainingIndices"].ravel(),indices.ravel())
                    nonzero = numpy.nonzero(mask)[0]
                    if len(nonzero) > 0:
                        if prop["trainingF"] is not None:
                            prop["trainingIndices"] = numpy.delete(prop["trainingIndices"],nonzero)
                            prop["trainingL"]  = numpy.delete(prop["trainingL"],nonzero)
                            prop["trainingL"].shape += (1,) #needed because numpy.delete is stupid
                            prop["trainingF"] = numpy.delete(prop["trainingF"],nonzero, axis = 0)
                    else: #no intersectoin, in erase mode just pass
                        pass
            except Exception, e:
                self.matrixLock.release()
                print e
                traceback.print_exc(file=sys.stdout)
        self.matrixLock.release()
        
    def clearFeaturesAndTrainingForImage(self, dataItemImage):
        totalsize = 1
        featureM = dataItemImage.module["Classification"]["featureM"]
        if featureM is not None:
            totalsize = featureM.shape[-1]
        prop = dataItemImage.module["Classification"]
        prop["trainingF"] = numpy.zeros((0, totalsize), 'float32')      
        prop["trainingL"] = numpy.zeros((0, 1), 'uint8')
        prop["trainingIndices"] = numpy.zeros((0, 1), 'uint32')
        
    def getFeatureSlicesForViewStateForImage(self, vs, dataItemImage):
        prop = dataItemImage.module["Classification"]
        tempM = []
        if prop["featureM"] is not None:
            tempM.append(prop["featureM"][vs[0],vs[1],:,:,:])
            tempM.append(prop["featureM"][vs[0],:,vs[2],:,:])
            tempM.append(prop["featureM"][vs[0],:,:,vs[3],:])
            for i, f in enumerate(tempM):
                tf = f.reshape((numpy.prod(f.shape[0:2]),) + (f.shape[2],))
                tempM[i] = tf
            return tempM
        else:
            return None


    def buildTrainingMatrix(self, sigma = 0):
        trainingF = []
        trainingL = []
        indices = []
        for item in self.dataMgr:
            trainingLabels, trainingFeatures, indic = self.getTrainingMatrixRefForImage(item)
            if trainingFeatures is not None:
                indices.append(indic)
                trainingL.append(trainingLabels)
                trainingF.append(trainingFeatures)
            
        self._trainingL = trainingL
        self._trainingF = trainingF
        self._trainingIndices = indices     

    def getTrainingMatrix(self, sigma = 0):
        """
        sigma: trainig _data that is within sigma to the image borders is not considered to prevent
        border artifacts in training
        """
        if self._trainingVersion < self._featureVersion:
            self.clearFeaturesAndTraining()
        self.buildTrainingMatrix()
        self._trainingVersion =  self._featureVersion
            
        if len(self._trainingF) == 0:
            self.buildTrainingMatrix()
        
        if len(self._trainingF) > 0:
            self.matrixLock.acquire()
            trainingF = numpy.vstack(self._trainingF)
            trainingL = numpy.vstack(self._trainingL)
            self.matrixLock.release()
            return trainingF, trainingL
        else:
            print "######### empty Training Matrix ##########"
            return None, None
        
    
    def updateTrainingMatrix(self, newLabels,  dataItemImage = None):
        if self._trainingF is None or len(self._trainingF) == 0 or self._trainingVersion < self._featureVersion:
            self.buildTrainingMatrix()        
        if dataItemImage is None:
            dataItemImage = self.dataMgr[self.dataMgr._activeImageNumber]
        self.updateTrainingMatrixForImage(newLabels, dataItemImage)

                    
    def clearFeaturesAndTraining(self):
        self._featureVersion += 1
        self._trainingF = [numpy.zeros((0, 1), 'float32')]
        self._trainingL = [numpy.zeros((0, 1), 'uint8')]
        self._trainingIndices = [numpy.zeros((0, 1), 'uint32')]
        self.classifiers = []
        
        for index, item in enumerate(self.dataMgr):
            self.clearFeaturesAndTrainingForImage(item)







    
#*******************************************************************************
# C l a s s i f i e r T r a i n T h r e a d                                    *
#*******************************************************************************

class ClassifierTrainThread(ThreadBase):
    def __init__(self, queueSize, dataMgr,
                 classifier = classifiers.classifierRandomForest.ClassifierRandomForest,
                 classifierOptions = ()):
        ThreadBase.__init__(self, None)
        self.numClassifiers = queueSize
        self.dataMgr = dataMgr
        self.count = 0
        self.classifierList = []
        self.stopped = False
        self.classifier = classifier
        self.classifierOptions = classifierOptions
        self.classificationMgr = dataMgr.module["Classification"]["classificationMgr"]
        self.jobMachine = jobMachine.JobMachine()
        self.classifiers = deque()

    def trainClassifier(self, F, L, workerNumber, numWorkers):
        #Construct classifier
        classifier = self.classifier(*self.classifierOptions)
        classifier.setWorker(workerNumber, numWorkers)
        classifier.train(F, L, False) # not interactive
        self.count += 1
        self.classifiers.append(classifier)
        
    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            self.classifiers = deque()
            F, L = self.classificationMgr.getTrainingMatrix()
            if F is not None and L is not None and F.shape[0] > 0:
                self.count = 0
                jobs = []
                for i in range(self.numClassifiers):
                    job = jobMachine.IlastikJob(ClassifierTrainThread.trainClassifier, [self, F, L, i, self.numClassifiers])
                    jobs.append(job)
                self.jobMachine.process(jobs)
                
            self.classificationMgr.classifiers = self.classifiers
            
            self.dataMgr.featureLock.release()
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)   
            self.dataMgr.featureLock.release()       


                    
#*******************************************************************************
# C l a s s i f i e r P r e d i c t T h r e a d                                *
#*******************************************************************************

class ClassifierPredictThread(ThreadBase):
    def __init__(self, dataMgr):
        ThreadBase.__init__(self, None)
        self.count = 0
        self.dataMgr = dataMgr
        self.classificationMgr = dataMgr.module["Classification"]["classificationMgr"]
        self.classifiers = self.classificationMgr.classifiers
        self.stopped = False
        self.jobMachine = jobMachine.JobMachine()
        self._prediction = range(len(self.dataMgr))
        self.predLock = threading.Lock()
        self.numberOfJobs = 0
        for i, item in enumerate(self.dataMgr):
            featureBlockAccessor = BlockAccessor(item.module["Classification"]["featureM"], 64)
            self.numberOfJobs += len(self.classificationMgr.classifiers) * featureBlockAccessor._blockCount
    
    def classifierPredict(self, itnr, bnr, fm):
        try:
            b = fm.getBlockBounds(bnr, 0)
            tfm = fm[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:]
            tfm2 = tfm.reshape(tfm.shape[0]*tfm.shape[1]*tfm.shape[2]*tfm.shape[3],tfm.shape[4])
            self.currentPred[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:] = 0
            
            tpred = self.currentPred[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:]
            for num in range(len(self.classifiers)):
                cf = self.classifiers[num]
                pred = cf.predict(tfm2)
                pred.shape = (tfm.shape[0],tfm.shape[1],tfm.shape[2],tfm.shape[3],pred.shape[1])
                tpred += pred[:,:,:,:]
                self.count += 1
            self.currentPred[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:] = tpred / len(self.classifiers)
        except Exception, e:
            print "######### Exception in ClassifierPredictThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)         
        #print "Prediction Job ", bnr, "/", fm._blockCount, "with classifiers ", len(self.classifiers),  " finished"
            
            
    
    def run(self):
        
        for itemindex, item in enumerate(self.dataMgr):
            cnt = 0
            interactiveMessagePrint( "Feature Item" )
            interactiveMessagePrint ( "Classifier %d _prediction" % cnt )
            self.dataMgr.featureLock.acquire()
            try:
                prop = item.module["Classification"]
                
                
                if len(self.classifiers) > 0 and prop["featureM"] is not None:
                    #make a little test _prediction to get the shape and see if it works:
                    tempPred = None
                    if prop["featureM"] is not None:
                        tfm = prop["featureM"][0,0,0,0,:]
                        tfm.shape = (1,) + (tfm.shape[-1],) 
                        tempPred = self.classifiers[0].predict(tfm)
                        featureBlockAccessor = BlockAccessor(prop["featureM"], 64)
                                            
                        if tempPred is not None:
                            self.currentPred = numpy.ndarray((prop["featureM"].shape[0:4]) + (tempPred.shape[1],) , 'float32')
                            jobs= []
                            for bnr in range(featureBlockAccessor._blockCount):
                                job = jobMachine.IlastikJob(ClassifierPredictThread.classifierPredict, [self, itemindex, bnr, featureBlockAccessor])
                                jobs.append(job)
                            self.jobMachine.process(jobs)
                            self._prediction[itemindex] = self.currentPred
                        else:
                            self._prediction[itemindex] = None
                    else:
                        self._prediction[itemindex] = None
                        
                else:
                    print "ClassifierPredictThread: no trained classifiers"
                    self._prediction = None
                self.dataMgr.featureLock.release()
            except Exception, e:
                print "########################## exception in ClassifierPredictThread ###################"
                print e
                traceback.print_exc(file=sys.stdout)                
                self.dataMgr.featureLock.release()
                
    def generateOverlays(self, activeImage = None):
        for itemindex, activeItem in enumerate(self.dataMgr):

            prediction = self._prediction
            descriptions =  self.dataMgr.module["Classification"]["labelDescriptions"]
            classifiers = self.dataMgr.module["Classification"]["classificationMgr"].classifiers
            
            if prediction is not None and prediction[itemindex] is not None:
                foregrounds = []
                for p_i, p_num in enumerate(classifiers[0].unique_vals):
                    #create Overlay for _prediction:
                    ov = overlayMgr.OverlayItem(prediction[itemindex][:,:,:,:,p_i],  color = long(descriptions[p_num-1].color), alpha = 0.4, colorTable = None, autoAdd = True, autoVisible = True, min = 0, max = 1)
                    ov.setColorGetter(descriptions[p_num-1].getColor, descriptions[p_num-1])
                    activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name] = ov
                    ov = activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]
                    ov.setColorGetter(descriptions[p_num-1].getColor, descriptions[p_num-1])
                    foregrounds.append(ov)
    
                import ilastik.core.overlays.thresholdOverlay as tho
                
                if len(foregrounds) > 1:
                    if activeItem.overlayMgr["Classification/Segmentation"] is None:
                        ov = tho.ThresholdOverlay(foregrounds, [], autoAdd = True, autoVisible = True)
                        activeItem.overlayMgr["Classification/Segmentation"] = ov
                    else:
                        ov = activeItem.overlayMgr["Classification/Segmentation"]
                        ov.setForegrounds(foregrounds)
    
    
                all =  range(len(descriptions))
                if len(classifiers) > 0:
                    not_predicted = numpy.setdiff1d(all, classifiers[0].unique_vals - 1)
                    if len(not_predicted) > 0:
                        print not_predicted
                        for p_i, p_num in enumerate(not_predicted):
                            if activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num].name] is not None:
                                print "clearing prediction for unused Label ", p_num
                                activeItem.overlayMgr["Classification/Prediction/" + descriptions[p_num].name][:,:,:,:,:] = 0
    
    
                    margin = activeLearning.computeEnsembleMargin(prediction[itemindex][:,:,:,:,:])

                    #create Overlay for uncertainty:
                    ov = overlayMgr.OverlayItem(margin, color = long(65535 << 16), alpha = 1.0, colorTable = None, autoAdd = True, autoVisible = False, min = 0, max = 1)
                    activeItem.overlayMgr["Classification/Uncertainty"] = ov
            else:
                print "Prediction for item ", itemindex, "is None, not generating Overlays"


                

#*******************************************************************************
# C l a s s i f i e r I n t e r a c t i v e T h r e a d                        *
#*******************************************************************************

class ClassifierInteractiveThread(ThreadBase):
    def __init__(self, parent, classificationMgr, classifier = classifiers.classifierRandomForest.ClassifierRandomForest, numClassifiers = 5, classifierOptions=(8,)):
        ThreadBase.__init__(self, None)
        
        self.classificationMgr = classificationMgr
        
        self.ilastik = parent
        
        self.stopped = False
               
        self.resultList = deque(maxlen=10)
               
        self.numberOfClassifiers = numClassifiers

        self.classifiers = deque(maxlen=numClassifiers)

        for i, item in enumerate(self.classificationMgr.classifiers):
            self.classifiers.append(item)
        
        self.result = deque(maxlen=1)

        self.dataPending = threading.Event()
        self.dataPending.clear()
        
        self.classifier = classifier
        self.classifierOptions = classifierOptions

        self.jobMachine = jobMachine.JobMachine()
        
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifiers)
    
    def trainClassifier(self, F, L, workerNumber, numWorkers):
        classifier = self.classifier()
        classifier.setWorker(workerNumber, numWorkers)
        classifier.train(F, L, True) # is interactive        
        self.classifiers.append(classifier)


    def classifierPredict(self, i, start, end, num, featureMatrix):
        try:
            cf = self.classifiers[num]
            pred = cf.predict(featureMatrix[i][start:end,:]) 
            self._prediction[i][start:end,:] += 1.0 * pred / len(self.classifiers)
            self.count += 1
        except Exception, e:
            print "### ClassifierInteractiveThread::classifierPredict"
            print e
            traceback.print_exc(file=sys.stdout)       


    def run(self):
        self.ilastik.activeImageLock.acquire()
        F, L = self.classificationMgr.getTrainingMatrix()
        self.ilastik.activeImageLock.release()
        self.dataPending.set()
        while not self.stopped:
            self.dataPending.wait()
            self.dataPending.clear()
            if not self.stopped: #no needed, but speeds up the final thread.join()
                features = None
                self.ilastik.activeImageLock.acquire()
                self.ilastik.project.dataMgr.featureLock.acquire()
                try:
                    activeImageNumber = self.ilastik._activeImageNumber
                    activeImage = self.ilastik._activeImage
                    newLabels = self.ilastik.labelWidget.getPendingLabels()
                    
                    self.classificationMgr.updateTrainingMatrixForImage(newLabels,  activeImage)
                    features,labels = self.classificationMgr.getTrainingMatrix()
                    #if len(newLabels) > 0 or len(self.classifiers) == 0:
                    if features is not None:
                        print "retraining..."
                        interactiveMessagePrint("1>> Pop training Data")
                        if features.shape[0] == labels.shape[0]:
                            #self.classifiers = deque()
                            jobs = []
                            for i in range(self.numberOfClassifiers):
                                job = jobMachine.IlastikJob(ClassifierInteractiveThread.trainClassifier, [self, features, labels, i, self.numberOfClassifiers])
                                jobs.append(job)
                            self.jobMachine.process(jobs)                        
                        else:
                            print "##################### shape mismatch #####################"
                    
                    vs = self.ilastik.labelWidget.getVisibleState()
                    features = self.classificationMgr.getFeatureSlicesForViewStateForImage(vs, activeImage)
                    vs.append(activeImage)
    
                    interactiveMessagePrint("1>> Pop _prediction Data")
                    if len(self.classifiers) > 0:
                        #make a little test _prediction to get the shape and see if it works:
                        tempPred = None
                        if features is not None:
                            tfm = features[0][0,:]
                            tfm.shape = (1,) + tfm.shape 
                            tempPred = self.classifiers[0].predict(tfm)
                                            
                        if tempPred is not None:
                            self._prediction = []
                            jobs= []
                            self.count = 0
                            for i in range(len(features)):
                                self._prediction.append(numpy.zeros((features[i].shape[0],) + (tempPred.shape[1],) , 'float32'))
                                for j in range(0,features[i].shape[0],128**2):
                                    for k in range(len(self.classifiers)):
                                        end = min(j+128**2,features[i].shape[0])
                                        job = jobMachine.IlastikJob(ClassifierInteractiveThread.classifierPredict, [self, i, j, end, k, features])
                                        jobs.append(job)
                                
                            self.jobMachine.process(jobs)

                            shape = activeImage.shape

                            tp = []
                            tp.append(self._prediction[0].reshape((shape[2],shape[3],self._prediction[0].shape[-1])))
                            tp.append(self._prediction[1].reshape((shape[1],shape[3],self._prediction[1].shape[-1])))
                            tp.append(self._prediction[2].reshape((shape[1],shape[2],self._prediction[2].shape[-1])))

                            descriptions =  self.ilastik.project.dataMgr.module["Classification"]["labelDescriptions"]
                            all =  range(len(descriptions))
                            not_predicted = numpy.setdiff1d(all, self.classifiers[0].unique_vals - 1)

                            uncertaintyData = activeImage.overlayMgr["Classification/Uncertainty"]._data

                            #Axis 0
                            tpc = tp[0]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba._blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)
                                
                                uncertaintyData[vs[0], vs[1], b[0]:b[1],b[2]:b[3],0] = margin
#                                seg = segmentationMgr.LocallyDominantSegmentation2D(lb, 1.0)
#                                self.ilastik.project.dataMgr[vs[-1]]._dataVol.segmentation[vs[0], vs[1], b[0]:b[1],b[2]:b[3]] = seg

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]._data
                                    predictionData[vs[0],vs[1],b[0]:b[1],b[2]:b[3],0] = tpc[b[0]:b[1],b[2]:b[3],p_i]

                                for p_i, p_num in enumerate(not_predicted):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num].name]._data
                                    predictionData[vs[0],vs[1],b[0]:b[1],b[2]:b[3],0] = 0

                            #Axis 1
                            tpc = tp[1]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba._blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)
                                uncertaintyData[vs[0], b[0]:b[1],vs[2],b[2]:b[3],0] = margin

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]._data
                                    predictionData[vs[0],b[0]:b[1],vs[2],b[2]:b[3],0] = tpc[b[0]:b[1],b[2]:b[3],p_i]

                                for p_i, p_num in enumerate(not_predicted):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num].name]._data
                                    predictionData[vs[0],b[0]:b[1],vs[2],b[2]:b[3],0] = 0


                            #Axis 2
                            tpc = tp[2]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba._blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)
                                uncertaintyData[vs[0], b[0]:b[1],b[2]:b[3], vs[3],0] = margin

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num-1].name]._data
                                    predictionData[vs[0],b[0]:b[1],b[2]:b[3],vs[3],0] = tpc[b[0]:b[1],b[2]:b[3],p_i]

                                for p_i, p_num in enumerate(not_predicted):
                                    predictionData = activeImage.overlayMgr["Classification/Prediction/" + descriptions[p_num].name]._data
                                    predictionData[vs[0],b[0]:b[1],b[2]:b[3],vs[3],0] = 0


                        else:
                            print "##################### _prediction None #########################"
                    else:
                        print "##################### No Classifiers ############################"
                    if have_qt:
                        self.emit(SIGNAL("resultsPending()"))
                    else:
                        raise "Need to add code to signal results pending without Qt"
                    self.ilastik.project.dataMgr.featureLock.release()
                    self.ilastik.activeImageLock.release()                     
                except Exception, e:
                    print "########################## exception in Interactivethread ###################"
                    print e
                    traceback.print_exc(file=sys.stdout)

                    self.ilastik.activeImageLock.release() 
                    self.ilastik.project.dataMgr.featureLock.release()




#class ClassifierOnlineThread(QThread):
#    def __init__(self, name, features, labels, ids, predictionList, predictionUpdated):
#        QThread.__init__(self, None)
#
#        self.commandQueue = queue()
#        self.stopped = False
#        if name=="online laSvm":
#            self.classifier = onlineClassifcator.OnlineLaSvm()
#        else:
#            if name=="online RF":
#                self.classifier = onlineClassifcator.OnlineRF()
#            else:
#                    raise RuntimeError('unknown online classificator selected')
#        self.classifier.start(features, labels, ids)
#
#        for k in range(len(predictionList)):
#            self.classifier.addPredictionSet(predictionList[k],k)
#        self.activeImageIndex = 0
#
#        self.predictions = [deque(maxlen=1) for k in range(len(predictionList))]
#        self.predictionUpdated = predictionUpdated
#        self.commandQueue.put(([],[],[],"noop"))
#
#    def run(self):
#        while not self.stopped:
#            try:
#                features, labels, ids, action = self.commandQueue.get(True, 0.5)
#            except QueueEmpty, empty:
#                action = 'improve'
#
#            if action == 'stop':
#                break
#            elif action == 'unlearn':
#                self.classifier.removeData(ids)
#            elif action == 'learn':
#                print "*************************************"
#                print "************* LEARNING **************"
#                print "*************************************"
#                self.classifier.addData(features, labels, ids)
#                self.classifier.fastLearn()
#                print "Done learning"
#            elif action == 'improve':
#                # get an segfault here
#                self.classifier.improveSolution()
#                continue
#            elif action == 'noop':
#                pass
#
#            if self.commandQueue.empty():
#                print "Will predict"
#                result = self.classifier.fastPredict(self.activeImageIndex)
#                self.predictions[self.activeImageIndex].append(result)
#                self.predictionUpdated()
            
            
#class ClassificationImpex(object):
#    def __init__(self):
#        print "Dont do it"
#
#    @staticmethod
#    def exportToSVMLight(data, labels, filename, with_namespace):
#        if data.shape[0]!=labels.shape[0]:
#            raise "labels must have same size as data has columns"
#
#        if labels.ndim == 2:
#            labels.shape = labels.shape[0]
#
#        permInd = numpy.random.permutation(data.shape[0])
#        f=open(filename,'wb')
#        #go through examples
#        for i in xrange(data.shape[0]):
#            f.write(str(int(labels[permInd[i]]-1))+" ")
#            if with_namespace==True:
#                f.write("|features ")
#            for j in xrange(data.shape[1]):
#                #if data[i,j]==0:
#                #    continue
#                f.write(repr(j+1)+":"+repr(data[permInd[i],j])+" ")
#            f.write("\n")
#        f.close()
#
#    @staticmethod
#    def exportToSVMLightNoLabels(data, filename, with_namespace):
#        labels = numpy.zeros((data.shape[0]),dtype=numpy.int)
#        ClassificationImpex.exportToSVMLight(data, labels, filename, with_namespace)
#
#    @staticmethod
#    def readSVMLightClassification(filename, labels=(1,0)):
#        f=open(filename,'r')
#        res=[]
#        for line in f:
#            val=float(line)
#            res.append(val)
#        return numpy.array(res, dtype=numpy.int)
