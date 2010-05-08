# -*- coding: utf-8 -*-
#
# Copyright © 2009 Christoph Straehle
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
Dataset Editor Dialog based on PyQt4
"""
import math
from OpenGL.GL import *
from OpenGL.GLU import *

from PyQt4 import QtCore, QtGui, QtOpenGL

import vigra, numpy
import qimage2ndarray
import h5py
import copy

# Local import
from spyderlib.config import get_icon, get_font

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
        super(VolumeEditorList, self).__init__()
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
        h5G.create_dataset(h5G,name,data = self.data)
         
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
        else:
            self.alphaChannel = numpy.ones(data.shape[0:2],'uint8')*255
            self.data = data

class VolumeOverlay(QtGui.QListWidgetItem, DataAccessor):
    def __init__(self, data, name = "Red Overlay", color = 0, alpha = 0.4, colorTable = None):
        QtGui.QListWidgetItem.__init__(self,name)
        DataAccessor.__init__(self,data)
        self.colorTable = colorTable
        self.setTooltip = name
        self.color = color
        self.alpha = alpha
        self.name = name
        self.visible = True

    def getOverlaySlice(self, num, axis, time = 0, channel = 0):
        return OverlaySlice(self.getSlice(num,axis,time,channel), self.color, self.alpha, self.colorTable)

class OverlayListView(QtGui.QListWidget):
    def __init__(self,parent):
        self.volumeEditor = parent
        super(OverlayListView, self).__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.overlays = [] #array of VolumeOverlays

    def clearOverlays(self):
        self.clear()
        self.overlays = []

    def addOverlay(self, overlay):
        self.overlays.append(overlay)
        self.addItem(overlay)

    def onContext(self, pos):
        index = self.indexAt(pos)

        if not index.isValid():
           return

        item = self.itemAt(pos)
        name = item.text()

        menu = QtGui.QMenu(self)

        #removeAction = menu.addAction("Remove")
        if item.visible is True:
            toggleHideAction = menu.addAction("Hide")
        else:
            toggleHideAction = menu.addAction("Show")

        action = menu.exec_(QtGui.QCursor.pos())
#        if action == removeAction:
#            self.overlays.remove(item)
#            it = self.takeItem(index.row())
#            del it
        if action == toggleHideAction:
            item.visible = not(item.visible)
            self.volumeEditor.repaint()
            


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
    
class VolumeLabels():
    def __init__(self, data = None):
        if issubclass(data.__class__, DataAccessor):
            self.data = data
        else:
            self.data = DataAccessor(data, channels = False)

        self.descriptions = [] #array of VolumeLabelDescriptions
        
    def serialize(self, h5G, name = "labels"):
        self.data.serialize(h5G, name)
        h5G[name].attrs['color'] = [] 
        h5G[name].attrs['name'] = []
        h5G[name].attrs['number'] = []
        for index, item in enumerate(self.descriptions):
            h5G[name].attrs['color'] +=  item.color
            h5G[name].attrs['name'] += item.name
            h5G[name].attrs['number'] += item.number
    
    @staticmethod    
    def deserialize(h5G, name ="labels"):
        if name in h5G.keys():
            data = DataAccessor.deserialize(h5G, name)
            colors = h5G[name].attrs['color']
            names = h5G[name].attrs['name']
            numbers = h5G[name].attrs['number']
            descriptions = []
            for index, item in enumerate(colors):
                descriptions.append(VolumeLabelDescription(names[index], numbers[index], colors[index]))
    
            vl =  VolumeLabels(data)
            vl.descriptions = desctiptions
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
        super(LabelListItem, self).__init__(name)
        self.number = number
        self.visible = True
        self.setColor(color)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        

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
        super(LabelListView, self).__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)
        self.colorTab = []
        self.items = []
        self.volumeEditor = parent
        self.initFromMgr(parent.labels)
        self.labelColorTable = [QtGui.QColor(QtCore.Qt.red), QtGui.QColor(QtCore.Qt.green), QtGui.QColor(QtCore.Qt.yellow), QtGui.QColor(QtCore.Qt.blue), QtGui.QColor(QtCore.Qt.magenta) , QtGui.QColor(QtCore.Qt.darkYellow), QtGui.QColor(QtCore.Qt.lightGray)]
        self.connect(self, QtCore.SIGNAL("currentTextChanged(QString)"), self.changeText)

    
    def initFromMgr(self, volumelabel):
        self.volumeLabel = volumelabel
        for index, item in enumerate(volumelabel.descriptions):
            li = LabelListItem(item.name,item.number, QtGui.QColor.fromRgb(item.color))
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
        
    def addLabel(self, labelName, labelNumber, color):
        description = VolumeLabelDescription(labelName, labelNumber, color.rgb())
        self.volumeLabel.descriptions.append(description)
        
        label =  LabelListItem(labelName, labelNumber, color)
        self.items.append(label)
        self.addItem(label)
        self.buildColorTab()
        self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))

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
            self.volumeLabel.descriptions.__delitem__(index.row())
            #TODO make nicer !
            temp = numpy.where(self.volumeLabel.data[:,:,:,:,:] == item.number, 0, self.volumeLabel.data[:,:,:,:,:])
            self.volumeLabel.data[:,:,:,:,:] = temp[:,:,:,:,:]
            self.items.remove(item)
            it = self.takeItem(index.row())
            del it
            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))
        elif action == toggleHideAction:
            item.toggleVisible()
        elif action == colorAction:
            color = QtGui.QColorDialog().getColor()
            item.setColor(color)
            self.volumeLabel.descriptions[index.row()].color = color.rgb()
            self.emit(QtCore.SIGNAL("labelPropertiesChanged()"))

        self.buildColorTab()

#abstract base class for undo redo stuff
class State():
    def __init__(self):
        pass

    def restore(self):
        pass


class LabelState(State):
    def __init__(self, title, axis, num, offsets, data, time):
        self.title = title
        self.time = time
        self.num = num
        self.offsets = offsets
        self.axis = axis
        self.data = data

    def restore(self, volumeEditor):
        temp = self.data.copy()
        self.data = volumeEditor.labels.data.getSubSlice(self.offsets, temp.shape, self.num, self.axis, self.time, 0).copy()
        volumeEditor.labels.data.setSubSlice(self.offsets, temp, self.num, self.axis, self.time, 0)
        volumeEditor.changeSlice(self.num, self.axis)



class HistoryManager(QtCore.QObject):
    def __init__(self, parent, maxSize = 30):
        self.volumeEditor = parent
        self.maxSize = maxSize
        self.history = []
        self.current = 0

    def append(self, state):
        if self.current + 1 < len(self.history):
            self.history = self.history[0:self.current+1]
        self.history.append(state)

        if len(self.history) > self.maxSize:
            self.history = self.history[len(self.history)-self.maxSize:len(self.history)]
        
        self.current = len(self.history) - 1

    def undo(self):
        if self.current > 0:
            self.history[self.current].restore(self.volumeEditor)
            self.current -= 1

    def redo(self):
        if self.current < len(self.history) - 1:
            self.history[self.current + 1].restore(self.volumeEditor)
            self.current += 1

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
        tempData = dataAcc[offsets[0]:offsets[0]+sizes[0],offsets[1]:offsets[1]+sizes[1],offsets[2]:offsets[2]+sizes[2],offsets[3]:offsets[3]+sizes[3],offsets[4]:offsets[4]+sizes[4]] 

        if self.erasing == True:
            tempData = numpy.where(self.data > 0, 0, tempData)
        else:
            tempData = numpy.where(self.data > 0, self.data, tempData)
        
        dataAcc[offsets[0]:offsets[0]+sizes[0],offsets[1]:offsets[1]+sizes[1],offsets[2]:offsets[2]+sizes[2],offsets[3]:offsets[3]+sizes[3],offsets[4]:offsets[4]+sizes[4]] = tempData  



class VolumeEditor(QtGui.QWidget):
    """Array Editor Dialog"""
    def __init__(self, image, name="", font=None,
                 readonly=False, size=(400, 300), labels = None ):
        super(VolumeEditor, self).__init__()
        self.name = name
        title = name

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
        self.imageScenes.append(ImageScene(self, self.image.shape[2:4], 0,self.drawManager))
        self.imageScenes.append(ImageScene( self, (self.image.shape[1], self.image.shape[3]) ,  1,self.drawManager))
        self.imageScenes.append(ImageScene(self, self.image.shape[1:3], 2,self.drawManager))
        self.grid.addWidget(self.imageScenes[2], 0, 0)
        self.grid.addWidget(self.imageScenes[0], 0, 1)
        self.grid.addWidget(self.imageScenes[1], 1, 0)
        
        self.overview = OverviewScene(self, self.image.shape[1:4])
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
        self.toolBox.setMaximumWidth(100)
        self.toolBox.setMinimumWidth(100)

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

        #Slice Selector Combo Box in right side toolbox
        self.sliceSelectors = []
        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceX)
        self.toolBoxLayout.addWidget(QtGui.QLabel("Slice 0:"))
        self.toolBoxLayout.addWidget(sliceSpin)
        sliceSpin.setRange(0,self.image.shape[1] - 1)
        self.sliceSelectors.append(sliceSpin)

        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceY)
        self.toolBoxLayout.addWidget(QtGui.QLabel("Slice 1:"))
        self.toolBoxLayout.addWidget(sliceSpin)
        sliceSpin.setRange(0,self.image.shape[2] - 1)
        self.sliceSelectors.append(sliceSpin)

        sliceSpin = QtGui.QSpinBox()
        sliceSpin.setEnabled(True)
        self.connect(sliceSpin, QtCore.SIGNAL("valueChanged(int)"), self.changeSliceZ)
        self.toolBoxLayout.addWidget(QtGui.QLabel("Slice 2:"))
        self.toolBoxLayout.addWidget(sliceSpin)
        sliceSpin.setRange(0,self.image.shape[3] - 1)
        self.sliceSelectors.append(sliceSpin)

        self.selSlices = []
        self.selSlices.append(0)
        self.selSlices.append(0)
        self.selSlices.append(0)


        #Overlay selector
        self.addOverlayButton = QtGui.QPushButton("Add Overlay")
        self.connect(self.addOverlayButton, QtCore.SIGNAL("pressed()"), self.addOverlayDialog)
        self.toolBoxLayout.addWidget(self.addOverlayButton)

        self.overlayView = OverlayListView(self)
        self.toolBoxLayout.addWidget( self.overlayView)

        #Label selector
        self.addLabelButton = QtGui.QPushButton("Create Label Class")
        self.connect(self.addLabelButton, QtCore.SIGNAL("pressed()"), self.addLabel)
        self.toolBoxLayout.addWidget(self.addLabelButton)

        self.labelView = LabelListView(self)

        self.toolBoxLayout.addWidget( self.labelView)


        self.toolBoxLayout.setAlignment( QtCore.Qt.AlignTop )

        self.layout.addWidget(self.toolBox)

        # Make the dialog act as a window and stay on top
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowIcon(get_icon('edit.png'))
        self.setWindowTitle(self.tr("Volume") + \
                            "%s" % (" - "+str(title) if str(title) else ""))

        #start viewing in the center of the volume
        self.changeSliceX(numpy.floor((self.image.shape[0] - 1) / 2))
        self.changeSliceY(numpy.floor((self.image.shape[1] - 1) / 2))
        self.changeSliceZ(numpy.floor((self.image.shape[2] - 1) / 2))

        #undo/redo
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self, self.historyUndo )
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self, self.historyRedo )

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
        ov = VolumeOverlay(data,name, color, alpha, colorTab)
        ov.visible = visible
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
                    tempoverlays.append(item.getOverlaySlice(self.selSlices[i],i, self.selectedTime, self.selectedChannel)) 
    
            tempImage = self.image.getSlice(self.selSlices[i], i, self.selectedTime, self.selectedChannel)
    
            if self.labels.data is not None:
                tempLabels = self.labels.data.getSlice(self.selSlices[i],i, self.selectedTime, self.selectedChannel)
    
            self.imageScenes[i].display(tempImage, tempoverlays, tempLabels)
        self.overview.redisplay()        


    def addLabel(self):
        self.labelView.createLabel()


    def get_copy(self):
        """Return modified text"""
        return unicode(self.edit.toPlainText())

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
        tempImage = None
        tempLabels = None
        tempoverlays = []
        self.sliceSelectors[axis].setValue(num)

        for index, item in enumerate(self.overlayView.overlays):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(num,axis, self.selectedTime, self.selectedChannel)) 

        tempImage = self.image.getSlice(num, axis, self.selectedTime, self.selectedChannel)


        if self.labels.data is not None:
            tempLabels = self.labels.data.getSlice(num,axis, self.selectedTime, self.selectedChannel)

        self.selSlices[axis] = num
        self.imageScenes[axis].display(tempImage, tempoverlays, tempLabels)
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
        if event.delta() > 0:
            scaleFactor = 1.1
        else:
            scaleFactor = 0.9
        self.imageScenes[0].doScale(scaleFactor)
        self.imageScenes[1].doScale(scaleFactor)
        self.imageScenes[2].doScale(scaleFactor)

    def setLabels(self, offsets, axis, labels, erase):
        num = self.sliceSelectors[axis].value()
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
        self.pendingLabels.append(vu)
        vu.applyTo(self.labels.data)
        self.emit(QtCore.SIGNAL('newLabelsPending()'))
            
    def getVisibleState(self):
        #TODO: ugly, make nicer
        vs = [self.selectedTime, self.sliceSelectors[0].value(), self.sliceSelectors[1].value(), self.sliceSelectors[2].value(), self.selectedChannel]
        return vs



    def show(self):
        super(VolumeEditor, self).show()
        return  self.labels



class DrawManager(QtCore.QObject):
    def __init__(self, parent):
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

    def initBoundingBox(self):
        self.leftMost = self.shape[0]
        self.rightMost = 0
        self.topMost = self.shape[1]
        self.bottomMost = 0

    def growBoundingBox(self):
        self.leftMost = max(0,self.leftMost - 10)
        self.topMost = max(0,self.topMost - 10)
        self.rightMost = min(self.shape[0],self.rightMost + 10)
        self.bottomMost = min(self.shape[1],self.bottomMost + 10)

    def toggleErase(self):
        self.erasing = not(self.erasing)

    def setBrushSize(self, size):
        self.brushSize = size
        self.penVis.setWidth(size)
        self.penDraw.setWidth(size)

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


class ImageScene( QtGui.QGraphicsView):
    def __init__(self, parent, imShape, axis, drawManager):
        QtGui.QGraphicsView.__init__(self)
        self.imShape = imShape
        self.drawManager = drawManager
        self.tempImageItems = []
        self.volumeEditor = parent
        self.axis = axis
        self.drawing = False
        self.view = self
        self.scene = QtGui.QGraphicsScene(self.view)
        self.scene.setSceneRect(0,0, imShape[0],imShape[1])
        self.view.setScene(self.scene)
        self.view.setSceneRect(0,0, imShape[0],imShape[1])
        brushImage = QtGui.QBrush(QtGui.QImage('gui/backGroundBrush.png'))
        self.setBackgroundBrush(brushImage)

        ##enable OpenGL acceleratino, flickers on Linux (background not redrawn ? -> investigate)
        #FRED opengl
        self.openglWidget = QtOpenGL.QGLWidget()
        self.setViewport(self.openglWidget)
        
        self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)
        self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)
        self.imageItem = None
        self.pixmap = None
        self.image = None
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

        #label updates while drawing, needed for interactive segmentation
        self.drawTimer = QtCore.QTimer()
        self.connect(self.drawTimer, QtCore.SIGNAL("timeout()"), self.updateLabels)


    def display(self, image, overlays = [], labels = None):
        if self.imageItem is not None:
            self.scene.removeItem(self.imageItem)
            del self.imageItem
            del self.pixmap
            del self.image
            self.imageItem = None

        for index, item in enumerate(self.tempImageItems):
            self.scene.removeItem(item)

        self.tempImageItems = []


        if image.dtype == 'uint16':
            image = (image / 255).astype(numpy.uint8)
        self.image = qimage2ndarray.array2qimage(image.swapaxes(0,1), normalize=False)

        self.image = self.image.convertToFormat(QtGui.QImage.Format_ARGB32_Premultiplied)
        
        #add overlays
        for index, item in enumerate(overlays):
            p = QtGui.QPainter(self.image)
            p.setOpacity(item.alpha)

            imageO = qimage2ndarray.array2qimage(item.data.swapaxes(0,1), normalize=False)
            alphaChan = item.alphaChannel
            
            if item.colorTable != None:
                imageO.setColorTable(item.colorTable)
            else:
                imageO.setAlphaChannel(qimage2ndarray.gray2qimage(alphaChan.swapaxes(0,1), False))

            p.drawImage(imageO.rect(), imageO)
            p.end()
            del p

        if labels is not None:
            p1 = QtGui.QPainter(self.image)
            #p1.setOpacity(0.99)
            image0 = qimage2ndarray.gray2qimage(labels.swapaxes(0,1), False)

            image0.setColorTable(self.volumeEditor.labelView.colorTab)
            mask = image0.createMaskFromColor(QtGui.QColor(0,0,0).rgb(),QtCore.Qt.MaskOutColor) #QtGui.QBitmap.fromImage(
            #alphaChan = numpy.where(labels > 0, 255, 0)
            #mask = qimage2ndarray.gray2qimage(alphaChan, False)
            image0.setAlphaChannel(mask)
            p1.drawImage(image0.rect(), image0)
            p1.end()
            del p1


        self.pixmap = QtGui.QPixmap.fromImage(self.image)

        self.imageItem = QtGui.QGraphicsPixmapItem(self.pixmap)

        self.scene.addItem(self.imageItem)
        
        self.view.repaint()        


    def updateLabels(self):
        result = self.drawManagerCopy.endDraw(self.mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelView.currentItem().number
        labels = numpy.where(labels > 0, number, 0)
        self.volumeEditor.setLabels(result[0:2], self.axis, labels, self.drawManager.erasing)        
        self.drawManagerCopy.beginDraw(self.mousePos, self.imShape)

    
    def beginDraw(self, pos):
        self.mousePos = pos
        self.drawManagerCopy = copy.copy(self.drawManager)
        self.drawing  = True
        line = self.drawManager.beginDraw(pos, self.imShape)
        line.setZValue(99)
        self.tempImageItems.append(line)
        self.scene.addItem(line)
        
        self.drawTimer.start(200) #update labels every some ms
        self.drawManagerCopy.beginDraw(pos, self.imShape)
        
    def endDraw(self, pos):
        self.drawTimer.stop()
        result = self.drawManager.endDraw(pos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelView.currentItem().number
        labels = numpy.where(labels > 0, number, 0)
        self.volumeEditor.setLabels(result[0:2], self.axis, labels, self.drawManager.erasing)
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
                
        
        if event.buttons() == QtCore.Qt.LeftButton and self.drawing == True:
            self.drawManagerCopy.moveTo(mousePos)
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


class OverviewScene(QtOpenGL.QGLWidget):
    '''
    Widget for drawing two spirals.
    '''

    def __init__(self, parent, shape):
        QtOpenGL.QGLWidget.__init__(self)
        self.sceneShape = shape
        self.parent = parent
        self.images = parent.imageScenes
        self.sceneItems = []
        self.initialized = False
        self.tex = []
        self.tex.append(0)
        self.tex.append(0)
        self.tex.append(0)

    def display(self, axis):
        #disable for FRED opengl
        self.initialized = False
        
        if self.initialized is True:
            #self.initializeGL()
            self.makeCurrent()
            if self.tex[axis] is not 0:
                self.deleteTexture(self.tex[axis])
            self.paintGL(axis)
            self.swapBuffers()
            
    def redisplay(self):
        if self.initialized is True:
            for i in range(3):
                self.makeCurrent()
                if self.tex[i] is not 0:
                    self.deleteTexture(self.tex[i])
                self.paintGL(i)
            self.swapBuffers()        

    def paintGL(self, axis = None):
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


        curCenter = -(( 1.0 * self.parent.selSlices[2] / self.sceneShape[2] ) - 0.5 )*2.0*ratio1h
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







        curCenter = (( (1.0 * self.parent.selSlices[0]) / self.sceneShape[0] ) - 0.5 )*2.0*ratio2w

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


        curCenter = (( 1.0 * self.parent.selSlices[1] / self.sceneShape[1] ) - 0.5 )*2.0*ratio2h


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

class OverviewScene2(QtGui.QGraphicsView):
    def __init__(self, images):
        QtGui.QGraphicsView.__init__(self)
        self.scene = QtGui.QGraphicsScene(self)
#        self.scene.setSceneRect(0,0, imShape[0],imShape[1])
        self.setScene(self.scene)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.images = images
        self.sceneItems = []

    def display(self):
        for index, item in enumerate(self.sceneItems):
            self.scene.removeItem(item)
            del item
        self.sceneItems = []
        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[0].pixmap))
        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[1].pixmap))
        self.sceneItems.append(QtGui.QGraphicsPixmapItem(self.images[2].pixmap))
        for index, item in enumerate(self.sceneItems):
            self.scene.addItem(item)

def test():
    """Text editor demo"""
    import numpy
    from spyderlib.utils.qthelpers import qapplication
    app = qapplication()

    im = (numpy.random.rand(1024,1024)*255).astype(numpy.uint8)
    im[0:10,0:10] = 255
    
    dialog = VolumeEditor(im)
    dialog.show()
    app.exec_()


    app = qapplication()

    im = (numpy.random.rand(128,128,128)*255).astype(numpy.uint8)
    im[0:10,0:10,0:10] = 255

    dialog = VolumeEditor(im)
    dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
