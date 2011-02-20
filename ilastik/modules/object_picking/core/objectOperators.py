import numpy, vigra
import os.path

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
        
        from enthought.mayavi import mlab
        # Returns the current scene.
        self.scene = mlab.figure(size = (2*self.max_spread_x, 2*self.max_spread_y), bgcolor = (1., 1., 1.))
        
        self.engine = mlab.get_engine()
        
        
    def getName(self):
        return "3d projection"
    
    def generateOutput(self, obj_points):
        from enthought.mayavi.sources.api import ArraySource
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
        
        #image = self.overlay._data[0, minx:maxx, miny:maxy, minz:maxz, 0]
        src = ArraySource(scalar_data=image)
        self.engine.add_source(src)
        

        #axes are needed to get all the images at the same scale
        from enthought.mayavi.modules.api import Axes
        axes = Axes()
        self.engine.add_module(axes)
        
        from enthought.mayavi.modules.api import IsoSurface
        iso = IsoSurface()
        self.engine.add_module(iso)
        iso.contour.contours = [1, 2]
        iso.actor.mapper.scalar_visibility = False
        iso.actor.property.specular_color = (0.58, 0.58, 0.58)
        iso.actor.property.diffuse_color = (0.58, 0.58, 0.58)
        iso.actor.property.ambient_color = (0.58, 0.58, 0.58)
        iso.actor.property.color = (0.58, 0.58, 0.58)
        fname = str(self.counter)+".png"
        fname = os.path.join(self.outputdir, fname)
        from enthought.mayavi import mlab
        azimuth, elevation, d, f = mlab.view()
        el_deg = numpy.rad2deg(elevation)
        az_deg = numpy.rad2deg(azimuth)
        mean = numpy.zeros((1, 3))
        if len(obj_points[0])>100:
            #TODO: This part is not really ready yet, but somehow works
            matr = numpy.array(obj_points)
            matr = matr.transpose()
            mean = numpy.mean(matr, 0)
            meanmatr = numpy.zeros(matr.shape)
            meanmatr[:, 0]=mean[0]
            meanmatr[:, 1]=mean[1]
            meanmatr[:, 2]=mean[2]
            
            matr = matr - meanmatr
            u, s, vh = numpy.linalg.svd(matr, full_matrices=False)            
            
            
            normal_index = numpy.argmin(s)
            normal_vector = vh[normal_index, :]
            elevation = numpy.arccos(normal_vector[2])
            azimuth = numpy.arctan(normal_vector[0]/normal_vector[1])
            el_deg = numpy.rad2deg(elevation)
            az_deg = numpy.rad2deg(azimuth)
            if normal_vector[1]<0 and normal_vector[0]<0:
                az_deg = az_deg + 180
            elif normal_vector[1]<0 and normal_vector[0]>0:
                az_deg = az_deg + 360
            elif normal_vector[1]>0 and normal_vector[0]<0:
                az_deg = az_deg + 180
            
        else:
            pass
        
        #print fname
        #print image.shape
        #a, e, d, f = self.scene.scene.view()
        #print a, e, d, f
        #self.scene.scene.view(azimuth, elevation, d, f)
        
        #mlab.view(numpy.rad2deg(azimuth), numpy.rad2deg(elevation), 'auto', focalpoint=[mean[0], mean[1], mean[2]])
        mlab.view(az_deg, el_deg)
        #self.scene.scene.camera.azimuth(azimuth)
        #self.scene.scene.camera.elevation(elevation)
        
        self.scene.scene.save(fname)
        self.counter = self.counter+1
        src.remove()
        strtowrite = "<img src=\"" + fname + "\"/>"
        return strtowrite
        
    def cleanUp(self):
        from enthought.mayavi import mlab
        mlab.close()
                    