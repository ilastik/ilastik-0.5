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
from core.utilities import irange
from core import onlineClassifcator

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
        
        print "Building trees"
        self.classifier = vigra.learning.RandomForestOld(features, labels, treeCount=treeCount)
        
        self.treeCount = treeCount
        if features is not None and labels is not None:
            pass
            #self.train(features, labels)
        #self.train(features, labels)
        self.usedForPrediction = set()
    
    def train(self, features, labels):
        
        if features.shape[0] != labels.shape[0]:
            interactiveMessagePrint( " 3, 2 ,1 ... BOOOM!! #features != # labels" )
            
        if not labels.dtype == numpy.uint32:
            labels = labels.astype(numpy.uint32)
        if not features.dtype == numpy.float32:
            features = features.astype(numpy.float32)
        # print "Create RF with ",self.treeCount," trees"
        #self.classifier = vigra.classification.RandomForest(features, labels, self.treeCount)
        if labels.ndim == 1:
            labels.shape = labels.shape + (1,)
        labels = labels - 1
        
        self.classifier.learnRF(features, labels)
        print "tree Count", self.treeCount
        
    
    def predict(self, target):
        #3d: check that only 1D data arrives here
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
            for classifier in self.dataMgr.classifiers:
                if cnt == 0:
                    interactiveMessagePrint ( "Classifier %d prediction" % cnt )
                    prediction = classifier.predict(item.getFeatureMatrix())     
                else:
                    interactiveMessagePrint( "Classifier %d prediction" % cnt )
                    prediction += classifier.predict(item.getFeatureMatrix())
                cnt += 1
                self.count += 1
            prediction = prediction / cnt
            #TODO: Time ! synchronize with featureMgr...
            item.prediction = prediction.reshape(item.dataVol.labels.data.shape[0:-1] + (prediction.shape[-1],))

class ClassifierInteractiveThread(threading.Thread):
    def __init__(self, trainingQueue, predictQueue, resultQueue, numberOfClassifiers=5, treeCount=5):
        threading.Thread.__init__(self)
        self.stopped = False
        
        
        self.trainingQueue = trainingQueue
        self.predictionQueue = predictQueue
        self.resultQueue = resultQueue
        
        self.resultList = deque(maxlen=10)
               
        self.numberOfClassifiers = numberOfClassifiers    

        self.treeCount = treeCount
        
        self.classifierList = deque(maxlen=numberOfClassifiers)
        
        self.result = deque(maxlen=1) 
        
        
    def classifierListFull(self):
        return self.numberOfClassifiers == len(self.classifierList)
    
    def finishPredictions(self):
        # Make sure that at last on classifier is used for each image
        pass
                    
    def run(self):
        while not self.stopped:
            try:
                features, labels = self.trainingQueue.pop()    
                interactiveMessagePrint("1>> Pop training Data")
                for i in range(self.numberOfClassifiers):
                    self.classifierList.append( ClassifierRandomForest(features, labels, treeCount=self.treeCount) )
            except IndexError:
                interactiveMessagePrint("1>> No training Data")
               
            try:
                pq = self.predictionQueue.pop()
                vs = pq[0]
                features = pq[1]
                interactiveMessagePrint("1>> Pop prediction Data")
                prediction = self.classifierList[0].predict(features)
                size = 1
                for iii in range(len(self.classifierList) - 1):
                    classifier = self.classifierList[iii + 1]
                    prediction += classifier.predict(features)
                    size += 1
                self.resultQueue.append((prediction / size, vs))  
            except IndexError:
                interactiveMessagePrint("1>> No prediction Data")
            

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
            
            
        
    
    

