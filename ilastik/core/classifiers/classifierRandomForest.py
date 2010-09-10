from classifierBase import *

class ClassifierRandomForest(ClassifierBase):
    #human readable information
    name = "RandomForest classifier New" 
    description = "Basic RandomForest classifier with extensions"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset
    minContext = 0
    treeCount = 10

    def __init__(self, treeCount = 10):
        ClassifierBase.__init__(self)
        self.treeCount = treeCount
        

    def train(self, features, labels):
        if features.shape[0] != labels.shape[0]:
            print " 3, 2 ,1 ... BOOOM!! #features != # labels"

        if not labels.dtype == numpy.uint32:
            labels = labels.astype(numpy.uint32)
        if not features.dtype == numpy.float32:
            features = features.astype(numpy.float32)

        if labels.ndim == 1:
            labels.shape = labels.shape + (1,)
        
        self.unique_vals = numpy.unique(labels)
        
        # Have to set this becauce the new rf dont set mtry properly by default
        mtry = max(1,int(numpy.sqrt(features.shape[1]))+1) 
        
        self.RF = vigra.learning.RandomForest(treeCount=self.treeCount)
        
        oob = self.RF.learnRF(features, labels)
        print "Out-of-bag error %f" % oob
        
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

