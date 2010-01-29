import numpy


try:
    import vigra
except ImportError:
    sys.exit("vigra module not found!")

class SegmentationBase(object):
    def __init__(self):
        self.smoothing = ''
        pass
    
    def segment(self):
        pass
    
class LocallyDominantSegmentation2D(SegmentationBase):
    def __init__(self, shape, sigma=2.0, smoothing='Gaussian'):
        SegmentationBase.__init__(self)
        self.smoothing = smoothing
        self.sigma = sigma
        self.shape = list(shape[0:2])
        self.shape.append(-1)
        self.result = None
    
    def segment(self, propmap):
        if not propmap.dtype == numpy.float32:
            propmap = propmap.astype(numpy.float32)

        propmap_ = propmap.reshape(self.shape)
        print propmap_.shape
        if self.smoothing in ['Gaussian']:
            res = numpy.zeros( propmap_.shape, dtype=numpy.float32)
            for k in range(0, propmap_.shape[2]):
                res[:,:,k] = vigra.filters.gaussianSmooth2d(propmap_[:,:,k], self.sigma)
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
        