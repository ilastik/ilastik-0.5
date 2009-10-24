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
    
class LocallyDominantSegmentation2D(SegmentationBase):
    def __init__(self, shape, sigma=1.0, smoothing='Gaussian'):
        SegmentationBase.__init__(self)
        self.smoothing = smoothing
        self.sigma = sigma
        self.shape = list(shape[0:2])
        self.shape.append(-1)
        self.result = None
    
    def segment(self, propmap):
        if not propmap.dtype == numpy.float32:
            propmap = propmap.astype(numpy.float32)
        
        propmap.shape = self.shape
        print propmap.shape
        if self.smoothing in ['Gaussian']:
            res = numpy.zeros( propmap.shape, dtype=numpy.float32)
            for k in range(0, propmap.shape[2]):
                res[:,:,k] = vm.gaussianSmooth2d(propmap[:,:,k], self.sigma)
        else:
            print "Invalid option for smoothing: %s" % self.smoothing
            return None
         
        self.result = numpy.argmax(res, axis=2)
        #vm.writeImage(self.result.astype(numpy.uint8),'c:/il_seg.jpg')

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 
        