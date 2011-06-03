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

from ilastik.modules.classification.core.features.featureBase import *
import vigra

#*******************************************************************************
# H e s s i a n O f G a u s s i a n                                            *
#*******************************************************************************

class HessianOfGaussian(FeatureBase):
    name = "Hessian matrix of Gaussian"
    groups = ['Orientation']
    numOutputChannels2d = 3
    numOutputChannels3d = 6

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        if hasattr(vigra.filters, 'hessianOfGaussian2D'):
            # Vigra with axistags
            def hessianOfGaussianEigenvalues(data, sigma):
                return vigra.filters.hessianOfGaussian2D(data, sigma)
            func = hessianOfGaussianEigenvalues
        elif hasattr(vigra.filters, 'hessianOfGaussianEigenvalues'):
            # Vigra without axistags
            func = vigra.filters.hessianOfGaussian
        else:
            raise RuntimeError('Vigra version does not have hessianOfGausian')
        
        result = self.applyToAllChannels(data, func, self.sigma)
        return result

    def compute3d(self, data):
        if hasattr(vigra.filters, 'hessianOfGaussian3D'):
            # Vigra with axistags
            def hessianOfGaussianEigenvalues(data, sigma):
                return vigra.filters.hessianOfGaussian3D(data, sigma)
            func = hessianOfGaussianEigenvalues
        elif hasattr(vigra.filters, 'hessianOfGaussianEigenvalues'):
            # Vigra without axistags
            func = vigra.filters.hessianOfGaussian
        else:
            raise RuntimeError('Vigra version does not have hessianOfGausian')
        
        result = self.applyToAllChannels(data, func, self.sigma)
        return result


#*******************************************************************************
# H e s s i a n O f G a u s s i a n E i g e n v a l u e s                      *
#*******************************************************************************

class HessianOfGaussianEigenvalues(FeatureBase):
    name = "Eigenvalues of Hessian matrix of Gaussian"
    groups = ['Texture']
    numOutputChannels2d = 2
    numOutputChannels3d = 3


    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        if hasattr(vigra.filters, 'hessianOfGaussian2D'):
            # Vigra with axistags
            def hessianOfGaussianEigenvalues(data, sigma):
                return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian2D(data, sigma))
            func = hessianOfGaussianEigenvalues
        
        elif hasattr(vigra.filters, 'hessianOfGaussianEigenvalues'):
            # Vigra without axistags
            func = vigra.filters.hessianOfGaussianEigenvalues
        else:
            raise RuntimeError('Vigra version does not have hessianOfGausian')
        
        result = self.applyToAllChannels(data, func, self.sigma)
        return result

    def compute3d(self, data):
        if hasattr(vigra.filters, 'hessianOfGaussian3D'):
            # Vigra with axistags
            def hessianOfGaussianEigenvalues(data, sigma):
                return vigra.filters.tensorEigenvalues(vigra.filters.hessianOfGaussian3D(data, sigma))
            func = hessianOfGaussianEigenvalues
        elif hasattr(vigra.filters, 'hessianOfGaussianEigenvalues'):
            # Vigra without axistags
            func = vigra.filters.hessianOfGaussianEigenvalues
        else:
            raise RuntimeError('Vigra version does not have hessianOfGausian')
        
        result = self.applyToAllChannels(data, func, self.sigma)
        return result



#*******************************************************************************
# S t r u c t u r e T e n s o r E i g e n v a l u e s                          *
#*******************************************************************************

class StructureTensorEigenvalues(FeatureBase):
    name = "Eigenvalues of structure tensor"
    groups = ['Texture']
    numOutputChannels2d = 2
    numOutputChannels3d = 3

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.structureTensorEigenvalues
        result = self.applyToAllChannels(data, func,  self.sigma, self.sigma / 2.0)
        return result

    def compute3d(self, data):
        func = vigra.filters.structureTensorEigenvalues
        result = self.applyToAllChannels(data, func,  self.sigma, self.sigma / 2.0)
        return result



#*******************************************************************************
# G a u s s i a n G r a d i e n t M a g n i t u d e                            *
#*******************************************************************************

class GaussianGradientMagnitude(FeatureBase):
    name = "Gradient Magnitude of Gaussian"
    groups = ['Edge']
    numOutputChannels2d = 1
    numOutputChannels3d = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.gaussianGradientMagnitude
        result = self.applyToAllChannels(data, func,  self.sigma)
        return result

    def compute3d(self, data):
        func = vigra.filters.gaussianGradientMagnitude
        result = self.applyToAllChannels(data, func,  self.sigma)
        return result


#*******************************************************************************
# G a u s s i a n S m o o t h i n g                                            *
#*******************************************************************************

class GaussianSmoothing(FeatureBase):
    name = "Gaussian Smoothing"
    groups = ['Color']
    numOutputChannels2d = 1
    numOutputChannels3d = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.gaussianSmoothing
        result = self.applyToAllChannels(data, func, self.sigma)
        return result

    def compute3d(self, data):
        func = vigra.filters.gaussianSmoothing
        result = self.applyToAllChannels(data, func, self.sigma)
        return result

#*******************************************************************************
# S t r u c t u r e T e n s o r                                                *
#*******************************************************************************

class StructureTensor(FeatureBase):
    name = "Structure Tensor"
    groups = ['Orientation']
    numOutputChannels2d = 3
    numOutputChannels3d = 6

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        func = vigra.filters.structureTensor
        result = self.applyToAllChannels(data, func, self.sigma, self.sigma / 2.0)
        return result

    def compute3d(self, data):
        func = vigra.filters.structureTensor
        result = self.applyToAllChannels(data, func, self.sigma, self.sigma / 2.0)
        return result

#*******************************************************************************
# L a p l a c i a n O f G a u s s i a n                                        *
#*******************************************************************************

class LaplacianOfGaussian(FeatureBase):
    name = "Laplacian of Gaussian"
    groups = ['Edge']
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


#*******************************************************************************
# D i f f e r e n c e O f G a u s s i a n s                                    *
#*******************************************************************************

class DifferenceOfGaussians(FeatureBase):
    name = "Difference of Gaussians"
    groups = ['Edge']
    numOutputChannels2d = 1
    numOutputChannels3d = 1

    def __init__(self, sigma):
        FeatureBase.__init__(self,sigma)
        self.minContext = int(numpy.ceil(sigma * 3.5))

    def compute2d(self, data):
        def differenceOfGaussians(data, sigma):
            return vigra.filters.gaussianSmoothing(data, sigma) - vigra.filters.gaussianSmoothing(data, sigma * 0.66)
        func = differenceOfGaussians
        result = self.applyToAllChannels(data, func, self.sigma) 
        return result

    def compute3d(self, data):
        def differenceOfGaussians(data, sigma):
            return vigra.filters.gaussianSmoothing(data, sigma) - vigra.filters.gaussianSmoothing(data, sigma * 0.66)
        func = differenceOfGaussians
        result = self.applyToAllChannels(data, func, self.sigma) 
        return result

#LocalFeature('Canny', ['Sigma' ], (1, 1), lambda x, s: vigra.analysis.cannyEdgeImage(x, s, 0, 1))
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
