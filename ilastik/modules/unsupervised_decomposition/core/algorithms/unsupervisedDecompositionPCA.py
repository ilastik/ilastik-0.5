from ilastik.modules.unsupervised_decomposition.core.algorithms.unsupervisedDecompositionBase import UnsupervisedDecompositionBase
import numpy


#*******************************************************************************
# U n s u p e r v i s e d D e c o m p o s i t i o n P C A                      *
#*******************************************************************************

class UnsupervisedDecompositionPCA(UnsupervisedDecompositionBase):
    
    #human readable information
    name = "Principal Component Analysis (PCA)" 
    shortname = "PCA"
    description = "also known as Karhunen-Loeve or Hotelling transform"
    author = "M. Hanselmann, HCI - University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    
    numComponents = 3
    
    def __init__(self):
        UnsupervisedDecompositionBase.__init__(self)
        self.numComponents = UnsupervisedDecompositionPCA.numComponents

    def decompose(self, features): # features are of dimension NUMVOXELSxNUMFEATURES
        # sanity checks
        self.numComponents = self.checkNumComponents(features.shape[1], self.numComponents)
        
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
    
    # helper method
    def meanData(self, X):
        return numpy.ones((X.shape[0],1)) * numpy.mean(X, axis=0)
        