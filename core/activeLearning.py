import numpy

def computeEnsembleMargin(pmap):
    pmap_sort = numpy.sort(pmap, axis=len(pmap.shape)-1)
    res = pmap_sort[:,:,:,:,-1] - pmap_sort[:,:,:,:,-2]
    return 1-res

def computeEnsembleMargin2D(pmap):
    pmap_sort = numpy.sort(pmap, axis=len(pmap.shape)-1)
    res = pmap_sort[:,:,-1] - pmap_sort[:,:,-2]
    return 1-res
