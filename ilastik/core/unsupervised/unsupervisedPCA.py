from unsupervisedBase import *
import numpy, scipy

class UnsupervisedPCA(UnsupervisedBase):
    #human readable information
    name = "Principal Component Analysis (PCA)" 
    description = "also known as Karhunen-Loeve or Hotelling transform"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    
    def __init__(self, numComponents = 0):
        UnsupervisedBase.__init__(self)
        self.numComponents = numComponents
        
    def decompose(self, features): # features are of dimension NUMVOXELSxNUMFEATURES
        print 'PCA'
        if (self.numComponents == 0):
            self.numComponents = features.shape[1]
        # sanity check
        #self.numComponents = numpy.min(self.numComponents, features.shape[1])
            
        # use singular value decomposition (SVD)
        meanData = self.meanData(features)
        features_centered = features - meanData
        U,s,Vh = numpy.linalg.svd(features_centered, full_matrices=False)
        print Vh.shape
        print (features.T).shape
        ZV = numpy.dot(Vh, features.T)#meanData + U.T#features_centered.T * U
        FZ = Vh 

        print ZV.shape
        print FZ.shape

        return FZ, ZV
    
    
    # helper method
    def meanData(self, X):
        return numpy.ones((X.shape[0],1)) * numpy.mean(X, 0)
        