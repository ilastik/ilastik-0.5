from classifierBase import *

class ClassifierRandomForest(ClassifierBase):
    #human readable information
    name = "RandomForest classifier" 
    description = "Basic RandomForest classifier"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset
    minContext = 0
    treeCount = 10

    def __init__(self, treeCount = 10):
        self.treeCount = treeCount
        ClassifierBase.__init__(self)

    def train(self, features, labels):
        if features is None:
            return

        if not labels.dtype == numpy.uint32:
            labels = labels.astype(numpy.uint32)
        if not features.dtype == numpy.float32:
            features = features.astype(numpy.float32)

        self.unique_vals = numpy.unique(labels)

        if len(self.unique_vals) > 1:
            # print "Learning RF %d trees: %d labels given, %d classes, and %d features " % (treeCount, features.shape[0], len(numpy.unique(labels)), features.shape[1])
            self.RF = vigra.learning.RandomForestOld(features, labels, treeCount=self.treeCount)
            #self.RF = vigra.learning.RandomForest(treeCount=self.treeCount)
            #self.RF.learnRF(features, labels)
        else:
            self.RF = None

        self.labels = labels
        self.features = features

    def predict(self, features):
        #3d: check that only 1D data arrives here
        if self.RF is not None and features is not None:
            if not features.dtype == numpy.float32:
                features = numpy.array(features, dtype=numpy.float32)
            return self.RF.predictProbabilities(features)
        else:
            return None
        
    def serialize(self, fileName, pathInFile):
        # cannot serilaze into grp because can not pass h5py handle to vigra yet
        # works only with new RF version
        self.RF.writeHDF5(fileName, pathInFile, True)

    @classmethod
    def deserialize(cls, fileName, pathInFile):
        classifier = cls()
        classifier.RF = vigra.learning.RandomForest(fileName, pathInFile)
        classifier.treeCount = classifier.RF.treeCount
        return classifier


#NEW RandomForest from Raoul: (reenable when new RF performance bug is fixed) :

#    def train(self, labels, features):
#
#        if features.shape[0] != labels.shape[0]:
#            interactiveMessagePrint( " 3, 2 ,1 ... BOOOM!! #features != # labels" )
#
#        if not labels.dtype == numpy.uint32:
#            labels = labels.astype(numpy.uint32)
#        if not features.dtype == numpy.float32:
#            features = features.astype(numpy.float32)
#        # print "Create RF with ",self.treeCount," trees"
#        #self.classifier = vigra.classification.RandomForest(features, labels, self.treeCount)
#        if labels.ndim == 1:
#            labels.shape = labels.shape + (1,)
#        labels = labels - 1
#
#        self.classifier.learnRF(features, labels)
#        #print "tree Count", self.treeCount