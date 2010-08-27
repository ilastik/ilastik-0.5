# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 15:31:09 2010

@author: Anna_2
"""

import numpy, vigra

class ConnectedComponents():
    def __init__(self):
        self.inputdata = None
        
    def connect(self):
        vol = self.transformToVigra()
        res = vigra.analysis.labelVolume(vol)
        return res
        
    def transformToVigra(self):
        if self.inputData is not None:
            #that's just for the time until segmentation is there
            #and the testing has to be done on prediction
            #TODO: REMOVE IT BEFORE PUSHING TO ILASTIK!!!
            vol = numpy.round(vol)
            return vol