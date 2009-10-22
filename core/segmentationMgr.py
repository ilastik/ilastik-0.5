import numpy

try:
    from vigra import vigranumpycmodule as vm
except ImportError:
    try:
        import vigranumpycmodule as vm
    except ImportError:
        sys.exit("vigranumpycmodule not found!")

class SegmentationBase(object):
    def __init__(self):
        self.smoothing = ''
        pass
    
    def segment(self):
        pass
    
class LocallyDominantSegmentation(SegmentationBase):
    def __init__(self, propmap):
        SegmentationBase.__init__(self)
        self.propmap = propmap.astype(numpy.float32)
        self.smoothing = 'Gaussian'
    
    def segment(self):
        
        if self.smoothing in ['Gaussian']:
            res = numpy.zeros( propmap.shape, dtype=numpy.float32)
            for k in range(0,propmap.shape[2]):
                res[:,:,k] = vm.gaussianSmooth2d(self.propmap[:,:,k])
        
        elif self.smoothing in ['Median']:
            res = numpy.zeros( propmap.shape, dtype=numpy.uint32)
            for k in range(0,propmap.shape[2]):
                res[:,:,k] = vm.gaussianSmooth2d(self.propmap[:,:,k])
        else
            res = self.propmap
         
        classLabel = numpy.argmax(res, axis=2)
        return classLabel
        