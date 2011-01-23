from vtk import vtkRenderer, vtkConeSource, vtkPolyDataMapper, vtkActor, \
                vtkImplicitPlaneWidget2, vtkImplicitPlaneRepresentation, \
                vtkObject, vtkPNGReader, vtkImageActor, QVTKWidget, \
                vtkRenderWindow, vtkOrientationMarkerWidget, vtkAxesActor, \
                vtkTransform, vtkPolyData, vtkPoints, vtkCellArray, \
                vtkTubeFilter, vtkQImageToImageSource, vtkImageImport, \
                vtkDiscreteMarchingCubes, vtkWindowedSincPolyDataFilter, \
                vtkMaskFields, vtkGeometryFilter, vtkThreshold, vtkDataObject, \
                vtkDataSetAttributes, vtkCutter, vtkPlane, vtkPropAssembly

from PyQt4.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt4.QtCore import SIGNAL
                
import qimage2ndarray

def toVtkImageData(a):
    importer = vtkImageImport()
    importer.SetDataScalarTypeToUnsignedChar()
    importer.SetDataExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
    importer.SetWholeExtent(0,a.shape[0]-1,0,a.shape[1]-1,0,a.shape[2]-1)
    importer.SetImportVoidPointer(a)
    importer.Update()
    return importer.GetOutput()

class Outliner(vtkPropAssembly):
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
    def __init__(self, dataShape):
        self.dataShape = dataShape
        self.planes = []
        self.coordinate = [0,0,0]
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
            pw.AddObserver("InteractionEvent", self.planesCallback)
            
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
        
    def planesCallback(self, obj, event):
        newCoordinate = [self.planes[i].GetRepresentation().GetOrigin()[i] \
                         for i in range(3)]
        if self.coordinate != newCoordinate:
            self.__UpdateCross()
            self.coordinate = newCoordinate
            self.InvokeEvent("CoordinatesEvent")
        
class OverviewScene(QWidget):
    def slicingCallback(self, obj, event):        
        newCoordinate = obj.GetCoordinate()
        oldCoordinate = [-1,-1,-1]
        if self.volumeEditor:
            oldCoordinate = self.volumeEditor.selSlices
        
        for i in range(3):
            if newCoordinate[i] != oldCoordinate[i]:
                if self.volumeEditor:
                    self.volumeEditor.changeSlice(int(newCoordinate[i]), i)
                print "update", i
                self.cutter[i].SetPlane(self.planes.Plane(i))
        self.qvtk.update()
    
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
    
    def __init__(self, parent, shape):
        super(OverviewScene, self).__init__(parent)
        
        self.sceneShape = shape
        self.volumeEditor = parent
        self.sceneItems = []
        self.cutter = 3*[None]
        
        layout = QVBoxLayout()
        self.qvtk = QVTKWidget()
        layout.addWidget(self.qvtk)
        self.setLayout(layout)
        
        hbox = QHBoxLayout(None)
        b1 = QPushButton("X")
        b1.setCheckable(True); b1.setChecked(True)
        b2 = QPushButton("Y")
        b2.setCheckable(True); b2.setChecked(True)
        b3 = QPushButton("Z")
        b3.setCheckable(True); b3.setChecked(True)
        hbox.addWidget(b1)
        hbox.addWidget(b2)
        hbox.addWidget(b3)
        b4 = QPushButton("FS")
        hbox.addWidget(b4)
        layout.addLayout(hbox)
        
        if self.volumeEditor:
            self.connect(b4, SIGNAL("clicked()"), parent.toggleFullscreen3D)
        
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(1,1,1)

        win2 = vtkRenderWindow()
        win2.AddRenderer(self.renderer)
        self.qvtk.SetRenderWindow(win2)

        renwin = self.qvtk.GetRenderWindow()

        self.planes = SlicingPlanesWidget(shape)
        self.planes.SetInteractor(self.qvtk.GetInteractor())

        self.planes.AddObserver("CoordinatesEvent", self.slicingCallback)
        
        ## Add RGB arrow axes
        self.axes = vtkAxesActor();
        self.axes.AxisLabelsOff()
        self.axes.SetTotalLength(0.5*shape[0], 0.5*shape[1], 0.5*shape[2])
        self.axes.SetShaftTypeToCylinder()
        #transform = vtkTransform()
        #transform.Translate(-0.125*shape[0], -0.125*shape[1], -0.125*shape[2])
        #self.axes.SetUserTransform(transform)
        self.renderer.AddActor(self.axes)
        
        self.connect(b1, SIGNAL("clicked()"), self.TogglePlaneWidgetX)
        self.connect(b2, SIGNAL("clicked()"), self.TogglePlaneWidgetY)
        self.connect(b3, SIGNAL("clicked()"), self.TogglePlaneWidgetZ)
        
        #self.planes.SetRenderer(self.renderer)
        self.renderer.AddActor(self.planes)
        self.renderer.ResetCamera() 
    
    def display(self, axis):
        if self.volumeEditor:
            self.planes.SetCoordinate(self.volumeEditor.selSlices)
        self.qvtk.update()
            
    def redisplay(self):
        self.qvtk.update()
        
    def DisplayObjectMeshes(self, v):
        #
        # SEE
        # http://www.vtk.org/Wiki/VTK/Examples/Cxx/Medical/GenerateModelsFromLabels
        #
        
        vol = toVtkImageData(v)
        
        #histogram = vtkImageAccumulate()
        discreteCubes = vtkDiscreteMarchingCubes()
        smoother = vtkWindowedSincPolyDataFilter()
        selector = vtkThreshold()
        scalarsOff = vtkMaskFields()
        geometry = vtkGeometryFilter()

        #http://www.vtk.org/Wiki/VTK/Examples/Cxx/Medical/GenerateModelsFromLabels
        startLabel = 2
        endLabel = 2
        smoothingIterations = 15
        passBand = 0.001
        featureAngle = 120.0

        discreteCubes.SetInput(vol)
        discreteCubes.GenerateValues(endLabel-startLabel+1, startLabel, endLabel)

        smoother.SetInput(discreteCubes.GetOutput())
        smoother.SetNumberOfIterations(smoothingIterations)
        smoother.BoundarySmoothingOff()
        smoother.FeatureEdgeSmoothingOff()
        smoother.SetFeatureAngle(featureAngle)
        smoother.SetPassBand(passBand)
        smoother.NonManifoldSmoothingOn()
        smoother.NormalizeCoordinatesOn()
        smoother.Update()

        selector.SetInput(smoother.GetOutput())
        selector.SetInputArrayToProcess(0, 0, 0,
                                        vtkDataObject.FIELD_ASSOCIATION_CELLS,
                                        vtkDataSetAttributes.SCALARS);

        scalarsOff.SetInput(selector.GetOutput());
        scalarsOff.CopyAttributeOff(vtkMaskFields.POINT_DATA,
                                    vtkDataSetAttributes.SCALARS);
        scalarsOff.CopyAttributeOff(vtkMaskFields.CELL_DATA,
                                    vtkDataSetAttributes.SCALARS);

        geometry.SetInput(scalarsOff.GetOutput())

        selector.ThresholdBetween(2, 2)

        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        
        self.cutter[0] = Outliner(geometry.GetOutput())
        self.cutter[0].GetOutlineProperty().SetColor(1,0,0)
        self.cutter[1] = Outliner(geometry.GetOutput())
        self.cutter[1].GetOutlineProperty().SetColor(0,1,0)
        self.cutter[2] = Outliner(geometry.GetOutput())
        self.cutter[2].GetOutlineProperty().SetColor(0,0,1)

        self.renderer.AddActor(self.cutter[0])
        self.renderer.AddActor(self.cutter[1])
        self.renderer.AddActor(self.cutter[2])

        mapper = vtkPolyDataMapper()
        mapper.SetInput(geometry.GetOutput())
        actor = vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        self.qvtk.update()

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    import sys, h5py

    app = QApplication(sys.argv)

    o = OverviewScene(None, [100,100,100])
    o.show()
    o.resize(600,600)
    
    f=h5py.File("/home/thorben/phd/src/vtkqt-test/seg.h5")
    seg=f['volume/data'][0,:,:,:,0]
    f.close()
    
    o.DisplayObjectMeshes(seg)
    
    app.exec_()