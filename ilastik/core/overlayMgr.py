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

"""
This file is about Overlays. To understand how they are used in the GUI of the Program 
please also have a look at :

    gui/labelWidget.py
    gui/overlayWidget.py
    gui/seedWidget.py
    gui/overlaySelectionDlg.py

overlays seem to enjoy heavy usage in the gui part of the programm, 
still i decided to put them here in the core part!?!

"""


from ilastik.core.volume import DataAccessor

class OverlaySlice():
    """
    Helper class to encapsulate the overlay slice and its drawing related settings
    for passing it around, mostly used in the volumeEditor (->move there ?)
    """
    def __init__(self, data, color, alpha, colorTable, min = None, max = None, autoAlphaChannel = True):
        self.colorTable = colorTable
        self.color = color
        self.alpha = alpha
        self.alphaChannel = None
        self.autoAlphaChannel = autoAlphaChannel
        self._data = data
        self.min = min
        self.max = max


class OverlayItemReference(object):
    """
    Helper class that references a full fledged OverlayItem and inherits its drawing related settings upon creation.
    the settings can be changed later on, what stays the same is the _data. 
    OverlayItemReferences get used in the overlayWidget.py file
    """    
    def __init__(self, overlayItem):
        self.overlayItem = overlayItem
        self.name = self.overlayItem.name
        self.visible = True
        self.alpha = self.overlayItem.alpha
        self.linkColor = self.overlayItem.linkColor
        if self.linkColor is False:
            self.color = self.overlayItem.color
        self.autoAlphaChannel = self.overlayItem.autoAlphaChannel
        if self.overlayItem.linkColorTable is False:
            self.colorTable = self.overlayItem.getColorTab()
        self.key = self.overlayItem.key
        self.channel = 0
        self.numChannels = self.overlayItem._data.shape[4]

    def __getitem__(self, args):
        return self.overlayItem._data[args]
            
    def __setitem__(self, args, data):
        self.overlayItem._data[args] = data
    
    def getColorTab(self):
        if self.overlayItem.linkColorTable is False:
            return self.colorTable
        else:
            return self.overlayItem.getColorTab()
        
      
    def getOverlaySlice(self, num, axis, time = 0, channel = 0):
        return OverlaySlice(self.overlayItem._data.getSlice(num,axis,time,self.channel), self.color, self.alpha, self.getColorTab(), self.overlayItem.min, self.overlayItem.max, self.autoAlphaChannel)       
        
    def __getattr__(self,  name):
        if name == "colorTable":
            return self.overlayItem.colorTable
        elif name == "color":
            return self.overlayItem.getColor()
        elif name == "_data":
            return self.overlayItem._data
        elif name == "min":
            return self.overlayItem.min
        elif name == "max":
            return self.overlayItem.max
        elif name == "dtype":
            return self._data.dtype
        elif name == "shape":
            return self._data.shape
        raise AttributeError,  name
        
        
    def setAlpha(self, alpha):
        self.alpha = alpha
        
        
    def setColor(self, color):
        self.color = color
        
    def remove(self):
        self.overlayItem = None
        
    def incChannel(self):
        if self.channel < self.overlayItem._data.shape[4] - 1:
            self.channel += 1

    def decChannel(self):
        if self.channel > 0:
            self.channel -= 1
            
    def setChannel(self,  channel):
        if channel >= 0 and channel < self.numChannels :
            self.channel = channel
        else:
            raise Exception

class OverlayReferenceMgr(list):
    def __init__(self):
        list.__init__(self)
    

class OverlayItem(object):
    """
    A Item that holds some scalar or multichannel _data and their drawing related settings.
    OverlayItems are held by the OverlayMgr
    """
    def __init__(self, dataItemImage, data, color = 0, alpha = 0.4, colorTable = None, autoAdd = False, autoVisible = False,  linkColorTable = False, autoAlphaChannel = True, min = None, max = None):
        self._data = DataAccessor(data)
        self.dataItemImage = dataItemImage
        self.linkColorTable = linkColorTable
        self.colorTable = colorTable
        self.defaultColor = color
        self.linkColor = False
        self.colorGetter = None
        self.colorGetterArguments = None
        self.alpha = alpha
        self.autoAlphaChannel = autoAlphaChannel
        self.channel = 0
        self.name = "Unnamed Overlay"
        self.key = "Unknown Key"
        self.autoAdd = autoAdd
        self.autoVisible = autoVisible
        self.references = []
        self.min = min
        self.max = max

    def __getitem__(self, args):
        return self._data[args]
            
    def __setitem__(self, args, data):
        self._data[args] = data

    def __getattr__(self, name):
        if name == "color":
            return self.getColor()
        elif name == "dtype":
            return self._data.dtype
        elif name == "shape":
            return self._data.shape
        else:
            raise AttributeError, name

    def getColorTab(self):
        return self.colorTable
    
    def getSubSlice(self, offsets, sizes, num, axis, time = 0, channel = 0):
        return self._data.getSubSlice(offsets, sizes, num, axis, time, channel)

        
    def setSubSlice(self, offsets, data, num, axis, time = 0, channel = 0):
        self._data.setSubSlice(offsets, data, num, axis, time, channel)
                          
    
    def getColor(self):
        if self.linkColor is False:
            return self.defaultColor
        else:
            return self.colorGetter()
                          
    
    def setColorGetter(self,colorGetter, colorGetterArguments):
        self.colorGetter = colorGetter
        self.colorGetterArguments = colorGetterArguments
        self.linkColor = True
    
    
    def getRef(self):
        ref = OverlayItemReference(self)
        ref.visible = self.autoVisible
        self.references.append(ref)
        return ref
        
    def remove(self):
        for r in self.references:
            r.remove()
        self.references = []
        self._data = None


    def setData(self,  data):
        self.overlayItem._data = data



class OverlayMgr():
    """
    Keeps track of the different overlays and is instanced by each DataItem
    supports the python dictionary interface for easy adding/updating of OverlayItems:
    
        mgr['GroupName1/SubgroupName/Itemname'] =  OverlayItem

    OverlayItems that have the autoAdd Property set to True are immediately added to the currently
    visible overlayWidget
    """
    def __init__(self,  dataMgr, ilastik = None):
        self._dict = {}
        self.ilastik = ilastik
        self.dataMgr = dataMgr
        self.currentModuleName = ""
        
    def remove(self,  key):
        it = self._dict.pop(key,  None)
        if it != None:
            it.remove()
            if self.ilastik != None:
                self.ilastik.labelWidget.overlayWidget.removeOverlay(key)
            
    def __setitem__(self,  key,  value):
        itemNew = False
        if issubclass(value.__class__,  OverlayItem):
            if not self._dict.has_key(key):
                #set the name of the overlayItem to the last part of the key
                value.name = key.split('/')[-1]
                itemNew = True
                self._dict.__setitem__( key,  value)
                res = value
            else:
                it = self._dict[key]
                it.name = value.name = key.split('/')[-1]
                it._data = value._data
                it.color = value.color
                res = it
            #update the key
            res.key = key
        if itemNew:
            self._addReference(res)
        return res
    
    def keys(self):
        return self._dict.keys()
    
    def values(self):
        return self._dict.values()
    
    def _addReference(self,  value):
        print "adding new overlay", value.key
        if value.autoAdd is True and self.dataMgr is not None:
            if self.ilastik != None and value.dataItemImage == self.ilastik._activeImage:
                print "adding to very active image"
                self.ilastik.labelWidget.overlayWidget.addOverlayRef(value.getRef())
            else:
                print "current Module :", self.dataMgr._currentModuleName
                print "adding to non active image", value.dataItemImage.name
                if value.dataItemImage.module[self.dataMgr._currentModuleName] is not None:
                    value.dataItemImage.module[self.dataMgr._currentModuleName].addOverlayRef(value.getRef())
            
            
    def __getitem__(self,  key):
        #if the requested key does not exist, construct a group corresponding to the key
        if self._dict.has_key(key):
            return self._dict.__getitem__( key)
        else:
            return None
