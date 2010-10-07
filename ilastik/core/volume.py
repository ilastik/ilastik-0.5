import numpy, vigra, h5py


"""
helper function to prevent the creation of endless deep DataAccessor chains
"""
def createDataAccessor( data, channels = False,  autoRgb = True):
        if issubclass(data.__class__,  DataAccessor):
            return data
        else:
            return DataAccessor(data, channels, autoRgb)


class DataAccessor():
    """
    This class gives consistent access to _data volumes, images channels etc.
    access is always of the form [time, x, y, z, channel]
    """
    
    def __init__(self, data, channels = False,  autoRgb = True):
        """
        _data should be a numpy/vigra array that transformed to the [time, x, y, z, channel] access like this:
            1d: (a,b), b != 3 and channels = False  (0,0,a,b,0)
            1d: (a,b), b == 3 or channels = True:  (0,0,0,a,b)
            2d: (a,b,c), c != 3 and channels = False:  (0,a,b,c,0)
            2d: (a,b,c), c == 3 or channels = True:  (0,0,a,b,c)
            etc.
        """
        
        if issubclass(data.__class__,  DataAccessor):
            self._data = data._data
            self.rgb = data.rgb
            self.shape = data.shape
            self.dtype = data.dtype
        else:

            if len(data.shape) == 5:
                channels = True
                
            if issubclass(data.__class__, DataAccessor):
                data = data._data
                channels = True
            
            rgb = 1
            if data.shape[-1] == 3 or channels:
                rgb = 0

            tempShape = data.shape

            self._data = data

            if issubclass(data.__class__, vigra.arraytypes._VigraArray):
                for i in range(len(data.shape)/2):
                    #self._data = self._data.swapaxes(i,len(_data.shape)-i)
                    pass
                self._data = self._data.view(numpy.ndarray)
                #self._data.reshape(tempShape)


            for i in range(5 - (len(data.shape) + rgb)):
                tempShape = (1,) + tempShape
                
            if rgb:
                tempShape = tempShape + (1,)
            
            if len(self._data.shape) != 5:
                self._data = self._data.reshape(tempShape)
                
            self.channels = self._data.shape[-1]

            self.rgb = False
            if autoRgb:
                if data.shape[-1] == 3:
                    self.rgb = True

            self.shape = self._data.shape
            self.dtype = self._data.dtype


    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, data):
        self._data[key] = data

    def getSlice(self, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                return self._data[time, num, :,: , :]
            elif axis == 1:
                return self._data[time, :,num,: , :]
            elif axis ==2:
                return self._data[time, :,: ,num,  :]
        else:
            if axis == 0:
                return self._data[time, num, :,: , channel]
            elif axis == 1:
                return self._data[time, :,num,: , channel]
            elif axis ==2:
                return self._data[time, :,: ,num,  channel]
            

    def setSlice(self, data, num, axis, time = 0, channel = 0):
        if self.rgb is True:
            if axis == 0:
                self._data[time, num, :,: , :] = data
            elif axis == 1:
                self._data[time, :,num,: , :] = data
            elif axis ==2:
                self._data[time, :,: ,num,  :] = data
        else:        
            if axis == 0:
                self._data[time, num, :,: , channel] = data
            elif axis == 1:
                self._data[time, :,num,: , channel] = data
            elif axis ==2:
                self._data[time, :,: ,num,  channel] = data

    def getSubSlice(self, offsets, sizes, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+sizes[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+sizes[1]

        if self.rgb is True:
            if axis == 0:
                return self._data[time, num, ax0l:ax0r,ax1l:ax1r , :]
            elif axis == 1:
                return self._data[time, ax0l:ax0r, num,ax1l:ax1r , :]
            elif axis ==2:
                return self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  :]
        else:
            if axis == 0:
                return self._data[time, num, ax0l:ax0r,ax1l:ax1r , channel]
            elif axis == 1:
                return self._data[time, ax0l:ax0r, num,ax1l:ax1r , channel]
            elif axis ==2:
                return self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel]
            

    def setSubSlice(self, offsets, data, num, axis, time = 0, channel = 0):
        ax0l = offsets[0]
        ax0r = offsets[0]+data.shape[0]
        ax1l = offsets[1]
        ax1r = offsets[1]+data.shape[1]

        if self.rgb is True:
            if axis == 0:
                self._data[time, num,  ax0l:ax0r, ax1l:ax1r , :] = data
            elif axis == 1:
                self._data[time, ax0l:ax0r,num, ax1l:ax1r , :] = data
            elif axis ==2:
                self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  :] = data
        else:
            if axis == 0:
                self._data[time, num,  ax0l:ax0r, ax1l:ax1r , channel] = data
            elif axis == 1:
                self._data[time, ax0l:ax0r,num, ax1l:ax1r , channel] = data
            elif axis ==2:
                self._data[time, ax0l:ax0r, ax1l:ax1r ,num,  channel] = data
     
    def serialize(self, h5G, name='data', destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0)):
        print self._data.dtype, self._data.shape, destbegin, destend, srcbegin, srcend, destshape
        
        if name not in h5G.keys():
            if destshape != (0,0,0):
                shape = (self._data.shape[0], destshape[0], destshape[1],destshape[2], self._data.shape[-1] )
            else:
                shape = self._data.shape
                
            h5G.create_dataset(name, shape, self._data.dtype)
            
        h5d = h5G[name]
        
        if destend != (0,0,0):
            h5d[:, destbegin[0]:destend[0], destbegin[1]:destend[1], destbegin[2]:destend[2],:] = self._data[:, srcbegin[0]:srcend[0], srcbegin[1]:srcend[1], srcbegin[2]:srcend[2],:]
        else:
            h5d[:,:,:,:,:] = self._data[:,:,:,:,:]
         
    @staticmethod
    def deserialize(h5G, name = 'data', offsets=(0, 0, 0), shape=(0, 0, 0)):
        if (h5G[name].value.shape[1]==1):
            #2d _data
            if shape == (0,0,0):        
                data = h5G[name].value[:,:,offsets[0]:, offsets[1]:, :]
            else:
                data = h5G[name].value[:,:,offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1], :]
        else:
            #3 and more d _data:
            if shape == (0,0,0):        
                data = h5G[name].value[:,offsets[0]:, offsets[1]:, offsets[2]:, :]
            else:
                data = h5G[name].value[:,offsets[0]:offsets[0]+shape[0], offsets[1]:offsets[1]+shape[1], offsets[2]:offsets[2]+shape[2],:]
        return DataAccessor(data, channels = True)
        
class VolumeLabelDescription():
    def __init__(self, name,number, color,  prediction):
        self.number = number
        self.name = name
        self.color = color
        self._prediction = prediction

        
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
        t = VolumeLabelDescription( self.name, self.number, self.color,  self._prediction)
        return t
    
class VolumeLabelDescriptionMgr(list):
    def __init__(self):
        list.__init__(self)

    def getLabelNames(self):
        labelNames = []
        for idx, it in enumerate(self):
            labelNames.append(it.name)
        return labelNames    
        
        
    def getColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0)) #QtGui.QColor(0,0,0,0).rgba()

        for index,item in enumerate(self):
            colorTab[item.number] = long(item.color)
        return colorTab
    
    
    
class VolumeLabels():
    def __init__(self, data = None):
        if issubclass(data.__class__, DataAccessor):
            self._data = data
        else:
            self._data = DataAccessor(data, channels = False)
        self._history = None    #_history of drawing operations
        self.descriptions = [] #array of VolumeLabelDescriptions
        
    def clear(self):
        #TODO: clear the labvles
        pass
        
    def serialize(self, h5G, name, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0) ):
        
        if name not in h5G.keys():
            group = h5G.create_group(name)
        else:
            group = h5G[name]
        
        self._data.serialize(group, 'data', destbegin, destend, srcbegin, srcend, destshape)
        
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
            
        if self._history is not None:
            self._history.serialize(group, '_history')        
            
    def getLabelNames(self):
        labelNames = []
        for idx, it in enumerate(self.descriptions):
            labelNames.append(it.name)
        return labelNames    
        
        
    def getColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0)) #QtGui.QColor(0,0,0,0).rgba()

        for index,item in enumerate(self.descriptions):
            colorTab[item.number] = long(item.color)
        return colorTab
        
    @staticmethod    
    def deserialize(h5G, name ="labels", offsets = (0,0,0), shape=(0,0,0)):
        if name in h5G.keys():
            t = h5G[name]
            if isinstance(t,h5py.highlevel.Group):
                data = DataAccessor.deserialize(t, 'data', offsets, shape)
            else:
                data = DataAccessor.deserialize(h5G, name, offsets, shape)
            colors = []
            names = []
            numbers = []
            if h5G[name].attrs.__contains__('color'):
                colors = h5G[name].attrs['color']
                names = h5G[name].attrs['name']
                numbers = h5G[name].attrs['number']
            descriptions = []
            for index, item in enumerate(colors):
                descriptions.append(VolumeLabelDescription(names[index], numbers[index], colors[index],  numpy.zeros(data.shape[0:-1],  'uint8')))
    
            vl =  VolumeLabels(data)
            vl.descriptions = descriptions
            return vl
        else:
            return None
        
class Volume():
    def __init__(self,  data, seeds = None,  uncertainty = None,  segmentation = None, background = None, objects = None, unsupervised = None):
        self._data = data
        self.shape = data.shape
        self.dtype = data.dtype
        
        #self.labels = labels
        self.seeds = seeds
        self.objects = objects
        
        self.projectOverlays = []
        self.seedOverlays = []
        #self.labelOverlays = []
        self.objectOverlays = []
        self.backgroundOverlays = []
        self.autosegOverlays = []
        self.unsupervisedOverlays = []
        
        self.uncertainty = uncertainty
        self.segmentation = segmentation
        self.background = background
        self.unsupervised = unsupervised
        
#        if self.labels is None:
#            l = numpy.zeros(self._data.shape[0:-1] + (1, ),  'uint8')
#            self.labels = VolumeLabels(l)
            
        if self.seeds is None:
            l = numpy.zeros(self._data.shape[0:-1] + (1, ),  'uint8')
            self.seeds = VolumeLabels(l)

        if self.objects is None:
            l = numpy.zeros(self._data.shape[0:-1] + (1, ),  'uint8')
            self.objects = VolumeLabels(l)

        if self.uncertainty is None:
            self.uncertainty = numpy.zeros(self._data.shape[0:-1],  'uint8')

        if self.segmentation is None:
            self.segmentation = numpy.zeros(self._data.shape[0:-1],  'uint8')

        if self.background is None:
            l = numpy.zeros(self._data.shape[0:-1], 'uint8')
            self.background = VolumeLabels(l)
    
        if self.unsupervised is None:
            self.unsupervised = numpy.zeros(self._data.shape[0:-1],  'uint8')

        #TODO: There should probably be an argument for that in the __init__ to enable reading from file
        #do this along with serialize/deserialize
        #self.selectedObjects = {}
        #self.selectedObjectsOverlay = None

    def serialize(self, h5G, destbegin = (0,0,0), destend = (0,0,0), srcbegin = (0,0,0), srcend = (0,0,0), destshape = (0,0,0)):
        self._data.serialize(h5G, "data", destbegin, destend, srcbegin, srcend, destshape )
        if self.seeds is not None:
            self.seeds.serialize(h5G, "seeds", destbegin, destend, srcbegin, srcend, destshape )
        
    @staticmethod
    def deserialize(dataItemImage, h5G, offsets = (0,0,0), shape=(0,0,0)):
        data = DataAccessor.deserialize(h5G, "data", offsets, shape)
        #seeds = VolumeLabels.deserialize(h5G,  "seeds")
        if "seeds" in h5G.keys():
            seeds = VolumeLabels.deserialize(h5G,  "seeds")
            v =  Volume(data,   seeds = seeds)
        else:
            v =  Volume(data)
        return v


