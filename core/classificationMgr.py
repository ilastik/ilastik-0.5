import numpy
import threading 
import multiprocessing
import time
import sys
import os
from Queue import Queue as queue
from Queue import Empty as QueueEmpty
from collections import deque
from PyQt4 import QtCore
sys.path.append('..')
from core.utilities import irange
from core import onlineClassifcator

import numpy

def interactiveMessagePrint(* args):
    #pass
    print "Thread: ", args

try:
    import vigra
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
        self.classifier = None
        self.treeCount = treeCount
#        if features and labels:
    #            self.train(features, labels)
        self.train(features, labels)
        self.usedForPrediction = set()
    
    def train(self, features, labels):
        
        if features.shape[0] != labels.shape[0]:
            interactiveMessagePrint( " 3, 2 ,1 ... BOOOM!! #features != # labels" )
            
        if not labels.dtype == numpy.uint32:
            labels = numpy.array(labels,dtype=numpy.uint32)
        if not features == numpy.float32:
            features = numpy.array(features,dtype=numpy.float32)
        self.classifier = vigra.classification.RandomForest(features, labels, self.treeCount)
        
    
    def predict(self, target):
        if self.classifier:
            if not target.dtype == numpy.float32:
                target = numpy.array(target, dtype=numpy.float32)
            return self.classifier.predictProbabilities(target)    
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
    def __init__(self, queueSize, featLabelTupel):
        threading.Thread.__init__(self)
        self.queueSize = 1
        self.featLabelTupel = featLabelTupel
        self.count = 0
        self.classifierList = deque(maxlen=self.queueSize)
        self.stopped = False
        self.classifier = ClassifierRandomForest
    
    def run(self):
        while not self.featLabelTupel.empty():
            (features, labels) = self.featLabelTupel.get()
            while self.count != self.queueSize:
                self.classifierList.append( self.classifier(features, labels) )
                self.count += 1
                
class ClassifierPredictThread(threading.Thread):
    def __init__(self, classifierList, featureList, featureList_dataIndices):
        threading.Thread.__init__(self)
        self.classifierList = classifierList
        self.count = 0
        self.featureList = featureList
        self.featureList_dataIndices = featureList_dataIndices
        self.stopped = False
        self.predictionList = []
        self.predictionList_dataIndices = featureList_dataIndices
    
    def run(self):
        for feature in self.featureList:
            cnt = 0
            interactiveMessagePrint( "Feature Item" )
            for classifier in self.classifierList:
                if cnt == 0:
                    interactiveMessagePrint ( "Classifier %d prediction" % cnt )
                    prediction = classifier.predict(feature)      
                else:
                    interactiveMessagePrint( "Classifier %d prediction" % cnt )
                    prediction += classifier.predict(feature)
                cnt += 1
                self.count += 1
            self.predictionList.append(prediction / cnt)

class ClassifierInteractiveThread(threading.Thread):
    def __init__(self, trainingQueue, predictDataList, labelWidget, numberOfClasses, numberOfClassifiers=10, treeCount=10):
        threading.Thread.__init__(self)
        self.stopped = False
        self.trainingQueue = trainingQueue
        self.resultList = [deque(maxlen=10) for k in range(0,len(predictDataList))]
        self.predictDataList = predictDataList
        self.numberOfClassifiers = numberOfClassifiers
        self.treeCount = treeCount
        self.classifierList = deque(maxlen=numberOfClassifiers)
        self.labelWidget = labelWidget
        self.resultLock = threading.Lock() 
        self.numberOfClasses = numberOfClasses
        self.result = [deque(maxlen=1) for k in range(len(self.predictDataList))]
        for ind, pred in irange(self.result):
            initPred = numpy.zeros(( self.predictDataList[ind].shape[0], self.numberOfClasses), dtype=numpy.float32 )
            pred.append(initPred)
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifierList)
    
    def finishPredictions(self):
        predictItemIndices = range(0,len(self.predictDataList))
        for k in predictItemIndices:
            for classifier in self.classifierList:
                if not k in classifier.usedForPrediction:
                    predictItemIdle = self.predictDataList[k]
                    predictionIdle = classifier.predict(predictItemIdle)      
                    classifier.usedForPrediction.add(k)
                    self.resultList[k].append(predictionIdle) 
        for k in self.resultList:
            k = list(k)
                    
    def run(self):
        while not self.stopped:
            try:
                features, labels = self.trainingQueue.pop()    
                newTrainingPending = self.numberOfClassifiers
            except IndexError:
                newTrainingPending -= 1
            
            if numpy.unique(labels).size < self.numberOfClasses:
                continue
            
            # Learn Classifier new with newest Data
            if newTrainingPending > 1:
                interactiveMessagePrint("New Training Data used %3.1f %% " % (100 - 100*(float(newTrainingPending)/self.numberOfClassifiers)) )
                self.classifierList.append( ClassifierRandomForest(features, labels, treeCount=self.treeCount) )
            else:
                interactiveMessagePrint("All Classifiers learned" )
            
            predictIndex = self.labelWidget.activeImage
            predictItem = self.predictDataList[predictIndex]
            
            newPredictionsMade = 0
            for classifier in self.classifierList:
                if predictIndex in classifier.usedForPrediction:
                    continue
                newPredictionsMade += 1
                prediction = classifier.predict(predictItem)      
                classifier.usedForPrediction.add(predictIndex)
                self.resultList[predictIndex].append(prediction)   
            
            if newPredictionsMade < 1 and len(self.predictDataList) > 1:
                # Predict the others while idle
                restList = range(0,len(self.predictDataList))
                restList.remove(predictIndex)
                for k in restList:
                    for classifier in self.classifierList:
                        if not k in classifier.usedForPrediction:
                            print ".",
                            predictItemIdle = self.predictDataList[k]
                            predictionIdle = classifier.predict(predictItemIdle)      
                            classifier.usedForPrediction.add(k)
                            self.resultList[k].append(predictionIdle) 
                            break

            image = reduce(numpy.ndarray.__add__, self.resultList[predictIndex]) / len(self.resultList[predictIndex])
            
            self.resultLock.acquire()
            self.result[predictIndex].append(image)
            interactiveMessagePrint("appending new prediction of image %d" % predictIndex)
            self.resultLock.release()

class ClassifierOnlineThread(threading.Thread):
    def __init__(self, name,features, labels, ids, predictionList, predictionUpdated):
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
        
        self.predictionList = predictionList
        self.activeImageIndex = 0
        
        self.predictions = [deque(maxlen=1) for k in range(len(predictionList))]
        self.predictionUpdated = predictionUpdated
    
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
            elif action == 'improve':
                # get an segfault here
                self.classifier.improveSolution()
            elif action == 'noop':
                pass
                
            if self.commandQueue.empty():
                result = self.classifier.predict(self.predictionList[self.activeImageIndex])
                self.predictions[self.activeImageIndex].append(result)
                self.predictionUpdated()
            
            
        
    
    

