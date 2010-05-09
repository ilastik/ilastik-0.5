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
    

   
def LocallyDominantSegmentation(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)

    res = numpy.zeros( propmap.shape, dtype=numpy.float32)
    for k in range(propmap.shape[-1]):
        #TODO: time !!!
        if propmap.shape[1] == 1:
            res[0,0,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,0,:,:,k], sigma)
        else:
            res[0,:,:,:,k] = vigra.filters.gaussianSmoothing(propmap[0,:,:,:,k], sigma)

    return  numpy.argmax(res, axis=len(propmap.shape)-1) + 1


def LocallyDominantSegmentation2D(propmap, sigma = 2.0):
    if not propmap.dtype == numpy.float32:
        propmap = propmap.astype(numpy.float32)
        
    return  numpy.argmax(propmap, axis=len(propmap.shape)-1) + 1

if __name__ == "__main__":
    a = numpy.random.rand(256,256,4)
    s = LocallyDominantSegmentation()
    r = s.segment(a)
    print r 
        