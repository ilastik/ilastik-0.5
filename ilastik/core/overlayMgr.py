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

from ilastik.core.volume import DataAccessor

class OverlaySlice():
    """
    Helper class to encapsulate the overlay slice and its drawing related settings
    """
    def __init__(self, data, color, alpha, colorTable):
        self.colorTable = colorTable
        self.color = color
        self.alpha = alpha
        self.alphaChannel = None
        self.data = data

        
class OverlayItem(object):
    def __init__(self, data, name = "Red Overlay", color = 0, alpha = 0.4, colorTable = None, visible = True,  autoVisible = True):
        self.data = DataAccessor(data)
        self.colorTable = colorTable
        self.color = color
        self.alpha = alpha
        self.name = name
        self.visible = visible
        self.autoVisible = autoVisible
        
    def getOverlaySlice(self, num, axis, time = 0, channel = 0):
        return OverlaySlice(self.data.getSlice(num,axis,time,channel), self.color, self.alpha, self.colorTable)       
        



class OverlayMgr(dict):
    """
    Keeps track of the different overlays
    supports the python dictionary interface
    """
    def __init__(self,  widget = None):
        dict.__init__(self)
        self.widget = widget
        
    def remove(self,  key):
        self.pop(key,  None)
        if self.widget != None:
            self.widget.remove(key)
            
    def __setitem__(self,  key,  value):
        addToWidget = False
        if issubclass(value.__class__,  OverlayItem):
            if not self.has_key(key):
                addToWidget = True
                dict.__setitem__(self,  key,  value)
                res = value
            else:
                it = self[key]
                it.colorTable = value.colorTable
                it.color = value.color
                it.data = it.data
                res = it
        
        if addToWidget:
            self.addToWidget(res)
            
        return res
        
    def addToWidget(self,  value):
        print "adding ",  value.name,  "to overlays"
        if self.widget != None and value.autoVisible is True:
            self.widget.addOverlay(value)
            
            
    def __getitem__(self,  key):
        #if the requested key does not exist, construct a group corresponding to the key
        if self.has_key(key):
            return dict.__getitem__(self,  key)
        else:
            return None
