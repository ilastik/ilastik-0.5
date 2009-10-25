import numpy
import threading 
import multiprocessing
import time
from Queue import Queue as queue
from Queue import Empty as QueueEmpty
from collections import deque
from PyQt4 import QtCore

import numpy

def interactiveMessagePrint(* args):
    pass
    #print args

try:
    from vigra import vigranumpycmodule as vm
except ImportError:
    try:
        import vigranumpycmodule as vm
    except ImportError:
        sys.exit("vigranumpycmodule not found!")

class ClassificationMgr(object):
    def __init__(self):
        pass
    

class ClassifierBase(object):
    def __init__(self):
        self.usedForPrediction = set()
    
class ClassifierRandomForest(ClassifierBase):
    def __init__(self, features=None, labels=None, treeCount=10):
        ClassifierBase.__init__(self)
        self.classifier = None
        self.treeCount = treeCount
#        if features and labels:
    #            self.train(features, labels)
        self.train(features, labels)
    
    def train(self, features, labels):
        
        if features.shape[0] != labels.shape[0]:
            interactiveMessagePrint( " 3, 2 ,1 ... BOOOM!! #features != # labels" )
            
        if not labels.dtype == numpy.uint32:
            labels = numpy.array(labels,dtype=numpy.uint32)
        if not features == numpy.float32:
            features = numpy.array(features,dtype=numpy.float32)
        self.classifier = vm.RandomForest(features, labels, self.treeCount)
        
    
    def predict(self, target):
        if self.classifier:
            if not target.dtype == numpy.float32:
                target = numpy.array(target, dtype=numpy.float32)
            return self.classifier.predictProbabilities(target)    
          

class ClassifierSVM(ClassifierBase):
    def __init__(self):
        ClassifierBase.__init__(self)
        pass
    
    def train(self):
        pass
    
    def predict(self):
        pass
    
class ClassifierTrainThread(threading.Thread):
    def __init__(self, queueSize, featLabelTupel):
        threading.Thread.__init__(self)
        self.queueSize = queueSize
        self.featLabelTupel = featLabelTupel
        self.count = 0
        self.classifierList = deque(maxlen=self.queueSize)
        self.stopped = False
    
    def run(self):
        while not self.featLabelTupel.empty():
            (features, labels) = self.featLabelTupel.get()
            while self.count != self.queueSize:
                self.classifierList.append( ClassifierRandomForest(features, labels) )
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
    def __init__(self, trainingQueue, predictDataList, resultList, labelWidget, numberOfClasses, numberOfClassifiers=10, treeCount=10):
        threading.Thread.__init__(self)
        self.stopped = False
        self.trainingQueue = trainingQueue
        self.resultList = resultList
        self.predictDataList = predictDataList
        self.numberOfClassifiers = numberOfClassifiers
        self.treeCount = treeCount
        self.classifierList = deque(maxlen=numberOfClassifiers)
        self.labelWidget = labelWidget
        self.resultLock = threading.Lock() 
        self.result = deque(maxlen=1)
        self.numberOfClasses = numberOfClasses
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifierList)
    
    def finishPredictions(self):
        predictItemIndices = range(0,len(self.predictDataList))
        for k in predictItemIndices:
            for classifier in self.classifierList:
                if not k in classifier.usedForPrediction:
                    predictItem = self.predictDataList[k]
                    prediction = classifier.predict(predictItem)      
                    classifier.usedForPrediction.add(k)
                    self.resultList[k].append(prediction) 
        for k in self.resultList:
            k = list(k)
                    
    def run(self):
        while not self.stopped:
            #print ",",
            try:
                features, labels = self.trainingQueue.pop()    
                newTrainingPending = self.numberOfClassifiers
            except IndexError:
                newTrainingPending -= 1
            
            if numpy.unique(labels).size < self.numberOfClasses:
                if self.stopped:
                    return
                time.sleep(0.01)
                continue
            
            # Learn Classifier new with newest Data
            if newTrainingPending > 1:
                interactiveMessagePrint( "New Training Data used %3.1f %% " % (100 - 100*(float(newTrainingPending)/self.numberOfClassifiers)) )
                self.classifierList.append( ClassifierRandomForest(features, labels, treeCount=self.treeCount) )
            else:
                interactiveMessagePrint( "All Classifiers learned" )
            
            # Predict wich classifiers
            predictIndex = self.labelWidget.activeImage
            predictItem = self.predictDataList[predictIndex]
            #print "predictIndex", predictIndex
            
            newPredictionsMade = False
            for classifier in self.classifierList:
                if predictIndex in classifier.usedForPrediction:
                    continue
                newPredictionsMade = True
                prediction = classifier.predict(predictItem)      
                classifier.usedForPrediction.add(predictIndex)
                self.resultList[predictIndex].append(prediction)   
            
            if not newPredictionsMade and len(self.predictDataList) > 1:
                # Predict the others while idle
                
                restList = range(0,len(self.predictDataList))
                restList.remove(predictIndex)
                for k in restList:
                    for classifier in self.classifierList:
                        if not k in classifier.usedForPrediction:
                            interactiveMessagePrint( "Time to Predict other images once" ) 
                            predictItemIdle = self.predictDataList[k]
                            predictionIdle = classifier.predict(predictItemIdle)      
                            classifier.usedForPrediction.add(k)
                            self.resultList[k].append(predictionIdle) 
                            break
                        interactiveMessagePrint( "Images %d is fully predicted with curren classifier set" % k ) 
            
            if len(self.resultList[predictIndex]) == 0:
                continue
            else:
                if newPredictionsMade:
                    image = reduce(numpy.ndarray.__add__, self.resultList[predictIndex]) / len(self.resultList[predictIndex])
            
            self.resultLock.acquire()
            self.result.append(image)
            self.resultLock.release()

            interactiveMessagePrint( "CLOCK **********************************************" )
            
            # Ist leider zu langsam, siehe interactiveTimer
            #self.labelWidget.emit(QtCore.SIGNAL("newPredictionPending()"))
             
               
        