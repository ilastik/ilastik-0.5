from PyQt4 import QtGui
from PyQt4 import QtCore
import sys, random, numpy
import os
from collections import deque
sys.path.append("..")
from core import labelMgr, activeLearning
from core.utilities import irange, debug
from gui.iconMgr import ilastikIcons
import time
#import qimage2ndarray
import labelArrayDrawQImage

try:
    import vigra
except ImportError:
    sys.exit("vigra module not found!")

#************************

labelwidgetInstance = None   # UGLY global
      

class labelingForOneImage:
    def __init__(self):
        self.DrawManagers = []       # different labeling-types (patch, pixel, geom...)
        self.activeLabel = None
        self.activeDrawManager = None
        
    def undoPush(self, undoPointDescription):
        for dmng in self.DrawManagers:
            dmng.undoPush(undoPointDescription)
    
    def undo(self):
        for dmng in self.DrawManagers:
            dmng.undo()
        
    def addDrawManager(self, dmngr):
        self.DrawManagers.append(dmngr)
        self.activeDrawManager = self.DrawManagers.__len__() - 1
        
    def getActiveDrawManager(self):
        return self.DrawManagers[self.activeDrawManager]
        
    def setActiveLabel(self, label):
        self.activeLabel = label
        for dmng in self.DrawManagers:
            dmng.setDrawLabel(label)
        
    def setOpacity(self, op):
        for dmngr in self.DrawManagers:
            dmngr.setDrawOpacity(op)
            
    def setBrushSize(self, rad):
        for dmngr in self.DrawManagers:
            dmngr.labelmngr.setPaintRad(rad)    
    def getLabelValue(self, pos):
        # todo: what, if different label-types (e.g. pixel, geom. objects..) are contradictory?
        value = 0
        for dmngr in self.DrawManagers:
            value = dmngr.labelmngr.getLabel(pos)
        return value
    
    def setCanvas(self, canvas):
        for dmngr in self.DrawManagers:
            dmngr.setCanvas(canvas)
            
    def canvas_clear(self):
        for dmngr in self.DrawManagers:
            dmngr.canvas_clear()
        
    def canvas_paint(self):
        for dmngr in self.DrawManagers:
            dmngr.canvas_paint()
    
    def __getstate__(self):
        self.pickleinfo_DrawManager_ids = []
        self.pickleinfo_LabelManagers = []
        #print self.pickleinfo
        for dm in self.DrawManagers:
            self.pickleinfo_DrawManager_ids.append(dm.classId)
            self.pickleinfo_LabelManagers.append(dm.labelmngr)
        cdict = self.__dict__.copy()
        del cdict['DrawManagers']
        return cdict
    
    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.DrawManagers = []
        i = 0
        for id in self.pickleinfo_DrawManager_ids:
            dmObject = drawManagerID.drawManagerObject[id]
            lm = self.pickleinfo_LabelManagers[i]
            self.DrawManagers.append(dmObject(lm, labelwidgetInstance.canvas))   # UGLY global
            i += 1
        pass

class drawManager:
    #todo: manage draw-data (topLevelItems, Pixmaps) in a dictionary: seperate labeltypes to make changing [opacity, color, ...] easy.    
    def __init__(self, labelmngr, canvas, imageIndex=0):
        self.classId = drawManagerID.IDdrawManager
        self.labelmngr = labelmngr
        self.canvas = canvas
        self.undolist = None
        
        self.drawLabel = 0
        self.drawSize = 1
        self.drawColor = {}
        self.activeDrawColor = QtGui.QColor(255, 128, 66)
        self.drawOpacity = 1;
        
        self.imageIndex = imageIndex 
        self.BrushQueues = {}
        self.createBrushQueue('undo')

        
    # drawSettings:
    def setDrawLabel(self, label):
        self.drawLabel = label
        col = self.drawColor.get(label, None)
        if col:
            self.activeDrawColor = col
            
    def setDrawSize(self, size):
        self.drawSize = size
    
    def setDrawColor(self, label, color):
        self.drawColor[label] = color
    def setDrawOpacity(self, opacity):
        self.drawOpacity = opacity
        
    def setCanvas(self, canvas):
        self.canvas = canvas
        
    def setUndoList(self, undolist):
        self.undolist = undolist
        
    def undoPush(self, undoPointDescription):
        self.labelmngr.undoPush(undoPointDescription)
    
    def undo(self):
        tic = time.clock()
        step = self.BrushQueues['undo'].pop()
        self.labelmngr.undo(step)
        step.isUndo = True
        
        for bq in self.BrushQueues.values():
            if bq != self.BrushQueues['undo']:
                bq.push(step)
        print "Undo Time %f " % (time.clock() - tic)
        
        tic = time.clock() 
        self.repaint()
        print "Repaint Time %f " % (time.clock() - tic)
    def repaint(self):
        pass
    
    def canvas_clear(self):
        pass
    
    def canvas_paint(self):
        pass

    def InitDraw(self, pos):
        print "InitDraw"
        self.labelmngr.currentBrushQueueEntry = labelMgr.LabelBrushQueueEntry(self.drawLabel, self.imageIndex)
        
    
    def DoDraw(self, pos):
        pass
    
    def EndDraw(self, pos):
        self.labelmngr.currentBrushQueueEntry.finalize()
        for bq in self.BrushQueues.values():
            bq.append(self.labelmngr.currentBrushQueueEntry)
        self.labelmngr.currentBrushQueueEntry = None
        
    
    def changeSize(self, size):
        pass
    
    def createBrushQueue(self, BrushQueueName):
        self.BrushQueues[BrushQueueName] = deque()       
    
    def deleteBrushQueue(self, BrushQueueName):
        del self.BrushQueues[BrushQueueName] 
        

class draw_geomObject(drawManager):
    def __init__(self, labelmngr, canvas, imageIndex):
        drawManager.__init__(self, labelmngr, canvas, imageIndex)
        self.classId = drawManagerID.IDdraw_geomObject
        self.topLevelItems = []
        self.topLevelItems_dict = {}
        
    def setDrawOpacity(self, opacity):
        drawManager.setDrawOpacity(self, opacity)
        for item in self.topLevelItems:
            item.setOpacity(opacity)
        
    def setDrawLabel(self, label):
        drawManager.setDrawLabel(self, label)
        #todo: manage topLevelItems-Dict for label.
        
    def addObject(self, pos):
        pass
    
    def canvas_clear(self):
        for tli in self.topLevelItems:
            self.canvas.removeItem(tli)
    
    def canvas_paint(self):
        for tli in self.topLevelItems:
            self.canvas.addItem(tli)
            
    def repaint(self):
        pass

    def InitDraw(self, pos):
        self.topLevelItems.append(TopLevelItem())
        self.canvas.addItem(self.topLevelItems[-1])
        self.topLevelItems[-1].setOpacity(self.drawOpacity)
        self.lastPoint = pos
        self.DoDraw(pos)
        #todo: undolist
    
    def DoDraw(self, pos):
        self.addObject(pos)
        self.labelmngr.setLabel(pos, self.drawLabel)
    
    def EndDraw(self, pos):
        pass

class draw_Ellipse(draw_geomObject):
    def __init__(self, labelmngr, canvas):
        draw_geomObject.__init__(self, labelmngr, canvas)
        self.classId = drawManagerID.IDdraw_Ellipse
        
    def addObject(self, pos):
        ell = QtGui.QGraphicsEllipseItem(pos[0], pos[1], self.drawSize, self.drawSize)
        ell.setPen(QtGui.QPen(self.activeDrawColor))
        ell.setBrush(QtGui.QBrush(self.activeDrawColor))
        ell.setParentItem(self.topLevelItems[-1])
      

class draw_Patch(drawManager):
    def __init__(self, labelmngr, canvas, imageIndex):
        drawManager.__init__(self, labelmngr, canvas, imageIndex)
        self.classId = drawManagerID.IDdraw_Patch
        
        # Get Size of the labelOverlay, = size of rawimage
        self.size = labelmngr.getSize()
        
        # Init Fully transparent Label OVerlay with correct size
        # Store it in self.image
        self.image = QtGui.QImage(self.size[0], self.size[1], QtGui.QImage.Format_ARGB32)
        self.image.fill(0)
        
        # self.imageItem is just used to display self.image, remember it is the labelOverlay
        self.imageItem = ImageItem(self.image)
        self.imageItem.setOpacity(self.drawOpacity)
        canvas.addItem(self.imageItem)
        self.pixelColor = self.activeDrawColor.rgba()
        labelmngr.setDrawCallback(self.setPixel)
        
    def setDrawOpacity(self, opacity):
        drawManager.setDrawOpacity(self, opacity)
        self.imageItem.setOpacity(opacity)
        
    def setDrawLabel(self, label):
        drawManager.setDrawLabel(self, label)
        self.pixelColor = self.activeDrawColor.rgba()
        #TODO: manage qimage-Dict for label.
        
    @staticmethod
    def __undoOperation(self):
        pass
    
    def changeSize(self):
        # todo: adjust qimage to new size
        pass
    
    def repaint(self):
	#array = qimage2ndarray.rgb_view(self.image)
	#for x in xrange(self.size[0]):
        #    for y in xrange(self.size[1]):
		  #array[y,x]=;
	#self.imageItem.update()
	#return
	
	#a = self.labelmngr.labelArray.copy()
	#print self.size
	#print a.shape
	#print " "
	#a.shape = self.size
	#size_rgb=self.size
	#size_rgb.append(3)
	#c=numpy.zeros(size_rgb)
	#for label in xrange( len(self.drawColor) ):
		#b= (a==label)
		#c[0,:][b]=self.drawColor[label+1].r()
		#c[1,:][b]=self.drawColor[label+1].g()
		#c[2,:][b]=self.drawColor[label+1].b()
		
	#self.image = qimage2ndarray.array2qimage(c)
	#self.imageItem.update()
	#return
		
	#a = 
	#print a.shape
	#self.imageItem.update()
	#return
        # todo: clear qimage, get labels from labelmngr and paint them.
        #self.image.loadFromData( self.labelmngr.labelArray )
	
	#a=numpy.ones(self.size)
	#self.image = qimage2ndarray.array2qimage(a)
	#self.imageItem.update()
	#returnj

	#
	# c++ drawing:
	pixcol = {}
	for label, col in self.drawColor.items():
        	pixcol[label] = col.rgba()
	# todo: pixcol contains more entries than expected...

	labelArrayDrawQImage.drawImage(self.image, pixcol, self.labelmngr.getLabelArrayAsImage().astype(numpy.float64));
	self.imageItem.update()
	return
	
	#
	# python drawing 1: use numpy to extract labeled pixels
	pixcol = {}
	for label, col in self.drawColor.items():
        	pixcol[label] = col.rgba()
	# todo: pixcol contains more entries than expected...
	shp = self.labelmngr.labelArray.shape
	self.labelmngr.labelArray.shape = self.size
	xx, yy = self.labelmngr.labelArray.nonzero()
	self.labelmngr.labelArray.shape = shp
	print "shape: " + str(shp)
	self.image.fill(0)
	for i in xrange(len(xx)):
		y = xx[i]
		x = yy[i]
		#print x,y
		lbl = self.labelmngr.getLabel([x, y])
		self.image.setPixel(x, y, pixcol[lbl])
	self.imageItem.update()
	return

	#
	# python drawing 2: draw all pixels in for loop. SLOOOWWW!!!
        pixcol = {}
        for label, col in self.drawColor.items():
            pixcol[label] = col.rgba()
        # todo: pixcol contains more entries than expected...
        for x in xrange(self.size[0]):
            for y in xrange(self.size[1]):
                lbl = self.labelmngr.getLabel([x, y])
                if lbl:
                    self.image.setPixel(x, y, pixcol[lbl])
                else:
                    self.image.setPixel(x, y, 0)
        self.imageItem.update()
        
    def canvas_clear(self):
        #self.imageItem.scene().removeItem(self.imageItem)
        #self.image = QtGui.QImage( self.size[0], self.size[1], QtGui.QImage.Format_ARGB32 )
        #self.image.fill(0)
        self.canvas.removeItem(self.imageItem)
    
    def canvas_paint(self):
        self.canvas.addItem(self.imageItem)
    
    def InitDraw(self, pos):
        drawManager.InitDraw(self, pos)
        
        self.startPos = pos
        self.lastPos = pos
        
        self.pixelColor = self.activeDrawColor.rgba()
        self.labelmngr.setLabel(pos, self.drawLabel)
        
        # todo: create/get qimage for given label and add to self.canvas.
        self.DoDraw(pos)
    
    # callback for label-manager:
    def setPixel(self, pos):
        if pos[0] > -1 and pos[1] > -1 and pos[0] < self.size[0] and pos[1] < self.size[1]:
            self.image.setPixel(pos[0], pos[1], self.pixelColor)
            
            #tmp =  QtGui.QColor(self.pixelColor)
            self.imageItem.update()
    
    def DoDraw(self, pos):
        if pos != self.lastPos:
            self.labelmngr.setLabelLine2D(self.lastPos, pos, self.drawLabel)
            self.lastPos = pos
    
    def EndDraw(self, pos):
        self.labelmngr.setLabel(pos, self.drawLabel)
        self.labelmngr.undoPush("after paint")
        drawManager.EndDraw(self, pos)
        
class draw_Pixel(draw_Patch):
    def __init__(self, labelmngr, canvas, imageIndex):
        draw_Patch.__init__(self, labelmngr, canvas, imageIndex)
        self.classId = drawManagerID.IDdraw_Pixel

class drawManagerID:
    IDdrawManager = 0
    IDdraw_geomObject = 1
    IDdraw_Ellipse = 2
    IDdraw_Patch = 3
    IDdraw_Pixel = 4
    drawManagerObject = {
        IDdrawManager: drawManager,
        IDdraw_geomObject: draw_geomObject,
        IDdraw_Ellipse: draw_Ellipse,
        IDdraw_Patch: draw_Patch,
        IDdraw_Pixel: draw_Pixel
    }


class labelType:
    def __init__(self, size=1, canvas=None):
        self.canvas = canvas
        self.size = size
        
    def draw(self, x, y):
        pass
    
    def convert(self):
        pass

class labelPatch(labelType):
    def __init__(self, canvas, ImDims, patchCount):
        labelType.__init__(self, dims)
        self.labelArray = numpy.ndarray(patchCount)
        self.canvas = canvas
        
class labelGrid(labelPatch):
    def __init__(self, canvas, ImDims, gridDims):
        patchCount = gridDims[0]
        for i in xrange(len(gridDims) - 1):
            patchCount *= gridDims[i]
        labelPatch.__init__(self, canvas, ImDims, patchCount)

class labelHex(labelPatch):
    pass

class labelPixel(labelGrid):
    def __init__(self, canvas, dims):
        labelGrid.__init__(self, canvas, dims, dims)

class labelPolygonPatches(labelPatch):
    pass

class labelVectorObjects(labelType):
    pass

class labelVector_ellipse(labelVectorObjects):
    pass

class labelVector_line(labelVectorObjects):
    pass
#******************************
class undoList:
    def __init__(self):
        self.undoOperationList = []
        self.itemList = []
        self.classNrList = []
        self.objectList = []
            
    def addLabelObject(self, labelObject, classNr, item):
        self.undoOperationList.append(self.__undoLabeling)
        self.objectList.append(labelObject)
        self.classNrList.append(classNr)
        self.itemList.append(item)
        
    def __undoLabeling(self):
        # private - calling from outside would mess up undoOperationList!
        classNr = self.classNrList.pop()
        item = self.itemList.pop()
        object = self.objectList.pop()
        object.removeLabelObject(classNr, item)
        
    def undo(self):
        if self.undoOperationList.__len__() > 0:
            op = self.undoOperationList.pop()
            op()
        

class labelManager:
    def __init__(self, canvas=None):
        self.canvas = canvas

class displayLabelClasses:
    def __init__(self, hash=None):
        if hash:
            __load(hash)
        else:
            self.classes = 0
            self.classNames = []
            self.classColors = []
            self.classSize = []
            self.currentOpacity = 0.25
            
    def addClass(self, name=None, color=None, size=None):
        if not name: name = "classname_" + str(self.classes)
        if not color: color = QtGui.QColor(random.random()*255, random.random()*255, random.random()*255)
        if not size: size = random.random()*30
        #self.graphicsItems.append(QtGui.QGraphicsItemGroup())
        self.classNames.append(name)
        self.classColors.append(color)
        self.classSize.append(size)
        self.classes += 1
        

class displayLabel:
    def __init__(self, hash=None):
        if hash:
            __load(hash)
        else:
            self.classes = 0
            self.classNames = []
            self.classColors = []
            self.classSize = []
            self.currentOpacity = 0.25
            self.LabelObjects = []  # is really a 2d list (list of lists), later on: labelObjects[classnr][labelnr]
            self.currentOpacity = 0.25
            self.undolist = None

    def __load(self, hash):
        pass
        
    def addUndoList(self, undolist):
        self.undolist = undolist
        
    def addClass(self, name=None, color=None, size=None):
        if not name: name = "classname_" + str(self.classes)
        if not color: color = QtGui.QColor(random.random()*255, random.random()*255, random.random()*255)
        if not size: size = random.random()*30
        #self.graphicsItems.append(QtGui.QGraphicsItemGroup())
        self.classNames.append(name)
        self.classColors.append(color)
        self.classSize.append(size)
        self.LabelObjects.append([])
        self.classes += 1            
    
    def addLabelObject(self, classnr, item):
        # add topLevelItem to list.
        self.LabelObjects[classnr].append(item)
        item.setOpacity(self.currentOpacity)
        self.undolist.addLabelObject(self, classnr, item)
        
    def removeLabelObject(self, classnr, item):
        self.LabelObjects[classnr].remove(item)
        item.scene().removeItem(item)
        del item
        
    def changeOpacity(self, classNr, op):
        self.currentOpacity = op
        if self.classes:
            for ob in self.LabelObjects[classNr]:
                ob.setOpacity(op)
        
    def getClassNames(self):
        return self.classNames
    
    def getColor(self, classnr):
        return self.classColors[classnr]
    
    def getSize(self, classnr):
        return self.classSize[classnr]


class displayImageChannel:
    def __init__(self, type):
        self.type = type

class displayImageChannelList:
    def __init__(self):
        self.list = []
    
    def appendChannel(self, channel):
        self.list.append(channel)


class displayImage:

    def __init__(self, filename="test.tif", user=None):
        self.imageData = None        
        self.filename = filename
        self.__loadImage()
        self.users = []
        self.channellist = None
        self.addUser(user)
        self.undolist = undoList()
        self.label = self.__getLabel()
    
    def __getLabel(self):
        # find label for active image
        # todo: hash-table?
        dl = displayLabel()
        dl.addUndoList(self.undolist)
        return dl
                
    # private:
    def __loadImage(self):
        if self.filename:
            try:
                self.imageData = QtGui.QImage(100, 100, QtGui.QImage.Format_ARGB32)
                self.imageData.load(self.filename)
            except Exception, inst:
                print "displayImage.__loadImage: Fehler beim Laden: ", inst
                
    # public:
    def addUndoList(self, lst):
        self.undolist = lst
        self.label.addUndoList(lst)
                
    def freeImageData(self):
        # only frees image data - doesn't delete the actual image-instance
        del self.imageData
        self.imageData = None
        
    def addUser(self, user):
        if user: self.users.append(user)
        
    def removeUser(self, user):
        self.users.remove(user)
        
    def getImageData(self):
        if not self.imageData: self.__loadImage()
        return self.imageData
    
    def getName(self):
        return self.filename
    
    def addLabelItem(self, item, classnr):
        pass
        
        

class displayImageList:
    def __init__(self, Image=None):
        self.list = []
        if isinstance(Image, displayImage): 
            self.list.append(Image)
        if isinstance(Image, str):
            img = DisplayImage(Image)
            self.list.append(img)
        
    def appendImage(self, image):
        if not image: 
            return
        if isinstance(image, displayImage): 
            self.list.append(image)
        if isinstance(image, str):
            image = [image]
        if isinstance(image, list):
            for item in image:
                if isinstance(item, displayImage): self.list.append(item)
                if isinstance(item, str):
                    dpi = displayImage(item)
                    self.list.append(dpi)
        
    def getImageData(self, nr):
        return self.list[nr].getImageData()
    
    def freeImageData(self, nr):
        self.list[nr].freeImageData
        
    def addUser(self, nr, user):
        self.list[nr].addUser(user)
    
    def removeUser(self, nr, user):
        self.list[nr].removeUser(user)
        
    def addLabelItem(self, item, nr, classnr):
        self.list[nr].addLabelItem(item, nr, classnr)
    
    def getFilenames(self):
        return [im.getName() for im in self.list]


# *********************************************************
class cloneView(QtGui.QGraphicsView):
    def __init__(self, view_orig):
        QtGui.QGraphicsView.__init__(self)
        self.clickdist = 5
        self.dragging = False
        self.zooming = False
        self.view_orig = view_orig
        self.zoom_box = None
        self.zoomdir = {"ul":False, "u":False, "ur":False, "r":False, "rd":False, "d":False, "dl":False, "l":False}
        self.oldrect = None
        self.clickpos = None
        
    def setZoomBox(self, zoombox):
        self.zoom_box = zoombox
    
    def mousePressEvent(self, event):
        QtGui.QGraphicsView.mousePressEvent(self, event)
        QtCore.Qt.LeftButton
        rect = self.zoom_box.rect()
        for k in self.zoomdir: self.zoomdir[k] = False
        if event.button() == QtCore.Qt.LeftButton:
            #self.oldrect = self.view_orig.sceneRect()
            self.oldrect = self.view_orig.mapToScene(self.view_orig.rect())
            pos = self.mapToScene(event.pos())
            self.clickpos = pos
            self.zooming = False
            if abs(rect.top() - pos.y()) <= self.clickdist: self.zoomdir["u"] = True; self.zooming = True
            if abs(rect.right() - pos.x()) <= self.clickdist: self.zoomdir["r"] = True; self.zooming = True
            if abs(rect.bottom() - pos.y()) <= self.clickdist: self.zoomdir["d"] = True; self.zooming = True
            if abs(rect.left() - pos.x()) <= self.clickdist: self.zoomdir["l"] = True; self.zooming = True
            if not self.zooming:
                if pos.y() <= rect.bottom():
                    if pos.y() >= rect.top():
                        if pos.x() >= rect.left():
                            if pos.x() <= rect.right():
                                self.dragging = True
            self.origmatrix = QtGui.QMatrix(self.view_orig.matrix())
            
    def mouseMoveEvent(self, event):
        QtGui.QGraphicsView.mouseMoveEvent(self, event)
        if self.zooming or self.dragging:
            pos = self.mapToScene(event.pos())
            delta = pos - self.clickpos
        else: return
        m = QtGui.QMatrix(self.origmatrix)
        if self.zooming:
            oldrect = self.oldrect.boundingRect()
            #for k in self.zoomdir:
            #    if self.zoomdir[k]: print k
            scalex = 1.0
            scaley = 1.0
            if self.zoomdir["u"]: scaley = 1.0 + delta.y() / oldrect.height(); self.dragging = True; delta.setX(0.0)
            if self.zoomdir["d"]: scaley = 1.0 - delta.y() / oldrect.height()
            if self.zoomdir["l"]: scalex = 1.0 + delta.x() / oldrect.width(); self.dragging = True; delta.setY(0.0)
            if self.zoomdir["r"]: scalex = 1.0 - delta.x() / oldrect.width()
            m.scale(scalex, scaley)
        if self.dragging:
            m.translate(-delta.x(), -delta.y())
        self.view_orig.setMatrix(m)
        self.view_orig.requestROIupdate()

    def mouseReleaseEvent(self, event):
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            self.zooming = False
        
class ZoomBox (QtGui.QGraphicsRectItem):
    def __init__(self):
        QtGui.QGraphicsRectItem.__init__(self)
    
    #def mouseMoveEvent(self, event):
    #    QtGui.QGraphicsRectItem.mouseMoveEvent(self, event)
    #    print "ZoomBox - mouseMoveEvent"
        
    #def sceneEvent(self, event):
    #    print event.type()

class cloneViewWidget(QtGui.QDockWidget):
    
    def __init_n(self, parent=None, labelwidget=None):
        self.initObject()
    
    def initObject(self):
        self.constructChildren()
        self.initChildren()
    
    def __init__(self, parent=None, labelwidget=None, view_orig=None):
        QtGui.QWidget.__init__(self, parent)
        self.resize(100, 100)
        self.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.TopDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        self.insidewidget = QtGui.QWidget()
        self.setWidget(self.insidewidget)

        #self.view = panView()
        self.labelwidget = labelwidget
        self.view = cloneView(view_orig)
        self.sceneToDraw = self.labelwidget.view.scene()
        self.sceneitem = SceneItem(self.sceneToDraw)
        self.par = parent
        self.view_orig = view_orig

        self.col = QtGui.QColor(255, 0, 0)
        #self.roi = QtGui.QGraphicsRectItem()
        self.roi = ZoomBox()
        self.roi.setPen(QtGui.QPen(self.col))
        #self.roi.setBrush(QtGui.QBrush(self.col))   # make solid for debugging purposes
        self.roi.setZValue(1)
        self.view.setZoomBox(self.roi)
        
        self.scene = QtGui.QGraphicsScene()
        self.scene.addItem(self.roi)
        self.scene.addItem(self.sceneitem)

        self.view.setScene(self.scene)
        
        # no events are passed to roi-object :-(
        self.view.setInteractive(True)
        self.roi.setAcceptHoverEvents(True)
        #self.roi.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        
        #self.view.scale(0.2,0.2)
        lo = QtGui.QHBoxLayout()
        lo.addWidget(self.view)
        self.insidewidget.setLayout(lo)
        self.oldZoomingview = None
        
        self.view.setSceneRect(self.sceneToDraw.sceneRect())
        
    def saveLayout(self, storage):
        oAttributeList = []
        oAttributeValueList = []

        ci = []
        ci.append(hash(self.par))
        ci.append(hash(self.labelwidget))
        storage.constructInfoDict[ hash(self) ] = ci
        
        storage.recurseSave(self, oAttributeList, oAttributeValueList)
    
    @staticmethod
    def generateObj(storage):
        ci = storage.constructInfoDict[  storage.idList[storage.index]  ]
        par = storage.objectDict[ci[0]]
        lw = storage.objectDict[ci[1]]
        return cloneViewWidget(par, lw)

    def connectROISignal(self, zoomingview):
        if self.oldZoomingview:
            self.disconnect(self.oldZoomingview, QtCore.SIGNAL("ROIchanged"), updateROI)
        self.connect(zoomingview, QtCore.SIGNAL("ROIchanged"), self.updateROI)
        self.oldZoomingview = zoomingview

    def fitView(self):
        #self.view.fitInView(self.view.sceneRect())
        #self.view.fitInView(self.sceneToDraw.sceneRect())
        self.view.fitInView(self.sceneitem)
        
    def showEvent(self, event):
        QtGui.QDockWidget.showEvent(self, event)
        self.fitView()
        
    def updateROI(self, rect):
        self.roi.setRect(rect)
        
    def resizeEvent(self, event):
        QtGui.QDockWidget.resizeEvent(self, event)
        self.fitView()

    def addScene(self, scene):
        if scene:
            self.sceneToDraw = scene
            self.view.setScene(self.scene)
            
        
class labelWidget(QtGui.QWidget):
    def __init__(self, parent=None, imageList=None):
        QtGui.QWidget.__init__(self, parent)
        global labelwidgetInstance          # TODO: UGLY global
        labelwidgetInstance = self          # TODO: UGLY global
        self.project = None
        if isinstance(imageList, str): 
            imageList = [imageList]
        if isinstance(imageList, list):
            dpil = displayImageList()
            for item in imageList:
                dpil.appendImage(item)
            imageList = dpil
            
        if not imageList:
            dpi = displayImage('test.tif', self)
            imageList = displayImageList(dpi)
        
        self.labelForImage = {}
        self.predictions = {}     
        self.segmentation = {}
        self.uncertainty = {}
        self.cloneviews = []
        self.overlayPixmapItems = []
        self.contextMenuLabel = None
        self.brushSize = 1
        
        self.imageList = imageList
        self.activeImage = 0
        self.activeLabel = 1
        # -1 for all at once (gray, rgb) a number for multi-spec data
        self.activeChannel = -1 
        self.image = imageList.list[self.activeImage]
        self.imageData = None
        self.pixmapitem = None
        
        
        
        self.initCanvas()
        self.canvas.setClass(0)
        self.makeView()
        self.makeToolBox()
        
    def makeToolBox(self):
        # ComboBox for Image Change
        self.cmbImageList = QtGui.QComboBox()
        self.cmbImageList.setMinimumWidth(142)
        self.connect(self.cmbImageList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeImage)
        
        # Undo Button for Image Change
        self.btnUndo = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.Undo) , "Undo")
        self.connect(self.btnUndo, QtCore.SIGNAL("clicked()"), self.undo)
        
        # Channel Selector Combo Box
        self.cmbChannelList = QtGui.QComboBox()
        self.cmbChannelList.setMinimumWidth(142)
        self.cmbChannelList.setEnabled(False)
        self.connect(self.cmbChannelList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeChannel)
        
        # Class Selector Combo Box
        self.cmbClassList = QtGui.QComboBox()
        self.cmbClassList.setMinimumWidth(142)
        self.connect(self.cmbClassList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeClass)
        
        # Clone View Button
        self.btnCloneView = QtGui.QPushButton(QtGui.QIcon(ilastikIcons.DoubleArrow), "Clone")
        self.connect(self.btnCloneView, QtCore.SIGNAL("clicked()"), self.makeCloneView)
        
        # Overlay Combobox
        self.cmbOverlayList = QtGui.QComboBox()
        self.cmbOverlayList.addItems(['None','Prediction','Uncertainty','Segmentation'])
        self.connect(self.cmbOverlayList, QtCore.SIGNAL("currentIndexChanged(int)"), self.on_changeOverlay)
        
        # Slider for Label Opasity
        self.sldOpacity = QtGui.QSlider()
        self.sldOpacity.setMinimum(0)
        self.sldOpacity.setMaximum(100)
        self.sldOpacity.setOrientation(QtCore.Qt.Horizontal)
        self.sldOpacity.setValue(100)
        self.sldOpacity.setMaximumWidth(100)
        self.changeOpacity(100)      
        self.connect(self.sldOpacity, QtCore.SIGNAL("valueChanged(int)"), self.changeOpacity)
        
        # Container Widget for Labeling
        self.labelingToolBox = QtGui.QWidget()
        
        
        labelingToolBox_lists = QtGui.QVBoxLayout()
        labelingToolBox_lists.addWidget(QtGui.QLabel('Data Items'))
        labelingToolBox_lists.addWidget(self.cmbImageList)
        labelingToolBox_lists.addWidget(QtGui.QLabel('Channel'))
        labelingToolBox_lists.addWidget(self.cmbChannelList)
        labelingToolBox_lists.addWidget(QtGui.QLabel('Classes'))
        labelingToolBox_lists.addWidget(self.cmbClassList)
        labelingToolBox_lists.addWidget(QtGui.QLabel('Overlay'))
        labelingToolBox_lists.addWidget(self.cmbOverlayList)
        labelingToolBox_lists.addWidget(QtGui.QLabel('Label Opasity'))
        labelingToolBox_lists.addWidget(self.sldOpacity)
        labelingToolBox_lists.addWidget(self.btnUndo)
        labelingToolBox_lists.addWidget(self.btnCloneView)
        labelingToolBox_lists.addStretch()
        self.labelingToolBox.setLayout(labelingToolBox_lists)
        
        
        
        # Container Widget for Viewing
        self.btnViewImage = QtGui.QPushButton('Image')
        self.btnViewPrediction = QtGui.QPushButton('Prediction')
        self.btnViewUncertainty = QtGui.QPushButton('Uncertainty')
        self.btnViewSegmentation = QtGui.QPushButton('Segmentation')
        
        # Connects
        self.connect(self.btnViewImage, QtCore.SIGNAL("clicked()"), self.on_viewImage)
        self.connect(self.btnViewPrediction, QtCore.SIGNAL("clicked()"), self.on_viewPrediction)
        self.connect(self.btnViewUncertainty, QtCore.SIGNAL("clicked()"), self.on_viewUncertainty)
        self.connect(self.btnViewSegmentation, QtCore.SIGNAL("clicked()"), self.on_viewSegmentation)
        
        # ToolBox Entry
        self.viewingToolBox = QtGui.QWidget()
        
        # Adding Buttons to Layout
        viewingToolBox_lists = QtGui.QVBoxLayout()
        viewingToolBox_lists.addWidget(self.btnViewImage)
        viewingToolBox_lists.addWidget(self.btnViewPrediction)
        viewingToolBox_lists.addWidget(self.btnViewUncertainty)
        viewingToolBox_lists.addWidget(self.btnViewSegmentation)
        
        viewingToolBox_lists.addWidget(self.btnViewSegmentation)
        viewingToolBox_lists.addStretch()

        self.viewingToolBox.setLayout(viewingToolBox_lists)
         
        # Creating of the QToolBox
        self.toolBox = QtGui.QToolBox()
        self.toolBox.setMaximumWidth(160)
        # Adding both Entries
        self.toolBox.addItem(self.labelingToolBox , QtGui.QIcon(ilastikIcons.Brush), 'Labeling')
        #self.toolBox.addItem(self.viewingToolBox, QtGui.QIcon(ilastikIcons.View), 'View')
        
        # At the right side of view
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.toolBox)

        self.setLayout(layout)

        self.pixmapitem = None
        #self.changeImage(0)       
        
#        try:
#            self.updateProject( self.parent().project)
#        except AttributeError:
#            pass
        
    def on_changeOverlay(self, ind):
        if ind == 0:
            self.on_viewImage()
        elif ind == 1:
            self.on_viewPrediction()
        elif ind == 2:
            self.on_viewUncertainty()
        elif ind == 3:
            self.on_viewSegmentation()

    def on_viewPrediction(self):
        displayImage = self.activeImage
        self.OverlayMgr.setOverlayState('Prediction')
                    
    def on_viewSegmentation(self):
        displayImage = self.activeImage
        self.OverlayMgr.setOverlayState('Segmentation')
        
    def on_viewImage(self):
        self.OverlayMgr.clearAll()
        
    def on_viewUncertainty(self): 
        displayImage = self.activeImage
        activeLearner = activeLearning.EnsembleMargin()

        pmap = self.project.dataMgr.prediction[displayImage]    
        image = activeLearner.compute(pmap)

        self.OverlayMgr.updateUncertaintyPixmaps({displayImage:image})
        self.OverlayMgr.setOverlayState('Uncertainty')
        
    def saveLayout(self, storage):
        oAttributeList = []
        oAttributeValueList = []

        #ci = []
        #ci.append(hash(self.par))
        #ci.append(hash(self.sceneToDraw))
        #storage.constructInfoDict[ hash(self) ] = ci
        
        storage.recurseSave(self, oAttributeList, oAttributeValueList)
        
    def initCanvas(self):
        self.imageData = self.imageList.getImageData(self.activeImage)
        self.imageList.addUser(self.activeImage, self)
        self.canvas = DisplayPanel(self)
        #pm = QtGui.QPixmap.fromImage(self.imageData)
        #self.pixmapitem = self.canvas.addPixmap(pm)
        self.canvas.setLabelObject(self.image.label)
        for labelClass in self.image.label.LabelObjects:
            for tli in labelClass:
                self.canvas.addItem(tli)

    def changeOpacity(self, op):
        #self.image.label.changeOpacity(self.labelClass, op/100.0)
        #self.drawManager.setDrawOpacity(op/100.0)
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].setOpacity(op / 100.0)
        
    def updateProject(self, project):
        self.project = project
        # Check for Multispectral Data and load ChannelList if present
        if self.project.dataMgr[0].dataKind in ['multi']:
            # activeChannel = 0 means there is now
            self.activeChannel = 0
            self.loadChannelList(0)  
        else:
            self.activeChannel = -1
            self.clearChannelList()
            
        for k in self.labelForImage:
            self.labelForImage[k].canvas_clear()
        self.labelForImage = {}
        
        self.loadImageList()
        self.loadLabelList()
        self.changeImage(0)
        self.updateDrawSettings()

        self.OverlayMgr = OverlayMgr(self.canvas, project.labelColors, project.dataMgr.dataItemsShapes(), self)
        self.OverlayMgr.updatePredictionsPixmaps(dict(irange(project.dataMgr.prediction)))
        self.OverlayMgr.updateSegmentationPixmaps(dict(irange(project.dataMgr.segmentation)))
        
        self.connect(self, QtCore.SIGNAL("imageChanged"), self.OverlayMgr.clearAll)
        
    def setBrushSize(self, rad):
        self.brushSize = rad
        self.labelForImage[self.activeImage].setBrushSize(rad)
        
    def updateDrawSettings(self):
        pass 
    
    def loadChannelList(self, imageIndex=0):
        self.cmbChannelList.clear()
        print self.project.dataMgr[imageIndex].channelDescription
        if self.project.dataMgr[imageIndex].dataKind == 'multi':
            self.cmbChannelList.addItems(self.project.dataMgr[imageIndex].channelDescription)
            self.cmbChannelList.setEnabled(True)
        
        
    def clearChannelList(self):
        # self.disconnect(self.cmbChannelList,QtCore.SIGNAL("currentIndexChanged(int)"), self.changeChannel)
        self.cmbChannelList.clear()
        self.cmbChannelList.setEnabled(False)
        self.activeChannel = -1
        
    def loadImageList(self):
        self.cmbImageList.clear()
        for item in self.project.dataMgr.dataItems:
            print item.fileName
        imagenames = [os.path.basename(item.fileName) for item in self.project.dataMgr.dataItems]
        self.cmbImageList.addItems(imagenames)
        
    def loadLabelList(self):
        self.cmbClassList.clear()
        self.cmbClassList.addItem("Erase")
        self.cmbClassList.addItems(self.project.labelNames)
        self.contextMenuLabel = contextMenuLabel(self.project.labelNames, self.project.labelColors, self.canvas)
        if len(self.project.labelNames) > 0:
            self.cmbClassList.setCurrentIndex(1)

    def getLabel(self, imageNr, pos):
        lfi = self.labelForImage.get(imageNr, None)
        if not lfi:
            return
        return lfi.getLabelValue(pos)
    
    def newLabelsPending(self):
        self.emit(QtCore.SIGNAL('newLabelsPending'))
    
    def updateLabelsOfDataItems(self, dataMgr):
        """ Extract Label Information out of the label Manager and put it to the dataItems attribute"""
        for dataItemIndex, dataItem in irange(dataMgr):
            # Check for Labels
            if self.labelForImage.get(dataItemIndex, False):
                dataItem.labels = self.labelForImage[dataItemIndex].DrawManagers[0].labelmngr.getLabelArrayAsImage()
                dataItem.hasLabels = True
    
    @QtCore.pyqtSignature("int")
    def changeImage(self, newImage):
        # Check Call from ComboBox reset with newImage == -1
        if newImage < 0:
            return
        # Check Call without Project
        if not self.project: 
            return
        
        if newImage != self.activeImage:
            # Image changed indeed
            self.loadChannelList(newImage) 
        
        # Delete old Image Display pixmapitem
        if self.pixmapitem:
            self.canvas.removeItem(self.pixmapitem)
        
        # Delete old Display Labels
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].canvas_clear()  
        
        # Set new Image Display and put it in self.pixmapitem
        if self.activeChannel < 0:
            self.img = self.project.dataMgr[newImage].data.qimage()
        else:
            tmpImg = self.project.dataMgr[newImage].data[:, :, self.activeChannel]
            self.img = tmpImg.qimage(normalize=True)
 
        pm = QtGui.QPixmap.fromImage(self.img)
        self.pixmapitem = self.canvas.addPixmap(pm)
        self.pixmapitem.setZValue(-1)
        
        # If the Labels are already initialized, just paint it
        if self.labelForImage.get(newImage, None):
            self.labelForImage[newImage].canvas_paint()
            # Change To Active Label
            self.labelForImage[newImage].setActiveLabel(self.activeLabel)
            
        # Init Label -> Should be called once per image when changing to it
        else:
            # Init Label Object labelForImage
            self.labelForImage[newImage] = labelingForOneImage()
            labelManager = labelMgr.label_Pixel([self.pixmapitem.pixmap().width(), self.pixmapitem.pixmap().height()])
            drawManager = draw_Pixel(labelManager, self.canvas, newImage)
            
            # Init colors
            for label, col in self.project.labelColors.items():
                drawManager.setDrawColor(label, col)
            erasecol = QtGui.QColor(0,0,0,0)
            drawManager.setDrawColor(0, erasecol)
            
            # Give drawManager to labelForImage
            self.labelForImage[newImage].addDrawManager(drawManager) 
            
            # Change To Active Label
            self.labelForImage[newImage].setActiveLabel(self.activeLabel)     
            
            # Maybe we loaded the data and we loaded also labels
            if self.project.dataMgr[newImage].hasLabels:
                # Just checking if they are really there
                if self.project.dataMgr[newImage].labels is not None:
                    # Get loaded labels into the labelArray 
                    labelManager.setLabelArrayFromImage(self.project.dataMgr[newImage].labels)
                    # Display them
                    drawManager.repaint()
        
        # Set new active Image    
        self.activeImage = newImage
        self.setBrushSize(self.brushSize)
        
        # Emit imageChanged Signal
        self.emit(QtCore.SIGNAL("imageChanged"), self.activeImage)
                    
    def updateClassList(self):
        self.cmbClassList.clear()
        self.cmbClassList.addItems(self.image.label.getClassNames())
        
    @QtCore.pyqtSignature("int")
    def changeClass(self, nr):
        print "Call to changeClass with Class: ", nr
        if nr < 0:
            return
        #nr += 1  # 0 is unlabeled !!
        self.activeLabel = nr
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].setActiveLabel(nr)
        self.emit(QtCore.SIGNAL("labelChanged"), nr)
    
    @QtCore.pyqtSignature("int")
    def changeChannel(self, channelIndex):
        if channelIndex < 0:
            print "Dumb Callbacks"
            return
        print "Change Channel to ", channelIndex
        self.activeChannel = channelIndex
        self.changeImage(self.activeImage)
         
    def undo(self):
        self.labelForImage[self.activeImage].undo()
        
    def makeView(self):
        #self.view = QtGui.QGraphicsView()
        self.view = panView()
        self.view.setScene(self.canvas)
        
    def makeCloneView(self):
        par = self.parent()
        if par: par = par.parent()
        cv = cloneViewWidget(par, self, self.view)
        self.cloneviews.append(cv)
        cv.connectROISignal(self.view)
        self.view.requestROIupdate()
        if par.__class__.__name__ == 'MainWindow':
            #par.addWidgetToDock(cv, QtCore.Qt.BottomDockWidgetArea, "Clone View")
            dock = par.addDockWidget(QtCore.Qt.BottomDockWidgetArea, cv)
            #dock.setObjectName('cloneView_'+hash(dock))
        else:
            cv.show()

class TopLevelItem(QtGui.QGraphicsItem):
    def __init__(self):
        QtGui.QGraphicsItem.__init__(self)
    def boundingRect(self):
        return QtCore.QRectF(0, 0, 0, 0)
    def paint(self, painter, option, widget):
        return

class ImageItem(QtGui.QGraphicsItem):
    def __init__(self, image=None):
        QtGui.QGraphicsItem.__init__(self)
        self.setImage(image)

    def boundingRect(self):
        if self.image:
            return QtCore.QRectF(self.image.rect())
        else:
            return QtCore.QRectF(0, 0, 0, 0)

    def setImage(self, image):
        self.image = image
        #image.connect(image, QtCore.SIGNAL("changed(const QList<QRectF>&)"), self.update)

    def paint(self, painter, option, widget):
        if self.image:
            #self.scene.render(painter, )
            #render (self, QPainter painter, QRectF target = QRectF(), QRect source = QRect(), Qt.AspectRatioMode aspectRatioMode = Qt.KeepAspectRatio)
            #drawItems (self, QPainter painter, list items, list options)
            
            #self.scene.drawItems(painter, self.scene.items(), None)
            #self.sceneToDraw.render(painter, self.sceneToDraw.sceneRect(), self.scene().sceneRect())
            #self.sceneToDraw.render(painter, self.sceneToDraw.sceneRect())
            painter.drawImage(self.image.rect(), self.image)

class SceneItem(QtGui.QGraphicsItem):
    def __init__(self, scene=None):
        QtGui.QGraphicsItem.__init__(self)
        self.addScene(scene)

    def boundingRect(self):
        if self.sceneToDraw:
            return self.sceneToDraw.sceneRect()
        else:
            return QtCore.QRectF(0, 0, 0, 0)

    def addScene(self, scene):
        self.sceneToDraw = scene
        scene.connect(scene, QtCore.SIGNAL("changed(const QList<QRectF>&)"), self.update)

    def paint(self, painter, option, widget):
        if self.sceneToDraw:
            #self.scene.render(painter, )
            #render (self, QPainter painter, QRectF target = QRectF(), QRect source = QRect(), Qt.AspectRatioMode aspectRatioMode = Qt.KeepAspectRatio)
            #drawItems (self, QPainter painter, list items, list options)
            
            #self.scene.drawItems(painter, self.scene.items(), None)
            #self.sceneToDraw.render(painter, self.sceneToDraw.sceneRect(), self.scene().sceneRect())
            self.sceneToDraw.render(painter, self.sceneToDraw.sceneRect())
            
    def addItem(self, item):
        if self.sceneToDraw:
            self.sceneToDraw.addItem(item)

class panView(QtGui.QGraphicsView):
    def __init__(self):
        QtGui.QGraphicsView.__init__(self)
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        #self.setSceneRect(QtCore.QRectF(-1e100, -1e100, 1e100, 1e100))
        self.panning = False
        self.zooming = False
        self.zoomFactor = 0.05
        
    def scrollContentsBy(self, dx, dy):
        QtGui.QGraphicsView.scrollContentsBy(self, dx, dy)
        self.requestROIupdate()                 # todo: inlining, no function?

    def mousePressEvent(self, event):
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        QtGui.QGraphicsView.mousePressEvent(self, event)
        if event.button() == QtCore.Qt.MidButton and not(event.modifiers() & QtCore.Qt.ControlModifier):
            self.pan_origin = self.mapToScene(event.pos())
            self.panning = True
        if event.button() == QtCore.Qt.MidButton and (event.modifiers() & QtCore.Qt.ControlModifier):
            self.zoom_origin = self.mapToScene(event.pos())
            self.zoom_origmatrix = QtGui.QMatrix(self.matrix())
            self.zooming = True
    
    def requestROIupdate(self):
        rect = self.mapToScene(self.rect())
        viewrect = QtCore.QRectF(rect[0], rect[2])
        self.emit(QtCore.SIGNAL('ROIchanged'), viewrect)
            
    def mouseMoveEvent(self, event):
        QtGui.QGraphicsView.mouseMoveEvent(self, event)
        if self.panning:
            pos = self.mapToScene(event.pos())
            delta = pos - self.pan_origin
            m = self.matrix()
            m.translate(delta.x(), delta.y())
            self.setMatrix(m)
            self.requestROIupdate()                 # todo: inlining, no function?
        if self.zooming:
            pos = self.mapToScene(event.pos())
            delta = pos - self.zoom_origin
            delta /= 500                             # todo: --> unhardcode zoomfactor
            delta += QtCore.QPointF(1, 1)
            m = QtGui.QMatrix(self.zoom_origmatrix)
            m.scale((delta.x() + delta.y()) / 2, (delta.x() + delta.y()) / 2)
            self.setMatrix(m)
            self.requestROIupdate()                 # todo: inlining, no function?

    def mouseReleaseEvent(self, event):
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        if event.button() == QtCore.Qt.MidButton:
            self.panning = False
            self.zooming = False
    
    def wheelEvent(self, wheel):
        if wheel.modifiers() & QtCore.Qt.ControlModifier:
            self.zoom_origin = self.mapToScene(wheel.pos())
            self.zoom_origmatrix = QtGui.QMatrix(self.matrix())
            sig = numpy.float32(numpy.sign(wheel.delta()))
            delta = 1 + sig * self.zoomFactor                 
            m = QtGui.QMatrix(self.zoom_origmatrix)
            m.scale(delta, delta)
            self.setMatrix(m)
            self.requestROIupdate()  
        
class DisplayPanel(QtGui.QGraphicsScene):
    def __init__(self, parent=None):
        QtGui.QGraphicsScene.__init__(self, parent)
        self.labeling = False
        self.labelObject = None
        self.classNr = 0
        self.setItemIndexMethod(self.NoIndex)   # todo: test if drawing becomes faster...
        
    def setLabelObject(self, lo):
        self.labelObject = lo
    
    def setClass(self, nr):
        self.classNr = nr
        
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.labeling = True

            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager = self.parent().labelForImage[self.parent().activeImage].getActiveDrawManager()

            self.drawManager.InitDraw(pos)
            
        if event.button() == QtCore.Qt.RightButton:
            if self.parent().contextMenuLabel:
                self.parent().contextMenuLabel.popup(event.screenPos())
         
    def mouseMoveEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton) and self.labeling:
            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager.DoDraw(pos)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.labeling:
            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager.EndDraw(pos)
            self.labeling = False
            self.parent().newLabelsPending()
            
    def addSomeStuffToCanvas(self, pos):
        ell = QtGui.QGraphicsEllipseItem(pos.x(), pos.y(), self.siz, self.siz)
        ell.setPen(QtGui.QPen(self.col))
        ell.setBrush(QtGui.QBrush(self.col))
        ell.setParentItem(self.topLevelObject)

class contextMenuLabel(QtGui.QMenu):
    def __init__(self, labelNames, labelColors, parent=None):
        QtGui.QMenu.__init__(self)
        self.parent = parent
        self.action = []
        
        erase_icon = QtGui.QIcon(ilastikIcons.Erase)
        action_erase = QtGui.QAction(erase_icon, "Erase", self)
        receiver_erase = lambda : parent.parent().cmbClassList.setCurrentIndex(0)
        self.connect( action_erase, QtCore.SIGNAL("triggered()"), receiver_erase )
        self.addAction(action_erase)
        
        self.addSeparator()
        for cnt, labelName in irange(labelNames):
            pixmap = QtGui.QPixmap(16, 16)
            color = QtGui.QColor(labelColors[cnt + 1])
            pixmap.fill(color)
            icon = QtGui.QIcon(pixmap)
            self.action.append(QtGui.QAction(icon, labelName, self))
            receiver = lambda cnt=cnt: parent.parent().cmbClassList.setCurrentIndex(cnt+1)
            self.connect(self.action[cnt], QtCore.SIGNAL("triggered()"), receiver)
            self.addAction(self.action[cnt])
        self.addSeparator()
        brushSelector = self.addMenu(QtGui.QIcon(ilastikIcons.Brush), 'Brush Size')
        for rad in range(1, 7):
            rad_ = rad * 2 - 1
            icon = QtGui.QIcon(self.createCirclePixmap(rad_))
            action = QtGui.QAction(icon, '', self);
            receiver = lambda rad = rad: parent.parent().parent().parent().ribbon.tabDict['Label'].itemDict['Brushsize'].setValue(rad)
            self.connect(action, QtCore.SIGNAL("triggered()"), receiver)
            
            brushSelector.addAction(action)
    
    def createCirclePixmap(self, rad):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        painter.setBrush(brush)
        painter.drawEllipse(16 - rad / 2, 16 - rad / 2, rad * 2 + 1, rad * 2 + 1)
        return pixmap

class OverlayMgr(object):
    def __init__(self, canvas, classColors, imageShapes, parent):       
        self.labelWidget = parent
        self.classColors = classColors;
        self.imageCount = len(imageShapes)
        self.classCount = len(classColors)
        
        self.canvas = canvas
        self.imageShapes = imageShapes
        
        # Init of the handeled overlays
        self.predictionPixmaps = {}
        for img in range(self.imageCount):
            self.predictionPixmaps[img] = {}
            for k in range(self.classCount):
                self.predictionPixmaps[img][k] = [False, False]
        
        self.segmentationPixmaps = {}
        for img in range(self.imageCount):
            self.segmentationPixmaps[img] = [False, False]
            
        self.uncertaintyPixmaps = {}
        for img in range(self.imageCount):
            self.uncertaintyPixmaps[img] = [False, False]
            
        self.stateNames = ['Image','Prediction','Uncertainty','Segmentation']
        self.stateList = {}
        self.stateList['Image'] = dict([(k,None) for k in range(self.imageCount)])
        self.stateList['Prediction'] = self.predictionPixmaps
        self.stateList['Uncertainty'] = self.uncertaintyPixmaps
        self.stateList['Segmentation'] = self.segmentationPixmaps
        self.state = 'Prediction'
        
        
        # self.classIndex = -1 all Classes at the same time, or just a specific nr.
        self.classIndex = -1
        
    def setOverlayState(self, state):
        self.state = state
        self.showOverlayPixmapByState()
        
    def setOverlayStateByIndex(self, index):
        self.state = self.stateNames[index]
        print self.state
        self.showOverlayPixmapByState()
    
    def setClassIndex(self, classIndex):
        self.classIndex = classIndex           

    def updatePredictionsPixmaps(self, predictions):
        for imageIndex, prediction in predictions.iteritems():
            if prediction is None:
                continue
            #if self.classCount>prediction.shape[1]:
            #    raise RuntimeError('I got more classes than prediction pixmaps')
            #TODO: The min (and the outcomented error above) is due to some bug, that has to be removed yet
            for classNr in range(min(self.classCount, prediction.shape[1])):
                print "classNr", classNr
                pm = self.rawImage2pixmap(prediction[:, classNr].reshape(self.imageShapes[imageIndex]), QtGui.QColor(self.classColors[classNr + 1]), 'continious', 0.7)
                self.predictionPixmaps[imageIndex][classNr][0] = pm 
    
    def updateSegmentationPixmaps(self, segmentations):
        for imageIndex, segmentation in segmentations.iteritems():
            if segmentation is None:
                continue
            pm = self.rawImage2pixmap(segmentation, 1, 'discrete', 1)
            self.segmentationPixmaps[imageIndex][0] = pm
    
    def updateUncertaintyPixmaps(self, uncertainties):
        for imageIndex, uncertainty in uncertainties.iteritems():
            pm = self.rawImage2pixmap(uncertainty.reshape(self.imageShapes[imageIndex]), QtGui.QColor(self.classColors[1]), 'continious', 0.7)
            self.uncertaintyPixmaps[imageIndex][0] = pm 
    
    def showOverlayPixmapByState(self):
        
        imageIndex = self.labelWidget.activeImage  
        
        classes = range(self.classCount)
        
        currentOverlay = self.stateList[self.state][imageIndex]
        
        # Some OVerlays Are For single Classes or all at once, Prediction could be both
        if self.state in ['Prediction']:
            if self.classIndex == -1:
                classes = range(self.classCount)        
            else:
                classes = [classIndex - 1]
            
            self.clearAll()
            for classNr in classes:
                if currentOverlay[classNr][1]:
                    currentOverlay[classNr][1].setPixmap(currentOverlay[classNr][0])
                else:
                    if currentOverlay[classNr][0]:
                        currentOverlay[classNr][1] = self.canvas.addPixmap(currentOverlay[classNr][0])
                        currentOverlay[classNr][1].setZValue(-1)
                        print currentOverlay[classNr][1]
        # Some Overlay which does not depend on the current ClassIndex 
        elif self.state in ['Image']:
            self.clearAll()           
        else:
            self.clearAll()
            if currentOverlay[1]:
                currentOverlay[1].setPixmap(currentOverlay[imageIndex][0])
            else:
                if currentOverlay[0]:
                    currentOverlay[1] = self.canvas.addPixmap(currentOverlay[0])
                    currentOverlay[1].setZValue(-1) 

    def rawImage2pixmap(self, rawImage, classColor, type, opasity=0.7):
        # Used for rawImages in [0,1]
        if type == 'continious':
            # old version of gray-numpy to qimage using qwt
            #image = qwt.toQImage((rawImage*255).astype(numpy.uint8))
            #image = qimage2ndarray.gray2qimage((rawImage*255).astype(numpy.uint8))
            image = vigra.arraytypes.ScalarImage(rawImage).qimage(normalize=(0.0, 1.0))
            for i in range(256):
                col = QtGui.QColor(classColor.red(), classColor.green(), classColor.blue(), i * opasity)
                image.setColor(i, col.rgba())
                
        # Used for images with uint8 indices, like segmentations
        if type == 'discrete':
            # old version of gray-numpy to qimage using qwt
            #image = qwt.toQImage(rawImage.astype(numpy.uint8))
            #image = qimage2ndarray.gray2qimage((rawImage).astype(numpy.uint8))
            image = vigra.arraytypes.ScalarImage(rawImage).qimage(normalize=False)
            classColor = self.classColors
            for i in range(rawImage.max() + 1):
                classColor = QtGui.QColor(self.classColors[i + 1])
                col = QtGui.QColor(classColor.red(), classColor.green(), classColor.blue(), 255 * opasity)
                image.setColor(i, col.rgba())
        
        return QtGui.QPixmap.fromImage(image)
    
    def clearAll(self):
        for imageIndex in self.predictionPixmaps.keys():
            for classNr in range(self.classCount):
                if self.predictionPixmaps[imageIndex][classNr][1]:
                    self.canvas.removeItem(self.predictionPixmaps[imageIndex][classNr][1])
                    self.predictionPixmaps[imageIndex][classNr][1] = False
                                                 
        for imageIndex in self.segmentationPixmaps.keys():
           if self.segmentationPixmaps[imageIndex][1]:
               self.canvas.removeItem(self.segmentationPixmaps[imageIndex][1])
               self.segmentationPixmaps[imageIndex][1] = False
        
        for imageIndex in self.uncertaintyPixmaps.keys():
           if self.uncertaintyPixmaps[imageIndex][1]:
               self.canvas.removeItem(self.uncertaintyPixmaps[imageIndex][1])
               self.uncertaintyPixmaps[imageIndex][1] = False
          
if __name__ == "__main__":
    print "Qt Version: ", QtCore.QT_VERSION_STR
    app = QtGui.QApplication(sys.argv)
    a = labelWidget(None, ['rgb1.jpg', 'rgb2.tif'])
    a.show()
    sys.exit(app.exec_())
