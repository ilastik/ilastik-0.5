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

import numpy
import threading 
import time
import sys
import os
from Queue import Queue as queue
from Queue import Empty as QueueEmpty
from collections import deque
from PyQt4 import QtCore
from core.utilities import irange
from core import onlineClassifcator
from core import activeLearning, segmentationMgr
from gui import volumeeditor as ve
from core import jobMachine
import sys, traceback

import numpy

def interactiveMessagePrint(* args):
    pass
    #print "Thread: ", args[0]

try:
    import vigra
    import vigra.learning
except ImportError:
    sys.exit("vigra module not found!")

class ClassificationMgr(object):
    def __init__(self):
        pass
    
    

class ClassifierBase(object):
    def __init__(self):
        pass
        
    def train(self):
        pass
    
    def predict(self):
        pass
    
class ClassifierRandomForest(ClassifierBase):
    def __init__(self, features=None, labels=None, treeCount=10):
        ClassifierBase.__init__(self)
        if not labels.dtype == numpy.uint32:
            labels = labels.astype(numpy.uint32)
        if not features.dtype == numpy.float32:
            features = features.astype(numpy.float32)
        
        if len(numpy.unique(labels)) > 1:
            print "Learning RF %d trees: %d labels given, %d classes, and %d features " % (treeCount, features.shape[0], len(numpy.unique(labels)), features.shape[1])
            self.classifier = vigra.learning.RandomForestOld(features, labels, treeCount=treeCount)
        else:
            self.classifier = None
            
        self.treeCount = treeCount
        self.labels = labels
        self.features = features

    
#    def train(self, labels, features):
#        
#        if features.shape[0] != labels.shape[0]:
#            interactiveMessagePrint( " 3, 2 ,1 ... BOOOM!! #features != # labels" )
#            
#        if not labels.dtype == numpy.uint32:
#            labels = labels.astype(numpy.uint32)
#        if not features.dtype == numpy.float32:
#            features = features.astype(numpy.float32)
#        # print "Create RF with ",self.treeCount," trees"
#        #self.classifier = vigra.classification.RandomForest(features, labels, self.treeCount)
#        if labels.ndim == 1:
#            labels.shape = labels.shape + (1,)
#        labels = labels - 1
#        
#        self.classifier.learnRF(features, labels)
#        #print "tree Count", self.treeCount
        
    
    def predict(self, target):
        #3d: check that only 1D data arrives here
        if self.classifier is not None and target is not None:
            if not target.dtype == numpy.float32:
                target = numpy.array(target, dtype=numpy.float32)
            return self.classifier.predictProbabilities(target)
        else:            
            return None
    def __getstate__(self): 
        # Delete This Instance for pickleling
        return {}    
          

class ClassifierSVM(ClassifierBase):
    def __init__(self, features=None, labels=None):
        ClassifierBase.__init__(self)
        pass
    
    def train(self):
        pass
    
    def predict(self):
        pass
    
    
class ClassifierVW(ClassifierBase):
    def __init__(self, features=None, labels=None, tmpFolder='.', regressorFile='vopalVabbitRegressor', trainFile='tmp_svm_light_file', testFile='tmp_svm_light_file_test', predictFile='tmp_svm_light_output'):
        ClassifierBase.__init__(self)
        self.tmpFolder = tmpFolder
        myjoin = lambda p,f: "%s/%s" % (p,f)
        self.regressorFile = myjoin(tmpFolder, regressorFile)
        self.trainFile = myjoin(tmpFolder, trainFile)
        self.predictFile = myjoin(tmpFolder, predictFile)
        self.testFile = myjoin(tmpFolder, testFile)
        
        if 'win' in sys.platform:
            self.trainCommand = 'c:/cygwin/bin/bash -c "./vw %s"'
            self.predictCommand = 'c:/cygwin/bin/bash -c "./vw %s"'
            
        elif 'linux' in sys.platform:
            self.trainCommand = './vw %s'
            self.predictCommand = './vw %s'
        else:
            print "ClassifierVW: Unkown platform"
        
        self.train(features, labels)
        
        
    def train(self, train_data, train_labels):
        #export the data
        ClassificationImpex.exportToSVMLight(train_data, train_labels, self.trainFile, True)
        
        options = " -d %s -f %s" % (self.trainFile, self.regressorFile)
        print self.trainCommand % options
        os.system(self.trainCommand % options)

        

        
    
    def predict(self, test_data):
        ClassificationImpex.exportToSVMLightNoLabels(test_data, self.testFile, True)
        options = " -t -d %s -i %s  -p %s" % (self.testFile, self.regressorFile, self.predictFile)
        print options
        os.system(self.predictCommand % options)
        res = ClassificationImpex.readSVMLightClassification(self.predictFile)
        res.shape = res.shape[0],-1
        res = numpy.concatenate((res,1-res),axis=1)
        return res
    
    
class ClassificationImpex(object):
    def __init__(self):
        print "Dont do it"
            
    @staticmethod
    def exportToSVMLight(data, labels, filename, with_namespace):
        if data.shape[0]!=labels.shape[0]:
            raise "labels must have same size as data has columns"
        
        if labels.ndim == 2:
            labels.shape = labels.shape[0]
            
        permInd = numpy.random.permutation(data.shape[0])
        f=open(filename,'wb')
        #go through examples
        for i in xrange(data.shape[0]):
            f.write(str(int(labels[permInd[i]]-1))+" ")
            if with_namespace==True:
                f.write("|features ")
            for j in xrange(data.shape[1]):
                #if data[i,j]==0:
                #    continue
                f.write(repr(j+1)+":"+repr(data[permInd[i],j])+" ")
            f.write("\n")
        f.close()
    
    @staticmethod
    def exportToSVMLightNoLabels(data, filename, with_namespace):
        labels = numpy.zeros((data.shape[0]),dtype=numpy.int)
        ClassificationImpex.exportToSVMLight(data, labels, filename, with_namespace)
        
    @staticmethod
    def readSVMLightClassification(filename, labels=(1,0)):
        f=open(filename,'r')
        res=[]
        for line in f:
            val=float(line)
            res.append(val)
        return numpy.array(res, dtype=numpy.int)
     
    
class ClassifierTrainThread(QtCore.QThread):
    def __init__(self, queueSize, dataMgr):
        QtCore.QThread.__init__(self, None)
        #threading.Thread.__init__(self)
        self.numClassifiers = queueSize
        self.dataMgr = dataMgr
        self.count = 0
        self.classifierList = []
        self.stopped = False
        self.classifier = ClassifierRandomForest
        self.jobMachine = jobMachine.JobMachine()
        self.classifiers = deque()

    def trainClassifier(self, F, L):
        classifier = self.classifier(F, L)
        self.count += 1
        self.classifiers.append(classifier)
        
    def run(self):
        self.dataMgr.featureLock.acquire()
        try:
            F, L = self.dataMgr.getTrainingMatrix()
            if F is not None and L is not None:
                self.count = 0
                self.classifiers = deque()
                jobs = []
                for i in range(self.numClassifiers):
                    job = jobMachine.IlastikJob(ClassifierTrainThread.trainClassifier, [self, F, L])
                    jobs.append(job)
                self.jobMachine.process(jobs)
                
                self.dataMgr.classifiers = self.classifiers

            self.dataMgr.featureLock.release()
        except Exception as e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)   
            self.dataMgr.featureLock.release()       


                    
class ClassifierPredictThread(QtCore.QThread):
    def __init__(self, dataMgr):
        QtCore.QThread.__init__(self, None)
        #threading.Thread.__init__(self)
        self.count = 0
        self.dataMgr = dataMgr
        self.stopped = False
        self.jobMachine = jobMachine.JobMachine()
        self.prediction = None
        self.predLock = threading.Lock()
        self.numberOfJobs = 0
        for i, item in enumerate(self.dataMgr):
            self.numberOfJobs += item.featureBlockAccessor.blockCount
    
    def classifierPredict(self, bnr, fm):
        try:
            b = fm.getBlockBounds(bnr, 0)
            tfm = fm[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:]
            tfm2 = tfm.reshape(tfm.shape[0]*tfm.shape[1]*tfm.shape[2]*tfm.shape[3],tfm.shape[4]*tfm.shape[5])
            for num in range(len(self.dataMgr.classifiers)):
                cf = self.dataMgr.classifiers[num]
                pred = cf.predict(tfm2)
                pred.shape = (tfm.shape[0],tfm.shape[1],tfm.shape[2],tfm.shape[3],pred.shape[1])
                self.prediction[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:] = self.prediction[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:] + pred[:,:,:,:]
            self.count += 1
        except Exception as e:
            print "######### Exception in ClassifierPredictThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)         
            
            
    
    def run(self):
        
        for item in self.dataMgr:
            cnt = 0
            interactiveMessagePrint( "Feature Item" )
            interactiveMessagePrint ( "Classifier %d prediction" % cnt )
            self.dataMgr.featureLock.acquire()
            try:
                #self.dataMgr.clearFeaturesAndTraining()
                if len(self.dataMgr.classifiers) > 0:
                    #make a little test prediction to get the shape and see if it works:
                    tempPred = None
                    if item._featureM is not None:
                        tfm = item._featureM[0,0,0,0,:,:]
                        tfm.shape = (1,) + (tfm.shape[0]*tfm.shape[1],) 
                        tempPred = self.dataMgr.classifiers[0].predict(tfm)
                                        
                    if tempPred is not None:
                        self.prediction = numpy.zeros((item._featureM.shape[0:4]) + (tempPred.shape[1],) , 'float32')
                        jobs= []
                        for bnr in range(item.featureBlockAccessor.blockCount):
                            job = jobMachine.IlastikJob(ClassifierPredictThread.classifierPredict, [self, bnr, item.featureBlockAccessor])
                            jobs.append(job)
                        self.jobMachine.process(jobs)
                        count = len(self.dataMgr.classifiers)
                        if count == 0:
                            count = 1
                        self.prediction = self.prediction / count
                        #item.prediction = ve.DataAccessor(self.prediction.reshape(item.dataVol.data.shape[0:-1] + (self.prediction.shape[-1],)), channels = True)
                        item.prediction = ve.DataAccessor(self.prediction, channels = True)
                        self.prediction = None
                self.dataMgr.featureLock.release()
            except Exception as e:
                print "########################## exception in ClassifierPredictThread ###################"
                print e
                traceback.print_exc(file=sys.stdout)                
                self.dataMgr.featureLock.release()


                

class ClassifierInteractiveThread(QtCore.QThread):
    def __init__(self, parent, trainingQueue, predictQueue, resultQueue, numberOfClassifiers=5, treeCount=10):
        #threading.Thread.__init__(self)
        #QtCore.QObject.__init__(self)
        QtCore.QThread.__init__(self, None)

        self.ilastik = parent
        
        self.stopped = False
        
        self.trainingQueue = trainingQueue
        self.predictionQueue = predictQueue
        self.resultQueue = resultQueue
        
        self.resultList = deque(maxlen=10)
               
        self.numberOfClassifiers = numberOfClassifiers    

        self.treeCount = treeCount

        self.classifiers = deque(maxlen=numberOfClassifiers)

        for i, item in enumerate(self.ilastik.project.dataMgr.classifiers):
            self.classifiers.append(item)
        
        self.result = deque(maxlen=1)

        self.dataPending = threading.Event()
        self.dataPending.clear()
        
        self.classifier = ClassifierRandomForest
                
        self.jobMachine = jobMachine.JobMachine()
        
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifiers)
    
    def trainClassifier(self, F, L):
        print "#### 1"
        classifier = self.classifier(F, L)
        print "#### 2"
        self.classifiers.append(classifier)
        print "#### 3"


    def classifierPredict(self, num, featureMatrix):
        try:
            cf = self.classifiers[num]
            pred = cf.predict(featureMatrix)
            #self.predLock.acquire()
            self.prediction += pred
            self.count += 1
            #self.predLock.release()
        except Exception as e:
            print "### ClassifierInteractiveThread::classifierPredict"
            print e
            traceback.print_exc(file=sys.stdout)        

                            
    def run(self):
        self.dataPending.set()
        while not self.stopped:
            self.dataPending.wait()
            self.dataPending.clear()
            if not self.stopped: #no needed, but speeds up the final thread.join()
                features = None
                self.ilastik.activeImageLock.acquire()
                self.ilastik.project.dataMgr.featureLock.acquire()
                try:
                    activeImage = self.ilastik.activeImage
                    newLabels = self.ilastik.labelWidget.getPendingLabels()
                    if len(newLabels) > 0:
                        self.ilastik.project.dataMgr.updateTrainingMatrix(activeImage, newLabels)
                    if len(newLabels) > 0 or self.ilastik.project.dataMgr.trainingVersion < self.ilastik.project.dataMgr.featureVersion:
                        features,labels = self.ilastik.project.dataMgr.getTrainingMatrix()
                    if features is not None:
                        print "retraining..."
                        interactiveMessagePrint("1>> Pop training Data")
                        if features.shape[0] == labels.shape[0]:
                            #self.classifiers = deque()
                            jobs = []
                            for i in range(self.numberOfClassifiers):
                                job = jobMachine.IlastikJob(ClassifierInteractiveThread.trainClassifier, [self, features, labels])
                                jobs.append(job)
                            self.jobMachine.process(jobs)                        
                        else:
                            print "##################### shape mismatch #####################"
                    vs = self.ilastik.labelWidget.getVisibleState()
                    features = self.ilastik.project.dataMgr[activeImage].getFeatureMatrixForViewState(vs)
                    vs.append(activeImage)
    
                    interactiveMessagePrint("1>> Pop prediction Data")
                    if len(self.classifiers) > 0:
                        #make a little test prediction to get the shape and see if it works:
                        tempPred = None
                        if features is not None:
                            tfm = features[0,:]
                            tfm.shape = (1,) + tfm.shape 
                            tempPred = self.classifiers[0].predict(tfm)
                                            
                        if tempPred is not None:
                            self.prediction = numpy.zeros((features.shape[0],) + (tempPred.shape[1],) , 'float32')
                            jobs= []
                            self.count = 0
                            for i in range(len(self.classifiers)):
                                job = jobMachine.IlastikJob(ClassifierInteractiveThread.classifierPredict, [self, i, features])
                                jobs.append(job)
                                
                            self.jobMachine.process(jobs)
                            
                            predictions = self.prediction / self.count
                                                   
                            shape = self.ilastik.project.dataMgr[vs[-1]].dataVol.data.shape
                            index0 = 0
                            count0 = numpy.prod(shape[2:4])
                            count1 = numpy.prod((shape[1],shape[3]))
                            count2 = numpy.prod(shape[1:3])
                            ax0 = predictions[0:count0,:]
                            ax1 = predictions[count0:count0+count1,:]
                            ax2 = predictions[count0+count1:count0+count1+count2,:]

                            tp0 = ax0.reshape((shape[2],shape[3],ax0.shape[-1]))
                            tp1 = ax1.reshape((shape[1],shape[3],ax0.shape[-1]))
                            tp2 = ax2.reshape((shape[1],shape[2],ax0.shape[-1]))

                            margin0 = activeLearning.computeEnsembleMargin2D(tp0)*255.0
                            margin1 = activeLearning.computeEnsembleMargin2D(tp1)*255.0
                            margin2 = activeLearning.computeEnsembleMargin2D(tp2)*255.0
                            
                            seg0 = segmentationMgr.LocallyDominantSegmentation2D(tp0, 1.0)
                            seg1 = segmentationMgr.LocallyDominantSegmentation2D(tp1, 1.0)
                            seg2 = segmentationMgr.LocallyDominantSegmentation2D(tp2, 1.0)
                            
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], vs[1], :, :] = margin0[:,:]
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], :, vs[2], :] = margin1[:,:]
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], :, :, vs[3]] = margin2[:,:]
    
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], vs[1], :, :] = seg0[:,:]
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], :, vs[2], :] = seg1[:,:]
                            self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], :, :, vs[3]] = seg2[:,:]
    
                            for p_i in range(ax0.shape[1]):
                                item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_i]
                                item.prediction[vs[0],vs[1],:,:] = (tp0[:,:,p_i]* 255).astype(numpy.uint8)
                                item.prediction[vs[0],:,vs[2],:] = (tp1[:,:,p_i]* 255).astype(numpy.uint8)
                                item.prediction[vs[0],:,:,vs[3]] = (tp2[:,:,p_i]* 255).astype(numpy.uint8)
                                
                        else:
                            print "##################### prediction None #########################"
                    else:
                        print "##################### No Classifiers ############################"
                    self.ilastik.project.dataMgr.featureLock.release()
                    self.ilastik.activeImageLock.release()                     
                    self.emit(QtCore.SIGNAL("resultsPending()"))
                except Exception as e:
                    print "########################## exception in Interactivethread ###################"
                    print e
                    traceback.print_exc(file=sys.stdout)

                    self.ilastik.activeImageLock.release() 
                    self.ilastik.project.dataMgr.featureLock.release()



class ClassifierOnlineThread(QtCore.QThread):
    def __init__(self, name, features, labels, ids, predictionList, predictionUpdated):
        #threading.Thread.__init__(self)
        QtCore.QThread.__init__(self, None)

        self.commandQueue = queue()
        self.stopped = False
        if name=="online laSvm":
            self.classifier = onlineClassifcator.OnlineLaSvm()
        else:
            if name=="online RF":
                self.classifier = onlineClassifcator.OnlineRF()
            else:
                    raise RuntimeError('unknown online classificator selected')
        self.classifier.start(features, labels, ids)
        
        for k in range(len(predictionList)):
            self.classifier.addPredictionSet(predictionList[k],k)
        self.activeImageIndex = 0
        
        self.predictions = [deque(maxlen=1) for k in range(len(predictionList))]
        self.predictionUpdated = predictionUpdated
        self.commandQueue.put(([],[],[],"noop"))
    
    def run(self):
        while not self.stopped:
            try:
                features, labels, ids, action = self.commandQueue.get(True, 0.5)
            except QueueEmpty as empty:
                action = 'improve'

            if action == 'stop':
                break
            elif action == 'unlearn':
                self.classifier.removeData(ids)
            elif action == 'learn':
                print "*************************************"
                print "************* LEARNING **************"
                print "*************************************"
                self.classifier.addData(features, labels, ids)
                self.classifier.fastLearn()
                print "Done learning"
            elif action == 'improve':
                # get an segfault here
                self.classifier.improveSolution()
                continue
            elif action == 'noop':
                pass
                
            if self.commandQueue.empty():
                print "Will predict"
                result = self.classifier.fastPredict(self.activeImageIndex)
                self.predictions[self.activeImageIndex].append(result)
                self.predictionUpdated()
            
            
        
    
    

