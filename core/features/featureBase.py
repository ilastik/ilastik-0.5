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
import numpy, h5py


class FeatureBase(object):
    """
    Implements features that are calculated by some functor
    """
    name = "Virtual Base Feature"
    groups = ['A', 'B']
    numOutputs2D = 0
    numOutputs3D = 0
    
    def __init__(self, sigma):
        self.sigma = sigma
        self.minContext = sigma*3.5
        self.featureFunktor = None

    def compute(self, data):
        if data.shape[1] > 1:
            return self.compute3d(data)
        else:
            return self.compute2d(data)
        
    def settings(self):
        pass

    def computeSizeForShape(self, shape):
        if shape[1] > 1:
            return self.__class__.numOutputs3D
        else:
            return self.__class__.numOutputs2D
        
    def serialize(self, h5grp):
        h5grp.create_dataset('name',data=self.name)
        h5grp.create_dataset('class',data=self.__class__)
        h5grp.create_dataset('sigma',data=self.sigma)


    @classmethod
    def deserialize(cls, h5grp):
        _name = h5grp['name']
        _class = h5grp['class']
        _sigma = h5grp['sigma']

        return cls(_class, _sigma)

    def compute2d(self, channel_data):
        pass

    def compute3d(self, channel_data):
        pass

    def __str__(self):
        return '%s: %s' % (self.name , ', '.join(["%s = %f" % (x[0], x[1]) for x in zip(self.argNames, self.args)]))

