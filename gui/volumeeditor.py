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
Dataset Editor Dialog based on PyQt4
"""
import math

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except Exception, e:
    print e
    pass

from PyQt4 import QtCore, QtGui, QtOpenGL

import vigra, numpy
import qimage2ndarray
import h5py
import copy
import os.path
from collections import deque
import threading

# Local import
#from spyderlib.config import get_icon, get_font

##mixin to enable label access
#class VolumeLabelAccessor():
    #def __init__():
        #self._labels = None

##extend ndarray with _label attribute
#numpy.ndarray.__base__ += (VolumeLabelAccessor, )


class LabeledVolumeArray(numpy.ndarray):
    def __new__(cls, input_array, labels=None):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = numpy.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj._labels = labels
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self,obj):
        # reset the attribute from passed original object
        self.info = getattr(obj, '_labels', None)
        # We do not need to return anything



def rgb(r, g, b):
    # use qRgb to pack the colors, and then turn the resulting long
    # into a negative integer with the same bitpattern.
    return (QtGui.qRgb(r, g, b) & 0xffffff) - 0x1000000



class VolumeEditorList(QtCore.QObject):
    editors = None #class variable to hold global editor list

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.editors = []


    def append(self, object):
        self.editors.append(object)
        self.emit(QtCore.SIGNAL('appended(int)'), self.editors.__len__() - 1)

    def remove(self, editor):
        for index, item in enumerate(self.editors):
            if item == editor:
                self.emit(QtCore.SIGNAL('removed(int)'), index)
                self.editors.__delitem__(index)

VolumeEditorList.editors = VolumeEditorList()


class DataAccessor():
    """
    This class gives consistent access to data volumes, images channels etc.
    access is always of the form [time, x, y, z, channel]
    """
    
    def __init__(self, data, channels = False):
        """
        data should be a numpy/vigra array that transformed to the [time, x, y, z, channel] access like this:
            (a,b), b != 3 and channels = False  (0,0,a,b,0)
            (a,b), b == 3 or channels = True:  (0,0,0,a,b)
            (a,b,c), c != 3 and channels = False:  (0,a,b,c,0)
            (a,b,c), c == 3 or channels = True:  (0,0,a,b,c)
            etc.
        """
        if len(data.shape) == 5:
            channels = True
            
        if issubclass(data.__class__, DataAccessor):
            data = data.data
            channels = True
        
        rgb = 1
        if data.shape[-1] == 3 or channels:
            rgb = 0

        tempShape = data.shape

        self.data = data

        if issubclass(data.__class__, vigra.arraytypes._VigraArray):
            for i in range(len(data.shape)/2):
                #self.data = self.data.swapaxes(i,len(data.shape)-i)
                pass
            self.data = self.data.view(numpy.ndarray)
            #self.data.reshape(tempShape)


        for i in range(5 - (len(data.shape) + rgb)):
            tempShape = (1,) + tempShape
            
        if rgb:
            tempShape = tempShape + (1,)

        self.data = self.data.reshape(tempShape)
        self.channels = self.data.shape[-1]

        self.rgb = False
        if data.shape[-1] == 3:
            self.rgb = True

        self.shape = self.data.shape


    def __getitem__(self, key):
        return self.data[tuple(key)]
    
    def __setitem__(self, key, data):
        self.data[tuple(key)] = data

    def getSlice(self, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                return self.data[time, num, :,: , :]
            elif axis == 1:
                return self.data[time, :,num,: , :]
            elif axis ==2:
                return self.data[time, :,: ,num,  :]
        else:
            if axis == 0:
                return self.data[time, num, :,: , channel]
            elif axis == 1:
                return self.data[time, :,num,: , channel]
            elif axis ==2:
                return self.data[time, :,: ,num,  channel]
            

    def setSlice(self, data, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                self.data[time, num, :,: , :] = data
            elif axis == 1:
                self.data[time, :,num,: , :] = data
            elif axis ==2:
                self.data[time, :,: ,num,  :] = data
        else:        
            if axis == 0:
                self.data[time, num, :,: , channel] = data
            elif axis == 1:
                self.data[time, :,num,: , channel] = data
            elif axis ==2:
                self.data[time, :,: ,num,  channel] = data

    def getSubSlice(self, offsets, sizes, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+sizes[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+sizes[1]

        if self.rgb is True:
            if axis == 0:
                return self.data[time, num, ax0l:ax0r,ax1l:ax1r , :]
            elif axis == 1:
                return self.data[time, ax0l:ax0r, num,ax1l:ax1r , :]
            elif axis ==2:
                return self.data[time, ax0l:ax0r, ax1l:ax1r ,num,  :]
        else:
            if axis == 0:
                return self.data[time, num, ax0l:ax0r,ax1l:ax1r , channel]
            elif axis == 1:
                return self.data[time, ax0l:ax0r, num,ax1l:ax1r , channel]
            elif axis ==2:
                return self.data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel]
            

    def setSubSlice(self, offsets, data, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+data.shape[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+data.shape[1]

        if self.rgb is True:
            if axis == 0:
                self.data[time, num,  ax0l:ax0r, ax1l:ax1r , :] = data
            elif axis == 1:
                self.data[time, ax0l:ax0r,num, ax1l:ax1r , :] = data
            elif axis ==2:
                self.data[time, ax0l:ax0r, ax1l:ax1r ,num,  :] = data
        else:
            if axis == 0:
                self.data[time, num,  ax0l:ax0r, ax1l:ax1r , channel] = data
            elif axis == 1:
                self.data[time, ax0l:ax0r,num, ax1l:ax1r , channel] = data
            elif axis ==2:
                self.data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel] = data
     
    def serialize(self, h5G, name='data'):
        h5G.create_dataset(name,data = self.data)
         
    @staticmethod
    def deserialize(h5G, name = 'data'):
        data = h5G[name].value
        return DataAccessor(data, channels = True)
        

class OverlaySlice():
    def __init__(self, data, color, alpha, colorTable):
        self.colorTable = colorTable
        self.color = color
        self.alpha = alpha

        if data.shape[-1] != 3 and colorTable == None:
            self.alphaChannel = data
    
            shape = data.shape
            shape +=(3,)
    
            self.data = numpy.zeros(shape, 'uint8')
            self.data[:,:,0] = data[:,:]*(self.color.red()/255.0)
            self.data[:,:,1] = data[:,:]*(self.color.green()/255.0)
            self.data[:,:,2] = data[:,:]*(self.color.blue()/255.0)
        elif colorTable == None:
            self.alphaChannel = numpy.ones(data.shape[0:2],'uint8')*255
            self.data = data
        else:
            self.alphaChannel = numpy.ones(data.shape[0:2],'uint8')
            self.data = data

class VolumeOverlay(QtGui.QListWidgetItem, DataAccessor):
    def __init__(self, data, name = "Red Overlay", color = 0, alpha = 0.4, colorTable = None, visible = True):
        QtGui.QListWidgetItem.__init__(self,name)
        DataAccessor.__init__(self,data)
        self.colorTable = colorTable
        self.setTooltip = name
        self.color = color
        self.alpha = alpha
        self.name = name
        self.visible = visible

	s = None
	if self.visible:
		s = QtCore.Qt.Checked
	else:
		s = QtCore.Qt.Unchecked

        self.setCheckState(s)
        self.oldCheckState = self.visible
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)


    def getOverlaySlice(self, num, axis, time = 0, channel = 0):
        return OverlaySlice(self.getSlice(num,axis,time,channel), self.color, self.alpha, self.colorTable)
         

class QSliderDialog(QtGui.QDialog):
    def __init__(self, min, max, value):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle('Change Alpha')
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setGeometry(20, 30, 140, 20)
        self.slider.setRange(min,max)
        self.slider.setValue(value)
        

class OverlayListView(QtGui.QListWidget):
    def __init__(self,parent):
        QtGui.QListWidget.__init__(self, parent)
        self.volumeEditor = parent
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.connect(self, QtCore.SIGNAL("clicked(QModelIndex)"), self.onItemClick)
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.onItemDoubleClick)
        self.overlays = [] #array of VolumeOverlays
        self.currentItem = None

    def onItemClick(self, itemIndex):
        item = self.itemFromIndex(itemIndex)
        if (item.checkState() == QtCore.Qt.Checked and not item.visible) or (item.checkState() == QtCore.Qt.Unchecked and item.visible):
            item.visible = not(item.visible)
            s = None
	    if item.visible:
                s = QtCore.Qt.Checked
            else:
                s = QtCore.Qt.Unchecked
            item.setCheckState(s)
            self.volumeEditor.repaint()
            
    def onItemDoubleClick(self, itemIndex):
        self.currentItem = item = self.itemFromIndex(itemIndex)
        if item.checkState() == item.visible * 2:
            dialog = QSliderDialog(1, 20, round(item.alpha*20))
            dialog.slider.connect(dialog.slider, QtCore.SIGNAL('valueChanged(int)'), self.setCurrentItemAlpha)
            dialog.exec_()
        else:
            self.onItemClick(self,itemIndex)
            
            
    def setCurrentItemAlpha(self, num):
        self.currentItem.alpha = 1.0 * num / 20.0
        self.volumeEditor.repaint()
        
    def clearOverlays(self):
        self.clear()
        self.overlays = []

    def addOverlay(self, overlay):
        self.overlays.append(overlay)
        self.addItem(overlay)

    def onContext(self, pos):
        index = self.indexAt(pos)

#        if not index.isValid():
#           return
#
#        item = self.itemAt(pos)
#        name = item.text()
#
#        menu = QtGui.QMenu(self)
#
#        #removeAction = menu.addAction("Remove")
#        if item.visible is True:
#            toggleHideAction = menu.addAction("Hide")
#        else:
#            toggleHideAction = menu.addAction("Show")
#
#        action = menu.exec_(QtGui.QCursor.pos())
##        if action == removeAction:
##            self.overlays.remove(item)
##            it = self.takeItem(index.row())
##            del it
#        if action == toggleHideAction:
#            item.visible = not(item.visible)
#            self.volumeEditor.repaint()
            


class VolumeLabelDescription():
    def __init__(self, name,number, color):
        self.number = number
        self.name = name
        self.color = color
        self.prediction = None

        
    def __eq__(self, other):
        answer = True
        if self.number != other.number:
            answer = False
        if self.name != other.name:
            answer = False
        if self.color != other.color:
            answer = False
        return answer

    def __ne__(self, other):
        return not(self.__eq__(other))

    def clone(self):
        t = VolumeLabelDescription( self.name, self.number, self.color)
        return t
    
class VolumeLabels():
    def __init__(self, data = None):
        if issubclass(data.__class__, DataAccessor):
            self.data = data
        else:
            self.data = DataAccessor(data, channels = False)

        self.descriptions = [] #array of VolumeLabelDescriptions
        
    def serialize(self, h5G, name = "labels"):
        self.data.serialize(h5G, name)
        
        tColor = []
        tName = []
        tNumber = []
        
        for index, item in enumerate(self.descriptions):
            tColor.append(item.color)
            tName.append(str(item.name))
            tNumber.append(item.number)

        if len(tColor) > 0:            
            h5G[name].attrs['color'] = tColor 
            h5G[name].attrs['name'] = tName
            h5G[name].attrs['number'] = tNumber
            
    
    @staticmethod    
    def deserialize(h5G, name ="labels"):
        if name in h5G.keys():
            data = DataAccessor.deserialize(h5G, name)
            colors = []
            names = []
            numbers = []
            if h5G[name].attrs.__contains__('color'):
                colors = h5G[name].attrs['color']
                names = h5G[name].attrs['name']
                numbers = h5G[name].attrs['number']
            descriptions = []
            for index, item in enumerate(colors):
                descriptions.append(VolumeLabelDescription(names[index], numbers[index], colors[index]))
    
            vl =  VolumeLabels(data)
            vl.descriptions = descriptions
            return vl
        else:
            return None
        
class Volume():
    def __init__(self):
        self.data = None
        self.labels = None
        self.uncertainty = None
        self.segmentation = None
        
    def serialize(self, h5G):
        self.data.serialize(h5G, "data")
        if self.labels is not None:
            self.labels.serialize(h5G, "labels")
        
    @staticmethod
    def deserialize(h5G):
        #TODO: make nicer
        data = DataAccessor.deserialize(h5G)
        labels = VolumeLabels.deserialize(h5G)
        v =  Volume()
        v.data = data
        v.labels = labels
        return v



class LabelListItem(QtGui.QListWidgetItem):
    def __init__(self, name , number, color):
        QtGui.QListWidgetItem.__init__(self, name)
        self.number = number
        self.visible = True
        self.setColor(color)
        #self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        #self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        

    def toggleVisible(self):
        self.visible = not(self.visible)

    def setColor(self, color):
        self.color = color
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(color)
        icon = QtGui.QIcon(pixmap)
        self.setIcon(icon)      


class LabelListView(QtGui.QListWidget):
    def __init__(self,parent = None):
        QtGui.QListWidget.__init__(self,parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.colorTab = []
        self.items = []
        self.volumeEditor = parent
        self.initFromMgr(parent.labels)
        self.labelColorTable = [QtGui.QColor(QtCore.Qt.red), QtGui.QColor(QtCore.Qt.green), QtGui.QColor(QtCore.Qt.yellow), QtGui.QColor(QtCore.Qt.blue), QtGui.QColor(QtCore.Qt.magenta) , QtGui.QColor(QtCore.Qt.darkYellow), QtGui.QColor(QtCore.Qt.lightGray)]
        #self.connect(self, QtCore.SIGNAL("currentTextChanged(QString)"), self.changeText)
        self.labelPropertiesChanged_callback = None

    
    def initFromMgr(self, volumelabel):
        self.volumeLabel = volumelabel
        for index, item in enumerate(volumelabel.descriptions):
            li = LabelListItem(item.name,item.number, QtGui.QColor.fromRgb(long(item.color)))
            self.addItem(li)
            self.items.append(li)
        self.buildColorTab()
        
    def changeText(self, text):
        self.volumeLabel.descriptions[self.currentRow()].name = text
        
    def createLabel(self):
        name = "Label " + len(self.items).__str__()
        number = len(self.items)
        if number > len(self.labelColorTable):
            color = QtGui.QColor.fromRgb(numpy.random.randint(255),numpy.random.randint(255),numpy.random.randint(255))
        else:
            color = self.labelColorTable[number]
        number +=1
        self.addLabel(name, number, color)
        self.buildColorTab()
        
    def addLabel(self, labelName, labelNumber, color):
        description = VolumeLabelDescription(labelName, labelNumber, color.rgb())
        self.volumeLabel.descriptions.append(description)
        
        label =  LabelListItem(labelName, labelNumber, color)
        self.items.append(label)
        self.addItem(label)
        self.buildColorTab()
        #self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
        if self.labelPropertiesChanged_callback is not None:
            self.labelPropertiesChanged_callback()

    def buildColorTab(self):
        self.colorTab = []
        for i in range(256):
            self.colorTab.append(QtGui.QColor.fromRgb(0,0,0).rgb())

        for index,item in enumerate(self.items):
            self.colorTab[item.number] = item.color.rgb()


    def onContext(self, pos):
        index = self.indexAt(pos)

        if not index.isValid():
           return

        item = self.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        removeAction = menu.addAction("Remove")
        colorAction = menu.addAction("Change Color")
        if item.visible is True:
            toggleHideAction = menu.addAction("Hide")
        else:
            toggleHideAction = menu.addAction("Show")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == removeAction:
            self.volumeEditor.history.removeLabel(item.number)
            for ii, it in enumerate(self.items):
                if it.number > item.number:
                    it.number -= 1
            self.items.remove(item)
            it = self.takeItem(index.row())
            del it
            self.buildColorTab()
            self.emit(QtCore.SIGNAL("labelRemoved(int)"), item.number)
            #self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
            if self.labelPropertiesChanged_callback is not None:
                self.labelPropertiesChanged_callback()
            self.volumeEditor.repaint()
        elif action == toggleHideAction:
            self.buildColorTab()
            item.toggleVisible()
        elif action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabel.descriptions[index.row()].color = color.rgb()
            
#            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
            if self.labelPropertiesChanged_callback is not None:
                self.labelPropertiesChanged_callback()
            self.buildColorTab()
            self.volumeEditor.repaint()

        

#abstract base class for undo redo stuff
class State():
    def __init__(self):
        pass

    def restore(self):
        pass


class LabelState(State):
    def __init__(self, title, axis, num, offsets, shape, time, volumeEditor, erasing, labels, labelNumber):
        self.title = title
        self.time = time
        self.num = num
        self.offsets = offsets
        self.axis = axis
        self.erasing = erasing
        self.labelNumber = labelNumber
        self.labels = labels
        self.dataBefore = volumeEditor.labels.data.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
        
    def restore(self, volumeEditor):
        temp = volumeEditor.labels.data.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
        restore  = numpy.where(self.labels > 0, self.dataBefore, 0)
        stuff = numpy.where(self.labels > 0, self.dataBefore + 1, 0)
        erase = numpy.where(stuff == 1, 1, 0)
        self.dataBefore = temp
        #volumeEditor.labels.data.setSubSlice(self.offsets, temp, self.num, self.axis, self.time, 0)
        volumeEditor.setLabels(self.offsets, self.axis, self.num, restore, False)
        volumeEditor.setLabels(self.offsets, self.axis, self.num, erase, True)
        if volumeEditor.sliceSelectors[self.axis].value() != self.num:
            volumeEditor.sliceSelectors[self.axis].setValue(self.num)
        else:
            volumeEditor.repaint()
        self.erasing = not(self.erasing)          



class HistoryManager(QtCore.QObject):
    def __init__(self, parent, maxSize = 3000):
        QtCore.QObject.__init__(self)
        self.volumeEditor = parent
        self.maxSize = maxSize
        self.history = []
        self.current = -1

    def append(self, state):
        if self.current + 1 < len(self.history):
            self.history = self.history[0:self.current+1]
        self.history.append(state)

        if len(self.history) > self.maxSize:
            self.history = self.history[len(self.history)-self.maxSize:len(self.history)]
        
        self.current = len(self.history) - 1

    def undo(self):
        if self.current >= 0:
            self.history[self.current].restore(self.volumeEditor)
            self.current -= 1

    def redo(self):
        if self.current < len(self.history) - 1:
            self.history[self.current + 1].restore(self.volumeEditor)
            self.current += 1
            
    def serialize(self, grp):
        histGrp= grp.create_group('history')
        for i, hist in enumerate(self.history):
            histItemGrp = histGrp.create_group('%04d'%i)
            histItemGrp.create_dataset('labels',data=hist.labels)
            histItemGrp.create_dataset('axis',data=hist.axis)
            histItemGrp.create_dataset('slice',data=hist.num)
            histItemGrp.create_dataset('labelNumber',data=hist.labelNumber)
            histItemGrp.create_dataset('offsets',data=hist.offsets)
            histItemGrp.create_dataset('time',data=hist.time)
            histItemGrp.create_dataset('erasing',data=hist.erasing)


    def removeLabel(self, number):
        tobedeleted = []
        for index, item in enumerate(self.history):
            if item.labelNumber != number:
                item.dataBefore = numpy.where(item.dataBefore == number, 0, item.dataBefore)
                item.dataBefore = numpy.where(item.dataBefore > number, item.dataBefore - 1, item.dataBefore)
                item.labels = numpy.where(item.labels == number, 0, item.labels)
                item.labels = numpy.where(item.labels > number, item.labels - 1, item.labels)
            else:
                #if item.erasing == False:
                    #item.restore(self.volumeEditor)
                tobedeleted.append(index - len(tobedeleted))
                if index <= self.current:
                    self.current -= 1

        for val in tobedeleted:
            it = self.history[val]
            self.history.__delitem__(val)
            del it

class VolumeUpdate():
    def __init__(self, data, offsets, sizes, erasing):
        self.offsets = offsets
        self.data = data
        self.sizes = sizes
        self.erasing = erasing
    
    def applyTo(self, dataAcc):
        offsets = self.offsets
        sizes = self.sizes
        #TODO: move part of function into DataAccessor class !! e.g. setSubVolume or somethign
        tempData = dataAcc[offsets[0]:offsets[0]+sizes[0],offsets[1]:offsets[1]+sizes[1],offsets[2]:offsets[2]+sizes[2],offsets[3]:offsets[3]+sizes[3],offsets[4]:offsets[4]+sizes[4]].copy()

        if self.erasing == True:
            tempData = numpy.where(self.data > 0, 0, tempData)
        else:
            tempData = numpy.where(self.data > 0, self.data, tempData)
        
        dataAcc[offsets[0]:offsets[0]+sizes[0],offsets[1]:offsets[1]+sizes[1],offsets[2]:offsets[2]+sizes[2],offsets[3]:offsets[3]+sizes[3],offsets[4]:offsets[4]+sizes[4]] = tempData  



class VolumeEditor(QtGui.QWidget):
    """Array Editor Dialog"""
    def __init__(self, image, name="", font=None,
                 readonly=False, size=(400, 300), labels = None , opengl = True, openglOverview = True, embedded = False, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.name = name
        title = name
        
        self.labelsAlpha = 1.0

        #Bordermargin settings - they control the blue markers that signal the region from wich the
        #labels are not used for trainig
        self.useBorderMargin = True
        self.borderMargin = 0


        #this setting controls the rescaling of the displayed data to the full 0-255 range
        self.normalizeData = False

        self.opengl = opengl
        self.openglOverview = openglOverview
        if self.opengl is True:
            #print "Using OpenGL Slice rendering"
            pass
        else:
            #print "Using Software Slice rendering"
            pass
        if self.openglOverview is True:
            #print "Enabling OpenGL Overview rendering"
            pass
            
        self.embedded = embedded
        
        if issubclass(image.__class__, DataAccessor):
            self.image = image
        elif issubclass(image.__class__, Volume):
            self.image = image.data
            labels = image.labels
        else:
            self.image = DataAccessor(image)

       
        if hasattr(image, '_labels'):
            self.labels = image._labels
        elif labels is not None:
            self.labels = labels
        else:
            tempData = DataAccessor(numpy.zeros(self.image.shape[1:4],'uint8'))
            self.labels = VolumeLabels(tempData)

        if issubclass(image.__class__, Volume):
            image.labels = self.labels

            
        self.editor_list = VolumeEditorList.editors

        self.linkedTo = None

        self.selectedTime = 0
        self.selectedChannel = 0

        self.pendingLabels = []

        self.ownIndex = self.editor_list.editors.__len__()
        #self.setAccessibleName(self.name)


        self.history = HistoryManager(self)

        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)


        self.grid = QtGui.QGridLayout()

        self.drawManager = DrawManager(self)

        self.imageScenes = []
        
        self.imageScenes.append(ImageScene(self, (self.image.shape[2],  self.image.shape[3], self.image.shape[1]), 0 ,self.drawManager))
        self.imageScenes.append(ImageScene(self, (self.image.shape[1],  self.image.shape[3], self.image.shape[2]), 1 ,self.drawManager))
        self.imageScenes.append(ImageScene(self, (self.image.shape[1],  self.image.shape[2], self.image.shape[3]), 2 ,self.drawManager))
        
        self.grid.addWidget(self.imageScenes[2], 0, 0)
        self.grid.addWidget(self.imageScenes[0], 0, 1)
        self.grid.addWidget(self.imageScenes[1], 1, 0)

        if self.openglOverview is True:
            self.overview = OverviewScene(self, self.image.shape[1:4])
        else:
            self.overview = OverviewSceneDummy(self, self.image.shape[1:4])
            
        self.grid.addWidget(self.overview, 1, 1)

        if self.image.shape[1] == 1:
            self.imageScenes[1].setVisible(False)
            self.imageScenes[2].setVisible(False)
            self.overview.setVisible(False)

        self.gridWidget = QtGui.QWidget()
        self.gridWidget.setLayout(self.grid)
        self.layout.addWidget(self.gridWidget)


        #right side toolbox
        self.toolBox = QtGui.QWidget()
        self.toolBoxLayout = QtGui.QVBoxLayout()
        self.toolBox.setLayout(self.toolBoxLayout)
        self.toolBox.setMaximumWidth(150)
        self.toolBox.setMinimumWidth(150)


        #Label selector
        self.addLabelButton = QtGui.QPushButton("Create Label Class")
        self.connect(self.addLabelButton, QtCore.SIGNAL("pressed()"), self.addLabel)
        self.toolBoxLayout.addWidget(self.addLabelButton)

        self.labelAlphaSlider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.labelAlphaSlider.setRange(0,20)
        self.labelAlphaSlider.setValue(20)
        self.labelAlphaSlider.setToolTip('Change Label Opacity')
        self.connect(self.labelAlphaSlider, QtCore.SIGNAL('valueChanged(int)'), self.setLabelsAlpha)
        self.toolBoxLayout.addWidget( self.labelAlphaSlider)

        self.labelView = LabelListView(self)

        self.toolBoxLayout.addWidget( self.labelView)


        if self.embedded == False:
            #Link to ComboBox
            self.editor_list.append(self)
            self.connect(self.editor_list, QtCore.SIGNAL("appended(int)"), self.linkComboAppend)
            self.connect(self.editor_list, QtCore.SIGNAL("removed(int)"), self.linkComboRemove)
    
            self.linkCombo = QtGui.QComboBox()
            self.linkCombo.setEnabled(True)
            self.linkCombo.addItem("None")
            for index, item in enumerate(self.editor_list.editors):
                self.linkCombo.addItem(item.name)
            self.connect(self.linkCombo, QtCore.SIGNAL("currentIndexChanged(int)"), self.linkToOther)
            self.toolBoxLayout.addWidget(QtGui.QLabel("Link to:"))
            self.toolBoxLayout.addWidget(self.linkCombo)

        self.toolBoxLayout.addSpacing(30)

        #Slice Selector Combo Box in right side toolbox
        self.sliceSelectors = []
        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceX)
        if self.image.shape[2] > 1 and self.image.shape[3] > 1: #only show when needed
            tempLay = QtGui.QHBoxLayout()
            tempLay.addWidget(QtGui.QLabel("<pre>X:</pre>"))
            tempLay.addWidget(sliceSpin, 1)
            self.toolBoxLayout.addLayout(tempLay)
        sliceSpin.setRange(0,self.image.shape[1] - 1)
        self.sliceSelectors.append(sliceSpin)
        

        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceY)
        if self.image.shape[1] > 1 and self.image.shape[3] > 1: #only show when needed
            tempLay = QtGui.QHBoxLayout()
            tempLay.addWidget(QtGui.QLabel("<pre>Y:</pre>"))
            tempLay.addWidget(sliceSpin, 1)
            self.toolBoxLayout.addLayout(tempLay)
        sliceSpin.setRange(0,self.image.shape[2] - 1)
        self.sliceSelectors.append(sliceSpin)

        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceZ)
        if self.image.shape[1] > 1 and self.image.shape[2] > 1 : #only show when needed
            tempLay = QtGui.QHBoxLayout()
            tempLay.addWidget(QtGui.QLabel("<pre>Z:</pre>"))
            tempLay.addWidget(sliceSpin, 1)
            self.toolBoxLayout.addLayout(tempLay)
        sliceSpin.setRange(0,self.image.shape[3] - 1)
        self.sliceSelectors.append(sliceSpin)


        self.selSlices = []
        self.selSlices.append(0)
        self.selSlices.append(0)
        self.selSlices.append(0)
        
        #Channel Selector Combo Box in right side toolbox
        self.channelSpin = QtGui.QSpinBox()
        self.channelSpin.setEnabled(True)
        self.connect(self.channelSpin, QtCore.SIGNAL("valueChanged(int)"), self.setChannel)
        self.channelSpinLabel = QtGui.QLabel("Channel:")
        self.toolBoxLayout.addWidget(self.channelSpinLabel)
        self.toolBoxLayout.addWidget(self.channelSpin)
        if self.image.shape[-1] == 1 or self.image.rgb is True: #only show when needed
            self.channelSpin.setVisible(False)
            self.channelSpinLabel.setVisible(False)
        self.channelSpin.setRange(0,self.image.shape[-1] - 1)

        if self.embedded == False:
            self.addOverlayButton = QtGui.QPushButton("Add Overlay")
            self.connect(self.addOverlayButton, QtCore.SIGNAL("pressed()"), self.addOverlayDialog)
            self.toolBoxLayout.addWidget(self.addOverlayButton)
        else:
            self.toolBoxLayout.addWidget(QtGui.QLabel("Overlays:"))



        #Overlay selector
        self.overlayView = OverlayListView(self)
        self.toolBoxLayout.addWidget( self.overlayView)
        self.toolBoxLayout.addStretch()


        self.toolBoxLayout.setAlignment( QtCore.Qt.AlignTop )

        self.layout.addWidget(self.toolBox)

        # Make the dialog act as a window and stay on top
        if self.embedded == False:
            pass
            #self.setWindowFlags(self.flags() | QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #self.setWindowIcon(get_icon('edit.png'))
        self.setWindowTitle(self.tr("Volume") + \
                            "%s" % (" - "+str(title) if str(title) else ""))

        #start viewing in the center of the volume
        self.changeSliceX(numpy.floor((self.image.shape[1] - 1) / 2))
        self.changeSliceY(numpy.floor((self.image.shape[2] - 1) / 2))
        self.changeSliceZ(numpy.floor((self.image.shape[3] - 1) / 2))

        ##undo/redo and other shortcuts
        self.shortcutUndo = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self, self.historyUndo, self.historyUndo) 
        self.shortcutRedo = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self, self.historyRedo, self.historyRedo)
        self.shortcutRedo2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Y"), self, self.historyRedo, self.historyRedo)
        self.togglePredictionSC = QtGui.QShortcut(QtGui.QKeySequence("Space"), self, self.togglePrediction, self.togglePrediction) 
        
        self.shortcutUndo.setContext(QtCore.Qt.ApplicationShortcut )
        self.shortcutRedo.setContext(QtCore.Qt.ApplicationShortcut )
        self.shortcutRedo2.setContext(QtCore.Qt.ApplicationShortcut )
        self.togglePredictionSC.setContext(QtCore.Qt.ApplicationShortcut)
        
        self.shortcutUndo.setEnabled(True)
        self.shortcutRedo.setEnabled(True)
        self.shortcutRedo2.setEnabled(True)
        self.togglePredictionSC.setEnabled(True)
        
        self.connect(self, QtCore.SIGNAL("destroyed()"),self.cleanUp)
        
        self.focusAxis =  0


    def focusNextPrevChild(self, forward = True):
        if forward is True:
            self.focusAxis += 1
            if self.focusAxis > 2:
                self.focusAxis = 0
        else:
            self.focusAxis -= 1
            if self.focusAxis < 0:
                self.focusAxis = 2
        self.imageScenes[self.focusAxis].setFocus()
        return True
        

    def cleanUp(self):
        for i, item in enumerate(self.imageScenes):
            del item

    def togglePrediction(self):
        print "toggling prediction.."
        maxi = self.overlayView.count() - 2
        if maxi >= 0:
            state = not(self.overlayView.item(0).visible)
            for index in range(0,maxi):
                item = self.overlayView.item(index)
                item.visible = state
                item.setCheckState(item.visible * 2)
        self.repaint()
        

    def setLabelsAlpha(self, num):
        self.labelsAlpha = num / 20.0
        self.repaint()
        
    def cleanup(self):
        del self.shortcutUndo
        del self.shortcutRedo
        
    def getPendingLabels(self):
        temp = self.pendingLabels
        self.pendingLabels = []
        return temp

    def historyUndo(self):
        self.history.undo()

    def historyRedo(self):
        self.history.redo()

    def clearOverlays(self):
        self.overlayView.clearOverlays()

    def addOverlay(self, visible, data, name, color, alpha, colorTab = None):
        ov = VolumeOverlay(data,name, color, alpha, colorTab, visible)
        self.overlayView.addOverlay(ov)

    def addOverlayDialog(self):
        overlays = []
        for index, item in enumerate(self.editor_list.editors):
            overlays.append(item.name)
        itemName, ok  = QtGui.QInputDialog.getItem(self,"Add Overlay", "Overlay:", overlays, 0, False)
        if ok is True:
            for index, item in enumerate(self.editor_list.editors):
                if item.name == itemName:
                    ov = VolumeOverlay(item.image, item.name)
                    self.overlayView.addOverlay(ov)
        self.repaint()

    def repaint(self):
        for i in range(3):
            tempImage = None
            tempLabels = None
            tempoverlays = []   
            for index, item in enumerate(self.overlayView.overlays):
                if item.visible:
                    tempoverlays.append(item.getOverlaySlice(self.selSlices[i],i, self.selectedTime, 0)) 
    
            tempImage = self.image.getSlice(self.selSlices[i], i, self.selectedTime, self.selectedChannel)
    
            if self.labels.data is not None:
                tempLabels = self.labels.data.getSlice(self.selSlices[i],i, self.selectedTime, 0)
    
            self.imageScenes[i].display(tempImage, tempoverlays, tempLabels, self.labelsAlpha)


    def addLabel(self):
        self.labelView.createLabel()


    def get_copy(self):
        """Return modified text"""
        return unicode(self.edit.toPlainText())

    def setRgbMode(self, mode):
        """
        change display mode of 3-channel images to either rgb, or 3-channels
        mode can bei either  True or False
        """
        if self.image.shape[-1] == 3:
            self.image.rgb = mode
            self.channelSpin.setVisible(not mode)
            self.channelSpinLabel.setVisible(not mode)

    def setUseBorderMargin(self, use):
        self.useBorderMargin = use
        self.setBorderMargin(self.borderMargin)

    def setBorderMargin(self, margin):
        if self.useBorderMargin is True:
            if self.borderMargin != margin:
                print "new border margin:", margin
                self.borderMargin = margin
                self.imageScenes[0].__borderMarginIndicator__(margin)
                self.imageScenes[1].__borderMarginIndicator__(margin)
                self.imageScenes[2].__borderMarginIndicator__(margin)
                self.repaint()
        else:
                self.imageScenes[0].__borderMarginIndicator__(0)
                self.imageScenes[1].__borderMarginIndicator__(0)
                self.imageScenes[2].__borderMarginIndicator__(0)
                self.repaint()

    def changeSliceX(self, num):
        self.changeSlice(num, 0)

    def changeSliceY(self, num):
        self.changeSlice(num, 1)

    def changeSliceZ(self, num):
        self.changeSlice(num, 2)

    def setChannel(self, channel):
        self.selectedChannel = channel
        for i in range(3):
            self.changeSlice(self.selSlices[i], i)

    def setTime(self, time):
        self.selectedTime = time
        for i in range(3):
            self.changeSlice(self.selSlices[i], i)


    def changeSlice(self, num, axis):
        self.selSlices[axis] = num
        tempImage = None
        tempLabels = None
        tempoverlays = []
        self.sliceSelectors[axis].setValue(num)

        for index, item in enumerate(self.overlayView.overlays):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(num,axis, self.selectedTime, 0)) 

        tempImage = self.image.getSlice(num, axis, self.selectedTime, self.selectedChannel)


        if self.labels.data is not None:
            tempLabels = self.labels.data.getSlice(num,axis, self.selectedTime, 0)

        self.selSlices[axis] = num
        self.imageScenes[axis].sliceNumber = num
        self.imageScenes[axis].display(tempImage, tempoverlays, tempLabels, self.labelsAlpha)
        self.overview.display(axis)
        self.emit(QtCore.SIGNAL('changedSlice(int, int)'), num, axis)
        self.emit(QtCore.SIGNAL('newLabelsPending()'))
#        for i in range(256):
#            col = QtGui.QColor(classColor.red(), classColor.green(), classColor.blue(), i * opasity)
#            image.setColor(i, col.rgba())

    def unlink(self):
        if self.linkedTo is not None:
            self.disconnect(self.editor_list.editors[self.linkedTo], QtCore.SIGNAL("changedSlice(int, int)"), self.changeSlice)
            self.linkedTo = None

    def linkToOther(self, index):
        self.unlink()
        if index > 0 and index != self.ownIndex + 1:
            other = self.editor_list.editors[index-1]
            self.connect(other, QtCore.SIGNAL("changedSlice(int, int)"), self.changeSlice)
            self.linkedTo = index - 1
        else:
            self.linkCombo.setCurrentIndex(0)

    def linkComboAppend(self, index):
        self.linkCombo.addItem( self.editor_list.editors[index].name )

    def linkComboRemove(self, index):
        if self.linkedTo == index:
            self.linkCombo.setCurrentIndex(0)
            self.linkedTo = None
        if self.linkedTo > index:
            self.linkedTo = self.linkedTo - 1
        if self.ownIndex > index:
            self.ownIndex = self.ownIndex - 1
            self.linkCombo.removeItem(index + 1)

    def closeEvent(self, event):
        self.disconnect(self.editor_list, QtCore.SIGNAL("appended(int)"), self.linkComboAppend)
        self.disconnect(self.editor_list, QtCore.SIGNAL("removed(int)"), self.linkComboRemove)
        self.unlink()
        self.editor_list.remove(self)
        event.accept()

    def wheelEvent(self, event):
        keys = QtGui.QApplication.keyboardModifiers()
        k_ctrl = (keys == QtCore.Qt.ControlModifier)
        
        if k_ctrl is True:        
            if event.delta() > 0:
                scaleFactor = 1.1
            else:
                scaleFactor = 0.9
            self.imageScenes[0].doScale(scaleFactor)
            self.imageScenes[1].doScale(scaleFactor)
            self.imageScenes[2].doScale(scaleFactor)

    def setLabels(self, offsets, axis, num, labels, erase):
        if axis == 0:
            offsets5 = (self.selectedTime,num,offsets[0],offsets[1],0)
            sizes5 = (1,1,labels.shape[0], labels.shape[1],1)
        elif axis == 1:
            offsets5 = (self.selectedTime,offsets[0],num,offsets[1],0)
            sizes5 = (1,labels.shape[0],1, labels.shape[1],1)
        else:
            offsets5 = (self.selectedTime,offsets[0],offsets[1],num,0)
            sizes5 = (1,labels.shape[0], labels.shape[1],1,1)
        
        vu = VolumeUpdate(labels.reshape(sizes5),offsets5, sizes5, erase)
        vu.applyTo(self.labels.data)
        self.pendingLabels.append(vu)
        self.emit(QtCore.SIGNAL('newLabelsPending()'))
            
    def getVisibleState(self):
        #TODO: ugly, make nicer
        vs = [self.selectedTime, self.selSlices[0], self.selSlices[1], self.selSlices[2], self.selectedChannel]
        return vs



    def show(self):
        QtGui.QWidget.show(self)
        return  self.labels



class DrawManager(QtCore.QObject):
    def __init__(self, parent):
        QtCore.QObject.__init__(self)
        self.volumeEditor = parent
        self.shape = None
        self.brushSize = 3
        #self.initBoundingBox()
        self.penVis = QtGui.QPen(QtCore.Qt.white, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDraw = QtGui.QPen(QtCore.Qt.white, 3, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDraw.setColor(QtCore.Qt.white)
        self.pos = None
        self.erasing = False
        self.lines = []
        self.scene = QtGui.QGraphicsScene()

    def copy(self):
        """
        make a shallow copy of DrawManager - needed for python 2.5 compatibility
        """
        cp = DrawManager(self.parent)
        cp.volumeEditor = self.volumeEditor
        cp.shape = self.shape
        cp.brushSize = self.brushSize
        cp.penVis = self.penVis
        cp.penDraw = self.penDraw
        cp.pos = self.pos
        cp.erasing = self.erasing
        cp.lines = self.lines
        cp.scene = self.scene
        return cp

    def initBoundingBox(self):
        self.leftMost = self.shape[0]
        self.rightMost = 0
        self.topMost = self.shape[1]
        self.bottomMost = 0

    def growBoundingBox(self):
        self.leftMost = max(0,self.leftMost - self.brushSize -1)
        self.topMost = max(0,self.topMost - self.brushSize -1 )
        self.rightMost = min(self.shape[0],self.rightMost + self.brushSize + 1)
        self.bottomMost = min(self.shape[1],self.bottomMost + self.brushSize + 1)

    def toggleErase(self):
        self.erasing = not(self.erasing)

    def setBrushSize(self, size):
        self.brushSize = size
        self.penVis.setWidth(size)
        self.penDraw.setWidth(size)
        
    def getCurrentPenPixmap(self):
        pixmap = QtGui.QPixmap(self.brushSize, self.brushSize)
        if self.erasing == True:
            self.penVis.setColor(QtCore.Qt.black)
        else:
            self.penVis.setColor(self.volumeEditor.labelView.currentItem().color)
                    
        painter = QtGui.QPainter(pixmap)
        painter.setPen(self.penVis)
        painter.drawPoint(QtGui.Q)

    def beginDraw(self, pos, shape):
        self.shape = shape
        self.initBoundingBox()
        self.scene.clear()
        if self.erasing == True:
            self.penVis.setColor(QtCore.Qt.black)
        else:
            self.penVis.setColor(self.volumeEditor.labelView.currentItem().color)
        self.pos = pos
        line = self.moveTo(pos)
        return line

    def endDraw(self, pos):
        self.moveTo(pos)
        self.growBoundingBox()

        tempi = QtGui.QImage(self.rightMost - self.leftMost, self.bottomMost - self.topMost, QtGui.QImage.Format_ARGB32_Premultiplied) #TODO: format
        tempi.fill(0)
        painter = QtGui.QPainter(tempi)
        
        self.scene.render(painter, QtCore.QRectF(0,0, self.rightMost - self.leftMost, self.bottomMost - self.topMost),
            QtCore.QRectF(self.leftMost, self.topMost, self.rightMost - self.leftMost, self.bottomMost - self.topMost))
        
        oldLeft = self.leftMost
        oldTop = self.topMost
        return (oldLeft, oldTop, tempi) #TODO: hackish, probably return a class ??

    def dumpDraw(self, pos):
        res = self.endDraw(pos)
        self.beginDraw(pos, self.shape)
        return res


    def moveTo(self, pos):      
        lineVis = QtGui.QGraphicsLineItem(self.pos.x(), self.pos.y(),pos.x(), pos.y())
        lineVis.setPen(self.penVis)
        
        line = QtGui.QGraphicsLineItem(self.pos.x(), self.pos.y(),pos.x(), pos.y())
        line.setPen(self.penDraw)
        self.scene.addItem(line)

        self.pos = pos
        x = pos.x()
        y = pos.y()
        #update bounding Box :
        if x > self.rightMost:
            self.rightMost = x
        if x < self.leftMost:
            self.leftMost = x
        if y > self.bottomMost:
            self.bottomMost = y
        if y < self.topMost:
            self.topMost = y
        return lineVis


class ImageSceneRenderThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, None)
        self.volumeEditor = parent.volumeEditor
        #self.queue = deque(maxlen=1) #python 2.6
        self.queue = deque() #python 2.5

        self.dataPending = threading.Event()
        self.dataPending.clear()
        self.stopped = False


    def run(self):
        while not self.stopped:
            self.dataPending.wait()
            self.dataPending.clear()
            while len(self.queue) > 0:
                stuff = self.queue.pop()
                image, overlays , labels , labelsAlpha  = stuff
                
                if image.dtype == 'uint16':
                    image = (image / 255).astype(numpy.uint8)
                self.image = qimage2ndarray.array2qimage(image.swapaxes(0,1), normalize=self.volumeEditor.normalizeData)
        
                self.image = self.image.convertToFormat(QtGui.QImage.Format_ARGB32_Premultiplied)
        
                p = QtGui.QPainter(self.image)
        
                #add overlays
                for index, item in enumerate(overlays):
                    p.setOpacity(item.alpha)
                   
                    if item.colorTable != None:
                        imageO = qimage2ndarray.gray2qimage(item.data.swapaxes(0,1), normalize=False)
                        alphaChan = item.alphaChannel
                        imageO.setColorTable(item.colorTable)
                    else:
                        imageO = qimage2ndarray.array2qimage(item.data.swapaxes(0,1), normalize=False)
                        alphaChan = item.alphaChannel
                        imageO.setAlphaChannel(qimage2ndarray.gray2qimage(alphaChan.swapaxes(0,1), False))
        
                    p.drawImage(imageO.rect(), imageO)
        
                if labels is not None:
                    #p.setOpacity(item.alpha)
                    
                    p.setOpacity(labelsAlpha)
                    image0 = qimage2ndarray.gray2qimage(labels.swapaxes(0,1), False)
        
                    image0.setColorTable(self.volumeEditor.labelView.colorTab)
                    mask = image0.createMaskFromColor(QtGui.QColor(0,0,0).rgb(),QtCore.Qt.MaskOutColor) #QtGui.QBitmap.fromImage(
                    image0.setAlphaChannel(mask)
                    p.drawImage(image0.rect(), image0)
        
                p.end()
                del p
                
            self.emit(QtCore.SIGNAL("finished()"))        

class ImageScene( QtGui.QGraphicsView):
    def __borderMarginIndicator__(self, margin):
        """
        update the border margin indicator (left, right, top, bottom)
        to reflect the new given margin
        """
        self.margin = margin
        if self.border:
            self.scene.removeItem(self.border)
        borderPath = QtGui.QPainterPath()
        borderPath.setFillRule(QtCore.Qt.WindingFill)
        borderPath.addRect(0,0, margin, self.imShape[1])
        borderPath.addRect(0,0, self.imShape[0], margin)
        borderPath.addRect(self.imShape[0]-margin,0, margin, self.imShape[1])
        borderPath.addRect(0,self.imShape[1]-margin, self.imShape[0], margin)
        self.border = QtGui.QGraphicsPathItem(borderPath)
        brush = QtGui.QBrush(QtGui.QColor(0,0,255))
        brush.setStyle( QtCore.Qt.DiagCrossPattern )
        self.border.setBrush(brush)
        self.border.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.border.setZValue(200)
        self.scene.addItem(self.border)
        
    def __init__(self, parent, imShape, axis, drawManager):
        """
        imShape: 3D shape of the block that this slice view displays.
                 first two entries denote the x,y extent of one slice,
                 the last entry is the extent in slice direction
        """
        QtGui.QGraphicsView.__init__(self)
        self.imShape = imShape[0:2]
        self.drawManager = drawManager
        self.tempImageItems = []
        self.volumeEditor = parent
        self.axis = axis
        self.sliceNumber = 0
        self.sliceExtent = imShape[2]
        self.drawing = False
        self.view = self
        self.scene = QtGui.QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.scene.setSceneRect(0,0, imShape[0],imShape[1])
        self.view.setSceneRect(0,0, imShape[0],imShape[1])
        self.border = None
        self.allBorder = None
        if os.path.isfile('gui/backGroundBrush.png'):
            brushImage = QtGui.QBrush(QtGui.QImage('gui/backGroundBrush.png'))
        else:
            brushImage = QtGui.QBrush(QtGui.QColor(QtCore.Qt.black))
        self.setBackgroundBrush(brushImage)

        ##enable OpenGL acceleratino
        if self.volumeEditor.opengl is True:
            self.openglWidget = QtOpenGL.QGLWidget()
            self.setViewport(self.openglWidget)
        
        self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)
        self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
        self.imageItem = None
        self.pixmap = None
        self.image = QtGui.QImage(imShape[0], imShape[1], QtGui.QImage.Format_ARGB32_Premultiplied)
        if self.axis is 0:
            self.setStyleSheet("QWidget { border: 2px solid red; border-radius: 4px; }")
            self.view.rotate(90.0)
            self.view.scale(1.0,-1.0)
        if self.axis is 1:
            self.setStyleSheet("QWidget { border: 2px solid green; border-radius: 4px; }")
        if self.axis is 2:
            self.setStyleSheet("QWidget { border: 2px solid blue; border-radius: 4px; }")
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        #############################
        #cross chair
        pen = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DotLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.setMouseTracking(True)
        
        # Fixed pen width
        pen.setCosmetic(True)
        self.linex = QtGui.QGraphicsLineItem()
        self.liney = QtGui.QGraphicsLineItem()
        self.linex.setZValue(100)

        self.linex.setPen(pen)
        self.liney.setPen(pen)
        self.liney.setZValue(100)
        self.scene.addItem(self.linex)
        self.scene.addItem(self.liney)
        ##############################

        #indicators for the biggest filter mask's size
        #marks the area where labels should not be placed
        # -> the margin top, left, right, bottom
        self.__borderMarginIndicator__(0)
        # -> the complete 2D slice is marked
        brush = QtGui.QBrush(QtGui.QColor(0,0,255))
        brush.setStyle( QtCore.Qt.DiagCrossPattern )
        allBorderPath = QtGui.QPainterPath()
        allBorderPath.setFillRule(QtCore.Qt.WindingFill)
        allBorderPath.addRect(0, 0, imShape[0], imShape[1])
        self.allBorder = QtGui.QGraphicsPathItem(allBorderPath)
        self.allBorder.setBrush(brush)
        self.allBorder.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.scene.addItem(self.allBorder)
        self.allBorder.setVisible(False)
        self.allBorder.setZValue(200)

        #label updates while drawing, needed for interactive segmentation
        self.drawTimer = QtCore.QTimer()
        self.connect(self.drawTimer, QtCore.SIGNAL("timeout()"), self.updateLabels)
        
        # invisible cursor to enable custom cursor
        self.hiddenCursor = QtGui.QCursor(QtCore.Qt.BlankCursor)
        
        # For screen recording BlankCursor dont work
        #self.hiddenCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        
        self.thread = ImageSceneRenderThread(self)
        self.connect(self.thread, QtCore.SIGNAL('finished()'),self.redrawScene)
        self.thread.start()
        
        self.connect(self, QtCore.SIGNAL("destroyed()"),self.cleanUp)

        self.shortcutZoomIn = QtGui.QShortcut(QtGui.QKeySequence("+"), self, self.zoomIn, self.zoomIn)
        self.shortcutZoomIn.setContext(QtCore.Qt.WidgetShortcut )

        self.shortcutZoomOut = QtGui.QShortcut(QtGui.QKeySequence("-"), self, self.zoomOut, self.zoomOut)
        self.shortcutZoomOut.setContext(QtCore.Qt.WidgetShortcut )

    def cleanUp(self):
        #print "stopping ImageSCeneRenderThread", str(self.axis)
        
        self.thread.stopped = True
        self.thread.dataPending.set()
        self.thread.wait()

    def display(self, image, overlays = [], labels = None, labelsAlpha = 1.0):
        stuff = [image, overlays, labels, labelsAlpha]
        self.thread.queue.clear()
        self.thread.queue.append(stuff)
        self.thread.dataPending.set()
             

    def redrawScene(self):
        if self.thread.stopped is False:
            #if, in slicing direction, we are within the margin of the image border
            #we set the border overlay indicator to visible
            self.allBorder.setVisible((self.sliceNumber < self.margin or self.sliceExtent - self.sliceNumber < self.margin) and self.sliceExtent > 1)
            
            if self.imageItem is not None:
                self.scene.removeItem(self.imageItem)
                self.imageItem = None
                self.pixmap = None
                self.image = None

            for index, item in enumerate(self.tempImageItems):
                self.scene.removeItem(item)

            self.tempImageItems = []
            self.image = self.thread.image
            self.pixmap = QtGui.QPixmap.fromImage(self.image)
            self.imageItem = QtGui.QGraphicsPixmapItem(self.pixmap)
            self.scene.addItem(self.imageItem)
            self.viewport().repaint()
            self.volumeEditor.overview.display(self.axis)
        
    def updateLabels(self):
        result = self.drawManager.dumpDraw(self.mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelView.currentItem().number
        labels = numpy.where(labels > 0, number, 0)
        ls = LabelState('drawing', self.axis, self.volumeEditor.selSlices[self.axis], result[0:2], labels.shape, self.volumeEditor.selectedTime, self.volumeEditor, self.drawManager.erasing, labels, number)
        self.volumeEditor.history.append(ls)        
        self.volumeEditor.setLabels(result[0:2], self.axis, self.volumeEditor.sliceSelectors[self.axis].value(), labels, self.drawManager.erasing)

    
    def beginDraw(self, pos):
        self.mousePos = pos
        self.drawing  = True
        line = self.drawManager.beginDraw(pos, self.imShape)
        line.setZValue(99)
        self.tempImageItems.append(line)
        self.scene.addItem(line)
        
        self.drawTimer.start(100) #update labels every some ms
        
    def endDraw(self, pos):
        self.drawTimer.stop()
        result = self.drawManager.endDraw(pos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelView.currentItem().number
        labels = numpy.where(labels > 0, number, 0)
        ls = LabelState('drawing', self.axis, self.volumeEditor.selSlices[self.axis], result[0:2], labels.shape, self.volumeEditor.selectedTime, self.volumeEditor, self.drawManager.erasing, labels, number)
        self.volumeEditor.history.append(ls)        
        self.volumeEditor.setLabels(result[0:2], self.axis, self.volumeEditor.sliceSelectors[self.axis].value(), labels, self.drawManager.erasing)
        self.drawing = False


    def wheelEvent(self, event):
        keys = QtGui.QApplication.keyboardModifiers()
        k_alt = (keys == QtCore.Qt.AltModifier)
        k_ctrl = (keys == QtCore.Qt.ControlModifier)

        if self.drawing == True:
            mousePos = self.mapToScene(event.pos())
            self.endDraw(mousePos)
            self.drawing = True
            self.drawManager.beginDraw(mousePos, self.imShape)



        if event.delta() > 0:
            if k_alt is True:
                self.volumeEditor.sliceSelectors[self.axis].stepBy(10)
            elif k_ctrl is True:
                scaleFactor = 1.1
                self.doScale(scaleFactor)
            else:
                self.volumeEditor.sliceSelectors[self.axis].stepUp()
        else:
            if k_alt is True:
                self.volumeEditor.sliceSelectors[self.axis].stepBy(-10)
            elif k_ctrl is True:
                scaleFactor = 0.9
                self.doScale(scaleFactor)
            else:
                self.volumeEditor.sliceSelectors[self.axis].stepDown()

    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def doScale(self, factor):
        self.view.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            if self.volumeEditor.labelView.currentItem() is not None:
                mousePos = self.mapToScene(event.pos())
                self.beginDraw(mousePos)
        elif event.buttons() == QtCore.Qt.RightButton:
            self.onContext(event.pos())

    def mouseReleaseEvent(self, event):
        if self.drawing == True:
            mousePos = self.mapToScene(event.pos())
            self.endDraw(mousePos)
            self.volumeEditor.changeSlice(self.volumeEditor.selSlices[self.axis], self.axis)

    def mouseMoveEvent(self,event):
        mousePos = self.mousePos = self.mapToScene(event.pos())
        x = mousePos.x()
        y = mousePos.y()

        if x > 0 and x < self.image.width() and y > 0 and y < self.image.height():
            #should we hide the cursor only when entering once ? performance?
            self.setCursor(self.hiddenCursor)
            
            self.linex.setZValue(100)
            self.liney.setZValue(100)
            
            self.linex.setLine(0,y,self.image.width(),y)
            self.liney.setLine(x,0,x,self.image.height())
            if self.axis == 0:
                scene1 = self.volumeEditor.imageScenes[1]
                scene2 = self.volumeEditor.imageScenes[2]
                scene1.linex.setZValue(-100)
                scene1.liney.setZValue(-100)
                scene2.liney.setZValue(-100)
                scene2.linex.setZValue(100)
                scene2.linex.setLine(0,x,scene2.image.width(),x)
            elif self.axis == 1:
                scene0 = self.volumeEditor.imageScenes[0]
                scene2 = self.volumeEditor.imageScenes[2]
                scene0.linex.setZValue(-100)
                scene0.liney.setZValue(-100)
                scene2.linex.setZValue(-100)
                scene2.liney.setZValue(100)
                scene2.liney.setLine(x,0,x,scene2.image.height())
            elif self.axis == 2:
                scene0 = self.volumeEditor.imageScenes[0]
                scene1 = self.volumeEditor.imageScenes[1]
                scene0.liney.setZValue(-100)
                scene0.linex.setZValue(100)
                scene0.linex.setLine(y,0,y,scene0.image.height())
                scene1.linex.setZValue(-100)
                scene1.liney.setZValue(100)
                scene1.liney.setLine(x,0,x,scene1.image.height())
        else:
            self.unsetCursor()
                
        
        if event.buttons() == QtCore.Qt.LeftButton and self.drawing == True:
            line = self.drawManager.moveTo(mousePos)
            line.setZValue(99)
            self.tempImageItems.append(line)
            self.scene.addItem(line)


    def mouseDoubleClickEvent(self, event):
        mousePos = self.mapToScene(event.pos())
        x = mousePos.x()
        y = mousePos.y()
        
          
        if self.axis == 0:
            self.volumeEditor.changeSlice(x, 1)
            self.volumeEditor.changeSlice(y, 2)
        elif self.axis == 1:
            self.volumeEditor.changeSlice(x, 0)
            self.volumeEditor.changeSlice(y, 2)
        elif self.axis ==2:
            self.volumeEditor.changeSlice(x, 0)
            self.volumeEditor.changeSlice(y, 1)

    def onContext(self, pos):
        menu = QtGui.QMenu(self)
        labeling = menu.addMenu("Labeling")
        toggleEraseA = None
        if self.drawManager.erasing == True:
            toggleEraseA = labeling.addAction("Enable Labelmode")
        else:
            toggleEraseA = labeling.addAction("Enable Eraser")
        brushM = labeling.addMenu("Brush size")
        brush1 = brushM.addAction("1")
        brush3 = brushM.addAction("3")
        brush5 = brushM.addAction("5")
        brush10 = brushM.addAction("10")

        action = menu.exec_(QtGui.QCursor.pos())
        if action == toggleEraseA:
            self.drawManager.toggleErase()
        elif action == brush1:
            self.drawManager.setBrushSize(1)
        elif action == brush3:
            self.drawManager.setBrushSize(3)
        elif action == brush5:
            self.drawManager.setBrushSize(5)
        elif action == brush10:
            self.drawManager.setBrushSize(10)


class OverviewSceneDummy(QtGui.QWidget):
    def __init__(self, parent, shape):
        QtGui.QWidget.__init__(self)
        pass
    
    def display(self, axis):
        pass

    def redisplay(self):
        pass
    
class OverviewScene(QtOpenGL.QGLWidget):
    def __init__(self, parent, shape):
        QtOpenGL.QGLWidget.__init__(self)
        self.sceneShape = shape
        self.volumeEditor = parent
        self.images = parent.imageScenes
        self.sceneItems = []
        self.initialized = False
        self.tex = []
        self.tex.append(0)
        self.tex.append(0)
        self.tex.append(0)
        if self.volumeEditor.openglOverview is False:
            self.setVisible(False)

    def display(self, axis):
        if self.volumeEditor.openglOverview is True:  
            if self.initialized is True and self.images[0].pixmap is not None and self.images[1].pixmap is not None and self.images[2].pixmap is not None:
                #self.initializeGL()
                self.makeCurrent()
                if self.tex[axis] is not 0:
                    self.deleteTexture(self.tex[axis])
                self.paintGL(axis)
                self.swapBuffers()
            
    def redisplay(self):
        if self.volumeEditor.openglOverview is True:
            if self.initialized is True:
                for i in range(3):
                    self.makeCurrent()
                    if self.tex[i] is not 0:
                        self.deleteTexture(self.tex[i])
                    self.paintGL(i)
                self.swapBuffers()        

    def paintGL(self, axis = None):
        if self.volumeEditor.openglOverview is True:
            '''
            Drawing routine
            '''
            pix0 = self.images[0].pixmap
            pix1 = self.images[1].pixmap
            pix2 = self.images[2].pixmap
    
            maxi = max(pix0.width(),pix1.width())
            maxi = max(maxi, pix2.width())
            maxi = max(maxi, pix0.height())
            maxi = max(maxi, pix1.height())
            maxi = max(maxi, pix2.height())
    
            ratio0w = 1.0 * pix0.width() / maxi
            ratio1w = 1.0 * pix1.width() / maxi
            ratio2w = 1.0 * pix2.width() / maxi
    
            ratio0h = 1.0 * pix0.height() / maxi
            ratio1h = 1.0 * pix1.height() / maxi
            ratio2h = 1.0 * pix2.height() / maxi
           
            glMatrixMode(GL_MODELVIEW)
    
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
    
            glRotatef(30,1.0,0.0,0.0)
    
            glTranslatef(0,-3,-5)        # Move Into The Screen
    
            glRotatef(-30,0.0,1.0,0.0)        # Rotate The Cube On X, Y & Z
    
            #glRotatef(180,1.0,0.0,1.0)        # Rotate The Cube On X, Y & Z
    
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
    
            glBegin(GL_QUADS)            # Start Drawing The Cube
    
            glColor3f(1.0,0.0,1.0)            # Set The Color To Violet
            
            glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Top)
            glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Top)
            glVertex3f(-ratio2w, ratio1h, ratio2h)        # Bottom Left Of The Quad (Top)
            glVertex3f( ratio2w, ratio1h, ratio2h)        # Bottom Right Of The Quad (Top)
    
            glVertex3f( ratio2w,-ratio1h, ratio2h)        # Top Right Of The Quad (Bottom)
            glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Top Left Of The Quad (Bottom)
            glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Bottom)
            glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Bottom)
    
            glVertex3f( ratio2w, ratio1h, ratio2h)        # Top Right Of The Quad (Front)
            glVertex3f(-ratio2w, ratio1h, ratio2h)        # Top from PyQt4 import QtCore, QtGui, QtOpenGLLeft Of The Quad (Front)
            glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Bottom Left Of The Quad (Front)
            glVertex3f( ratio2w,-ratio1h, ratio2h)        # Bottom Right Of The Quad (Front)
    
            glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Back)
            glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Back)
            glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Back)
            glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Back)
    
            glVertex3f(-ratio2w, ratio1h, ratio2h)        # Top Right Of The Quad (Left)
            glVertex3f(-ratio2w, ratio1h,-ratio2h)        # Top Left Of The Quad (Left)
            glVertex3f(-ratio2w,-ratio1h,-ratio2h)        # Bottom Left Of The Quad (Left)
            glVertex3f(-ratio2w,-ratio1h, ratio2h)        # Bottom Right Of The Quad (Left)
    
            glVertex3f( ratio2w, ratio1h,-ratio2h)        # Top Right Of The Quad (Right)
            glVertex3f( ratio2w, ratio1h, ratio2h)        # Top Left Of The Quad (Right)
            glVertex3f( ratio2w,-ratio1h, ratio2h)        # Bottom Left Of The Quad (Right)
            glVertex3f( ratio2w,-ratio1h,-ratio2h)        # Bottom Right Of The Quad (Right)
            glEnd()                # Done Drawing The Quad
    
    
            curCenter = -(( 1.0 * self.volumeEditor.selSlices[2] / self.sceneShape[2] ) - 0.5 )*2.0*ratio1h
            if axis is 2 or self.tex[2] is 0:
                self.tex[2] = self.bindTexture(self.images[2].image, GL_TEXTURE_2D, GL_RGB)
            else:
                glBindTexture(GL_TEXTURE_2D,self.tex[2])
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode
    
            glBegin(GL_QUADS) #horizontal quad (e.g. first axis)
            glColor3f(1.0,1.0,1.0)            # Set The Color To White
            glTexCoord2d(0.0, 1.0)
            glVertex3f( -ratio2w,curCenter, -ratio2h)        # Top Right Of The Quad
            glTexCoord2d(1.0, 1.0)
            glVertex3f(+ ratio2w,curCenter, -ratio2h)        # Top Left Of The Quad
            glTexCoord2d(1.0, 0.0)
            glVertex3f(+ ratio2w,curCenter, + ratio2h)        # Bottom Left Of The Quad
            glTexCoord2d(0.0, 0.0)
            glVertex3f( -ratio2w,curCenter, + ratio2h)        # Bottom Right Of The Quad
            glEnd()
    
    
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture
    
            glBegin(GL_QUADS)
            glColor3f(0.0,0.0,1.0)            # Set The Color To Blue, Z Axis
            glVertex3f( ratio2w,curCenter, ratio2h)        # Top Right Of The Quad (Bottom)
            glVertex3f(- ratio2w,curCenter, ratio2h)        # Top Left Of The Quad (Bottom)
            glVertex3f(- ratio2w,curCenter,- ratio2h)        # Bottom Left Of The Quad (Bottom)
            glVertex3f( ratio2w,curCenter,- ratio2h)        # Bottom Right Of The Quad (Bottom)
            glEnd()
    
    
    
    
    
    
    
            curCenter = (( (1.0 * self.volumeEditor.selSlices[0]) / self.sceneShape[0] ) - 0.5 )*2.0*ratio2w
    
            if axis is 0 or self.tex[0] is 0:
                self.tex[0] = self.bindTexture(self.images[0].image, GL_TEXTURE_2D, GL_RGB)
            else:
                glBindTexture(GL_TEXTURE_2D,self.tex[0])
    
    
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode
    
            glBegin(GL_QUADS)
            glColor3f(0.8,0.8,0.8)            # Set The Color To White
            glTexCoord2d(1.0, 1.0)
            glVertex3f(curCenter, ratio0h, ratio0w)        # Top Right Of The Quad (Left)
            glTexCoord2d(0.0, 1.0)
            glVertex3f(curCenter, ratio0h, - ratio0w)        # Top Left Of The Quad (Left)
            glTexCoord2d(0.0, 0.0)
            glVertex3f(curCenter,- ratio0h,- ratio0w)        # Bottom Left Of The Quad (Left)
            glTexCoord2d(1.0, 0.0)
            glVertex3f(curCenter,- ratio0h, ratio0w)        # Bottom Right Of The Quad (Left)
            glEnd()
    
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture
    
            glBegin(GL_QUADS)
            glColor3f(1.0,0.0,0.0)            # Set The Color To Red, 
            glVertex3f(curCenter, ratio0h, ratio0w)        # Top Right Of The Quad (Left)
            glVertex3f(curCenter, ratio0h, - ratio0w)        # Top Left Of The Quad (Left)
            glVertex3f(curCenter,- ratio0h,- ratio0w)        # Bottom Left Of The Quad (Left)
            glVertex3f(curCenter,- ratio0h, ratio0w)        # Bottom Right Of The Quad (Left)
            glEnd()
    
    
            curCenter = (( 1.0 * self.volumeEditor.selSlices[1] / self.sceneShape[1] ) - 0.5 )*2.0*ratio2h
    
    
            if axis is 1 or self.tex[1] is 0:
                self.tex[1] = self.bindTexture(self.images[1].image, GL_TEXTURE_2D, GL_RGB)
            else:
                glBindTexture(GL_TEXTURE_2D,self.tex[1])
    
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode
    
            glBegin(GL_QUADS)
            glColor3f(0.6,0.6,0.6)            # Set The Color To White
            glTexCoord2d(1.0, 1.0)
            glVertex3f( ratio1w,  ratio1h, curCenter)        # Top Right Of The Quad (Front)
            glTexCoord2d(0.0, 1.0)
            glVertex3f(- ratio1w, ratio1h, curCenter)        # Top Left Of The Quad (Front)
            glTexCoord2d(0.0, 0.0)
            glVertex3f(- ratio1w,- ratio1h, curCenter)        # Bottom Left Of The Quad (Front)
            glTexCoord2d(1.0, 0.0)
            glVertex3f( ratio1w,- ratio1h, curCenter)        # Bottom Right Of The Quad (Front)
            glEnd()
    
            glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) #wireframe mode
            glBindTexture(GL_TEXTURE_2D,0) #unbind texture
            glBegin(GL_QUADS)
            glColor3f(0.0,1.0,0.0)            # Set The Color To Green
            glVertex3f( ratio1w,  ratio1h, curCenter)        # Top Right Of The Quad (Front)
            glVertex3f(- ratio1w, ratio1h, curCenter)        # Top Left Of The Quad (Front)
            glVertex3f(- ratio1w,- ratio1h, curCenter)        # Bottom Left Of The Quad (Front)
            glVertex3f( ratio1w,- ratio1h, curCenter)        # Bottom Right Of The Quad (Front)
            glEnd()
    
            glFlush()

    def resizeGL(self, w, h):
        '''
        Resize the GL window
        '''

        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 30.0)

    def initializeGL(self):
        '''
        Initialize GL
        '''

        # set viewing projection
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClearDepth(1.0)

        glDepthFunc(GL_LESS)                # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)                # Enables Depth Testing
        glShadeModel(GL_SMOOTH)                # Enables Smooth Color Shading
        glEnable(GL_TEXTURE_2D)
        glLineWidth( 2.0 );

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 30.0)
        
        self.initialized = True

#class OverviewScene2(QtGui.QGraphicsView):
#    def __init__(self, images):
#        QtGui.QGraphicsView.__init__(self)
#        self.scene = QtGui.QGraphicsScene(self)
##        self.scene.setSceneRect(0,0, imShape[0],imShape[1])
#        self.setScene(self.scene)
#        self.setRenderHint(QtGui.QPainter.Antialiasing)
#        self.images = images
#        self.sceneItems = []
#
#    def display(self):
#        for index, item in enumerate(self.sceneItems):
#            self.scene.removeItem(item)
#            del item
#        self.sceneItems = []
#        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[0].pixmap))
#        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[1].pixmap))
#        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[2].pixmap))
#        for index, item in enumerate(self.sceneItems):
#            self.scene.addItem(item)

def test():
    """Text editor demo"""
    import numpy
    app = QtGui.QApplication([""])

    im = (numpy.random.rand(1024,1024)*255).astype(numpy.uint8)
    im[0:10,0:10] = 255
    
    dialog = VolumeEditor(im)
    dialog.show()
    app.exec_()
    del app

    app = QtGui.QApplication([""])

    im = (numpy.random.rand(128,128,128)*255).astype(numpy.uint8)
    im[0:10,0:10,0:10] = 255

    dialog = VolumeEditor(im)
    dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
