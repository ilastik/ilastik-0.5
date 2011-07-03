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

import numpy, threading

#*******************************************************************************
# B l o c k A c c e s s o r                                                    *
#*******************************************************************************

class BlockAccessor():
    def __init__(self, data, blockSize = None):
        self._data = data
        if blockSize is None:
            max = int(numpy.max(self._data.shape[1:4]))
            if max > 128:
                self._blockSize = blockSize = 128
            else:
                self._blockSize = blockSize = max / 2
        else:
            self._blockSize = blockSize
        
        self._cX = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[1] % self._blockSize
        if self._cXend > 0 and self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0
                
        self._cY = int(numpy.ceil(1.0 * data.shape[2] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[2] % self._blockSize
        if self._cYend > 0 and self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0

        self._cZ = int(numpy.ceil(1.0 * data.shape[3] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cZend = data.shape[3] % self._blockSize
        if self._cZend > 0 and self._cZend < self._blockSize / 3 and self._cZ > 1:
            self._cZ -= 1
        else:
            self._cZend = 0

        self._blockCount = self._cX * self._cY * self._cZ
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True
        
    def getBlockBounds(self, blockNum, overlap):
        self._lock.acquire()
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX
        
        startx = max(0, x*self._blockSize - overlap) 
        endx = min(self._data.shape[1], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[1]
        
        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[2], (y+1)*self._blockSize + overlap) 
        if y+1 >= self._cY:
            endy = self._data.shape[2]
    
        startz = max(0, z*self._blockSize - overlap)
        endz = min(self._data.shape[3], (z+1)*self._blockSize + overlap)
        if z+1 >= self._cZ:
            endz = self._data.shape[3]
        res = (startx,endx,starty,endy,startz,endz,)
        self._lock.release()
        return res

    def __getitem__(self, args):
        self._lock.acquire()
        res =  self._data[args]
        self._lock.release()
        return res

    def __setitem__(self, args, data):
        self._lock.acquire()
        self._data[args] = data
        self._lock.release()
            
#*******************************************************************************
# B l o c k A c c e s s o r 2 D                                                *
#*******************************************************************************

class BlockAccessor2D():
    def __init__(self, data, blockSize = 128):
        self._data = data
        self._blockSize = blockSize

        self._cX = int(numpy.ceil(1.0 * data.shape[0] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[0] % self._blockSize
        if self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0

        self._cY = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[1] % self._blockSize
        if self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0

        self._blockCount = self._cX * self._cY
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True

    def getBlockBounds(self, blockNum, overlap):
        self._lock.acquire()
        
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX

        startx = max(0, x*self._blockSize - overlap)
        endx = min(self._data.shape[0], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[0]

        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[1], (y+1)*self._blockSize + overlap)
        if y+1 >= self._cY:
            endy = self._data.shape[1]

        res = (startx,endx,starty,endy,)
        self._lock.release()

        return res

    def __getitem__(self, args):
        self._lock.acquire()
        temp =  self._data[args]
        self._lock.release()
        return temp
            
    def __setitem__(self, args, data):
        self._lock.acquire()
        self._data[args] = data
        self._lock.release()

#*******************************************************************************
# B l o c k A c c e s s o r                                                    *
#*******************************************************************************

class BlockAccessor():
    def __init__(self, data, blockSize = None):
        self._data = data
        if blockSize is None:
            max = int(numpy.max(self._data.shape[1:4]))
            if max > 128:
                self._blockSize = blockSize = 128
            else:
                self._blockSize = blockSize = max / 2
        else:
            self._blockSize = blockSize
        
        self._cX = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[1] % self._blockSize
        if self._cXend > 0 and self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0
                
        self._cY = int(numpy.ceil(1.0 * data.shape[2] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[2] % self._blockSize
        if self._cYend > 0 and self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0

        self._cZ = int(numpy.ceil(1.0 * data.shape[3] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cZend = data.shape[3] % self._blockSize
        if self._cZend > 0 and self._cZend < self._blockSize / 3 and self._cZ > 1:
            self._cZ -= 1
        else:
            self._cZend = 0

        self._blockCount = self._cX * self._cY * self._cZ
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True
        
    def getBlockBounds(self, blockNum, overlap):
        self._lock.acquire()
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX
        
        startx = max(0, x*self._blockSize - overlap) 
        endx = min(self._data.shape[1], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[1]
        
        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[2], (y+1)*self._blockSize + overlap) 
        if y+1 >= self._cY:
            endy = self._data.shape[2]
    
        startz = max(0, z*self._blockSize - overlap)
        endz = min(self._data.shape[3], (z+1)*self._blockSize + overlap)
        if z+1 >= self._cZ:
            endz = self._data.shape[3]
        res = (startx,endx,starty,endy,startz,endz,)
        self._lock.release()
        return res

    def __getitem__(self, args):
        self._lock.acquire()
        res =  self._data[args]
        self._lock.release()
        return res

    def __setitem__(self, args, data):
        self._lock.acquire()
        self._data[args] = data
        self._lock.release()
            
#*******************************************************************************
# B l o c k A c c e s s o r 2 D                                                *
#*******************************************************************************

class BlockAccessor2D():
    def __init__(self, data, blockSize = 128):
        self._data = data
        self._blockSize = blockSize

        self._cX = int(numpy.ceil(1.0 * data.shape[0] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cXend = data.shape[0] % self._blockSize
        if self._cXend < self._blockSize / 3 and self._cX > 1:
            self._cX -= 1
        else:
            self._cXend = 0

        self._cY = int(numpy.ceil(1.0 * data.shape[1] / self._blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self._cYend = data.shape[1] % self._blockSize
        if self._cYend < self._blockSize / 3 and self._cY > 1:
            self._cY -= 1
        else:
            self._cYend = 0

        self._blockCount = self._cX * self._cY
        self._lock = threading.Lock()
        if issubclass(self._data.__class__, numpy.ndarray):
            self._fileBacked = False
        else:
            self._fileBacked = True

    def getBlockBounds(self, blockNum, overlap):
        self._lock.acquire()
        
        z = int(numpy.floor(blockNum / (self._cX*self._cY)))
        rest = blockNum % (self._cX*self._cY)
        y = int(numpy.floor(rest / self._cX))
        x = rest % self._cX

        startx = max(0, x*self._blockSize - overlap)
        endx = min(self._data.shape[0], (x+1)*self._blockSize + overlap)
        if x+1 >= self._cX:
            endx = self._data.shape[0]

        starty = max(0, y*self._blockSize - overlap)
        endy = min(self._data.shape[1], (y+1)*self._blockSize + overlap)
        if y+1 >= self._cY:
            endy = self._data.shape[1]

        res = (startx,endx,starty,endy,)
        self._lock.release()

        return res

    def __getitem__(self, args):
        self._lock.acquire()
        temp =  self._data[args]
        self._lock.release()
        return temp
            
    def __setitem__(self, args, data):
        self._lock.acquire()
        self._data[args] = data
        self._lock.release()
