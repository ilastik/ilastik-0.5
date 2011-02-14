from vtk import vtkRenderer, vtkConeSource, vtkPolyDataMapper, vtkActor, \
                vtkImplicitPlaneWidget2, vtkImplicitPlaneRepresentation, \
                vtkObject, vtkPNGReader, vtkImageActor, QVTKWidget2, \
                vtkRenderWindow, vtkOrientationMarkerWidget, vtkAxesActor, \
                vtkTransform, vtkPolyData, vtkPoints, vtkCellArray, \
                vtkTubeFilter, vtkQImageToImageSource, vtkImageImport, \
                vtkDiscreteMarchingCubes, vtkWindowedSincPolyDataFilter, \
                vtkMaskFields, vtkGeometryFilter, vtkThreshold, vtkDataObject, \
                vtkDataSetAttributes, vtkCutter, vtkPlane, vtkPropAssembly, \
                vtkGenericOpenGLRenderWindow, QVTKWidget

from PyQt4.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
                        QSizePolicy, QSpacerItem
from PyQt4.QtCore import SIGNAL

import qimage2ndarray

from numpy2vtk import toVtkImageData

from GenerateModelsFromLabels_thread import *

class QVTKOpenGLWidget(QVTKWidget2):
    wireframe = False
    
    def __init__(self, parent = None):
        QVTKWidget2.__init__(self, parent)

        self.renderer = vtkRenderer()
        self.renderer.SetUseDepthPeeling(1); ####
        self.renderer.SetBackground(1,1,1)
        self.renderWindow = vtkGenericOpenGLRenderWindow()
        self.renderWindow.SetAlphaBitPlanes(True) ####
        self.renderWindow.AddRenderer(self.renderer)
        self.SetRenderWindow(self.renderWindow)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.actors = vtkPropCollection()
        #self.picker = vtkCellPicker()
        #self.picker = vtkPointPicker()
        #self.picker.PickFromListOn()
        
    def registerObject(self, o):
        print "add item to prop collection"
        self.actors.AddItem(o)
        #self.picker.AddPickList(o)

    def resizeEvent(self, event):
        #ordering is important here
        #1.) Let the QVTKWidget2 resize itself
        QVTKWidget2.resizeEvent(self,event)
        
        #2.) Make sure the interactor is assigned a correct new size
        #    This works around a bug in VTK.
        w,h = self.width(), self.height()
        self.w = w
        self.h = h
        self.renderWindow.GetInteractor().SetSize(w,h)
        
    def update(self):
        #for some reason the size of the interactor is reset all the time
        #fix this
        self.renderWindow.GetInteractor().SetSize(self.width(), self.height())
        QVTKWidget2.update(self)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_W:
            self.actors.InitTraversal();
            for i in range(self.actors.GetNumberOfItems()):
                if self.wireframe:
                    "to surface"
                    self.actors.GetNextProp().GetProperty().SetRepresentationToSurface()
                else:
                    self.actors.GetNextProp().GetProperty().SetRepresentationToWireframe()
            self.wireframe = not self.wireframe
            self.update()
    
    def mousePressEvent(self, e):
        if e.type() == QEvent.MouseButtonDblClick:
            print "double clicked"
            #self.picker.SetTolerance(0.05)
            picker = vtkCellPicker()
            #picker.SetTolerance(0.05)
            res = picker.Pick(e.pos().x(), e.pos().y(), 0, self.renderer)
            if res > 0:
                c = picker.GetPickPosition()
                print res, c
                
                #c = [0,0,0,0]
                #vtkInteractorObserver.ComputeDisplayToWorld(self.renderer, e.pos().x(), e.pos().y(), 0, c)
                #print c
                
                self.emit(SIGNAL("objectPicked"), c[0:3])
        else:
            QVTKWidget2.mouseReleaseEvent(self, e)

class Outliner(vtkPropAssembly):
    def SetPickable(self, pickable):
        props = self.GetParts()
        props.InitTraversal();
        for i in range(props.GetNumberOfItems()):
            props.GetNextProp().SetPickable(pickable)
    
    def __init__(self, mesh):
        self.cutter = vtkCutter()
        self.cutter.SetCutFunction(vtkPlane())
        self.tubes = vtkTubeFilter()
        self.tubes.SetInputConnection(self.cutter.GetOutputPort())
        self.tubes.SetRadius(1)
        self.tubes.SetNumberOfSides(8)
        self.tubes.CappingOn()
        self.mapper = vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.tubes.GetOutputPort())
        self.actor = vtkActor()
        self.actor.SetMapper(self.mapper)
        self.cutter.SetInput(mesh)
        self.AddPart(self.actor)
    
    def GetOutlineProperty(self):
        return self.actor.GetProperty()
        
    def SetPlane(self, plane):
        self.cutter.SetCutFunction(plane)
        self.cutter.Update()

class SlicingPlanesWidget(vtkPropAssembly):
    def SetPickable(self, pickable):
        props = self.GetParts()
        props.InitTraversal();
        for i in range(props.GetNumberOfItems()):
            props.GetNextProp().SetPickable(pickable)
    
    def __init__(self, dataShape):
        self.dataShape = dataShape
        self.planes = []
        self.coordinate = [0,0,0]
        self.lastChangedAxis = -1
        for i in range(3):
            p = vtkImplicitPlaneRepresentation()
            p.SetPlaceFactor(1.0)
            p.OutsideBoundsOn()
            p.ScaleEnabledOff()
            p.SetOrigin(0.25,0.25,0.25)
            p.PlaceWidget([0.1,dataShape[0],0.1,dataShape[1],0.1,dataShape[2]])
            if i==0:
                p.SetNormal(1,0,0)
                p.GetSelectedPlaneProperty().SetColor(1,0,0)
                p.GetEdgesProperty().SetColor(1,0,0) #bug in VTK
            elif i==1:
                p.SetNormal(0,1,0)
                p.GetSelectedPlaneProperty().SetColor(0,1,0)
                p.GetEdgesProperty().SetColor(0,1,0) #bug in VTK
            else: 
                p.SetNormal(0,0,1)
                p.GetSelectedPlaneProperty().SetColor(0,0,1)
                p.GetEdgesProperty().SetColor(0,0,1) #bug in VTK
            p.GetPlaneProperty().SetOpacity(0.001)
            #do not draw outline
            p.GetOutlineProperty().SetColor(0,0,0)
            p.GetOutlineProperty().SetOpacity(0.0)
            #do not draw normal
            p.GetSelectedNormalProperty().SetOpacity(0.0)
            p.GetNormalProperty().SetOpacity(0.0)
            p.OutlineTranslationOff()
            p.TubingOff()
            
            self.cross = vtkPolyData()
            points = vtkPoints()
            polys = vtkCellArray()
            points.SetNumberOfPoints(6)
            for i in range(3):
                polys.InsertNextCell(2)
                polys.InsertCellPoint(2*i); polys.InsertCellPoint(2*i+1)
            self.cross.SetPoints(points)
            self.cross.SetLines(polys)
            
            pw = vtkImplicitPlaneWidget2()
            pw.SetRepresentation(p)
            pw.AddObserver("InteractionEvent", self.__PlanePositionCallback)
            
            self.planes.append(pw)
            
        tubes = vtkTubeFilter()
        tubes.SetNumberOfSides(16)
        tubes.SetInput(self.cross)
        tubes.SetRadius(1.0)
        
        crossMapper = vtkPolyDataMapper()
        crossMapper.SetInput(self.cross)
        crossActor = vtkActor()
        crossActor.SetMapper(crossMapper)
        crossActor.GetProperty().SetColor(0,0,0)
        self.AddPart(crossActor)
    
    def Plane(self, axis):
        p = vtkPlane()
        self.planes[axis].GetRepresentation().GetPlane(p)
        return p
    def PlaneX(self):
        return self.Plane(0)
    def PlaneY(self):
        return self.Plane(1)
    def PlaneZ(self):
        return self.Plane(2)
        
    def ShowPlaneWidget(self, axis, show):
        self.planes[axis].SetEnabled(show)
    
    def TogglePlaneWidget(self, axis):
        show = not self.planes[axis].GetEnabled()
        self.planes[axis].SetEnabled(show)
    
    def SetInteractor(self, interactor):
        for i in range(3):
            self.planes[i].SetInteractor(interactor)
            self.planes[i].On()
    
    def GetCoordinate(self):
        return self.coordinate
        
    def SetCoordinate(self, coor):
        self.coordinate = coor
        for i in range(3):
            self.planes[i].GetRepresentation().SetOrigin(coor[0], coor[1], coor[2])
        self.__UpdateCross()
    
    def __UpdateCross(self):
        p = self.cross.GetPoints()
        x,y,z = self.coordinate[0], self.coordinate[1], self.coordinate[2]
        X,Y,Z = self.dataShape[0], self.dataShape[1], self.dataShape[2] 
        p.SetPoint(0,  0,y,z)
        p.SetPoint(1,  X,y,z)
        p.SetPoint(2,  x,0,z)
        p.SetPoint(3,  x,Y,z)
        p.SetPoint(4,  x,y,0)
        p.SetPoint(5,  x,y,Z)
        self.cross.Modified()
    
    def __PlanePositionCallback(self, obj, event):
        newCoordinate = [int(self.planes[i].GetRepresentation().GetOrigin()[i]) \
                         for i in range(3)]
        axis = -1
        for i in range(3):
            if newCoordinate[i] != self.coordinate[i]: axis = i; break
        if axis < 0: return
                         
        self.__UpdateCross()
        self.lastChangedAxis = axis
        self.coordinate = newCoordinate
        #print "__PlanePositionCallback: setting coordinate to", self.coordinate
        self.InvokeEvent("CoordinatesEvent")
   
class OverviewScene(QWidget):
    colorTable = None
    
    def slicingCallback(self, obj, event):
        num = obj.coordinate[obj.lastChangedAxis]
        axis = obj.lastChangedAxis
        #print "OverviewScene emits 'changedSlice(%d,%d)'" % (num,axis)
        self.emit(SIGNAL('changedSlice(int, int)'), num, axis)
    
    def ShowPlaneWidget(self, axis, show):
        self.planes.ShowPlane(axis, show)
        self.qvtk.update()
        
    def TogglePlaneWidgetX(self):
        self.planes.TogglePlaneWidget(0)
        self.qvtk.update()
    def TogglePlaneWidgetY(self):
        self.planes.TogglePlaneWidget(1)
        self.qvtk.update()
    def TogglePlaneWidgetZ(self):
        self.planes.TogglePlaneWidget(2)
        self.qvtk.update()
    
    
    #vtkInteractorStyleTrackballCamera style
    #style AddObserver LeftButtonReleaseEvent cbLBR
    #style AddObserver LeftButtonReleaseEvent {style OnLeftButtonUp}

    #proc cbLBR {} {

    #if {[iren GetRepeatCount] == 1} {
        #eval picker Pick [iren GetEventPosition] 0 ren1
    #}

    #}
    
    def __init__(self, parent, shape):
        super(OverviewScene, self).__init__(parent)
        
        self.anaglyph = False
        self.sceneShape = shape
        self.sceneItems = []
        self.cutter = 3*[None]
        
        layout = QVBoxLayout()
        self.qvtk = QVTKOpenGLWidget()
        #self.qvtk = QVTKWidget()
        layout.addWidget(self.qvtk)
        self.setLayout(layout)
        
        hbox = QHBoxLayout(None)
        b1 = QPushButton("X")
        b1.setCheckable(True); b1.setChecked(True)
        b2 = QPushButton("Y")
        b2.setCheckable(True); b2.setChecked(True)
        b3 = QPushButton("Z")
        b3.setCheckable(True); b3.setChecked(True)
        bAnaglyph = QPushButton("A")
        bAnaglyph.setCheckable(True); bAnaglyph.setChecked(False)
        
        hbox.addWidget(b1)
        hbox.addWidget(b2)
        hbox.addWidget(b3)
        hbox.addStretch()
        hbox.addWidget(bAnaglyph)
        layout.addLayout(hbox)
        
        self.planes = SlicingPlanesWidget(shape)
        self.planes.SetInteractor(self.qvtk.GetInteractor())
        self.planes.AddObserver("CoordinatesEvent", self.slicingCallback)
        self.planes.SetCoordinate([0,0,0])
        self.planes.SetPickable(False)
        
        ## Add RGB arrow axes
        self.axes = vtkAxesActor();
        self.axes.AxisLabelsOff()
        self.axes.SetTotalLength(0.5*shape[0], 0.5*shape[1], 0.5*shape[2])
        self.axes.SetShaftTypeToCylinder()
        #transform = vtkTransform()
        #transform.Translate(-0.125*shape[0], -0.125*shape[1], -0.125*shape[2])
        #self.axes.SetUserTransform(transform)
        self.qvtk.renderer.AddActor(self.axes)
        
        self.qvtk.renderer.AddActor(self.planes)
        self.qvtk.renderer.ResetCamera() 
        
        self.connect(b1, SIGNAL("clicked()"), self.TogglePlaneWidgetX)
        self.connect(b2, SIGNAL("clicked()"), self.TogglePlaneWidgetY)
        self.connect(b3, SIGNAL("clicked()"), self.TogglePlaneWidgetZ)
        self.connect(bAnaglyph, SIGNAL("clicked()"), self.ToggleAnaglyph3D)
        
        self.connect(self.qvtk, SIGNAL("objectPicked"), self.__onObjectPicked)
        
        self.qvtk.renderWindow.GetInteractor().SetSize(self.qvtk.width(), self.qvtk.height())
        
        self.qvtk.setFocus()

    def __onObjectPicked(self, coor):
        self.ChangeSlice( coor[0], 0)
        self.ChangeSlice( coor[1], 1)
        self.ChangeSlice( coor[2], 2)
        
    def __onLeftButtonReleased(self):
        print "CLICK"
    
    def ToggleAnaglyph3D(self):
        self.anaglyph = not self.anaglyph
        if self.anaglyph:
            print 'setting stero mode ON'
            self.qvtk.renderWindow.StereoRenderOn()
            self.qvtk.renderWindow.SetStereoTypeToAnaglyph()
        else:
            print 'setting stero mode OFF'
            self.qvtk.renderWindow.StereoRenderOff()
        self.qvtk.update()
    
    def ChangeSlice(self, num, axis):
        #print "OverviewScene::ChangeSlice"
        c = self.planes.coordinate
        c[axis] = num
        self.planes.SetCoordinate(c)
        for i in range(3):
            if self.cutter[i]: self.cutter[i].SetPlane(self.planes.Plane(i))
        self.qvtk.update()
    
    def display(self, axis):
        self.qvtk.update()
            
    def redisplay(self):
        self.qvtk.update()
        
    def DisplayObjectMeshes(self, v, suppressLabels=()):
        print "OverviewScene::DisplayObjectMeshes", suppressLabels
        self.dlg = MeshExtractorDialog(self)
        self.dlg.extractor.SuppressLabels(suppressLabels)
        self.connect(self.dlg, SIGNAL('done()'), self.onObjectMeshesComputed)
        self.dlg.show()
        self.dlg.run(v)
    
    def SetColorTable(self, table):
        self.colorTable = table
    
    def onObjectMeshesComputed(self):
        self.dlg.accept()
        print "onObjectMeshesComputed"
        g = self.dlg.extractor.meshes[2]
        
        self.polygonAppender = vtkAppendPolyData()
        for g in self.dlg.extractor.meshes.values():
            self.polygonAppender.AddInput(g)
        
        self.cutter[0] = Outliner(self.polygonAppender.GetOutput())
        self.cutter[0].GetOutlineProperty().SetColor(1,0,0)
        self.cutter[1] = Outliner(self.polygonAppender.GetOutput())
        self.cutter[1].GetOutlineProperty().SetColor(0,1,0)
        self.cutter[2] = Outliner(self.polygonAppender.GetOutput())
        self.cutter[2].GetOutlineProperty().SetColor(0,0,1)
        for c in self.cutter:
            c.SetPickable(False)

        self.qvtk.renderer.AddActor(self.cutter[0])
        self.qvtk.renderer.AddActor(self.cutter[1])
        self.qvtk.renderer.AddActor(self.cutter[2])
        
        ## 1. Use a render window with alpha bits (as initial value is 0 (false)):
        #self.renderWindow.SetAlphaBitPlanes(True);
        ## 2. Force to not pick a framebuffer with a multisample buffer
        ## (as initial value is 8):
        #self.renderWindow.SetMultiSamples(0);
        ## 3. Choose to use depth peeling (if supported) (initial value is 0 (false)):
        #self.renderer.SetUseDepthPeeling(True);
        ## 4. Set depth peeling parameters
        ## - Set the maximum number of rendering passes (initial value is 4):
        #self.renderer.SetMaximumNumberOfPeels(100);
        ## - Set the occlusion ratio (initial value is 0.0, exact image):
        #self.renderer.SetOcclusionRatio(0.0);

        for i, g in self.dlg.extractor.meshes.items():
            print "xxx", i
            mapper = vtkPolyDataMapper()
            mapper.SetInput(g)
            actor = vtkActor()
            actor.SetMapper(mapper)
            if i>=2:
                self.qvtk.registerObject(actor)
            if self.colorTable:
                c = self.colorTable[i]
                c = QColor.fromRgba(c)
                actor.GetProperty().SetColor(c.red()/255.0, c.green()/255.0, c.blue()/255.0)
            
            self.qvtk.renderer.AddActor(actor)
        
        self.qvtk.update()

if __name__ == '__main__':
    import numpy
    
    def updateSlice(num, axis):
        o.ChangeSlice(num,axis)
    
    from PyQt4.QtGui import QApplication
    import sys, h5py

    app = QApplication(sys.argv)

    o = OverviewScene(None, [100,100,100])
    o.connect(o, SIGNAL("changedSlice(int,int)"), updateSlice)
    o.show()
    o.resize(600,600)
    
    #f=h5py.File("/home/thorben/phd/src/vtkqt-test/seg.h5")
    #seg=f['volume/data'][0,:,:,:,0]
    #f.close()
    
    seg = numpy.ones((120,120,120), dtype=numpy.uint8)
    seg[20:40,20:40,20:40] = 2
    seg[50:70,50:70,50:70] = 3
    seg[80:100,80:100,80:100] = 4
    seg[80:100,80:100,20:50] = 5
    
    colorTable = [qRgb(255,0,0), qRgb(0,255,0), qRgb(255,255,0), qRgb(255,0,255), qRgb(0,0,255), qRgb(128,0,128)]
    o.SetColorTable(colorTable)
    
    QTimer.singleShot(0, partial(o.DisplayObjectMeshes, seg, suppressLabels=(1,)))
    app.exec_()
    

# [vtkusers] Depth peeling not used, but I can't see why.
# http://public.kitware.com/pipermail/vtkusers/2010-August/111040.html
