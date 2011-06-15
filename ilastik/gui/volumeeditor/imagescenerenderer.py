from PyQt4.QtCore import QObject, QThread, pyqtSignal
from PyQt4.QtGui import QPainter, QColor, QImage

import numpy, qimage2ndarray
import threading
from collections import deque

try:
    from OpenGL.GL import *
except Exception, e:
    print e
    pass

class ImageSceneRenderer(QObject):
    def __init__(self, imageScene):
        QObject.__init__(self)
        self.imageScene = imageScene # TODO: remove dependency
        self.patchAccessor = imageScene.patchAccessor
        
        self.min = 0
        self.max = 255
        
        self.thread = ImageSceneRenderThread(imageScene, imageScene.patchAccessor)
        self.thread.finishedQueue.connect(self.renderingThreadFinished)
        self.thread.start()

    def renderImage(self, image, overlays = ()):
        self.thread.queue.clear()
        self.thread.newerDataPending.set()

        self.updatePatches(range(self.patchAccessor.patchCount), image, overlays)
        
    def updatePatches(self, patchNumbers ,image, overlays = ()):
        stuff = [patchNumbers,image, overlays, self.min, self.max]
        #print patchNumbers
        if patchNumbers is not None:
            self.thread.queue.append(stuff)
            self.thread.dataPending.set()

    def renderingThreadFinished(self):
        #only proceed if there is no new _data already in the rendering thread queue
        if not self.thread.dataPending.isSet():

            #if we are in opengl 2d render mode, update the texture
            if self.imageScene.openglWidget is not None:
                self.imageScene.sharedOpenGLWidget.context().makeCurrent()
                for patchNr in self.thread.outQueue:
                    t = self.imageScene.scene.tex
                    if t > -1:
                        pass
                    else:
                        self.imageScene.scene.tex = glGenTextures(1)
                        glBindTexture(GL_TEXTURE_2D,self.imageScene.scene.tex)
                        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGB, self.imageScene.scene.image.width(), self.imageScene.scene.image.height(), 0, GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.scene.image.bits().__int__()))
                        
                    glBindTexture(GL_TEXTURE_2D,self.imageScene.scene.tex)
                    b = self.imageScene.patchAccessor.getPatchBounds(patchNr,0)
                    glTexSubImage2D(GL_TEXTURE_2D, 0, b[0], b[2], b[1]-b[0], b[3]-b[2], GL_RGB, GL_UNSIGNED_BYTE, ctypes.c_void_p(self.imageScene.imagePatches[patchNr].bits().__int__()))
                    
            self.thread.outQueue.clear()
            #if all updates have been rendered remove tempitems
            if self.thread.queue.__len__() == 0:
                for index, item in enumerate(self.imageScene.tempImageItems):
                    self.imageScene.scene.removeItem(item)
                self.imageScene.tempImageItems = []
 
        #update the scene, and the 3d overview
        print "updating slice view ", self.imageScene.axis
        self.imageScene.viewport().repaint()
        self.thread.freeQueue.set()
        
        #FIXME this is a hack
        #self.imageScene.updatedSlice.emit(self.imageScene.axis)
    

#*******************************************************************************
# I m a g e S c e n e R e n d e r T h r e a d                                  *
#*******************************************************************************
class ImageSceneRenderThread(QThread):
    finishedQueue = pyqtSignal()
    
    def __init__(self, imageScene, patchAccessor):
        QThread.__init__(self, None)
        #self.paintDevice = paintDevice
        self.imageScene = imageScene #TODO make independent
        self.patchAccessor = patchAccessor

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
        
        print "initialized ImageSceneRenderThread"
    
    def run(self):
        while not self.stopped:
            self.finishedQueue.emit()
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
                            p = QPainter(self.imageScene.scene.image)
                            p.translate(bounds[0],bounds[2])
                        else:
                            p = QPainter(self.imageScene.imagePatches[patchNr])
                        
                        p.eraseRect(0,0,bounds[1]-bounds[0],bounds[3]-bounds[2])

                        #add overlays
                        for index, origitem in enumerate(overlays):
                            p.setOpacity(origitem.alpha)
                            itemcolorTable = origitem.colorTable
                            
                            
                            itemdata = origitem._data[bounds[0]:bounds[1],bounds[2]:bounds[3]]
                            
                            origitemColor = None
                            if isinstance(origitem.color,  long) or isinstance(origitem.color,  int):
                                origitemColor = QColor.fromRgba(long(origitem.color))
                            else:
                                origitemColor = origitem.color
                                 
                            # if itemdata is uint16
                            # convert it for displayporpuse
                            if itemdata.dtype == numpy.uint16:
                                itemdata = (itemdata*255.0/4095.0).astype(numpy.uint8)
                            
                            if itemcolorTable != None:         
                                if itemdata.dtype != 'uint8':
                                    """
                                    if the item is larger we take the values module 256
                                    since QImage supports only 8Bit Indexed images
                                    """
                                    olditemdata = itemdata              
                                    itemdata = numpy.ndarray(olditemdata.shape, 'float32')
                                    #print "moduo", olditemdata.shape, olditemdata.dtype
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
                                        #raise TypeError(str(olditemdata.dtype) + ' <- unsupported image _data type (in the rendering thread, you know) ')
                                        # TODO: Workaround: tried to fix the problem
                                        # with the segmentation display, somehow it arrieves
                                        # here in float32
                                        print TypeError(str(olditemdata.dtype) + ': unsupported dtype of overlay in ImageSceneRenderThread.run()')
                                        continue
                                   
                                if len(itemdata.shape) > 2 and itemdata.shape[2] > 1:
                                    image0 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize=False)
                                else:
                                    image0 = qimage2ndarray.gray2qimage(itemdata.swapaxes(0,1), normalize=False)
                                    image0.setColorTable(itemcolorTable[:])
                                
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
                                        tempdat = numpy.zeros(itemdata.shape[0:2] + (3,), 'float32')
                                        tempdat[:,:,0] = origitemColor.redF()*itemdata[:]
                                        tempdat[:,:,1] = origitemColor.greenF()*itemdata[:]
                                        tempdat[:,:,2] = origitemColor.blueF()*itemdata[:]
                                        image1 = qimage2ndarray.array2qimage(tempdat.swapaxes(0,1), normalize)
                                        image0 = image1
                                else:
                                    image1 = qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize)
                                    image0 = QImage(itemdata.shape[0],itemdata.shape[1],QImage.Format_ARGB32)#qimage2ndarray.array2qimage(itemdata.swapaxes(0,1), normalize=False)
                                    image0.fill(origitemColor.rgba())
                                    image0.setAlphaChannel(image1)
                            p.drawImage(0,0, image0)

                        p.end()
                        self.outQueue.append(patchNr)

            self.dataPending.clear()