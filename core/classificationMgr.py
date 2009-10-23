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
    def __init__(self, features=None, labels=None):
        ClassifierBase.__init__(self)
        self.classifier = None
        self.treeCount = 5
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
        self.classifierList = deque(self.queueSize)
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
    def __init__(self, trainingQueue, predictDataList, labelWidget, dataMgr):
        threading.Thread.__init__(self)
        self.stopped = False
        self.trainingQueue = trainingQueue
        self.predictDataList = predictDataList
        self.predictResultList = [ deque(maxlen=10) for k in range(0,len(predictDataList))]
        self.predictResultListCounter = [0 for k in range(0,len(predictDataList))]
        self.classifierList = deque(maxlen=20)
        self.labelWidget = labelWidget
        self.dataMgr = dataMgr

        
        
    def run(self):
        init = 1
        self.predictResultNormalized = [None for k in range(0,len(self.predictResultList))]
        
        while not self.stopped:
            print "Waiting for new training data..."
            try:
                (features, labels) = self.trainingQueue.get(True, 0.5)
          
            except QueueEmpty:
                print "No new Training Data available"
            
            if numpy.unique(labels).size < 2:
                if self.stopped:
                    return
                time.sleep(0.5)
                continue
            
            for tmp in range(0,2):
                print "Train classifier and put to Classifier Deque %d" % len(self.classifierList) 
                self.classifierList.append( ClassifierRandomForest(features, labels) )
            
            predictIndex = self.labelWidget.activeImage
            predictItem = self.predictDataList[predictIndex]
            
            print "Predict for Image %d " % predictIndex
            cnt = 0
            for classifier in self.classifierList:
                if predictIndex in classifier.usedForPrediction :
                    continue
                if cnt == 0:
                    print ".",
                    prediction = classifier.predict(predictItem)      
                else:
                    print ".",
                    prediction += classifier.predict(predictItem)
                cnt += 1 
                classifier.usedForPrediction.append(predictIndex)
                self.predictResultList[predictIndex].append((prediction, cnt))
            print ""

            totalCnt = 0
            for p, c in self.predictResultList[predictIndex]:
                if totalCnt == 0:
                    image = p
                else:
                    image += p
                totalCnt += c
            image = image / totalCnt
                
            print "Maximum" ,numpy.max(image)
            print "Minimum", numpy.min(image)
            
            
            displayClassNr = self.labelWidget.activeLabel           
            image = image[:,displayClassNr-1]
            imshape = self.dataMgr[predictIndex].data.shape
            image = image.reshape( [imshape[0],imshape[1]] )
            
            
            self.labelWidget.predictionImage_add(predictIndex, displayClassNr, image)
            self.labelWidget.predictionImage_setOpacity(predictIndex, displayClassNr, 0.7)
                    
                    
                    
                
            
        