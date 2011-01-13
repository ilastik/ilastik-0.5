from classifierBase import *

from PyQt4.QtGui import QInputDialog

import numpy, h5py

class ClassifierRandomForest(ClassifierBase):
    #human readable information
    name = "Random forest classifier" 
    description = "Random forest classifier with extensions"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset
    minContext = 0
    
    #The _total_ number of trees.
    #For performance reason, the classifier is split up into self.numWorkers
    #parts.
    treeCount = 100

    def __init__(self):
        ClassifierBase.__init__(self)
    
    @classmethod
    def settings(cls):
        (number, ok) = QInputDialog.getInt(None, "Random Forest parameters", "Number of trees", cls.treeCount, 20, 255)
        if ok:
          cls.treeCount = number
        
        print "setting number of trees to", cls.treeCount

    def train(self, features, labels, isInteractive):
        thisTreeCount = int(self.treeCount/self.numWorkers)
        if(self.workerNumber == self.numWorkers-1):
            thisTreeCount += self.treeCount % self.numWorkers
        #print "RandomForest training [%d of %d] with %d trees" % (self.workerNumber, self.numWorkers, thisTreeCount)
        
        self.RF = None
        if features is None:
            return
        if features.shape[0] != labels.shape[0]:
            # #features != # labels"
            return
        if not labels.dtype == numpy.uint32:
            labels = labels.astype(numpy.uint32)
        if not features.dtype == numpy.float32:
            features = features.astype(numpy.float32)

        if labels.ndim == 1:
            labels.shape = labels.shape + (1,)
        
        self.unique_vals = numpy.unique(labels)
        
        # Have to set this becauce the new rf dont set mtry properly by default
        mtry = max(1,int(numpy.sqrt(features.shape[1]))+1) 
        
        self.RF = vigra.learning.RandomForest(treeCount=thisTreeCount)
        
        oob = self.RF.learnRF(features, labels)
        ClassifierBase.printLock.acquire()
        print "Out-of-bag error %4.3f" % oob
        ClassifierBase.printLock.release()
    def predict(self, features):
        #3d: check that only 1D data arrives here
        if self.RF is not None and features is not None and len(self.unique_vals) > 1:
            if not features.dtype == numpy.float32:
                features = numpy.array(features, dtype=numpy.float32)
            return self.RF.predictProbabilities(features)
        else:
            return None
        
    def serialize(self, fileName, pathInFile, overwriteFlag=False):
        # cannot serilaze into grp because can not pass h5py handle to vigra yet
        # works only with new RF version
        self.RF.writeHDF5(fileName, pathInFile, overwriteFlag)

    @classmethod
    def deserialize(cls, h5G):
        """FIXME: we do not load the complete random forest here, but require the user to re-train
           after loading the project file. The only thing we do load is the total number of
           trees (in a very hackish way)."""
        thisForestPath = h5G.name
        allForestsPath = thisForestPath[0:thisForestPath.rfind("/")]
      
        if allForestsPath in h5G.file:
          trees = h5G.file[allForestsPath].keys()
          
          treeCount = 0
          for t in trees:
              treeCount += h5G.file[allForestsPath+"/"+t+"/_options/tree_count_"][0]
          print "total number of RandomForest trees = ", treeCount
          ClassifierRandomForest.treeCount = treeCount
      
        return 0

