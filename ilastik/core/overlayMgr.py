#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010, 2011 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
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

overlays seem to enjoy heavy usage in the gui part of the program, 
still i decided to put them here in the core part!?!

"""

from ilastik.core.volume import DataAccessor

from ilastikdeps.core.overlayMgr import OverlaySlice, OverlayItemReference, OverlayItem

#*******************************************************************************
# O v e r l a y M g r                                                          *
#*******************************************************************************

class OverlayMgr():
    """
    Keeps track of the different overlays and is instanced by each DataItem
    supports the python dictionary interface for easy adding/updating of OverlayItems:
    
        mgr['GroupName1/SubgroupName/Itemname'] =  OverlayItem

    OverlayItems that have the autoAdd Property set to True are immediately added to the currently
    visible overlayWidget
    """
    def __init__(self,  dataItem, ilastik = None):
        self._dict = {}
        self.ilastik = ilastik
        self.dataItem = dataItem
        self.currentModuleName = ""
        
    def __getattr__(self,name):
        if name == "dataMgr":
            return self.dataItem.dataMgr
        elif name == "dataItemImage":
            return self.dataItem
    
    def remove(self,  key):
        it = self._dict.pop(key,  None)
        if it != None:
            if self.ilastik != None:
                self.ilastik.labelWidget.overlayWidget.removeOverlay(key)
            it.remove()
            
    def __setitem__(self,  key,  value):
        itemNew = False
        value.overlayMgr = self
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
    
    def changeKey(self, oldKey, newKey):
        o = self[oldKey]
        if o is not None:
            if self[newKey] is None:
                print oldKey, newKey
                o.key = newKey
                o.name = newKey.split('/')[-1]
                self._dict.pop(oldKey)
                self._dict[newKey] = o
                if self.ilastik is not None:
                    self.ilastik.labelWidget.overlayWidget.changeOverlayName(o, o.name)
                    print o.name
                return True
        return False
            
    def keys(self):
        return self._dict.keys()
    
    def values(self):
        return self._dict.values()
    
    def _addReference(self,  value):
        print "Adding new overlay", value.key
        if value.autoAdd is True and self.dataMgr is not None:
            if self.ilastik != None and value.dataItemImage == self.ilastik._activeImage:
                #print "Adding to active image"
                self.ilastik.labelWidget.overlayWidget.addOverlayRef(value.getRef())
            else:
                #print "Current Module:", self.dataMgr._currentModuleName
                #print "adding to non active image", value.dataItemImage
                if value.dataItemImage.module[self.dataMgr._currentModuleName] is not None:
                    value.dataItemImage.module[self.dataMgr._currentModuleName].addOverlayRef(value.getRef())
            
    def __getitem__(self,  key):
        #if the requested key does not exist, construct a group corresponding to the key
        if self._dict.has_key(key):
            return self._dict.__getitem__( key)
        else:
            return None
