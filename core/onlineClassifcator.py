from classificationMgr import *
import lasvm
import numpy

class OnlineClassifier():
    def __init__(self):
        pass
    def start(self,features,labels,ids):
        pass
    def addData(self,features,labels,ids):
        pass
    def removeData(self,ids):
        pass
    def fastLearn(self):
        pass
    def improveSolution(self):
        pass
    def predict(self,features):
        pass

class OnlineLaSvm(OnlineClassifier):
    def __init__(self,cacheSize=1000):
        self.cacheSize=cacheSize
        self.svm=None

    def start(self,features,labels,ids):
        # TODO Cast to float64!
        self.svm=lasvm.createLaSvmMultiPar(1.0,features.shape[1],1.0,0.001,self.cacheSize,True)
        self.addData(features,labels,ids)
        self.svm.enableResampleBorder(0.1)
        self.fastLearn()

    def addData(self,features,labels,ids):
        # TODO Cast to float64!
        features = features
        labels = labels
        labels=labels*2-3;
        print numpy.unique(labels)
        if(self.svm==None):
            raise RuntimeError("run \"start\" before addData")
        print features.dtype
        print labels.dtype
        print ids.dtype
        self.svm.addData(features,labels,ids)

    def removeData(self,ids):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        self.svm.removeData(ids)

    def fastLearn(self):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        print "Begin fast learn"
        self.svm.fastLearn(2,1,True)
        self.svm.finish(True)
        print "End fast learn"

    def improveSolution(self):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        print "Begin improving solution"
        self.svm.optimizeKernelStep(0)
        print "Done improving solution"

    def predict(self,features):
        print "Begin predict"
        pred=self.svm.predict(features)
        print "End predict"
        return (pred+1)/2




