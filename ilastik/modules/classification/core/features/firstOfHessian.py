from featureBase import *
import vigra, numpy

class HessianOfGaussianEigenvaluesFirst(FeatureBase):
    name = "First Eigenvalue of Hessian matrix of Gaussian"
    groups = ['First Hessian Eigenvalue']
    numOutputChannels2d = 1
    numOutputChannels3d = 1


    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        def hessianOfGaussianEigenvalues(data, sigma):
            return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian2D(data, sigma))
        func = hessianOfGaussianEigenvalues
        result = self.applyToAllChannels(data, func, self.sigma)
        return result[:,:,0]

    def compute3d(self, data):
        def hessianOfGaussianEigenvalues(data, sigma):
            return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(data, sigma))
        func = hessianOfGaussianEigenvalues
        result = self.applyToAllChannels(data, func, self.sigma)
        return result[:,:,:,0]
