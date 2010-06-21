#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

from featureBase import *
import vigra

class HessianOfGaussian(FeatureBase):
    name = "Hessian matrix of Gaussian"
    groups = ['Orientation']
    numOutputs2D = 3
    numOutputs3D = 6

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.hessianOfGaussian2D(data[i, 0, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape((1,) + temp.shape))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.hessianOfGaussian3D(data[i, :, :, :].astype('float32'), self.sigma)
            result.append(temp)
        return result


class HessianOfGaussianEigenvalues(FeatureBase):
    name = "Eigenvalues of Hessian matrix of Gaussian"
    groups = ['Texture']
    numOutputs2D = 2
    numOutputs3D = 3


    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian2D(data[i, 0, :, :].astype('float32'), self.sigma))
            result.append(temp.reshape((1,) + temp.shape))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(data[i, :, :, :].astype('float32'), self.sigma))
            result.append(temp)
        return result

class StructureTensorEigenvalues(FeatureBase):
    name = "Eigenvalues of structure tensor"
    groups = ['Texture']
    numOutputs2D = 2
    numOutputs3D = 3

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.structureTensorEigenvalues(data[i, 0, :, :].astype('float32'), self.sigma, self.sigma / 2.0)
            result.append(temp.reshape((1,) + temp.shape))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.structureTensorEigenvalues(data[i, :, :, :].astype('float32'), self.sigma, self.sigma / 2.0)
            result.append(temp)
        return result



class GaussianGradientMagnitude(FeatureBase):
    name = "Gradient Magnitude of Gaussian"
    groups = ['Texture']
    numOutputs2D = 1
    numOutputs3D = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianGradientMagnitude(data[i, 0, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape((1,) + temp.shape + (1,)))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianGradientMagnitude(data[i, :, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape(temp.shape + (1,)))
        return result


class GaussianSmoothing(FeatureBase):
    name = "Gaussian Smoothing"
    groups = ['Color']
    numOutputs2D = 1
    numOutputs3D = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianSmoothing(data[i, 0, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape((1,) + temp.shape + (1,)))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianSmoothing(data[i, :, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape(temp.shape + (1,)))
        return result

class StructureTensor(FeatureBase):
    name = "Structure Tensor"
    groups = ['Orientation']
    numOutputs2D = 3
    numOutputs3D = 6

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.structureTensor(data[i, 0, :, :].astype('float32'), self.sigma, self.sigma)
            result.append(temp.reshape((1,) + temp.shape))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.structureTensor(data[i, :, :, :].astype('float32'), self.sigma, self.sigma)
            result.append(temp)
        return result

class LaplacianOfGaussian(FeatureBase):
    name = "Laplacian of Gaussian"
    groups = ['Edge']
    numOutputs2D = 1
    numOutputs3D = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.laplacianOfGaussian(data[i, 0, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape((1,) + temp.shape + (1,)))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.laplacianOfGaussian(data[i, :, :, :].astype('float32'), self.sigma)
            result.append(temp.reshape(temp.shape + (1,)))
        return result


class DifferenceOfGaussians(FeatureBase):
    name = "Difference of Gaussians"
    groups = ['Edge']
    numOutputs2D = 1
    numOutputs3D = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianSmoothing(data[i, 0, :, :].astype('float32'), self.sigma) - vigra.filters.gaussianSmoothing(data[i, 0, :, :].astype('float32'), self.sigma * 0.66)
            result.append(temp.reshape((1,) + temp.shape + (1,)))
        return result

    def compute3d(self, data):
        result = []
        for i in range(data.shape[0]):
            temp = vigra.filters.gaussianSmoothing(data[i, :, :, :].astype('float32'), self.sigma) - vigra.filters.gaussianSmoothing(data[i, :, :, :].astype('float32'), self.sigma * 0.66)
            result.append(temp.reshape(temp.shape + (1,)))
        return result


##gaussianGradientMagnitude = LocalFeature('Gradient Magnitude', ['Sigma' ], (1, 1), vigra.filters.gaussianGradientMagnitude)
##gaussianSmooth = LocalFeature('Gaussian', ['Sigma' ], (1, 1), vigra.filters.gaussianSmoothing)
##structureTensor = LocalFeature('Structure Tensor', ['InnerScale', 'OuterScale'], (3, 6), vigra.filters.structureTensor)
##hessianMatrixOfGaussian = LocalFeature('Hessian', ['Sigma' ], (3, 6), myHessianOfGaussian)
##eigStructureTensor2d = LocalFeature('Eigenvalues of Structure Tensor', ['InnerScale', 'OuterScale'], (2, 3), myStructureTensorEigenvalues)
##laplacianOfGaussian = LocalFeature('LoG', ['Sigma' ], (1, 1), vigra.filters.laplacianOfGaussian)
##eigHessianTensor2d = LocalFeature('Eigenvalues of Hessian', ['Sigma' ], (2, 3), myHessianOfGaussianEigenvalues)




#differenceOfGaussians = LocalFeature('DoG', ['Sigma' ], (1, 1), lambda x, s: vigra.filters.gaussianSmoothing(x, s) - vigra.filters.gaussianSmoothing(x, s / 3 * 2))
#cannyEdge = LocalFeature('Canny', ['Sigma' ], (1, 1), lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1))
#morphologicalOpening = LocalFeature('Morph Opening', ['Sigma' ], (1, 1), lambda x, s: vigra.morphology.discOpening(x.astype(numpy.uint8), int(s * 1.5 + 1)))
#morphologicalClosing = LocalFeature('Morph Colosing', ['Sigma' ], (1, 1), lambda x, s: vigra.morphology.discClosing(x.astype(numpy.uint8), int(s * 1.5 + 1)))

#svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 1', [], (1, 1), lambda x: svenSpecial(x))
#svenSpecialWaveFrontDistance = LocalFeature('SvenSpecial 2', [], (1, 1), lambda x: svenSpecialSpecial(x))




#def svenSpecial(x):
#    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
#    if numpy.max(res) == 0:
#        res[:, :] = 3000
#        return res
#    else:
#        return vigra.filters.distanceTransform2D(res)
#
#def svenSpecialSpecial(x):
#    temp = numpy.zeros(x.shape + (4,))
#
#    res = vigra.analysis.cannyEdgeImage(x, 2.0, 0.39, 1)
#    if numpy.max(res) == 0:
#        res[:, :] = 3000
#    else:
#        res = vigra.filters.distanceTransform2D(res)
#    temp[:, :, 0] = res
#
#    res = vigra.analysis.cannyEdgeImage(x, 2.2, 0.42, 1)
#    if numpy.max(res) == 0:
#        res[:, :] = 3000
#    else:
#        res = vigra.filters.distanceTransform2D(res)
#    temp[:, :, 1] = res
#
#    res = vigra.analysis.cannyEdgeImage(x, 1.9, 0.38, 1)
#    if numpy.max(res) == 0:
#        res[:, :] = 3000
#    else:
#        res = vigra.filters.distanceTransform2D(res)
#    temp[:, :, 2] = res
#
#    res = vigra.analysis.cannyEdgeImage(x, 1.8, 0.38, 1)
#    if numpy.max(res) == 0:
#        res[:, :] = 3000
#    else:
#        res = vigra.filters.distanceTransform2D(res)
#    temp[:, :, 3] = res
#
#
#    return temp
