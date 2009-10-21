import numpy
import threading 
import multiprocessing
import time
from Queue import PriorityQueue as pq
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
        pass
    
class ClassifierRandomForest(ClassifierBase):
    def __init__(self, features=None, labels=None):
        ClassifierBase.__init__(self)
        self.classifier = None
        self.treeCount = 5
#        if features and labels:
#            self.train(features, labels)
        self.train(features, labels)
    
    def train(self, features, labels):
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
        self.classifierList = []
        self.stopped = False
    
    def run(self):
        while not self.featLabelTupel.empty():
            (features, labels) = self.featLabelTupel.get()
            while self.count != self.queueSize:
                self.classifierList.append( ClassifierRandomForest(features, labels) )
                self.count += 1
                
class ClassifierPredictThread(threading.Thread):
    def __init__(self, classifierList, featureList):
        threading.Thread.__init__(self)
        self.classifierList = classifierList
        self.count = 0
        self.featureList = featureList
        self.stopped = False
        self.predictionList = []
    
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