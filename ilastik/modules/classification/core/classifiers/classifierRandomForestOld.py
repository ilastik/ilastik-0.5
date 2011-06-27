from classifierBase import *

#*******************************************************************************
# C l a s s i f i e r R a n d o m F o r e s t O l d                            *
#*******************************************************************************

#class ClassifierRandomForestOld(ClassifierBase):
#    #human readable information
#    name = "Random forest classifier (stable)" 
#    description = "Basic random forest classifier (no extensions)"
#    author = "HCI, University of Heidelberg"
#    homepage = "http://hci.iwr.uni-heidelberg.de"
#
#    #minimum required isotropic context
#    #0 means pixel based classification
#    #-1 means whole dataset
#    minContext = 0
#    treeCount = 10
#
#    def __init__(self, treeCount = 10):
#        ClassifierBase.__init__(self)
#        self.treeCount = treeCount
#
#    def train(self, features, labels, interactive):
#        if features is None:
#            return
#
#        if not labels.dtype == numpy.uint32:
#            labels = labels.astype(numpy.uint32)
#        if not features.dtype == numpy.float32:
#            features = features.astype(numpy.float32)
#
#        self.unique_vals = numpy.unique(labels)
#
#        if len(self.unique_vals) > 1:
#            # print "Learning RF %d trees: %d labels given, %d classes, and %d features " % (treeCount, features.shape[0], len(numpy.unique(labels)), features.shape[1])
#            self.RF = vigra.learning.RandomForestOld(features, labels, treeCount=self.treeCount)
#            #self.RF = vigra.learning.RandomForest(treeCount=self.treeCount)
#            #self.RF.learnRF(features, labels)
#        else:
#            self.RF = None
#
#        self.labels = labels
#        self.features = features
#
#    def predict(self, features):
#        #3d: check that only 1D data arrives here
#        if self.RF is not None and features is not None:
#            if not features.dtype == numpy.float32:
#                features = numpy.array(features, dtype=numpy.float32)
#            return self.RF.predictProbabilities(features)
#        else:
#            return None
#        
#    def serialize(self, fileName, pathInFile, overWriteFlage):
#        raise IOError('This classifier cannot be saved.')
#
##    @classmethod
##    def deserialize(cls, fileName, pathInFile):
##        classifier = cls()
##        classifier.RF = vigra.learning.RandomForest(fileName, pathInFile)
##        classifier.treeCount = classifier.RF.treeCount
##        return classifier
