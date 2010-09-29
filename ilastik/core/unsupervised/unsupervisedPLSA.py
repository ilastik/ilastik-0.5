from unsupervisedBase import *
import numpy

class UnsupervisedPLSA(UnsupervisedBase):
    #human readable information
    name = "probabilistic Latent Semantic Analysis (pLSA)" 
    description = "Standard pLSA method as proposed by Hofmann 99"
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"
    
    def __init__(self, numComponents = 3, minRelGain = 1e-3, maxIterations = 100):
        UnsupervisedBase.__init__(self)
        self.numComponents = numComponents
        self.minRelGain = minRelGain
        self.maxIterations = maxIterations
        
    def decompose(self, features): # features are of dimension NUMVOXELSxNUMFEATURES
        # sanity check
        #self.numComponents = numpy.min(self.numComponents, features.shape[1])
        
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
            ZV = self.normalizeColumn(ZV * numpy.dot(FZ.T, features / (FZV + numpy.finfo(float).eps)))
            FZ = self.normalizeColumn(FZ * numpy.dot(features / (FZV + numpy.finfo(float).eps), ZV.T))
            FZV = numpy.dot(FZ, ZV) # pre-calculate
            # check relative change in least squares model fit
            model = numpy.tile(voxelSums, (numFeatures, 1)) * FZV
            error_old = err;
            err = numpy.sum((features - model)**2)
            lastChange = numpy.abs((err - error_old)/(numpy.finfo(float).eps+err))
            iteration = iteration + 1;
        return FZ, ZV
    
    # Helper function
    def normalizeColumn(self, X):
        res = X / (numpy.ones((X.shape[0], 1)) * numpy.sum(X, 0) + numpy.finfo(float).eps)
        return res
    