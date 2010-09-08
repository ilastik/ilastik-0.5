# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 15:31:09 2010

@author: Anna_2
"""

import numpy, vigra
import random

class ConnectedComponents():
    def __init__(self):
        self.inputdata = None
        self.backgroundSet = set()
        
    def connect(self, inputData, background):
        vol, back_value = self.transformToVigra(inputData, background)
        print back_value
        res = None
        if back_value is not None:
            res = vigra.analysis.labelVolumeWithBackground(vol, 6, float(back_value))
        else:
            res = vigra.analysis.labelVolume(vol)
        if res is not None:
            res = res.swapaxes(0,2).view(vigra.ScalarVolume)
            return res.reshape(res.shape + (1,))
        
    def transformToVigra(self, vol, background):
        if len(background)==0:
            return vigra.ScalarVolume(vol), None
        else:
            print "non empty set ", background
            vol_merged = vol
            back_value = background.pop()
            #for i in range(len(background)):
            while len(background)>0:
                back_value_temp = background.pop()
                ind = numpy.where(vol_merged==back_value_temp)
                vol_merged[ind]=float(back_value)
            return vigra.ScalarVolume(vol_merged), back_value
        #return vol