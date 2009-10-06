import numpy

class label_Base:
    """ label structure
    convention for label values: 0 is unlabeled, first label is 1 and so on.
    """
    def __init__(self, size):
        self.size = size
        self.dims = size.__len__()
    
    def getObjects(self):
        # retruns generator expression of the parameters of label-objects.
        # example:   [ [pos], [pos], [pos], ... ] for pixels
        #            [ [pos,r], [pos,r], [pos,r], ... ] for circles
        #            [ [pos,r1,r2], [pos,r1,r2], [pos,r1,r2], ... ] for ellipses  
        pass

    def setLabel(self, pos):
        pass
    
    def getLabel(self, pos):
        pass

class label_Patch(label_Base):
    def __init__(self, size):
        label_Base.__init__(self, size)
        self.init_storage()
        
    def init_storage(self):
        self.labelArray = {}   # not sure how this performs. better use special storage like arrays in descendant classes.
        
    def getPatchNrFromPosition(self, pos):
        pass
    
    def getPositionFromPatchNr(self, nr):
        pass
    
    def getPatchCount(self):
        lastpos = []
        for el in self.size:
            lastpos.append(el-1)
        return getPatchNrFromPosition(self, lastpos)
    
    def setLabel(self, pos, label):
        self.labelArray[ self.getPatchNrFromPosition(pos) ] = label
        
    def getLabel(self, pos):
        return self.labelArray[ self.getPatchNrFromPosition(pos)]
    
    def getObjects(self):
        # use generator expressions for memory efficiency
        len = self.labelArray.__len__()
        for i in xrange(len):
            el = self.labelArray[i]
            if el != 0:
                yield el

class label_Grid(label_Patch):
    pass
            
class label_Pixel(label_Grid):
    def __init__(self, size):
        label_Patch.__init__(self, size)
    
    def init_storage(self):
        self.labelArray = numpy.ndarray(self.getPatchCount())
    
    def getPatchNrFromPosition(self, pos):
        nr = 0
        blocksize = 1
        for i in xrange(self.dims):
            #attrnr = ord("x")
            #if hasattr(pos, chr(attrnr)):
            #nr += blocksize * getattr(pos, chr(attrnr))
            nr += blocksize * pos[i]
            blocksize *= self.dims[i]
            
    def getPositionFromPatchNr(self, nr):
        pass
    
    def getPatchCount(self):
        cnt = self.dims[0]
        for i in xrange(1,self.dims):
            cnt *= self.dims[i]
        return cnt
            
            
            