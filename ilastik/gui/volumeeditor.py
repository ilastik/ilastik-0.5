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
import qimage2ndarray.qimageview
import math
import ctypes 

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
except Exception, e:
    print e
    pass

from PyQt4 import QtCore, QtGui, QtOpenGL
import sip
import vigra, numpy
import qimage2ndarray
import h5py
import copy
import os.path
from collections import deque
import threading
import traceback
import os, sys

from ilastik.core.volume import DataAccessor,  Volume

from shortcutmanager import *

from ilastik.gui.overlayWidget import OverlayListWidget
from ilastik.gui.labelWidget import LabelListWidget
import ilastik.gui.exportDialog as exportDialog

from ilastik.gui.iconMgr import ilastikIcons # oli todo
# Local import
#from spyderlib.config import get_icon, get_font

##mixin to enable label access
#class VolumeLabelAccessor():
    #def __init__():
        #self._labels = None

##extend ndarray with _label attribute
#numpy.ndarray.__base__ += (VolumeLabelAccessor, )





def rgb(r, g, b):
    # use qRgb to pack the colors, and then turn the resulting long
    # into a negative integer with the same bitpattern.
    return (QtGui.qRgb(r, g, b) & 0xffffff) - 0x1000000



# oli todo
class MyQLabel(QtGui.QLabel):
    def __init(self, parent):
        QtGui.QLabel.__init__(self, parent)
    #enabling clicked signal for QLable
    def mouseReleaseEvent(self, ev):
        self.emit(QtCore.SIGNAL('clicked()'))
        

class PatchAccessor():
    def __init__(self, size_x,size_y, blockSize = 128):
        self.blockSize = blockSize
        self.size_x = size_x
        self.size_y = size_y

        self.cX = int(numpy.ceil(1.0 * size_x / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cXend = size_x % self.blockSize
        if self.cXend < self.blockSize / 3 and self.cXend != 0 and self.cX > 1:
            self.cX -= 1
        else:
            self.cXend = 0

        self.cY = int(numpy.ceil(1.0 * size_y / self.blockSize))

        #last blocks can be very small -> merge them with the secondlast one
        self.cYend = size_y % self.blockSize
        if self.cYend < self.blockSize / 3 and self.cYend != 0 and self.cY > 1:
            self.cY -= 1
        else:
            self.cYend = 0


        self.patchCount = self.cX * self.cY


    def getPatchBounds(self, blockNum, overlap = 0):
        z = int(numpy.floor(blockNum / (self.cX*self.cY)))
        rest = blockNum % (self.cX*self.cY)
        y = int(numpy.floor(rest / self.cX))
        x = rest % self.cX

        startx = max(0, x*self.blockSize - overlap)
        endx = min(self.size_x, (x+1)*self.blockSize + overlap)
        if x+1 >= self.cX:
            endx = self.size_x

        starty = max(0, y*self.blockSize - overlap)
        endy = min(self.size_y, (y+1)*self.blockSize + overlap)
        if y+1 >= self.cY:
            endy = self.size_y


        return [startx,endx,starty,endy]

    def getPatchesForRect(self,startx,starty,endx,endy):
        sx = int(numpy.floor(1.0 * startx / self.blockSize))
        ex = int(numpy.ceil(1.0 * endx / self.blockSize))
        sy = int(numpy.floor(1.0 * starty / self.blockSize))
        ey = int(numpy.ceil(1.0 * endy / self.blockSize))
        
        
        if ey > self.cY:
            ey = self.cY

        if ex > self.cX :
            ex = self.cX

        nums = []
        for y in range(sy,ey):
            nums += range(y*self.cX+sx,y*self.cX+ex)
        
        return nums

        
    

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
        self.dataBefore = volumeEditor.labelWidget.volumeLabels.data.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
        
    def restore(self, volumeEditor):
        temp = volumeEditor.labelWidget.volumeLabels.data.getSubSlice(self.offsets, self.labels.shape, self.num, self.axis, self.time, 0).copy()
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
            #volumeEditor.repaint()
            #repainting is already done automatically by the setLabels function
            pass
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
            
    def serialize(self, grp, name='history'):
        histGrp = grp.create_group(name)
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




class DummyLabelWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.volumeLabels = None
        
    def currentItem(self):
        return None

class DummyOverlayListWidget(QtGui.QWidget):
    def __init__(self,  parent):
        QtGui.QWidget.__init__(self)
        self.volumeEditor = parent
        self.overlays = []


class VolumeEditor(QtGui.QWidget):
    """Array Editor Dialog"""
    def __init__(self, image, parent,  name="", font=None,
                 readonly=False, size=(400, 300), opengl = True, openglOverview = True):
        QtGui.QWidget.__init__(self, parent)
        self.ilastik = parent
        self.name = name
        title = name
        
        self.labelsAlpha = 1.0

        #Bordermargin settings - they control the blue markers that signal the region from wich the
        #labels are not used for trainig
        self.useBorderMargin = False
        self.borderMargin = 0


        #this setting controls the rescaling of the displayed data to the full 0-255 range
        self.normalizeData = False

        #this settings controls the timer interval during interactive mode
        #set to 0 to wait for complete brushstrokes !
        self.drawUpdateInterval = 300

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
        
        self.embedded = True


        QtGui.QPixmapCache.setCacheLimit(100000)


        if issubclass(image.__class__, DataAccessor):
            self.image = image
        elif issubclass(image.__class__, Volume):
            self.image = image.data
        else:
            self.image = DataAccessor(image)

        self.save_thread = ImageSaveThread(self)
              
        self.selectedTime = 0
        self.selectedChannel = 0

        self.pendingLabels = []

        #self.setAccessibleName(self.name)


        self.history = HistoryManager(self)

        self.layout = QtGui.QHBoxLayout()
        self.setLayout(self.layout)


        self.grid = QtGui.QGridLayout()

        self.drawManager = DrawManager(self)

        self.imageScenes = []

        if self.openglOverview is True:
            self.sharedOpenGLWidget = QtOpenGL.QGLWidget()
            self.overview = OverviewScene(self, self.image.shape[1:4])
        else:
            self.overview = OverviewSceneDummy(self, self.image.shape[1:4])
            
        self.grid.addWidget(self.overview, 1, 1)
        
        self.imageScenes.append(ImageScene(self, (self.image.shape[2],  self.image.shape[3], self.image.shape[1]), 0 ,self.drawManager))
        self.imageScenes.append(ImageScene(self, (self.image.shape[1],  self.image.shape[3], self.image.shape[2]), 1 ,self.drawManager))
        self.imageScenes.append(ImageScene(self, (self.image.shape[1],  self.image.shape[2], self.image.shape[3]), 2 ,self.drawManager))
        
        self.grid.addWidget(self.imageScenes[2], 0, 0)
        self.grid.addWidget(self.imageScenes[0], 0, 1)
        self.grid.addWidget(self.imageScenes[1], 1, 0)


        if self.image.shape[1] == 1:
            self.imageScenes[1].setVisible(False)
            self.imageScenes[2].setVisible(False)
            self.overview.setVisible(False)

        self.gridWidget = QtGui.QWidget()
        self.gridWidget.setLayout(self.grid)
        tempLayout = QtGui.QVBoxLayout(self)
        tempLayout.addWidget(self.gridWidget)
        self.posLabel = QtGui.QLabel("Mouse")
        tempLayout.addWidget(self.posLabel)
        self.layout.addLayout(tempLayout)

        #right side toolbox
        self.toolBox = QtGui.QWidget()
        self.toolBoxLayout = QtGui.QVBoxLayout()
        self.toolBox.setLayout(self.toolBoxLayout)
        self.toolBox.setMaximumWidth(190)
        self.toolBox.setMinimumWidth(190)

        self.labelWidget = None
        self.setLabelWidget(DummyLabelWidget())


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
        self.channelLayout = QtGui.QHBoxLayout()
        
        self.channelSpinLabel = QtGui.QLabel("Channel:")
        
        self.channelSpin = QtGui.QSpinBox()
        self.channelSpin.setEnabled(True)
        self.connect(self.channelSpin, QtCore.SIGNAL("valueChanged(int)"), self.setChannel)
        
        self.channelEditBtn = QtGui.QPushButton('Edit channels')
        self.connect(self.channelEditBtn, QtCore.SIGNAL("clicked()"), self.on_editChannels)
        
        
        self.toolBoxLayout.addWidget(self.channelSpinLabel)
        self.channelLayout.addWidget(self.channelSpin)
        self.channelLayout.addWidget(self.channelEditBtn)
        self.toolBoxLayout.addLayout(self.channelLayout)
        
        if self.image.shape[-1] == 1 or self.image.rgb is True: #only show when needed
            self.channelSpin.setVisible(False)
            self.channelSpinLabel.setVisible(False)
            self.channelEditBtn.setVisible(False)
        self.channelSpin.setRange(0,self.image.shape[-1] - 1)


        #Overlay selector
        self.overlayWidget = DummyOverlayListWidget(self)
        self.toolBoxLayout.addWidget( self.overlayWidget)

        #Save the current images button
        self.saveAsImageBtn = QtGui.QPushButton('Export Images')
        self.connect(self.saveAsImageBtn, QtCore.SIGNAL("clicked()"), self.on_saveAsImage)
        self.toolBoxLayout.addWidget(self.saveAsImageBtn)
        
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
        shortcutManager.register(self.shortcutUndo, "history undo")
        
        self.shortcutRedo = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Z"), self, self.historyRedo, self.historyRedo)
        shortcutManager.register(self.shortcutRedo, "history redo")
        
        self.shortcutRedo2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Y"), self, self.historyRedo, self.historyRedo)
        shortcutManager.register(self.shortcutRedo2, "history redo")
        
        self.togglePredictionSC = QtGui.QShortcut(QtGui.QKeySequence("Space"), self, self.togglePrediction, self.togglePrediction)
        shortcutManager.register(self.togglePredictionSC, "toggle prediction overlays")
        
        self.shortcutNextLabel = QtGui.QShortcut(QtGui.QKeySequence("l"), self, self.nextLabel, self.nextLabel)
        shortcutManager.register(self.shortcutNextLabel, "go to next label (cyclic, forward)")
        
        self.shortcutPrevLabel = QtGui.QShortcut(QtGui.QKeySequence("k"), self, self.prevLabel, self.prevLabel)
        shortcutManager.register(self.shortcutPrevLabel, "go to previous label (cyclic, backwards)")
        
        self.shortcutToggleFullscreenX = QtGui.QShortcut(QtGui.QKeySequence("x"), self, self.toggleFullscreenX, self.toggleFullscreenX)
        shortcutManager.register(self.shortcutToggleFullscreenX, "enlarge slice view x to full size")
        
        self.shortcutToggleFullscreenY = QtGui.QShortcut(QtGui.QKeySequence("y"), self, self.toggleFullscreenY, self.toggleFullscreenY)
        shortcutManager.register(self.shortcutToggleFullscreenY, "enlarge slice view y to full size")
        
        self.shortcutToggleFullscreenZ = QtGui.QShortcut(QtGui.QKeySequence("z"), self, self.toggleFullscreenZ, self.toggleFullscreenZ)
        shortcutManager.register(self.shortcutToggleFullscreenZ, "enlarge slice view z to full size")
        
        self.shortcutUndo.setContext(QtCore.Qt.ApplicationShortcut )
        self.shortcutRedo.setContext(QtCore.Qt.ApplicationShortcut )
        self.shortcutRedo2.setContext(QtCore.Qt.ApplicationShortcut )
        self.togglePredictionSC.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutPrevLabel.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutNextLabel.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutToggleFullscreenX.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutToggleFullscreenY.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutToggleFullscreenZ.setContext(QtCore.Qt.ApplicationShortcut)
        
        self.shortcutUndo.setEnabled(True)
        self.shortcutRedo.setEnabled(True)
        self.shortcutRedo2.setEnabled(True)
        self.togglePredictionSC.setEnabled(True)
        
        self.connect(self, QtCore.SIGNAL("destroyed()"), self.widgetDestroyed)
        
        self.focusAxis =  0

    def toggleFullscreenX(self):
        self.maximizeSliceView(0, self.imageScenes[1].isVisible())
    
    def toggleFullscreenY(self):
        self.maximizeSliceView(1, self.imageScenes[0].isVisible())
        
    def toggleFullscreenZ(self):
        self.maximizeSliceView(2, self.imageScenes[1].isVisible())

    def maximizeSliceView(self, axis, maximize):
        if self.image.shape[1] > 1:
            a = range(3)
            if maximize:
                for i in a:
                    self.imageScenes[i].setVisible(i == axis)
            else:
                for i in range(3):
                    self.imageScenes[i].setVisible(True)
        
            self.imageScenes[axis].setFocus()
            for i in a:
                self.imageScenes[i].setImageSceneFullScreenLabel()
    
    def nextLabel(self):
        self.labelWidget.nextLabel()
        
    def prevLabel(self):
        self.labelWidget.nextLabel()

    def onLabelSelected(self, index):
        if self.labelWidget.currentItem() is not None:
            self.drawManager.setBrushColor(self.labelWidget.currentItem().color)
            for i in range(3):
                self.imageScenes[i].crossHairCursor.setColor(self.labelWidget.currentItem().color)

    def onOverlaySelected(self, index):
        if self.labelWidget.currentItem() is not None:
            pass

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
        
    def widgetDestroyed(self):
        print "yippeah, volumeeditor deleted"

    def cleanUp(self):
        print "VolumeEditor: cleaning up"
        for index, s in enumerate( self.imageScenes ):
            s.cleanUp()
            s.close()
            s.deleteLater()
        self.imageScenes = []
        self.save_thread.stopped = True
        self.save_thread.imagePending.set()
        self.save_thread.wait()
        print "finished saving thread"


    def on_editChannels(self):
        from ilastik.gui.channelEditDialog import EditChannelsDialog 
        
        dlg = EditChannelsDialog(self.ilastik.project.dataMgr.selectedChannels, self.ilastik.project.dataMgr[0].dataVol.data.shape[-1], self)
        
        result = dlg.exec_()
        if result is not None:
            self.ilastik.project.dataMgr.selectedChannels = result

    def togglePrediction(self):
        labelNames = self.labelWidget.volumeLabels.getLabelNames()
        for index,  item in enumerate(self.overlayWidget.overlays):
            if item.name in labelNames:
                self.overlayWidget.toggleVisible(index)
        self.repaint()
        

    def setLabelsAlpha(self, num):
        print "####################### function not used anymore"
        
    def getPendingLabels(self):
        temp = self.pendingLabels
        self.pendingLabels = []
        return temp

    def historyUndo(self):
        self.history.undo()

    def historyRedo(self):
        self.history.redo()

    def addOverlay(self, visible, data, name, color, alpha, colorTab = None):
        ov = VolumeOverlay(data,name, color, alpha, colorTab, visible)
        self.overlayWidget.addOverlay(ov)

    def addOverlayObject(self, ov):
        self.overlayWidget.addOverlay(ov)
        
    def repaint(self):
        for i in range(3):
            tempImage = None
            tempLabels = None
            tempoverlays = []   
            for index, item in enumerate(reversed(self.overlayWidget.overlays)):
                if item.visible:
                    tempoverlays.append(item.getOverlaySlice(self.selSlices[i],i, self.selectedTime, 0)) 
    
            if len(self.overlayWidget.overlays) > 0:
                tempImage = self.overlayWidget.overlays[-1].data.getSlice(self.selSlices[i], i, self.selectedTime, self.selectedChannel)
            else:
                tempImage = None
#            if self.labelWidget.volumeLabels is not None:
#                if self.labelWidget.volumeLabels.data is not None:
#                    tempLabels = self.labelWidget.volumeLabels.data.getSlice(self.selSlices[i],i, self.selectedTime, 0)
            self.imageScenes[i].displayNewSlice(tempImage, tempoverlays, fastPreview = False)

    def on_saveAsImage(self):
        sliceOffsetCheck = False
        if self.image.shape[1]>1:
            #stack z-view is stored in imageScenes[2], for no apparent reason
            sliceOffsetCheck = True
        timeOffsetCheck = self.image.shape[0]>1
        formatList = QtGui.QImageWriter.supportedImageFormats()
        expdlg = exportDialog.ExportDialog(formatList, timeOffsetCheck, sliceOffsetCheck, None)
        expdlg.exec_()
        try:
            tempname = str(expdlg.path.text()) + "/" + str(expdlg.prefix.text())
            filename = str(QtCore.QDir.convertSeparators(tempname))
            self.save_thread.start()
            stuff = (filename, expdlg.timeOffset, expdlg.sliceOffset, expdlg.format)
            self.save_thread.queue.append(stuff)
            self.save_thread.imagePending.set()
            
        except:
            pass
        
    def setLabelWidget(self,  widget):
        """
        Public interface function for setting the labelWidget toolBox
        """
        if self.labelWidget is not None:
            self.toolBoxLayout.removeWidget(self.labelWidget)
            self.labelWidget.close()
            del self.labelWidget
        self.labelWidget = widget
        self.connect(self.labelWidget , QtCore.SIGNAL("selectedLabel(int)"), self.onLabelSelected)
        self.toolBoxLayout.insertWidget( 4, self.labelWidget)        
    
    def setOverlayWidget(self,  widget):
        """
        Public interface function for setting the overlayWidget toolBox
        """
        if self.overlayWidget is not None:
            self.toolBoxLayout.removeWidget(self.overlayWidget)
            self.overlayWidget.close()
            del self.overlayWidget
        self.overlayWidget = widget
        self.connect(self.overlayWidget , QtCore.SIGNAL("selectedOverlay(int)"), self.onOverlaySelected)
        self.toolBoxLayout.insertWidget( 5, self.overlayWidget)        
        self.ilastik.project.dataMgr[self.ilastik.activeImage].overlayMgr.widget = self.overlayWidget


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

    def updateTimeSliceForSaving(self, time, num, axis):
        self.imageScenes[axis].thread.freeQueue.clear()
        if self.sliceSelectors[axis].value() != num:
            #this will emit the signal and change the slice
            self.sliceSelectors[axis].setValue(num)
        elif self.selectedTime!=time:
            #if only the time is changed, we don't want to update all 3 slices
            self.selectedTime = time
            self.changeSlice(num, axis)
        else:
            #no need to update, just save the current image
            self.imageScenes[axis].thread.freeQueue.set()

    def changeSlice(self, num, axis):
        self.selSlices[axis] = num
        tempImage = None
        tempLabels = None
        tempoverlays = []
        #This bloody call is recursive, be careful!
        self.sliceSelectors[axis].setValue(num)

        for index, item in enumerate(reversed(self.overlayWidget.overlays)):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(num,axis, self.selectedTime, 0)) 
        
        if len(self.overlayWidget.overlays) > 0:
            tempImage = self.overlayWidget.overlays[-1].data.getSlice(num, axis, self.selectedTime, self.selectedChannel)
        else:
            tempImage = None            
        #tempImage = self.image.getSlice(num, axis, self.selectedTime, self.selectedChannel)

#        if self.labelWidget.volumeLabels is not None:
#            if self.labelWidget.volumeLabels.data is not None:
#                tempLabels = self.labelWidget.volumeLabels.data.getSlice(num,axis, self.selectedTime, 0)

        self.selSlices[axis] = num
        self.imageScenes[axis].sliceNumber = num
        self.imageScenes[axis].displayNewSlice(tempImage, tempoverlays)
        self.emit(QtCore.SIGNAL('changedSlice(int, int)'), num, axis)
#        for i in range(256):
#            col = QtGui.QColor(classColor.red(), classColor.green(), classColor.blue(), i * opasity)
#            image.setColor(i, col.rgba())


    def closeEvent(self, event):
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
        vu.applyTo(self.labelWidget.volumeLabels.data)
        self.pendingLabels.append(vu)

        patches = self.imageScenes[axis].patchAccessor.getPatchesForRect(offsets[0], offsets[1],offsets[0]+labels.shape[0], offsets[1]+labels.shape[1])

        tempImage = None
        tempLabels = None
        tempoverlays = []
        for index, item in enumerate(reversed(self.overlayWidget.overlays)):
            if item.visible:
                tempoverlays.append(item.getOverlaySlice(self.selSlices[axis],axis, self.selectedTime, 0))

        if len(self.overlayWidget.overlays) > 0:
            tempImage = self.overlayWidget.overlays[-1].data.getSlice(num, axis, self.selectedTime, self.selectedChannel)
        else:
            tempImage = None            

        self.imageScenes[axis].updatePatches(patches, tempImage, tempoverlays)

        newLabels = self.getPendingLabels()
        self.labelWidget.labelMgr.newLabels(newLabels)

        self.emit(QtCore.SIGNAL('newLabelsPending()'))
            
    def getVisibleState(self):
        #TODO: ugly, make nicer
        vs = [self.selectedTime, self.selSlices[0], self.selSlices[1], self.selSlices[2], self.selectedChannel]
        return vs



    def show(self):
        QtGui.QWidget.show(self)



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

    def setErasing(self):
        self.erasing = True
    
    def disableErasing(self):
        self.erasing = False

    def setBrushSize(self, size):
        for i in range(3):
            self.volumeEditor.imageScenes[i].crossHairCursor.setBrushSize(size)
        
        self.brushSize = size
        self.penVis.setWidth(size)
        self.penDraw.setWidth(size)
        
    def getBrushSize(self):
        return self.brushSize
        
    def setBrushColor(self, color):
        self.penVis.setColor(color)
        
    def getCurrentPenPixmap(self):
        pixmap = QtGui.QPixmap(self.brushSize, self.brushSize)
        if self.erasing == True or not self.volumeEditor.labelWidget.currentItem():
            self.penVis.setColor(QtCore.Qt.black)
        else:
            self.penVis.setColor(self.volumeEditor.labelWidget.currentItem().color)
                    
        painter = QtGui.QPainter(pixmap)
        painter.setPen(self.penVis)
        painter.drawPoint(QtGui.Q)

    def beginDraw(self, pos, shape):
        self.shape = shape
        self.initBoundingBox()
        self.scene.clear()
        if self.erasing == True or not self.volumeEditor.labelWidget.currentItem():
            self.penVis.setColor(QtCore.Qt.black)
        else:
            self.penVis.setColor(self.volumeEditor.labelWidget.currentItem().color)
        self.pos = QtCore.QPoint(pos.x()+0.0001, pos.y()+0.0001)
        
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

class ImageSaveThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, None)
        self.ve = parent
        self.queue = deque()
        self.imageSaved = threading.Event()
        self.imageSaved.clear()
        self.imagePending = threading.Event()
        self.imagePending.clear()
        self.stopped = False
        self.previousSlice = None
        
    def run(self):
        while not self.stopped:
            self.imagePending.wait()
            while len(self.queue)>0:
                stuff = self.queue.pop()
                if stuff is not None:
                    filename, timeOffset, sliceOffset, format = stuff
                    if self.ve.image.shape[1]>1:
                        axis = 2
                        self.previousSlice = self.ve.sliceSelectors[axis].value()
                        for t in range(self.ve.image.shape[0]):
                            for z in range(self.ve.image.shape[3]):                   
                                self.filename = filename
                                if (self.ve.image.shape[0]>1):
                                    self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                                self.filename = self.filename + ("_z%05i" %(z+sliceOffset))
                                self.filename = self.filename + "." + format
                        
                                #only change the z slice display
                                self.ve.imageScenes[axis].thread.queue.clear()
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
                                self.ve.updateTimeSliceForSaving(t, z, axis)
                                
                                
                                self.ve.imageScenes[axis].thread.freeQueue.wait()
        
                                self.ve.imageScenes[axis].saveSlice(self.filename)
                    else:
                        axis = 0
                        for t in range(self.ve.image.shape[0]):                 
                            self.filename = filename
                            if (self.ve.image.shape[0]>1):
                                self.filename = self.filename + ("_time%03i" %(t+timeOffset))
                            self.filename = self.filename + "." + format
                            self.ve.imageScenes[axis].thread.queue.clear()
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.updateTimeSliceForSaving(t, self.ve.selSlices[0], axis)                              
                            self.ve.imageScenes[axis].thread.freeQueue.wait()
                            self.ve.imageScenes[axis].saveSlice(self.filename)
            self.imageSaved.set()
            self.imagePending.clear()
            if self.previousSlice is not None:
                self.ve.sliceSelectors[axis].setValue(self.previousSlice)
                self.previousSlice = None
            

class ImageSceneRenderThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self, None)
        self.imageScene = parent
        self.patchAccessor = parent.patchAccessor
        self.volumeEditor = parent.volumeEditor
        #self.queue = deque(maxlen=1) #python 2.6
        self.queue = deque() #python 2.5
        self.outQueue = deque()
        self.dataPending = threading.Event()
        self.dataPending.clear()
        self.newerDataPending = threading.Event()
        self.newerDataPending.clear()
        self.freeQueue = threading.Event()
        self.freeQueue.clear()
        self.stopped = False
        if self.imageScene.openglWidget is not None:
            self.contextPixmap = QtGui.QPixmap(2,2)
            self.context = QtOpenGL.QGLContext(self.imageScene.openglWidget.context().format(), self.contextPixmap)
            self.context.create(self.imageScene.openglWidget.context())
        else:
            self.context = None
        
            
    def run(self):
        #self.context.makeCurrent()

        while not self.stopped:
            self.dataPending.wait()
            self.newerDataPending.clear()
            self.freeQueue.clear()
            while len(self.queue) > 0:
                stuff = self.queue.pop()
                if stuff is not None:
                    nums, origimage, overlays , min, max  = stuff
                    for patchNr in nums:
                        if self.newerDataPending.isSet():
                            self.newerDataPending.clear()
                            break
                        bounds = self.patchAccessor.getPatchBounds(patchNr)

                        if self.imageScene.openglWidget is None:
                            p = QtGui.QPainter(self.imageScene.scene.image)
                            p.translate(bounds[0],bounds[2])
                        else:
                            p = QtGui.QPainter(self.imageScene.imagePatches[patchNr])
                        
#                        if origimage is not None:
#                            image = origimage[bounds[0]:bounds[1],bounds[2]:bounds[3]]
#    
#                            if image.dtype == 'uint16':
#                                image = (image / 255).astype(numpy.uint8)
#    
#                            temp_image = qimage2ndarray.array2qimage(image.swapaxes(0,1), normalize=(min,max))
#                            p.drawImage(0,0,temp_image)
#                        else:
                        p.eraseRect(0,0,bounds[1]-bounds[0],bounds[3]-bounds[2])

                        #add overlays
                        for index, origitem in enumerate(overlays):
                            p.setOpacity(origitem.alpha)
                            itemcolorTable = origitem.colorTable
                            itemdata = origitem.data[bounds[0]:bounds[1],bounds[2]:bounds[3]]
                            if origitem.colorTable != None:         
                                if itemdata.dtype != 'uint8':
                                    """
                                    if the item is larger we take the values module 256
                                    since QImage supports only 8Bit Indexed images
                                    """
                                    olditemdata = itemdata              
                                    itemdata = numpy.ndarray(olditemdata.shape, 'uint8')
                                    if olditemdata.dtype == 'uint32':
                                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
                                    elif olditemdata.dtype == 'uint64':
                                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
                                    elif olditemdata.dtype == 'int32':
                                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,24),24)[:]
                                    elif olditemdata.dtype == 'int64':
                                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,56),56)[:]
                                    elif olditemdata.dtype == 'uint16':
                                        itemdata[:] = numpy.right_shift(numpy.left_shift(olditemdata,8),8)[:]
                                    else:
                                        raise TypeError(str(olditemdata.dtype) + ' <- unsupported image data type (in the rendering thread, you know) ')
                                   
                                       
                                image0 = qimage2ndarray.gray2qimage(itemdata.swapaxes(0,1), normalize=False)
                                image0.setColorTable(origitem.colorTable[:])
                                
                            else:
                                if origitem.min is not None and origitem.max is not None:
                                    normalize = (origitem.min, origitem.max)
                                else:
                                    normalize = False
                                
                                                                
                                if origitem.autoAlphaChannel is False:
                                    if len(itemdata.shape) == 3 and itemdata.shape[2] == 3:
                                        image1 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
                                        image0 = image1
                                    else:
                                        tempdat = numpy.zeros(itemdata.shape[0:2] + (3,), 'uint8')
                                        tempdat[:,:,0] = origitem.color.redF()*itemdata[:]
                                        tempdat[:,:,1] = origitem.color.greenF()*itemdata[:]
                                        tempdat[:,:,2] = origitem.color.blueF()*itemdata[:]
                                        image1 = qimage2ndarray.array2qimage(tempdat.swapaxes(0,1), normalize)
                                        image0 = image1
                                else:
                                    image1 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
                                    image0 = QtGui.QImage(itemdata.shape[0],itemdata.shape[1],QtGui.QImage.Format_ARGB32)#qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize=False)
                                    if isinstance(origitem.color,  int):
                                        image0.fill(origitem.color)
                                    else: #shold be QColor then !
                                        image0.fill(origitem.color.rgba())
                                    image0.setAlphaChannel(image1)
                            p.drawImage(0,0, image0)

                        p.end()
                        self.outQueue.append(patchNr)
                        
#                        if self.imageScene.scene.tex > -1:
#                            self.context.makeCurrent()    
#                            glBindTexture(GL_TEXTURE_2D,self.imageScene.scene.tex)
#                            b = self.imageScene.patchAccessor.getPatchBounds(patchNr,0)
#                            glTexSubImage2D(GL_TEXTURE_2D, 0, b[0], b[2], b[1]-b[0], b[3]-b[2], GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.imageScene.imagePatches[patchNr].bits().__int__()))
#                            
#                        self.outQueue.clear()
                                       

            self.dataPending.clear()
            #self.freeQueue.set()
            self.emit(QtCore.SIGNAL('finishedQueue()'))


class CrossHairCursor(QtGui.QGraphicsItem) :
    modeYPosition  = 0
    modeXPosition  = 1
    modeXYPosition = 2
    
    def boundingRect(self):
        return QtCore.QRectF(0,0, self.width, self.height)
    def __init__(self, width, height):
        QtGui.QGraphicsItem.__init__(self)
        
        self.width = width
        self.height = height
        
        self.penDotted = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DotLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDotted.setCosmetic(True)
        
        self.penSolid = QtGui.QPen(QtCore.Qt.red, 2)
        self.penSolid.setCosmetic(True)
        
        self.x = 0
        self.y = 0
        self.brushSize = 0
        
        self.mode = self.modeXYPosition
    
    def setColor(self, color):
        self.penDotted = QtGui.QPen(color, 2, QtCore.Qt.DotLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.penDotted.setCosmetic(True)
        self.penSolid  = QtGui.QPen(color, 2)
        self.penSolid.setCosmetic(True)
        self.update()
    
    def showXPosition(self, x):
        """only mark the x position by displaying a line f(y) = x"""
        self.setVisible(True)
        self.mode = self.modeXPosition
        self.setPos(x,0)
        
    def showYPosition(self, y):
        """only mark the y position by displaying a line f(x) = y"""
        self.setVisible(True)
        self.mode = self.modeYPosition
        self.setPos(0,y)
        
    def showXYPosition(self, x,y):
        """mark the (x,y) position by displaying a cross hair cursor
           including a circle indicating the current brush size"""
        self.setVisible(True)
        self.mode = self.modeXYPosition
        self.setPos(x,y)
    
    def paint(self, painter, option, widget=None):
        painter.setPen(self.penDotted)
        
        if self.mode == self.modeXPosition:
            painter.drawLine(self.x, 0, self.x, self.height)
        elif self.mode == self.modeYPosition:
            painter.drawLine(0, self.y, self.width, self.y)
        else:
            painter.drawLine(0,                         self.y, self.x-0.5*self.brushSize, self.y)
            painter.drawLine(self.x+0.5*self.brushSize, self.y, self.width,                self.y)

            painter.drawLine(self.x, 0,                         self.x, self.y-0.5*self.brushSize)
            painter.drawLine(self.x, self.y+0.5*self.brushSize, self.x, self.height)

            painter.setPen(self.penSolid)
            painter.drawEllipse(self.x-0.5*self.brushSize, self.y-0.5*self.brushSize, 1*self.brushSize, 1*self.brushSize)
        
    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.update()
        
    def setBrushSize(self, size):
        self.brushSize = size
        self.update()

class ImageGraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, image):
        QtGui.QGraphicsItem.__init__(self)
        self.image = image

    def paint(self,painter, options, widget):
        painter.setClipRect( options.exposedRect )
        painter.drawImage(0,0,self.image)

    def boundingRect(self):
        return QtCore.QRectF(self.image.rect())


class CustomGraphicsScene( QtGui.QGraphicsScene):#, QtOpenGL.QGLWidget):
    def __init__(self,parent,widget,image):
        QtGui.QGraphicsScene.__init__(self)
        #QtOpenGL.QGLWidget.__init__(self)
        self.widget = widget
        self.imageScene = parent
        self.image = image
        self.images = []
        self.bgColor = QtGui.QColor(QtCore.Qt.black)
        self.tex = -1

            
    def drawBackground(self, painter, rect):
        #painter.fillRect(rect,self.bgBrush)
        if self.widget != None:

            self.widget.context().makeCurrent()
            
            glClearColor(self.bgColor.redF(),self.bgColor.greenF(),self.bgColor.blueF(),1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if self.tex > -1:
                #self.widget.drawTexture(QtCore.QRectF(self.image.rect()),self.tex)
                d = painter.device()
                dc = sip.cast(d,QtOpenGL.QGLFramebufferObject)

                rect = QtCore.QRectF(self.image.rect())
                tl = rect.topLeft()
                br = rect.bottomRight()
                
                #flip coordinates since the texture is flipped
                #this is due to qimage having another representation thatn OpenGL
                rect.setCoords(tl.x(),br.y(),br.x(),tl.y())
                
                #switch corrdinates if qt version is small
                painter.beginNativePainting()
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
                dc.drawTexture(rect,self.tex)
                painter.endNativePainting()

        else:
            painter.setClipRect(rect)
            painter.drawImage(0,0,self.image)
        



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
        brush.setStyle( QtCore.Qt.Dense7Pattern )
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
        self.image = QtGui.QImage(imShape[0], imShape[1], QtGui.QImage.Format_RGB888) #Format_ARGB32
        self.border = None
        self.allBorder = None

        self.min = 0
        self.max = 255

        self.openglWidget = None
        ##enable OpenGL acceleratino
        if self.volumeEditor.opengl is True:
            self.openglWidget = QtOpenGL.QGLWidget(shareWidget = self.volumeEditor.sharedOpenGLWidget)
            self.setViewport(self.openglWidget)
            self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
            


        self.scene = CustomGraphicsScene(self, self.openglWidget, self.image)

        # oli todo
        if self.volumeEditor.image.shape[1] > 1:
            grviewHudLayout = QtGui.QVBoxLayout(self)
            tempLayout = QtGui.QHBoxLayout()
            #self.fullSceenButton = QtGui.QPushButton("+")
            self.fullSceenButton = MyQLabel()
            self.fullSceenButton.setPixmap(QtGui.QPixmap(ilastikIcons.AddSelx22))
            self.fullSceenButton.setStyleSheet("border: none")
            self.connect(self.fullSceenButton, QtCore.SIGNAL('clicked()'), self.imageSceneFullScreen)
            tempLayout.addStretch()
            tempLayout.addWidget(self.fullSceenButton)
            grviewHudLayout.addLayout(tempLayout)
            grviewHudLayout.addStretch()
        
        
        if self.openglWidget is not None:
            self.openglWidget.context().makeCurrent()
            self.scene.tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D,self.scene.tex)
            glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, self.scene.image.width(), self.scene.image.height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.scene.image.bits().__int__()))
            
        self.view.setScene(self.scene)
        self.scene.setSceneRect(0,0, imShape[0],imShape[1])
        self.view.setSceneRect(0,0, imShape[0],imShape[1])
        self.scene.bgColor = QtGui.QColor(QtCore.Qt.white)
        if os.path.isfile('gui/backGroundBrush.png'):
            self.scene.bgBrush = QtGui.QBrush(QtGui.QImage('gui/backGroundBrush.png'))
        else:
            self.scene.bgBrush = QtGui.QBrush(QtGui.QColor(QtCore.Qt.black))
        #self.setBackgroundBrush(brushImage)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)
        #self.view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, False)

        self.patchAccessor = PatchAccessor(imShape[0],imShape[1],64)
        print "PatchCount :", self.patchAccessor.patchCount

        self.imagePatches = range(self.patchAccessor.patchCount)
        for i,p in enumerate(self.imagePatches):
            b = self.patchAccessor.getPatchBounds(i, 0)
            self.imagePatches[i] = QtGui.QImage(b[1]-b[0], b[3] -b[2], QtGui.QImage.Format_RGB888)

        self.pixmap = QtGui.QPixmap.fromImage(self.image)
        self.imageItem = QtGui.QGraphicsPixmapItem(self.pixmap)
        
        if self.axis is 0:
            self.setStyleSheet("QWidget:!focus { border: 2px solid red; border-radius: 4px; }\
                                QWidget:focus { border: 2px solid white; border-radius: 4px; }")
            self.view.rotate(90.0)
            self.view.scale(1.0,-1.0)
        if self.axis is 1:
            self.setStyleSheet("QWidget:!focus { border: 2px solid green; border-radius: 4px; } \
                                QWidget:focus { border: 2px solid white; border-radius: 4px; }")
        if self.axis is 2:
            self.setStyleSheet("QWidget:!focus { border: 2px solid blue; border-radius: 4px; } \
                                QWidget:focus { border: 2px solid white; border-radius: 4px; }")
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(QPoint)"), self.onContext)

        self.setMouseTracking(True)

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
        self.allBorder.setZValue(99)

        #label updates while drawing, needed for interactive segmentation
        self.drawTimer = QtCore.QTimer()
        self.connect(self.drawTimer, QtCore.SIGNAL("timeout()"), self.updateLabels)
        
        # invisible cursor to enable custom cursor
        self.hiddenCursor = QtGui.QCursor(QtCore.Qt.BlankCursor)
        
        # For screen recording BlankCursor dont work
        #self.hiddenCursor = QtGui.QCursor(QtCore.Qt.ArrowCursor)
        
        self.thread = ImageSceneRenderThread(self)
        self.connect(self.thread, QtCore.SIGNAL('finishedPatch(int)'),self.redrawPatch)
        self.connect(self.thread, QtCore.SIGNAL('finishedQueue()'), self.clearTempitems)
        self.thread.start()
        
        self.connect(self, QtCore.SIGNAL("destroyed()"),self.cleanUp)

        self.shortcutZoomIn = QtGui.QShortcut(QtGui.QKeySequence("+"), self, self.zoomIn, self.zoomIn)
        shortcutManager.register(self.shortcutZoomIn, "zoom in")
        self.shortcutZoomIn.setContext(QtCore.Qt.WidgetShortcut )

        self.shortcutZoomOut = QtGui.QShortcut(QtGui.QKeySequence("-"), self, self.zoomOut, self.zoomOut)
        shortcutManager.register(self.shortcutZoomOut, "zoom out")
        self.shortcutZoomOut.setContext(QtCore.Qt.WidgetShortcut )
        
        self.shortcutSliceUp = QtGui.QShortcut(QtGui.QKeySequence("p"), self, self.sliceUp, self.sliceUp)
        shortcutManager.register(self.shortcutSliceUp, "slice up")
        self.shortcutSliceUp.setContext(QtCore.Qt.WidgetShortcut )
        
        self.shortcutSliceDown = QtGui.QShortcut(QtGui.QKeySequence("o"), self, self.sliceDown, self.sliceDown)
        shortcutManager.register(self.shortcutSliceDown, "slice down")
        self.shortcutSliceDown.setContext(QtCore.Qt.WidgetShortcut )

        self.shortcutSliceUp2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Up"), self, self.sliceUp, self.sliceUp)
        shortcutManager.register(self.shortcutSliceUp2, "slice up")
        self.shortcutSliceUp2.setContext(QtCore.Qt.WidgetShortcut )

        self.shortcutSliceDown2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Down"), self, self.sliceDown, self.sliceDown)
        shortcutManager.register(self.shortcutSliceDown2, "slice down")
        self.shortcutSliceDown2.setContext(QtCore.Qt.WidgetShortcut )


        self.shortcutSliceUp10 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Up"), self, self.sliceUp10, self.sliceUp10)
        shortcutManager.register(self.shortcutSliceUp10, "10 slices up")
        self.shortcutSliceUp10.setContext(QtCore.Qt.WidgetShortcut )

        self.shortcutSliceDown10 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+Down"), self, self.sliceDown10, self.sliceDown10)
        shortcutManager.register(self.shortcutSliceDown10, "10 slices down")
        self.shortcutSliceDown10.setContext(QtCore.Qt.WidgetShortcut )


        self.shortcutBrushSizeUp = QtGui.QShortcut(QtGui.QKeySequence("n"), self, self.brushSmaller, self.brushSmaller)
        shortcutManager.register(self.shortcutBrushSizeUp, "increase brush size")
        self.shortcutBrushSizeDown = QtGui.QShortcut(QtGui.QKeySequence("m"), self, self.brushBigger, self.brushBigger)
        shortcutManager.register(self.shortcutBrushSizeDown, "decrease brush size")
 
        self.crossHairCursor = CrossHairCursor(self.image.width(), self.image.height())
        self.crossHairCursor.setZValue(100)
        self.scene.addItem(self.crossHairCursor)

        self.tempErase = False

    def imageSceneFullScreen(self): #oli todo
        if self.volumeEditor.imageScenes[0] == self.fullSceenButton.parent():
            self.volumeEditor.toggleFullscreenX()
        if self.volumeEditor.imageScenes[1] == self.fullSceenButton.parent():
            self.volumeEditor.toggleFullscreenY()
        if self.volumeEditor.imageScenes[2] == self.fullSceenButton.parent():
            self.volumeEditor.toggleFullscreenZ()

    def setImageSceneFullScreenLabel(self): #oli todo
        self.allVisible = True
        a = range(3)
        for i in a:
            if not self.volumeEditor.imageScenes[i].isVisible():
                self.allVisible = False
                break
        if self.allVisible:
            self.fullSceenButton.setPixmap(QtGui.QPixmap(ilastikIcons.AddSelx22))
        else:
            self.fullSceenButton.setPixmap(QtGui.QPixmap(ilastikIcons.RemSelx22))

        
    def changeSlice(self, delta):
        if self.drawing == True:
            self.endDraw(self.mousePos)
            self.drawing = True
            self.drawManager.beginDraw(self.mousePos, self.imShape)

        self.volumeEditor.sliceSelectors[self.axis].stepBy(delta)


    def sliceUp(self):
        self.changeSlice(1)
        
    def sliceUp10(self):
        self.changeSlice(10)

    def sliceDown(self):
        self.changeSlice(-1)

    def sliceDown10(self):
        self.changeSlice(-10)


    def brushSmaller(self):
        b = self.drawManager.brushSize
        if b > 2:
            self.drawManager.setBrushSize(b-1)
            self.crossHairCursor.setBrushSize(b-1)
        
    def brushBigger(self):
        b = self.drawManager.brushSize
        if b < 20:
            self.drawManager.setBrushSize(b+1)
            self.crossHairCursor.setBrushSize(b+1)

    def cleanUp(self):
        #print "stopping ImageSCeneRenderThread", str(self.axis)
        
        self.thread.stopped = True
        self.thread.dataPending.set()
        self.thread.wait()
        print "finished thread"

    def updatePatches(self, patchNumbers ,image, overlays = []):
        stuff = [patchNumbers,image, overlays, self.min, self.max]
        #print patchNumbers
        if patchNumbers is not None:
            self.thread.queue.append(stuff)
            self.thread.dataPending.set()

    def displayNewSlice(self, image, overlays = [], fastPreview = True):
        self.thread.queue.clear()
        self.thread.newerDataPending.set()

        #if we are in opengl 2d render mode, quickly update the texture without any overlays
        #to get a fast update on slice change
        if image is not None:
            if fastPreview is True and self.volumeEditor.opengl is True and len(image.shape) == 2:
                self.volumeEditor.sharedOpenGLWidget.context().makeCurrent()
                t = self.scene.tex
                ti = qimage2ndarray.array2qimage(image.swapaxes(0,1), normalize = self.volumeEditor.normalizeData)
    
                if not t > -1:
                    self.scene.tex = glGenTextures(1)
                    glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                    glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, ti.width(), ti.height(), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, ctypes.c_void_p(ti.bits().__int__()))
                else:
                    glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, ti.width(), ti.height(), GL_LUMINANCE, GL_UNSIGNED_BYTE, ctypes.c_void_p(ti.bits().__int__()))
                
                self.viewport().repaint()
    
            if self.volumeEditor.normalizeData:
                self.min = numpy.min(image)
                self.max = numpy.max(image)
            else:
                self.min = 0
                self.max = 255
        ########### 
        self.updatePatches(range(self.patchAccessor.patchCount),image, overlays)
        
    def saveSlice(self, filename):
        print "Saving in ", filename, "slice #", self.sliceNumber, "axis", self.axis
        
        result_image = QtGui.QImage(self.scene.image.size(), self.scene.image.format())
        p = QtGui.QPainter(result_image)
        for patchNr in range(self.patchAccessor.patchCount):
            bounds = self.patchAccessor.getPatchBounds(patchNr)
            if self.openglWidget is None:
                p.drawImage(0, 0, self.scene.image)
            else:
                p.drawImage(bounds[0], bounds[2], self.imagePatches[patchNr])
        p.end()
        result_image.save(QtCore.QString(filename))

    def display(self, image, overlays = []):
        self.thread.queue.clear()
        self.updatePatches(range(self.patchAccessor.patchCount),image, overlays)

    def clearTempitems(self):
        #only proceed if htere is no new data already in the rendering thread queue
        if not self.thread.dataPending.isSet():
            #if, in slicing direction, we are within the margin of the image border
            #we set the border overlay indicator to visible
            self.allBorder.setVisible((self.sliceNumber < self.margin or self.sliceExtent - self.sliceNumber < self.margin) and self.sliceExtent > 1)

            #if we are in opengl 2d render mode, update the texture
            self.volumeEditor.sharedOpenGLWidget.context().makeCurrent()
            if self.openglWidget is not None:
                for patchNr in self.thread.outQueue:
                    t = self.scene.tex
                    #self.scene.tex = -1
                    if t > -1:
                        #self.openglWidget.deleteTexture(t)
                        pass
                    else:
                        #self.scene.tex = self.openglWidget.bindTexture(self.scene.image, GL_TEXTURE_2D, GL_RGBA)
                        self.scene.tex = glGenTextures(1)
                        glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, self.scene.image.width(), self.scene.image.height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.scene.image.bits().__int__()))
                        
                    glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                    b = self.patchAccessor.getPatchBounds(patchNr,0)
                    glTexSubImage2D(GL_TEXTURE_2D, 0, b[0], b[2], b[1]-b[0], b[3]-b[2], GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.imagePatches[patchNr].bits().__int__()))
            else:
                    t = self.scene.tex
                    #self.scene.tex = -1
                    if t > -1:
                        #self.openglWidget.deleteTexture(t)
                        pass
                    else:
                        #self.scene.tex = self.openglWidget.bindTexture(self.scene.image, GL_TEXTURE_2D, GL_RGBA)
                        self.scene.tex = glGenTextures(1)
                        glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, self.scene.image.width(), self.scene.image.height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.scene.image.bits().__int__()))
                        
                    glBindTexture(GL_TEXTURE_2D,self.scene.tex)
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.scene.image.width(), self.scene.image.height(), GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.scene.image.bits().__int__()))
                    
            self.thread.outQueue.clear()
            #if all updates have been rendered remove tempitems
            if self.thread.queue.__len__() == 0:
                for index, item in enumerate(self.tempImageItems):
                    self.scene.removeItem(item)
                self.tempImageItems = []

            #update the scene, and the 3d overvie
        #print "updating slice view ", self.axis
        self.viewport().repaint() #update(QtCore.QRectF(self.image.rect()))
        self.volumeEditor.overview.display(self.axis)
        self.thread.freeQueue.set()
        
    def redrawPatch(self, patchNr):
        if self.thread.stopped is False:
            pass
#            patch = self.thread.imagePatches[patchNr]
#            if self.textures[patchNr] < 0 :
#                t = self.openglWidget.bindTexture(patch)
#                self.textures[patchNr] = t
#            else:
#                t_old = self.textures[patchNr]
#
#                t_new = self.openglWidget.bindTexture(patch)
#                self.textures[patchNr] = t_new
#
#                self.openglWidget.deleteTexture(t_old)

#            bounds = self.patchAccessor.getPatchBounds(patchNr)
#            p = QtGui.QPainter(self.scene.image)
#            p.drawImage(bounds[0],bounds[2],self.thread.imagePatches[patchNr])
#            p.end()

            #self.scene.update(bounds[0],bounds[2],bounds[1]-bounds[0],bounds[3]-bounds[2])
        
    def updateLabels(self):
        result = self.drawManager.dumpDraw(self.mousePos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelWidget.currentItem().number
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

        if self.volumeEditor.drawUpdateInterval > 0:
            self.drawTimer.start(self.volumeEditor.drawUpdateInterval) #update labels every some ms
        
    def endDraw(self, pos):
        self.drawTimer.stop()
        result = self.drawManager.endDraw(pos)
        image = result[2]
        ndarr = qimage2ndarray.rgb_view(image)
        labels = ndarr[:,:,0]
        labels = labels.swapaxes(0,1)
        number = self.volumeEditor.labelWidget.currentItem().number
        labels = numpy.where(labels > 0, number, 0)
        ls = LabelState('drawing', self.axis, self.volumeEditor.selSlices[self.axis], result[0:2], labels.shape, self.volumeEditor.selectedTime, self.volumeEditor, self.drawManager.erasing, labels, number)
        self.volumeEditor.history.append(ls)        
        self.volumeEditor.setLabels(result[0:2], self.axis, self.volumeEditor.sliceSelectors[self.axis].value(), labels, self.drawManager.erasing)
        self.drawing = False


    def wheelEvent(self, event):
        keys = QtGui.QApplication.keyboardModifiers()
        k_alt = (keys == QtCore.Qt.AltModifier)
        k_ctrl = (keys == QtCore.Qt.ControlModifier)

        self.mousePos = self.mapToScene(event.pos())

        if event.delta() > 0:
            if k_alt is True:
                self.changeSlice(10)
            elif k_ctrl is True:
                scaleFactor = 1.1
                self.doScale(scaleFactor)
            else:
                self.changeSlice(1)
        else:
            if k_alt is True:
                self.changeSlice(-10)
            elif k_ctrl is True:
                scaleFactor = 0.9
                self.doScale(scaleFactor)
            else:
                self.changeSlice(-1)

    def zoomOut(self):
        self.doScale(0.9)

    def zoomIn(self):
        self.doScale(1.1)

    def doScale(self, factor):
        self.view.scale(factor, factor)


    def tabletEvent(self, event):
        self.setFocus(True)
        
        if not self.volumeEditor.labelWidget.currentItem():
            return
        
        self.mousePos = mousePos = self.mapToScene(event.pos())
        
        x = mousePos.x()
        y = mousePos.y()
        if event.pointerType() == QtGui.QTabletEvent.Eraser or QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            self.drawManager.setErasing()
        elif event.pointerType() == QtGui.QTabletEvent.Pen and QtGui.QApplication.keyboardModifiers() != QtCore.Qt.ShiftModifier:
            self.drawManager.disableErasing()
        if self.drawing == True:
            if event.pressure() == 0:
                self.endDraw(mousePos)
                self.volumeEditor.changeSlice(self.volumeEditor.selSlices[self.axis], self.axis)
            else:
                if self.drawManager.erasing:
                    #make the brush size bigger while erasing
                    self.drawManager.setBrushSize(int(event.pressure()*10))
                else:
                    self.drawManager.setBrushSize(int(event.pressure()*7))
        if self.drawing == False:
            if event.pressure() > 0:
                self.beginDraw(mousePos)
                
                
        self.mouseMoveEvent(event)


    def mousePressEvent(self, event):
        if not self.volumeEditor.labelWidget.currentItem():
            return
        
        if event.buttons() == QtCore.Qt.LeftButton:
            if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
                self.drawManager.setErasing()
                self.tempErase = True
            mousePos = self.mapToScene(event.pos())
            self.beginDraw(mousePos)
        elif event.buttons() == QtCore.Qt.RightButton:
            self.onContext(event.pos())

    def mouseReleaseEvent(self, event):
        if self.drawing == True:
            mousePos = self.mapToScene(event.pos())
            self.endDraw(mousePos)
        if self.tempErase == True:
            self.drawManager.disableErasing()
            self.tempErase = False
            
    def mouseMoveEvent(self,event):
        self.mousePos = mousePos = self.mousePos = self.mapToScene(event.pos())
        x = mousePos.x()
        y = mousePos.y()
        posX = 0
        posY = 0
        posZ = 0

        if x > 0 and x < self.image.width() and y > 0 and y < self.image.height():
            
            #should we hide the cursor only when entering once ? performance?
            #self.setCursor(self.hiddenCursor)
            
            self.crossHairCursor.showXYPosition(x,y)
            #self.crossHairCursor.setPos(x,y)
            
            if self.axis == 0:
                posY = y
                posZ = x
                posX = self.volumeEditor.selSlices[0]
                self.volumeEditor.posLabel.setText("<b>x:</b> %i  <b>y:</b> %i  <b>z:</b> %i" % (posX, posY, posZ))
                yView = self.volumeEditor.imageScenes[1].crossHairCursor
                zView = self.volumeEditor.imageScenes[2].crossHairCursor
                
                yView.setVisible(False)
                zView.showYPosition(x)
                
            elif self.axis == 1:
                posY = posX = self.volumeEditor.selSlices[1]
                posZ = y
                posX = x
                self.volumeEditor.posLabel.setText("<b>x:</b> %i  <b>y:</b> %i  <b>z:</b> %i" % (posX, posY, posZ))
                xView = self.volumeEditor.imageScenes[0].crossHairCursor
                zView = self.volumeEditor.imageScenes[2].crossHairCursor
                
                zView.showXPosition(x)
                xView.setVisible(False)
            else:
                posY = y
                posZ = posX = self.volumeEditor.selSlices[2]
                posX = x
                self.volumeEditor.posLabel.setText("<b>x:</b> %i  <b>y:</b> %i  <b>z:</b> %i" % (posX, posY, posZ))
                xView = self.volumeEditor.imageScenes[0].crossHairCursor
                yView = self.volumeEditor.imageScenes[1].crossHairCursor
                
                xView.showXPosition(y)
                yView.showXPosition(x)
        else:
            self.unsetCursor()
                
        
        if self.drawing == True:
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
        menu = QtGui.QMenu('Labeling menu', self)
        
        toggleEraseA = None
        if self.drawManager.erasing == True:
            toggleEraseA = menu.addAction("Enable Labelmode",  self.drawManager.toggleErase)
        else:
            toggleEraseA = menu.addAction("Enable Eraser", self.drawManager.toggleErase)
        
        menu.addSeparator()
        labelList = []
        volumeLabel = self.volumeEditor.labelWidget.volumeLabels
        for index, item in enumerate(volumeLabel.descriptions):
            labelColor = QtGui.QColor.fromRgb(long(item.color))
            labelIndex = item.number
            labelName = item.name
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(labelColor)
            icon = QtGui.QIcon(pixmap)
            
            act = QtGui.QAction(icon, labelName, menu)
            i = self.volumeEditor.labelWidget.listWidget.model().index(labelIndex-1,0)
            # print self.volumeEditor.labelView.selectionModel()
            self.connect(act, QtCore.SIGNAL("triggered()"), lambda i=i: self.volumeEditor.labelWidget.listWidget.selectionModel().setCurrentIndex(i, QtGui.QItemSelectionModel.ClearAndSelect))
            labelList.append(menu.addAction(act))

        menu.addSeparator()
        # brushM = labeling.addMenu("Brush size")
        brushGroup = QtGui.QActionGroup(self)
        
        defaultBrushSizes = [1,3,7,11,31]
        brush = []
        for ind, b in enumerate(defaultBrushSizes):
            act = QtGui.QAction(str(b), brushGroup)
            act.setCheckable(True)
            self.connect(act, QtCore.SIGNAL("triggered()"), lambda b=b: self.drawManager.setBrushSize(b))
            if b == self.drawManager.getBrushSize():
                act.setChecked(True)
            brush.append(menu.addAction(act))
        
        #menu.setTearOffEnabled(True)

        action = menu.exec_(QtGui.QCursor.pos())
        #if action == toggleEraseA:
            #



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
        QtOpenGL.QGLWidget.__init__(self, shareWidget = parent.sharedOpenGLWidget)
        self.sceneShape = shape
        self.volumeEditor = parent
        self.images = parent.imageScenes
        self.sceneItems = []
        self.initialized = False
        self.tex = []
        self.tex.append(-1)
        self.tex.append(-1)
        self.tex.append(-1)
        if self.volumeEditor.openglOverview is False:
            self.setVisible(False)

    def display(self, axis):
        if self.volumeEditor.openglOverview is True:  
            if self.initialized is True:
                #self.initializeGL()
                self.makeCurrent()
                self.paintGL(axis)
                self.swapBuffers()
            
    def redisplay(self):
        if self.volumeEditor.openglOverview is True:
            if self.initialized is True:
                for i in range(3):
                    self.makeCurrent()
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
            if axis is 2:
                self.tex[2] = self.images[2].scene.tex
            if self.tex[2] != -1:
                glBindTexture(GL_TEXTURE_2D,self.tex[2])
                
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

                glBegin(GL_QUADS) #horizontal quad (e.g. first axis)
                glColor3f(1.0,1.0,1.0)            # Set The Color To White
                glTexCoord2d(0.0, 0.0)
                glVertex3f( -ratio2w,curCenter, -ratio2h)        # Top Right Of The Quad
                glTexCoord2d(1.0, 0.0)
                glVertex3f(+ ratio2w,curCenter, -ratio2h)        # Top Left Of The Quad
                glTexCoord2d(1.0, 1.0)
                glVertex3f(+ ratio2w,curCenter, + ratio2h)        # Bottom Left Of The Quad
                glTexCoord2d(0.0, 1.0)
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
    
            if axis is 0:
                self.tex[0] = self.images[0].scene.tex
            if self.tex[0] != -1:
                glBindTexture(GL_TEXTURE_2D,self.tex[0])


                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

                glBegin(GL_QUADS)
                glColor3f(0.8,0.8,0.8)            # Set The Color To White
                glTexCoord2d(1.0, 0.0)
                glVertex3f(curCenter, ratio0h, ratio0w)        # Top Right Of The Quad (Left)
                glTexCoord2d(0.0, 0.0)
                glVertex3f(curCenter, ratio0h, - ratio0w)        # Top Left Of The Quad (Left)
                glTexCoord2d(0.0, 1.0)
                glVertex3f(curCenter,- ratio0h,- ratio0w)        # Bottom Left Of The Quad (Left)
                glTexCoord2d(1.0, 1.0)
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
    
    
            if axis is 1:
                self.tex[1] = self.images[1].scene.tex
            if self.tex[1] != -1:
                glBindTexture(GL_TEXTURE_2D,self.tex[1])
    
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
                glPolygonMode( GL_FRONT_AND_BACK, GL_FILL ) #solid drawing mode

                glBegin(GL_QUADS)
                glColor3f(0.6,0.6,0.6)            # Set The Color To White
                glTexCoord2d(1.0, 0.0)
                glVertex3f( ratio1w,  ratio1h, curCenter)        # Top Right Of The Quad (Front)
                glTexCoord2d(0.0, 0.0)
                glVertex3f(- ratio1w, ratio1h, curCenter)        # Top Left Of The Quad (Front)
                glTexCoord2d(0.0, 1.0)
                glVertex3f(- ratio1w,- ratio1h, curCenter)        # Bottom Left Of The Quad (Front)
                glTexCoord2d(1.0, 1.0)
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
