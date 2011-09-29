import numpy, vigra
import os.path
from ilastik.gui import numpy2vtk
import vtk

#*******************************************************************************
# s i z e _ i n _ p i x e l s                                                  *
#*******************************************************************************

class size_in_pixels():
    def __init__(self):
        pass
    
    def getName(self):
        return "size in pixels"
    
    def generateOutput(self, obj_points):
        #generate output for the html table only for one object
        #as it's done row by row
        return str(len(obj_points[0]))

    def cleanUp(self):
        pass

#*******************************************************************************
# c o o r d s                                                                  *
#*******************************************************************************

class coords():
    def __init__(self):
        pass
    def getName(self):
        return "(X, Y, Z)"
    def generateOutput(self, obj_points):
        #take the central scan
        x = min(obj_points[0]) + (max(obj_points[0])-min(obj_points[0]))/2
        y = min(obj_points[1]) + (max(obj_points[1])-min(obj_points[1]))/2
        z = min(obj_points[2]) + (max(obj_points[2])-min(obj_points[2]))/2
        strtowrite = "(" + str(x)+" ,"+str(y)+" ,"+str(z)+")"
        return strtowrite
    
    def cleanUp(self):
        pass
        
#*******************************************************************************
# s l i c e _ v i e w                                                          *
#*******************************************************************************

class slice_view():
    def __init__(self, objects, raw_data, outputdir):
        self.objects = objects
        self.raw_data = raw_data
        self.max_spread_x = 0
        self.max_spread_y = 0
        self.max_spread_z = 0
        for iobj in self.objects.values():
            spread_x = max(iobj[0])-min(iobj[0])
            if self.max_spread_x < spread_x:
                self.max_spread_x = spread_x
            spread_y = max(iobj[1])-min(iobj[1])
            if self.max_spread_y < spread_y:
                self.max_spread_y = spread_y
            spread_z = max(iobj[2])-min(iobj[2])
            if self.max_spread_z < spread_z:
                self.max_spread_z = spread_z
            
        self.max_spread_x = self.max_spread_x/2+10
        self.max_spread_y = self.max_spread_y/2+10
        self.max_spread_z = self.max_spread_z/2+10
        self.counter = 0
        self.outputdir = outputdir
    
    def getName(self):
        return "XY projection" + "<th>" + "XZ projection" + "</th>" + "<th>" + "YZ projection"
        
    def generateOutput(self, obj_points):
        #take the central scan
        x = min(obj_points[0]) + (max(obj_points[0])-min(obj_points[0]))/2
        y = min(obj_points[1]) + (max(obj_points[1])-min(obj_points[1]))/2
        z = min(obj_points[2]) + (max(obj_points[2])-min(obj_points[2]))/2
        minx = max(x-self.max_spread_x, 0)
        maxx = min(x+self.max_spread_x, self.raw_data.shape[1])
        miny = max(y-self.max_spread_y, 0)
        maxy = min(y+self.max_spread_y, self.raw_data.shape[2])
        minz = max(z-self.max_spread_z, 0)
        maxz = min(z+self.max_spread_z, self.raw_data.shape[3])
        image = self.raw_data[0, minx:maxx, miny:maxy, z, 0]
        fnamexy = str(self.counter)+ "_xy"+".png"
        fnamexy = os.path.join(self.outputdir, fnamexy)
        #print fnamexy
        vigra.impex.writeImage(image, fnamexy)
        image = self.raw_data[0, minx:maxx, y, minz:maxz, 0]
        fnamexz = str(self.counter)+"_xz"+".png"
        fnamexz = os.path.join(self.outputdir, fnamexz)
        #print fnamexz
        vigra.impex.writeImage(image, fnamexz)
        image = self.raw_data[0, x, miny:maxy, minz:maxz, 0]
        fnameyz = str(self.counter)+"_yz"+".png"
        fnameyz = os.path.join(self.outputdir, fnameyz)
        #print fnameyz
        vigra.impex.writeImage(image, fnameyz)
        
        self.counter = self.counter+1
        strtowrite = "<img src=\"" + fnamexy + "\"/>"+"</td>"
        strtowrite = strtowrite + "<td align=\"center\">"+"<img src=\"" + fnamexz + "\"/>"+"</td>"
        strtowrite = strtowrite +"<td align=\"center\">"+"<img src=\"" + fnameyz + "\"/>"
        return strtowrite

    def cleanUp(self):
        pass

#*******************************************************************************
# p c _ p r o j e c t i o n _ 3 d                                              *
#*******************************************************************************

class pc_projection_3d():
    def __init__(self, objects, objectsOverlay, objectInputOverlay, outputdir):
        self.objects = objects
        self.objectsOverlay = objectsOverlay
        self.objectsInputOverlay = objectInputOverlay
        self.outputdir = outputdir
        self.counter = 0        
        self.max_spread_x = 0
        self.max_spread_y = 0
        self.max_spread_z = 0
        for iobj in self.objects.values():
            spread_x = max(iobj[0])-min(iobj[0])
            if self.max_spread_x < spread_x:
                self.max_spread_x = spread_x
            spread_y = max(iobj[1])-min(iobj[1])
            if self.max_spread_y < spread_y:
                self.max_spread_y = spread_y
            spread_z = max(iobj[2])-min(iobj[2])
            if self.max_spread_z < spread_z:
                self.max_spread_z = spread_z
        self.max_spread_x = self.max_spread_x/2+10
        self.max_spread_y = self.max_spread_y/2+10
        self.max_spread_z = self.max_spread_z/2
        
    def getName(self):
        return "3d projection"
    
    def generateOutput(self, obj_points):
        x = min(obj_points[0]) + (max(obj_points[0])-min(obj_points[0]))/2
        y = min(obj_points[1]) + (max(obj_points[1])-min(obj_points[1]))/2
        z = min(obj_points[2]) + (max(obj_points[2])-min(obj_points[2]))/2
        
        minx = max(x-self.max_spread_x, 0)
        maxx = min(x+self.max_spread_x, self.objectsInputOverlay._data.shape[1])
        miny = max(y-self.max_spread_y, 0)
        maxy = min(y+self.max_spread_y, self.objectsInputOverlay._data.shape[2])
        minz = max(z-self.max_spread_z, 0)
        maxz = min(z+self.max_spread_z, self.objectsInputOverlay._data.shape[3])
        image_comp = self.objectsInputOverlay._data[0, minx:maxx, miny:maxy, minz:maxz, 0]
        
        value = self.objectsInputOverlay._data[0, obj_points[0][0], obj_points[1][0], obj_points[2][0], 0]
        image = numpy.where(image_comp==value, 1, 0)
        image = image.astype(numpy.uint8)
        
        dataImporter = numpy2vtk.toVtkImageData(image)
        
        cubes = vtk.vtkMarchingCubes()
        cubes.SetInput(dataImporter)
        cubes.SetValue(0, 1)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(cubes.GetOutput())
        mapper.ScalarVisibilityOff()
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 1, 1)
        
        ren = vtk.vtkRenderer()
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(ren)
        ren.AddActor(actor)
        ren.SetBackground(1, 1, 1)
        renWin.SetSize(2*self.max_spread_x, 2*self.max_spread_y)
        #renWin.SetSize(200, 200)
        
        renWin.Render()
        
        w2i = vtk.vtkWindowToImageFilter()
        writer = vtk.vtkPNGWriter()
        w2i.SetInput(renWin)
        w2i.Update()
        writer.SetInput(w2i.GetOutput())
        
        fname = str(self.counter)+".png"
        fname = os.path.join(self.outputdir, fname)

        writer.SetFileName(fname)
        writer.Write()
        
        self.counter = self.counter+1
        
        strtowrite = "<img src=\"" + fname + "\"/>"
        return strtowrite
    
    def cleanUp(self):
        pass
                    