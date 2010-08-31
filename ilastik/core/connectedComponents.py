# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 15:31:09 2010

@author: Anna_2
"""

import numpy, vigra

class ConnectedComponents():
    def __init__(self):
        self.inputdata = None
        
    def connect(self, inputData):
        vol = self.transformToVigra(inputData)
        
        res = vigra.analysis.labelVolume(vol)
        
        res = res.swapaxes(0,2).view(vigra.ScalarVolume)
        #res = vol
        return res.reshape(res.shape + (1,))
        
    def transformToVigra(self, vol):
        #if self.inputData is not None:
            #that's just for the time until segmentation is there
            #and the testing has to be done on prediction
            #TODO: REMOVE IT BEFORE PUSHING TO ILASTIK!!!
        vol = vol/255.    
        vol = numpy.round(vol)
        return vigra.ScalarVolume(vol)
        #return vol