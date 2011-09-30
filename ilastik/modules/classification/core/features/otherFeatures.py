from ilastik.modules.classification.core.features.featureBase import *
import vigra 

class MedianFilter(FeatureBase):
    name = "Median Filter"
    groups = ['Median']
    numOutputChannels2d = 1
    numOutputChannels3d = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.discMedian
        result = self.applyToAllChannels(data.astype(numpy.uint8), func, int(self.sigma))
        return result

    def compute3d(self, data):
        func = vigra.filters.discMedian
        result = self.applyToAllChannels(data.astype(numpy.uint8), func, int(self.sigma))
        return result

class LaplacianOfGaussian(FeatureBase):
    name = "Laplacian of Gaussian"
    groups = ['Laplacian']
    numOutputChannels2d = 1
    numOutputChannels3d = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.laplacianOfGaussian
        result = self.applyToAllChannels(data, func, self.sigma)
        return result

    def compute3d(self, data):
        func = vigra.filters.laplacianOfGaussian
        result = self.applyToAllChannels(data, func, self.sigma)
        return result