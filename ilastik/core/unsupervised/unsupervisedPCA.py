from unsupervisedBase import *
import numpy, scipy

class UnsupervisedPCA(UnsupervisedBase):
    #human readable information
    name = "Principal Component Analysis (PCA)" 
    shortname = "PCA"
    description = "also known as Karhunen-Loeve or Hotelling transform"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    
    numComponents = 10
    
    def __init__(self):
        UnsupervisedBase.__init__(self)
        
    def decompose(self, features): # features are of dimension NUMVOXELSxNUMFEATURES
        # sanity checks
        self.numComponents = numpy.min((self.numComponents, features.shape[1]))
        self.numComponents = numpy.max((self.numComponents, 1))
        
        # use singular value decomposition (SVD)
        meanData = self.meanData(features)
        features_centered = features - meanData
        U,s,Vh = numpy.linalg.svd(features_centered, full_matrices=False)
        ZV = (U*s).T #equivalent: numpy.dot(Vh, features.T)
        FZ = Vh
        # preselect components
        ZV = ZV[range(0, self.numComponents), :]
        FZ = FZ[:, range(0, self.numComponents)]
        return FZ, ZV
    
    def configure(self, options):
        self.numComponents = options[0]
    
    # helper method
    def meanData(self, X):
        return numpy.ones((X.shape[0],1)) * numpy.mean(X, 0)
        