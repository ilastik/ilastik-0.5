import numpy
from core import utilities.irange

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
    def __init__(self, sigma=1.0, smoothing='Gaussian'):
        SegmentationBase.__init__(self)
        self.smoothing = smoothing
        self.sigma = sigma
    
    def segment(self, propmap):
        if not propmap.dtype == numpy.float32:
            propmap = propmap.astype(numpy.float32)
        if self.smoothing in ['Gaussian']:
            res = numpy.zeros( propmap.shape, dtype=numpy.float32)
            for k in range(0, propmap.shape[2]):
                res[:,:,k] = vm.gaussianSmooth2d(propmap[:,:,k], self.sigma)
        else:
            print "Invalid option for smoothing: %s" % self.smoothing
            return None
         
        self.result = numpy.argmax(res, axis=2)

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 
        