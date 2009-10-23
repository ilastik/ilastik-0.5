import numpy
import threading 
import multiprocessing
import time
from Queue import Queue as queue
from Queue import Empty as QueueEmpty
from collections import deque

import numpy

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
        self.usedForPrediction = []
    
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
            print " 3, 2 ,1 ... BOOOM!! #features != # labels"
            
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
            print "Feature Item"
            for classifier in self.classifierList:
                if cnt == 0:
                    print "Classifier %d prediction" % cnt
                    prediction = classifier.predict(feature)      
                else:
                    print "Classifier %d prediction" % cnt
                    prediction += classifier.predict(feature)
                cnt += 1
                self.count += 1
            self.predictionList.append(prediction / cnt)

class ClassifierInteractiveThread(threading.Thread):
    def __init__(self, trainingQueue, predictDataList, resultList, labelWidget):
        threading.Thread.__init__(self)
        self.stopped = False
        self.trainingQueue = trainingQueue
        self.resultList = resultList
        self.predictDataList = predictDataList
        self.classifierList = deque(maxlen=10)
        self.labelWidget = labelWidget
        self.resultLock = threading.Lock() 
        self.result = numpy.array(1)
        
    def run(self):
        while not self.stopped:
            print "Waiting for new training data..."
            try:
                (features, labels) = self.trainingQueue.pop()
            except IndexError:
                pass
            
            if numpy.unique(labels).size < 2:
                if self.stopped:
                    return
                time.sleep(0.2)
                continue
            
            # Learn Classifier new with newest Data
            self.classifierList.append( ClassifierRandomForest(features, labels) )
            self.classifierList.append( ClassifierRandomForest(features, labels) )
            
            # Predict wich classifiers
            predictIndex = self.labelWidget.activeImage
            predictItem = self.predictDataList[predictIndex]
            print "predictIndex", predictIndex
            
            for classifier in self.classifierList:
                if predictIndex in classifier.usedForPrediction:
                    continue
                prediction = classifier.predict(predictItem)      
                classifier.usedForPrediction.append(predictIndex)
                
                self.resultLock.acquire()
                self.resultList[predictIndex].append(prediction)   
                self.resultLock.release()
        
            predictIndex = 0
            cnt = 0
            for p in self.resultList[predictIndex]:
                if cnt == 0:
                    image = p
                else:
                    image += p
                cnt += 1
            if cnt == 0:
                continue
            
            self.resultLock.acquire()
            self.result = image / cnt
            self.resultLock.release()
             
               
        