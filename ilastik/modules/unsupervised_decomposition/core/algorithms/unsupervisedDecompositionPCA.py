from ilastik.modules.unsupervised_decomposition.core.algorithms.unsupervisedDecompositionBase import UnsupervisedDecompositionBase
import numpy

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
    
    # it is probably NOT a good idea to define this a class level (more than one PLSA 
    # instance with different numbers of components might exist), but in the current 
    # ilastik architecture this method is called before the instance is even created,  
    # so it HAS to be a class method for now
    # workaround: set self.numComponents in init function
    @classmethod   
    def setNumberOfComponents(cls, numComponents):
        cls.numComponents = numComponents
        
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
        return numpy.ones((X.shape[0],1)) * numpy.mean(X, axis=0)
        