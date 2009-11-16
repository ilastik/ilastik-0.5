import numpy

class EnsembleMargin(object):
    def __init__(self):
        pass
    
    def compute(self, pmap):
        pmap_sort = numpy.sort(pmap, axis=1)
        res = pmap_sort[:,-1] - pmap_sort[:,-2]
        return 1-res

