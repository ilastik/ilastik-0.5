from PyQt4 import QtGui
from PyQt4 import QtCore
import sys, random, numpy
sys.path.append("..")
from core import labelMgr
from gui import qimage2ndarray
import os


#************************

labelwidgetInstance = None   # UGLY global
      

class labelingForOneImage:
    def __init__(self):
        self.DrawManagers = []       # different labeling-types (patch, pixel, geom...)
        self.activeLabel = None
        self.activeDrawManager = None
        
    def addDrawManager(self, dmngr):
        self.DrawManagers.append(dmngr)
        self.activeDrawManager = self.DrawManagers.__len__()-1
        
    def getActiveDrawManager(self):
        return self.DrawManagers[self.activeDrawManager]
        
    def setActiveLabel(self, label):
        self.activeLabel = label
        for dmng in self.DrawManagers:
            dmng.setDrawLabel(label)
        
    def setOpacity(self, op):
        for dmngr in self.DrawManagers:
            dmngr.setDrawOpacity(op)
    
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
            self.pickleinfo_LabelManagers.append( dm.labelmngr )
        cdict = self.__dict__.copy()
        del cdict['DrawManagers']
        return cdict
    
    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.DrawManagers = []
        i=0
        for id in self.pickleinfo_DrawManager_ids:
            dmObject = drawManagerID.drawManagerObject[id]
            lm = self.pickleinfo_LabelManagers[i]
            self.DrawManagers.append(dmObject(lm, labelwidgetInstance.canvas))   # UGLY global
            i+=1
        pass

class drawManager:
    #todo: manage draw-data (topLevelItems, Pixmaps) in a dictionary: seperate labeltypes to make changing [opacity, color, ...] easy.    
    def __init__(self, labelmngr, canvas):
        self.classId = drawManagerID.IDdrawManager
        self.labelmngr = labelmngr
        self.canvas = canvas
        self.undolist = None
        
        self.drawLabel = 0
        self.drawSize = 1
        self.drawColor = QtGui.QColor(255,0,0)
        self.drawOpacity = 1;

        
    # drawSettings:
    def setDrawLabel(self, label):
        self.drawLabel = label
    def setDrawSize(self, size):
        self.drawSize = size
    def setDrawColor(self, color):
        self.drawColor = color
    def setDrawOpacity(self, opacity):
        self.drawOpacity = opacity
        
    def setCanvas(self, canvas):
        self.canvas = canvas
        
    def setUndoList(self, undolist):
        self.undolist = undolist
        
    def repaint(self):
        pass
    
    def canvas_clear(self):
        pass
    
    def canvas_paint(self):
        pass

    def InitDraw(self, pos):
        pass
    
    def DoDraw(self, pos):
        pass
    
    def EndDraw(self, pos):
        pass
    
    def changeSize(self, size):
        pass

class draw_geomObject(drawManager):
    def __init__(self, labelmngr, canvas):
        drawManager.__init__(self, labelmngr, canvas)
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
        self.topLevelItems.append( TopLevelItem() )
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
        
    def addObject(self,pos):
        ell = QtGui.QGraphicsEllipseItem(pos[0], pos[1], self.drawSize, self.drawSize)
        ell.setPen(QtGui.QPen(self.drawColor))
        ell.setBrush(QtGui.QBrush(self.drawColor))
        ell.setParentItem(self.topLevelItems[-1])
      

class draw_Patch(drawManager):
    def __init__(self, labelmngr, canvas):
        drawManager.__init__(self, labelmngr, canvas)
        self.classId = drawManagerID.IDdraw_Patch
        
        self.size = labelmngr.getSize()
        self.image = QtGui.QImage( self.size[0], self.size[1], QtGui.QImage.Format_ARGB32 )

        self.imageItem = ImageItem( self.image)
        self.imageItem.setOpacity(self.drawOpacity)
        canvas.addItem(self.imageItem)
        self.pixelColor = self.drawColor.rgb()
        labelmngr.setDrawCallback(self.setPixel)
        
    def setDrawOpacity(self, opacity):
        drawManager.setDrawOpacity(self, opacity)
        self.imageItem.setOpacity(opacity)
        
    def setDrawLabel(self, label):
        drawManager.setDrawLabel(self, label)
        #todo: manage qimage-Dict for label.
        
    @staticmethod
    def __undoOperation(self):
        pass
    
    def changeSize(self):
        # todo: adjust qimage to new size
        pass
    
    def repaint(self):
        # todo: clear qimage, get labels from labelmngr and paint them.
        pass
        
    def canvas_clear(self):
        #self.imageItem.scene().removeItem(self.imageItem)
        self.canvas.removeItem(self.imageItem)
    
    def canvas_paint(self):
        self.canvas.addItem(self.imageItem)
    
    def InitDraw(self, pos):
        self.startPos = pos
        self.lastPos = pos
        
        self.labelmngr.setLabel(pos, self.drawLabel)
        self.pixelColor = self.drawColor.rgb()
        # todo: create/get qimage for given label and add to self.canvas.
        self.DoDraw(pos)
    
    # callback for label-manager:
    def setPixel(self, pos):
        self.image.setPixel(pos[0], pos[1], self.pixelColor)
        self.imageItem.update()
    
    def DoDraw(self, pos):
        if pos != self.lastPos:
            self.labelmngr.setLabelLine2D(self.lastPos, pos, self.drawLabel)
            self.lastPos = pos
    
    def EndDraw(self, pos):
        self.labelmngr.setLabel(pos, self.drawLabel)
        
class draw_Pixel(draw_Patch):
    def __init__(self, labelmngr, canvas):
        draw_Patch.__init__(self, labelmngr, canvas)
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
        for i in xrange(len(gridDims)-1):
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
        if not name: name = "classname_"+str(self.classes)
        if not color: color = QtGui.QColor(random.random()*255, random.random()*255, random.random()*255)
        if not size: size = random.random()*30
        #self.graphicsItems.append(QtGui.QGraphicsItemGroup())
        self.classNames.append(name)
        self.classColors.append(color)
        self.classSize.append(size)
        self.classes+=1
        

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
        print ""
        
    def addUndoList(self, undolist):
        self.undolist = undolist
        
    def addClass(self, name=None, color=None, size=None):
        if not name: name = "classname_"+str(self.classes)
        if not color: color = QtGui.QColor(random.random()*255, random.random()*255, random.random()*255)
        if not size: size = random.random()*30
        #self.graphicsItems.append(QtGui.QGraphicsItemGroup())
        self.classNames.append(name)
        self.classColors.append(color)
        self.classSize.append(size)
        self.LabelObjects.append([])
        self.classes+=1            
    
    def addLabelObject(self, classnr, item):
        # add topLevelItem to list.
        self.LabelObjects[classnr].append(item)
        item.setOpacity(self.currentOpacity)
        self.undolist.addLabelObject(self, classnr, item)
        
    def removeLabelObject(self, classnr, item):
        self.LabelObjects[classnr].remove(item)
        item.scene().removeItem(item)
        del item
        
    def changeOpacity(self,  classNr, op):
        self.currentOpacity = op
        if self.classes:
            for ob in self.LabelObjects[classNr]:
                ob.setOpacity(op)
        
    def getClassNames(self):
        return self.classNames
    
    def getColor(self,classnr):
        return self.classColors[classnr]
    
    def getSize(self,classnr):
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
                self.imageData = QtGui.QImage(100,100,QtGui.QImage.Format_ARGB32)
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
        print ""
        
        

class displayImageList:
    def __init__(self, Image = None):
        self.list = []
        if isinstance(Image, displayImage): self.list.append(Image)
        if isinstance(Image, str):
            img = DisplayImage(Image)
            self.list.append(img)
        
    def appendImage(self, image):
        if not image: return
        if isinstance(image, displayImage): self.list.append(image)
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
class cloneViewWidget(QtGui.QDockWidget):
    
    def __init_n(self, parent=None, labelwidget=None):
        self.initObject()
    
    def initObject(self):
        self.constructChildren()
        self.initChildren()
        
    
        
    

    
    def __init__(self, parent=None, labelwidget=None):
        QtGui.QWidget.__init__(self, parent)
        self.resize(100,100)
        self.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.RightDockWidgetArea| QtCore.Qt.TopDockWidgetArea| QtCore.Qt.LeftDockWidgetArea)
        self.insidewidget = QtGui.QWidget()
        self.setWidget(self.insidewidget)

        #self.view = panView()
        self.labelwidget = labelwidget
        self.view = QtGui.QGraphicsView()
        self.sceneToDraw = self.labelwidget.view.scene()
        self.sceneitem = SceneItem(self.sceneToDraw)
        self.par = parent

        self.col = QtGui.QColor(255,0,0)
        self.roi = QtGui.QGraphicsRectItem()
        self.roi.setPen(QtGui.QPen(self.col))
        #self.roi.setBrush(QtGui.QBrush(self.col))
        self.roi.setZValue(1)

        self.scene = QtGui.QGraphicsScene()
        self.scene.addItem(self.roi)
        self.scene.addItem(self.sceneitem)

        self.view.setScene(self.scene)
        #self.view.scale(0.2,0.2)
        lo = QtGui.QHBoxLayout()
        lo.addWidget(self.view)
        self.insidewidget.setLayout(lo)
        self.oldZoomingview = None
        
        self.view.setSceneRect(self.sceneToDraw.sceneRect())
        
    def saveLayout(self, storage):
        print "save cloneView"
        oAttributeList = []
        oAttributeValueList = []

        ci = []
        ci.append(hash(self.par))
        ci.append(hash(self.labelwidget))
        storage.constructInfoDict[ hash(self) ] = ci
        
        storage.recurseSave(self, oAttributeList, oAttributeValueList)
    
    @staticmethod
    def generateObj(storage):
        ci=storage.constructInfoDict[  storage.idList[storage.index]  ]
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

    def addScene(self,scene):
        if scene:
            self.sceneToDraw=scene
            self.view.setScene(self.scene)
            
        
class labelWidget(QtGui.QWidget):
    def __init__(self, parent=None, imageList=None):
        QtGui.QWidget.__init__(self, parent)
        global labelwidgetInstance          # UGLY global
        labelwidgetInstance = self          # UGLY global
        self.project = None
        if isinstance(imageList,str): imageList = [imageList]
        if isinstance(imageList,list):
            dpil = displayImageList()
            for item in imageList:
                dpil.appendImage(item)
            imageList = dpil
        if not imageList:
            dpi = displayImage('test.tif', self)
            imageList = displayImageList(dpi)
        
        self.labelForImage = {}
        self.predictions = {}                # predictions[imageNr]
        self.cloneviews = []
        self.overlayPixmapItems = []
        
        self.imageList = imageList
        self.activeImage = 0
        self.activeLabel = 1
        self.image = imageList.list[self.activeImage]
        self.imageData = None
        self.pixmapitem = None
        
        
        self.initCanvas()
        self.canvas.setClass(0)
        self.makeView()
        
        self.cmbImageList = QtGui.QComboBox()
        self.connect(self.cmbImageList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeImage)
        
        self.btnUndo = QtGui.QPushButton("Undo")
        self.connect(self.btnUndo,QtCore.SIGNAL("clicked()"), self.undo)
        
        self.cmbChannelList = QtGui.QComboBox()
        
        self.cmbClassList = QtGui.QComboBox()
        self.connect(self.cmbClassList, QtCore.SIGNAL("currentIndexChanged(int)"), self.changeClass)
        
        self.btnCloneView = QtGui.QPushButton("clone View")
        self.connect(self.btnCloneView, QtCore.SIGNAL("clicked()"), self.makeCloneView)
        
        layout_lists = QtGui.QGridLayout()
        layout_lists.addWidget(self.cmbImageList,2,1)
        layout_lists.addWidget(self.cmbChannelList,2,2)
        layout_lists.addWidget(self.cmbClassList,2,3)
        layout_lists.addWidget(self.btnUndo,2,4)
        layout_lists.addWidget(self.btnCloneView,2,5)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(layout_lists)
        
        #self.view2 = QtGui.QGraphicsView()
        #self.sceneitem = SceneItem(self.view.scene())
        #self.scene2 = QtGui.QGraphicsScene()
        #self.scene2.addItem(self.sceneitem)
        #self.view2.setScene(self.scene2)
        ##self.view2.fitInView(self.view2.sceneRect())
        #self.view2.scale(0.2,0.2)
        #layout.addWidget(self.view2)
        
        self.setLayout(layout)
        
       
        
        # debug
        #self.image.label.addClass()
        #self.image.label.addClass()
        #self.image.label.addClass()
        #self.image.label.addClass("Klasse ", QtGui.QColor(0,255,0), 10)
        #self.updateClassList()
        for img in self.imageList.list:
            img.label.addClass()
            img.label.addClass()
            img.label.addClass()
            img.label.addClass("Klasse ", QtGui.QColor(0,255,0), 10)
        #self.updateClassList()
        self.pixmapitem = None
        self.changeImage(0)
        
        self.sldOpacity = QtGui.QSlider()
        self.sldOpacity.setMinimum(0)
        self.sldOpacity.setMaximum(100)
        self.sldOpacity.setOrientation(QtCore.Qt.Horizontal)
        self.sldOpacity.setValue(25)
        self.changeOpacity(25)      
        self.connect(self.sldOpacity, QtCore.SIGNAL("valueChanged(int)"), self.changeOpacity)
        layout_lists.addWidget(self.sldOpacity,3,3)
        try:
            self.updateProject( self.parent().project)
        except AttributeError:
            pass
        
    def addOverlayPixmap(self, pm):
        if isinstance(pm, numpy.ndarray):
            img = qimage2ndarray.numpy2qimage(pm)
            pm = QtGui.QPixmap.fromImage(img)
        pi = self.canvas.addPixmap(pm)
        self.overlayPixmapItems.append( pi )
        return pi
    def drawOverlayPixmaps(self):
        for pi in self.overlayPixmapItems:
            self.canvas.addItem(pi)
    def removeOverlayPixmap(self, pixmapItem):
        self.overlayPixmapItems.remove(pixmapItem)
        self.canvas.removeItem(pixmapItem)
        
    def predictionImage_add(self, dataItemIndex, classnr, predictionMatrix):
        if not self.predictions.get(dataItemIndex, None):
            self.predictions[dataItemIndex] = {}
        if self.predictions[dataItemIndex].get(classnr, None):
            self.canvas.removeItem( self.predictions[dataItemIndex][classnr] )
        classColor = QtGui.QColor.fromRgb( self.parent().parent().project.labelColors.get(classnr,0) )
        gray = numpy.require(predictionMatrix, numpy.uint8, 'C') * 255
        h, w = gray.shape
        image = QtGui.QImage(gray.data, w, h, QtGui.QImage.Format_Indexed8)
        image.ndarray = gray
        col = classColor
        print "r: %i, g: %i, b: %i" % (col.red(), col.green(), col.blue() )
        for i in range(256):
            col = classColor.darker((256-i)*100)
            print "r: %i, g: %i, b: %i" % (col.red(), col.green(), col.blue() ) 
            image.setColor(i, classColor.darker(i*10).rgb() )
        print gray
        pm = QtGui.QPixmap.fromImage(image)
        self.predictions[dataItemIndex][classnr] = self.canvas.addPixmap(pm)
        self.predictions[dataItemIndex][classnr].setZValue(-2)
        
    def predictionImage_setOpacity(self, dataItemIndex, classnr, opacity):
        if not self.predictions.get(dataItemIndex, None):
            return
        if not self.predictions[dataItemIndex].get(classnr, None):
            return
        self.predictions[dataItemIndex][classnr].setOpacity(opacity)
        
    def predictionImage_remove(self, dataItemIndex, classnr):
        if not self.predictions.get(dataItemIndex, None):
            return
        if not self.predictions[dataItemIndex].get(classnr, None):
            return
        self.canvas.removeItem(self.predictions[dataItemIndex][classnr])
    
    def predictionImage_clearAll(self):
        print self.predictions
        for key, val in self.predictions.items():
            for key2, val2 in val.items():
                self.canvas.removeItem(val2)
        
    def saveLayout(self, storage):
        print "save labelWidget"
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
            self.labelForImage[self.activeImage].setOpacity(op/100.0)
        
    def updateProject(self, project):
        self.project = project
        self.loadImageList()
        self.loadLabelList()
        self.updateDrawSettings()
        project.dataMgr.labels = self.labelForImage
        print project.dataMgr.labels
        self.labelForImage = project.dataMgr.labels
        
    def updateDrawSettings(self):
        pass 
        
    def loadImageList(self):
        self.cmbImageList.clear()
        imagenames = [os.path.basename(item.fileName) for item in self.project.dataMgr.dataItems]
        self.cmbImageList.addItems(imagenames)
        
    def loadLabelList(self):
        self.cmbClassList.clear()
        self.cmbClassList.addItems(self.project.labelNames)

    def getLabel(self, imageNr, pos):
        lfi = self.labelForImage.get(imageNr, None)
        if not lfi:
            return
        return lfi.getLabelValue(pos)
    
    def changeImage(self, nr):
        self.predictionImage_remove(self.activeImage, self.activeLabel)
        
        if not self.project: return
        #self.imageList.freeImageData(self.activeImage)
        #self.imageList.removeUser(self.activeImage, self)
        #for labelClass in self.image.label.LabelObjects:
        #    for tli in labelClass:
        #        self.canvas.removeItem(tli)
        
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].canvas_clear()
        
        self.activeImage = nr
        #self.image = self.imageList.list[self.activeImage]
        #self.imageData = self.imageList.getImageData(self.activeImage)
        #self.imageList.addUser(self.activeImage, self)
        if self.pixmapitem:
            self.canvas.removeItem(self.pixmapitem)

        #try:
        #    self.img = QtGui.QImage(100,100,QtGui.QImage.Format_ARGB32)
        #    self.img.load(self.project.dataMgr.dataItems[nr].fileName)
        #except Exception, inst:
        #    print "displayImage.__loadImage: Fehler beim Laden: ", inst
        
        # todo: use data-manager instance of vigra-image
        self.img = qimage2ndarray.numpy2qimage(self.project.dataMgr[nr].data)
        
        pm = QtGui.QPixmap.fromImage(self.img)
        
        self.pixmapitem = self.canvas.addPixmap(pm)
        self.pixmapitem.setZValue(-2)
        
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].canvas_paint()
        else:
            self.labelForImage[nr] = labelingForOneImage()
            self.labelForImage[nr].setActiveLabel(0)
            labelManager = labelMgr.label_Pixel([self.pixmapitem.pixmap().width(), self.pixmapitem.pixmap().height()])
            drawManager = draw_Pixel(labelManager, self.canvas)
            self.labelForImage[self.activeImage].addDrawManager( drawManager ) 
        
        #self.canvas.setLabelObject(self.image.label)
        #self.updateClassList()
        
        #for labelClass in self.image.label.LabelObjects:
        #    for tli in labelClass:
        #        #tli.setZValue(1000)
        #        self.canvas.addItem(tli)
        self.changeClass(self.cmbClassList.currentIndex() )
                    

    def updateClassList(self):
        self.cmbClassList.clear()
        self.cmbClassList.addItems(self.image.label.getClassNames())
        
    def changeClass(self, nr):
        self.activeLabel = nr
        nr+=1  # 0 is unlabeled !!
        if self.labelForImage.get(self.activeImage, None):
            self.labelForImage[self.activeImage].setActiveLabel(nr)
        self.emit( QtCore.SIGNAL("labelChanged"), nr)

                
    def undo(self):
        self.image.undolist.undo()
        
    def makeView(self):
        #self.view = QtGui.QGraphicsView()
        self.view = panView()
        self.view.setScene(self.canvas)
        
    def makeCloneView(self):
        par = self.parent()
        if par: par = par.parent()
        cv = cloneViewWidget(par, self)
        self.cloneviews.append(cv)
        cv.connectROISignal(self.view)
        self.view.requestROIupdate()
        if par.__class__.__name__ == 'MainWindow':
            #par.addWidgetToDock(cv, QtCore.Qt.BottomDockWidgetArea, "Clone View")
            dock=par.addDockWidget(QtCore.Qt.BottomDockWidgetArea, cv)
            #dock.setObjectName('cloneView_'+hash(dock))
        else:
            cv.show()

class TopLevelItem(QtGui.QGraphicsItem):
    def __init__(self):
        QtGui.QGraphicsItem.__init__(self)
    def boundingRect(self):
        return QtCore.QRectF(0,0,0,0)
    def paint(self, painter, option, widget):
        return

class ImageItem(QtGui.QGraphicsItem):
    def __init__(self, image = None):
        QtGui.QGraphicsItem.__init__(self)
        self.setImage(image)

    def boundingRect(self):
        if self.image:
            return QtCore.QRectF(self.image.rect())
        else:
            return QtCore.QRectF(0,0,0,0)

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
            painter.drawImage( self.image.rect(), self.image  )
            #print "painting.."

class SceneItem(QtGui.QGraphicsItem):
    def __init__(self, scene = None):
        QtGui.QGraphicsItem.__init__(self)
        self.addScene(scene)

    def boundingRect(self):
        if self.sceneToDraw:
            return self.sceneToDraw.sceneRect()
        else:
            return QtCore.QRectF(0,0,0,0)

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
        
    def scrollContentsBy(self, dx, dy):
        QtGui.QGraphicsView.scrollContentsBy(self, dx, dy)
        self.requestROIupdate()                 # todo: inlining, no function?

    def mousePressEvent(self, event):
        self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
        QtGui.QGraphicsView.mousePressEvent(self, event)
        if event.button() == QtCore.Qt.MidButton and not(event.modifiers() & QtCore.Qt.ControlModifier):
            self.pan_origin = self.mapToScene( event.pos() )
            self.panning = True
        if event.button() == QtCore.Qt.MidButton and (event.modifiers() & QtCore.Qt.ControlModifier):
            self.zoom_origin = self.mapToScene( event.pos() )
            self.zoom_origmatrix = QtGui.QMatrix(self.matrix())
            self.zooming = True
    
    def requestROIupdate(self):
        rect = self.mapToScene(self.rect())
        viewrect = QtCore.QRectF( rect[0], rect[2])
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
            delta /=500                             # todo: --> unhardcode zoomfactor
            delta += QtCore.QPointF(1,1)
            m = QtGui.QMatrix(self.zoom_origmatrix)
            m.scale(delta.x(), delta.y())
            self.setMatrix(m)
            self.requestROIupdate()                 # todo: inlining, no function?

    def mouseReleaseEvent(self, event):
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)
        if event.button() == QtCore.Qt.MidButton:
            self.panning = False
            self.zooming = False

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
            #self.col = self.labelObject.getColor(self.classNr)
            #self.siz = self.labelObject.getSize(self.classNr)
            #self.topLevelObject = TopLevelItem()
            #self.labelObject.addLabelObject(self.classNr, self.topLevelObject)
            #self.addItem(self.topLevelObject)
            #self.lastPoint = event.scenePos()
            try:
                self.drawManager = self.parent().labelForImage[self.parent().activeImage].getActiveDrawManager()
            except KeyError, AttributeError:
                return

            self.labeling = True
            ##print event.buttons(), " == " ,QtCore.Qt.LeftButton, "=" ,event.button() == QtCore.Qt.LeftButton
            #self.addSomeStuffToCanvas(event.scenePos())
            ##self.makeView()
            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager = self.parent().labelForImage[self.parent().activeImage].getActiveDrawManager()
            #print self.parent().parent().parent()
            try:
                self.drawManager.setDrawColor( QtGui.QColor.fromRgb( self.parent().parent().parent().project.labelColors.get(self.parent().labelForImage[self.parent().activeImage].activeLabel,0) ) )
            except AttributeError:
                pass
            self.drawManager.InitDraw(pos)
         
    def mouseMoveEvent(self, event):
        if (event.buttons() == QtCore.Qt.LeftButton) and self.labeling:
            ##print "Mouse Moving at " ,event.pos()
            #self.addSomeStuffToCanvas(event.scenePos())
            ##self.makeView()
            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager.DoDraw(pos)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.labeling:
            ##print "Mouse Released at " ,event.scenePos()
            pos = [event.scenePos().x(), event.scenePos().y()]
            self.drawManager.EndDraw(pos)
            self.labeling = False
            
    def addSomeStuffToCanvas(self,pos):
        ell = QtGui.QGraphicsEllipseItem(pos.x(), pos.y(), self.siz, self.siz)
        ell.setPen(QtGui.QPen(self.col))
        ell.setBrush(QtGui.QBrush(self.col))
        #self.addItem(ell)
        ell.setParentItem(self.topLevelObject)

        
if __name__ == "__main__":
    print "Qt Version: ", QtCore.QT_VERSION_STR
    app = QtGui.QApplication(sys.argv)
    a = labelWidget(None,['rgb1.jpg','rgb2.tif'])
    a.show()
    sys.exit(app.exec_())