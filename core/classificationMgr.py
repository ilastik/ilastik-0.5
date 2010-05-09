# -*- coding: utf-8 -*-
import numpy
import threading 
#import multiprocessing
import time
import sys
import os
from Queue import Queue as queue
from Queue import Empty as QueueEmpty
from collections import deque
from PyQt4 import QtCore
from core.utilities import irange
from core import onlineClassifcator
from core import activeLearning

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
        
        interactiveMessagePrint("Building trees..")
        if len(numpy.unique(labels)) > 1:
            self.classifier = vigra.learning.RandomForestOld(features, labels, treeCount=treeCount)
        else:
            self.classifier = None
            
        self.treeCount = treeCount

    
#    def train(self, features, labels):
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
#        print "tree Count", self.treeCount
        
    
    def predict(self, target):
        #3d: check that only 1D data arrives here
        if self.classifier is not None:
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
     
    
class ClassifierTrainThread(threading.Thread):
    def __init__(self, queueSize, dataMgr):
        threading.Thread.__init__(self)
        self.numClassifiers = queueSize
        self.dataMgr = dataMgr
        self.count = 0
        self.classifierList = []
        self.stopped = False
        self.classifier = ClassifierRandomForest
    
    def run(self):
        F, L = self.dataMgr.getTrainingMatrix()

        classifiers = []
        for i in range(self.numClassifiers):
            classifiers.append( self.classifier(F, L))
            self.count += 1
        self.dataMgr.classifiers = classifiers
                
class ClassifierPredictThread(threading.Thread):
    def __init__(self, dataMgr):
        threading.Thread.__init__(self)
        self.count = 0
        self.dataMgr = dataMgr
        self.stopped = False

    
    def run(self):
        for item in self.dataMgr:
            cnt = 0
            interactiveMessagePrint( "Feature Item" )
            interactiveMessagePrint ( "Classifier %d prediction" % cnt )
            prediction = self.dataMgr.classifiers[0].predict(item.getFeatureMatrix())
            cnt = 1
            if prediction is not None:
                
                for ii in range(len(self.dataMgr.classifiers) - 1) :
                    interactiveMessagePrint( "Classifier %d prediction" % cnt )
                    prediction += self.dataMgr.classifiers[ii+1].predict(item.getFeatureMatrix())
                    cnt += 1
                    self.count += 1
                prediction = prediction / cnt
                #TODO: Time ! synchronize with featureMgr...
                item.prediction = prediction.reshape(item.dataVol.data.shape[0:-1] + (prediction.shape[-1],))

class ClassifierInteractiveThread(QtCore.QObject, threading.Thread):
    def __init__(self, parent, trainingQueue, predictQueue, resultQueue, numberOfClassifiers=5, treeCount=5):
        threading.Thread.__init__(self)
        QtCore.QObject.__init__(self)

        self.ilastik = parent
        
        self.stopped = False
        
        
        self.trainingQueue = trainingQueue
        self.predictionQueue = predictQueue
        self.resultQueue = resultQueue
        
        self.resultList = deque(maxlen=10)
               
        self.numberOfClassifiers = numberOfClassifiers    

        self.treeCount = treeCount
        
        self.classifierList = deque(maxlen=numberOfClassifiers)
        
        self.result = deque(maxlen=1)

        self.dataPending = threading.Event()
        self.dataPending.clear()
        
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifierList)
    
                    
    def run(self):
        self.ilastik.project.dataMgr.getTrainingMatrix()
        self.dataPending.set()
        while not self.stopped:
            self.dataPending.wait()
            self.dataPending.clear()
            if not self.stopped: #no needed, but speeds up the final thread.join()
                self.ilastik.activeImageLock.acquire()
                newLabels = self.ilastik.labelWidget.getPendingLabels()
                if len(newLabels) > 0:
                    features,labels = self.ilastik.project.dataMgr.updateTrainingMatrix(self.ilastik.activeImage, newLabels)
                    print features.shape
                    interactiveMessagePrint("1>> Pop training Data")
                    for i in range(self.numberOfClassifiers):
                        self.classifierList.append( ClassifierRandomForest(features, labels, treeCount=self.treeCount) )
                
                vs = self.ilastik.labelWidget.getVisibleState()
                features = self.ilastik.project.dataMgr[self.ilastik.activeImage].getFeatureMatrixForViewState(vs)
                vs.append(self.ilastik.activeImage)

                interactiveMessagePrint("1>> Pop prediction Data")
                if len(self.classifierList) > 0:
                    prediction = self.classifierList[0].predict(features)
                    if prediction is not None:
                        size = 1
                        for iii in range(len(self.classifierList) - 1):
                            classifier = self.classifierList[iii + 1]
                            prediction += classifier.predict(features)
                            size += 1
                                                
                        predictions = prediction / size
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
                                               
                        self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], vs[1], :, :] = margin0[:,:]
                        self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], :, vs[2], :] = margin1[:,:]
                        self.ilastik.project.dataMgr[vs[-1]].dataVol.uncertainty[vs[0], :, :, vs[3]] = margin2[:,:]
                        
                        for p_i in range(ax0.shape[1]):
                            item = self.ilastik.project.dataMgr[vs[-1]].dataVol.labels.descriptions[p_i]
                            item.prediction[vs[0],vs[1],:,:] = (tp0[:,:,p_i]* 255).astype(numpy.uint8)
                            item.prediction[vs[0],:,vs[2],:] = (tp1[:,:,p_i]* 255).astype(numpy.uint8)
                            item.prediction[vs[0],:,:,vs[3]] = (tp2[:,:,p_i]* 255).astype(numpy.uint8)
                        
                        self.emit(QtCore.SIGNAL("resultsPending()"))
                self.ilastik.activeImageLock.release()


class ClassifierOnlineThread(threading.Thread):
    def __init__(self, name, features, labels, ids, predictionList, predictionUpdated):
        threading.Thread.__init__(self)
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
            
            
        
    
    

