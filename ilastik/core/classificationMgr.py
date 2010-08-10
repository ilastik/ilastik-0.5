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
try:
    from PyQt4 import QtCore
    ThreadBase = QtCore.QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False
from ilastik.core.utilities import irange
import onlineClassifcator
import dataMgr as DM
import activeLearning, segmentationMgr
import classifiers
from ilastik.core.volume import DataAccessor as DataAccessor
import jobMachine
import sys, traceback
import ilastik.core.classifiers.classifierRandomForest

import numpy


""" Import all classification plugins"""
pathext = os.path.dirname(__file__)

try:
    for f in os.listdir(os.path.abspath(pathext + '/classifiers')):
        module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
        if ext == '.py': # Important, ignore .pyc/othesr files.
            module = __import__('ilastik.core.classifiers.' + module_name)
except Exception, e:
    pass

for i, c in enumerate(classifiers.classifierBase.ClassifierBase.__subclasses__()):
    print "loaded classifier ", c.name


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
    
class ClassifierTrainThread(ThreadBase):
    def __init__(self, queueSize, dataMgr, classifier = ilastik.core.classifiers.classifierRandomForest.ClassifierRandomForest, classifierOptions = (10,)):
        ThreadBase.__init__(self, None)
        self.numClassifiers = queueSize
        self.dataMgr = dataMgr
        self.count = 0
        self.classifierList = []
        self.stopped = False
        self.classifier = classifier
        self.classifierOptions = classifierOptions
        self.jobMachine = jobMachine.JobMachine()
        self.classifiers = deque()

    def trainClassifier(self, F, L):
        classifier = self.classifier(*self.classifierOptions)
        classifier.train(F, L)
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
        except Exception, e:
            print "######### Exception in ClassifierTrainThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)   
            self.dataMgr.featureLock.release()       


                    
class ClassifierPredictThread(ThreadBase):
    def __init__(self, dataMgr):
        ThreadBase.__init__(self, None)
        self.count = 0
        self.dataMgr = dataMgr
        self.stopped = False
        self.jobMachine = jobMachine.JobMachine()
        self.prediction = None
        self.predLock = threading.Lock()
        self.numberOfJobs = 0
        for i, item in enumerate(self.dataMgr):
            self.numberOfJobs += item.featureBlockAccessor.blockCount * len(self.dataMgr.classifiers)
    
    def classifierPredict(self, bnr, fm):
        try:
            b = fm.getBlockBounds(bnr, 0)
            tfm = fm[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:]
            tfm2 = tfm.reshape(tfm.shape[0]*tfm.shape[1]*tfm.shape[2]*tfm.shape[3],tfm.shape[4]*tfm.shape[5])
	    tpred = self.prediction[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:]
            for num in range(len(self.dataMgr.classifiers)):
                cf = self.dataMgr.classifiers[num]
                pred = cf.predict(tfm2)
                pred.shape = (tfm.shape[0],tfm.shape[1],tfm.shape[2],tfm.shape[3],pred.shape[1])
                tpred += pred[:,:,:,:]
		self.count += 1
	    self.prediction[:,b[0]:b[1],b[2]:b[3],b[4]:b[5],:] = tpred
        except Exception, e:
            print "######### Exception in ClassifierPredictThread ##########"
            print e
            traceback.print_exc(file=sys.stdout)         
        # print "Prediction Job ", self.count, "/", self.numberOfJobs, " finished"
            
            
    
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
                        item.prediction = DataAccessor(self.prediction, channels = True)
                        self.prediction = None
                self.dataMgr.featureLock.release()
            except Exception, e:
                print "########################## exception in ClassifierPredictThread ###################"
                print e
                traceback.print_exc(file=sys.stdout)                
                self.dataMgr.featureLock.release()


                

class ClassifierInteractiveThread(ThreadBase):
    def __init__(self, parent, classifier = ilastik.core.classifiers.classifierRandomForest.ClassifierRandomForest, numClassifiers = 5, classifierOptions=(8,)):
        ThreadBase.__init__(self, None)

        self.ilastik = parent
        
        self.stopped = False
               
        self.resultList = deque(maxlen=10)
               
        self.numberOfClassifiers = numClassifiers

        self.classifiers = deque(maxlen=numClassifiers)

        for i, item in enumerate(self.ilastik.project.dataMgr.classifiers):
            self.classifiers.append(item)
        
        self.result = deque(maxlen=1)

        self.dataPending = threading.Event()
        self.dataPending.clear()
        
        self.classifier = classifier
        self.classifierOptions = classifierOptions

        self.jobMachine = jobMachine.JobMachine()
        
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifiers)
    
    def trainClassifier(self, F, L):
        classifier = self.classifier(*self.classifierOptions)
        classifier.train(F, L)
        self.classifiers.append(classifier)


    def classifierPredict(self, i, start, end, num, featureMatrix):
        try:
            cf = self.classifiers[num]
            pred = cf.predict(featureMatrix[i][start:end,:]) / len(self.classifiers)
            self.prediction[i][start:end,:] += pred
            self.count += 1
        except Exception, e:
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
                    features = self.ilastik.project.dataMgr[activeImage].getFeatureSlicesForViewState(vs)
                    vs.append(activeImage)
    
                    interactiveMessagePrint("1>> Pop prediction Data")
                    if len(self.classifiers) > 0:
                        #make a little test prediction to get the shape and see if it works:
                        tempPred = None
                        if features is not None:
                            tfm = features[0][0,:]
                            tfm.shape = (1,) + tfm.shape 
                            tempPred = self.classifiers[0].predict(tfm)
                                            
                        if tempPred is not None:
                            self.prediction = []
                            jobs= []
                            self.count = 0
                            for i in range(len(features)):
                                self.prediction.append(numpy.zeros((features[i].shape[0],) + (tempPred.shape[1],) , 'float32'))
                                for j in range(0,features[i].shape[0],128**2):
                                    for k in range(len(self.classifiers)):
                                        end = min(j+128**2,features[i].shape[0])
                                        job = jobMachine.IlastikJob(ClassifierInteractiveThread.classifierPredict, [self, i, j, end, k, features])
                                        jobs.append(job)
                                
                            self.jobMachine.process(jobs)

                            shape = self.ilastik.project.dataMgr[vs[-1]].dataVol.data.shape

                            tp = []
                            tp.append(self.prediction[0].reshape((shape[2],shape[3],self.prediction[0].shape[-1])))
                            tp.append(self.prediction[1].reshape((shape[1],shape[3],self.prediction[1].shape[-1])))
                            tp.append(self.prediction[2].reshape((shape[1],shape[2],self.prediction[2].shape[-1])))

                            all =  range(len(self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions))
                            not_predicted = numpy.setdiff1d(all, self.classifiers[0].unique_vals - 1)

                            #Axis 0
                            tpc = tp[0]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba.blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)*255.0
                                
                                self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], vs[1], b[0]:b[1],b[2]:b[3]] = margin
#                                seg = segmentationMgr.LocallyDominantSegmentation2D(lb, 1.0)
#                                self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], vs[1], b[0]:b[1],b[2]:b[3]] = seg

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num-1]
                                    item.prediction[vs[0],vs[1],b[0]:b[1],b[2]:b[3]] = (tpc[b[0]:b[1],b[2]:b[3],p_i]* 255).astype(numpy.uint8)

                                for p_i, p_num in enumerate(not_predicted):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num]
                                    item.prediction[vs[0],vs[1],b[0]:b[1],b[2]:b[3]] = 0

                            #Axis 1
                            tpc = tp[1]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba.blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)*255.0
                                seg = segmentationMgr.LocallyDominantSegmentation2D(lb, 1.0)
                                self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], b[0]:b[1],vs[2],b[2]:b[3]] = margin
#                                self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], b[0]:b[1],vs[2],b[2]:b[3]] = seg

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num-1]
                                    item.prediction[vs[0],b[0]:b[1],vs[2],b[2]:b[3]] = (tpc[b[0]:b[1],b[2]:b[3],p_i]* 255).astype(numpy.uint8)

                                for p_i, p_num in enumerate(not_predicted):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num]
                                    item.prediction[vs[0],b[0]:b[1],vs[2],b[2]:b[3]] = 0


                            #Axis 2
                            tpc = tp[2]
                            ba = DM.BlockAccessor2D(tpc[:,:,:])
                            for i in range(ba.blockCount):
                                b = ba.getBlockBounds(i,0)
                                lb = tpc[b[0]:b[1],b[2]:b[3],:]
                                margin = activeLearning.computeEnsembleMargin2D(lb)*255.0
                                seg = segmentationMgr.LocallyDominantSegmentation2D(lb, 1.0)
                                self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], b[0]:b[1],b[2]:b[3], vs[3]] = margin
#                                self.ilastik.project.dataMgr[vs[-1]].dataVol.segmentation[vs[0], b[0]:b[1],b[2]:b[3],vs[3]] = seg

                                for p_i, p_num in enumerate(self.classifiers[0].unique_vals):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num-1]
                                    item.prediction[vs[0],b[0]:b[1],b[2]:b[3],vs[3]] = (tpc[b[0]:b[1],b[2]:b[3],p_i]* 255).astype(numpy.uint8)

                                for p_i, p_num in enumerate(not_predicted):
                                    item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_num]
                                    item.prediction[vs[0],b[0]:b[1],b[2]:b[3],vs[3]] = 0




                        else:
                            print "##################### prediction None #########################"
                    else:
                        print "##################### No Classifiers ############################"
                    if have_qt:
                        self.emit(QtCore.SIGNAL("resultsPending()"))
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




#class ClassifierOnlineThread(QtCore.QThread):
#    def __init__(self, name, features, labels, ids, predictionList, predictionUpdated):
#        QtCore.QThread.__init__(self, None)
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
