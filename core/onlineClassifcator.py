from classificationMgr import *
import lasvm
import numpy
import math
import matplotlib as mpl

try:
    import vigra
except ImportError:
    sys.exit("vigra module not found!")

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

class CumulativeOnlineClassifier(OnlineClassifier):
    """Base class for all online classifiers, which can not unlearn and need to be shown the data from the last around every round"""
    def __init__(self):
        self.labels=None
        self.features=None
        self.ids=None

    def start(self,features,labels,ids):
        self.features=features
        self.labels=labels
        self.ids=ids
        print "Start features:",self.features

    def addData(self,features,labels,ids):
        print "Features before:",self.features
        print "Adding features:",features
        self.features=numpy.append(self.features,features,axis=0)
        print "Result:",self.features
        self.labels=numpy.append(self.labels,labels)
        self.ids=numpy.append(self.ids,ids)

    def removeData(self,ids):
        indexes=ids
        for i in xrange(len(indexes)):
            for j in xrange(len(indexes)):
                if self.ids[j]==indexes[i]:
                    indexes[i]=j
                    break
            raise RuntimeError('removing a non existing example from online learner')
        #remove all those selected things
        self.ids=numpy.delete(self.ids,indexes)
        self.labels=numpy.delete(self.labels,indexes)
        self.features=numpy.delete(self.features,indexes,axis=0)

class OnlineRF(CumulativeOnlineClassifier):
    def __init__(self,tree_count=100):
        CumulativeOnlineClassifier.__init__(self)
        self.rf=None
        self.tree_count=tree_count
        self.learnedRange=0

    def start(self,features,labels,ids):
        CumulativeOnlineClassifier.start(self,features,labels.astype(numpy.uint32),ids)
        self.startRF()

    def startRF(self):
        self.rf=vigra.classification.RandomForest(self.features,self.labels,self.tree_count,prepare_online_learning=True)
        self.learnedRange=len(self.labels.flatten())

    def addData(self,features,labels,ids):
        CumulativeOnlineClassifier.addData(self,features,labels.astype(numpy.uint32),ids)

    def removeData(self,ids):
        CumulativeOnlineClassifier.removeData(self,ids)
        self.learnedRange=0

    def fastLearn(self):
        #learn everything not learned so far
        if(self.learnedRange==0):
            self.startRF()
        else:
            self.rf.onlineLearn(self.features,self.labels,self.learnedRange)
        self.learnedRange=len(self.labels.flatten())

    def improveSolution(self):
        #TODO: relearn trees
        pass

    def predict(self,features):
        return self.rf.predictProbabilities(features)



class OnlineLaSvm(OnlineClassifier):
    def __init__(self,cacheSize=1000):
        self.cacheSize=cacheSize
        self.svm=None
        #mpl.interactive(True)
        #mpl.use('WXAgg')

    def start(self,features,labels,ids):
        # TODO Cast to float64!
        self.svm=lasvm.createLaSvmMultiPar(1.0,features.shape[1],1.0,0.001,self.cacheSize,True)
        self.addData(features,labels,ids)
        self.svm.startGuessParameters()
        print numpy.min(features.flatten())
        print numpy.max(features.flatten())
        self.svm.enableResampleBorder(0.1)
        self.fastLearn()
        self.numFeatures=features.shape[1]
        f=open('./g_run.txt','w')
        f_v=open('./var_run.txt','w')
        f.close()
        f_v.close()
        #pylab.figure()

    def addData(self,features,labels,ids):
        # TODO Cast to float64!
        features = features
        labels = labels
        labels=labels*2-3;
        if(self.svm==None):
            raise RuntimeError("run \"start\" before addData")
        print features.dtype
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
        f=open('g_run.txt','a')
        f_v=open('./var_run.txt','a')
        for i in xrange(self.numFeatures):
            f.write(repr(math.log(self.svm.gamma(i))))
            f_v.write(repr(self.svm.variance(i)))
            if i==self.numFeatures-1:
                f.write("\n")
                f_v.write("\n")
            else:
                f.write("\t")
                f_v.write("\t")
        f.close()
        f_v.close()

    def predict(self,features):
        print "Begin predict"
        pred=self.svm.predictF(features)
        pred=self.svm.predictFdualCoverTree(features,0.001);
        print "End predict"
        pred=(pred>0.0)
        pred=(pred.astype(numpy.int32)*2)-1
        pred=pred.reshape((pred.shape[0],1))
        return numpy.append(1.0-(pred+1)/2,(pred+1)/2.0,axis=1)




