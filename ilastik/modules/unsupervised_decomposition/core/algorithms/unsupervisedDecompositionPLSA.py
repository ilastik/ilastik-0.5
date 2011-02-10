from ilastik.modules.unsupervised_decomposition.core.algorithms.unsupervisedDecompositionBase import UnsupervisedDecompositionBase
from ilastik.core.testThread import TestHelperFunctions
import numpy
        
class UnsupervisedDecompositionPLSA(UnsupervisedDecompositionBase):
    #human readable information
    name = "probabilistic Latent Semantic Analysis (pLSA)"
    shortname = "pLSA" 
    description = "Standard pLSA method as proposed by Hofmann 99"
    author = "M. Hanselmann, HCI - University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    
    numComponents = 3
    minRelGain = 1e-3
    maxIterations = 100
    
    def __init__(self):
        UnsupervisedDecompositionBase.__init__(self)
        self.numComponents = UnsupervisedDecompositionPLSA.numComponents
        
    # it is probably NOT a good idea to define this a class level (more than one PLSA 
    # instance with different numbers of components might exist), but in the current 
    # ilastik architecture  this method is called before the instance is even created,  
    # so it HAS to be a class method for now
    # workaround: set self.numComponents in init function
    @classmethod   
    def setNumberOfComponents(cls, numComponents):
        cls.numComponents = numComponents
        
    @classmethod
    def setRandomSeed(cls):
        seed = TestHelperFunctions.getRandomSeed()
        numpy.random.seed(seed)
        
    # NOTE: the pLSA will also be part of the upcoming vigra release
    def decompose(self, features): # features are of dimension NUMVOXELSxNUMFEATURES
        # sanity checks
        self.numComponents = numpy.min((self.numComponents, features.shape[1]))
        self.numComponents = numpy.max((self.numComponents, 1))
                
        features = features.T
        numFeatures, numVoxels = features.shape # this should be the shape of features!
        # initialize result matrices
        # features/hidden and hidden/pixels
        FZ = self.normalizeColumn(numpy.random.random((numFeatures, self.numComponents)))
        ZV = self.normalizeColumn(numpy.random.random((self.numComponents, numVoxels)))
        # init vars
        lastChange = 1/numpy.finfo(float).eps
        err = 0;
        iteration = 0;
        # expectation maximization (EM) algorithm
        voxelSums = numpy.sum(features, 0)
        FZV = numpy.dot(FZ, ZV) # pre-calculate
        while(lastChange > self.minRelGain and iteration < self.maxIterations):
            if(numpy.mod(iteration, 25)==0):
                print "iteration %d" % iteration
                print "last relative change %f" % lastChange
            factor = features / (FZV + numpy.finfo(float).eps)    
            ZV = self.normalizeColumn(ZV * numpy.dot(FZ.T, factor))
            FZ = self.normalizeColumn(FZ * numpy.dot(factor, ZV.T))
            FZV = numpy.dot(FZ, ZV) # pre-calculate
            # check relative change in least squares model fit
            model = numpy.tile(voxelSums, (numFeatures, 1)) * FZV
            error_old = err;
            err = numpy.sum((features - model)**2)
            lastChange = numpy.abs((err - error_old)/(numpy.finfo(float).eps+err))
            iteration = iteration + 1;
        return FZ, ZV
    
    def configure(self, options):
        self.numComponents = options[0]
        self.minRelGain = options[1]
        self.maxIterations = options[2]
    
    # Helper function
    def normalizeColumn(self, X):
        res = X / (numpy.ones((X.shape[0], 1)) * numpy.sum(X, 0) + numpy.finfo(float).eps)
        return res            