import numpy

class label_Base:
    """ label structure
    convention for label values: 0 is unlabeled, first label is 1 and so on.
    """
    def __init__(self, size):
        self.size = size
        self.dims = size.__len__()
        self.drawCallback = None
        
    def setDrawCallback(self, callback):
        self.drawCallback = callback
    
    def getObjects(self):
        # retruns generator expression of the parameters of label-objects.
        # example:   [ [pos], [pos], [pos], ... ] for pixels
        #            [ [pos,r], [pos,r], [pos,r], ... ] for circles
        #            [ [pos,r1,r2], [pos,r1,r2], [pos,r1,r2], ... ] for ellipses  
        pass
    
    def getLastObject(self):
        # returns label-object that has been added with the previous "setLabel" call
        # todo: remove or convert to return object-stack since last call.
        pass

    def setLabel(self, pos, label):
        if self.drawCallback != None:
            self.drawCallback(pos)
    
    def setLabelLine2D(self, pos1, pos2, label):
        pass
    
    def getLabel(self, pos):
        pass
    
    def getSize(self):
        return self.size

class label_Patch(label_Base):
    def __init__(self, size):
        label_Base.__init__(self, size)
        self.init_storage()
        self.lastPatchNr = 0
        
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
        self.lastPatchNr = self.getPatchNrFromPosition(pos)
        self.labelArray[ self.lastPatchNr ] = label
        label_Base.setLabel(self, pos, label)
        
    def setLabelLine2D(self, pos1, pos2, label):
        (x0, y0) = pos1
        (x1, y1) = pos2
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        if y0 < y1: 
            ystep = 1
        else:
            ystep = -1
        deltax = x1 - x0
        deltay = abs(y1 - y0)
        error = -deltax / 2
        y = y0
        for x in range(x0, x1 + 1): # We add 1 to x1 so that the range includes x1
            if steep:
                self.setLabel((y, x), label)
            else:
                self.setLabel((x, y), label)
            error = error + deltay
            if error > 0:
                y = y + ystep
                error = error - deltax

        
    def getLabel(self, pos):
        return self.labelArray[ self.getPatchNrFromPosition(pos)]
    
    def getObjects(self):
        # use generator expressions for memory efficiency
        len = self.labelArray.__len__()
        for i in xrange(len):
            el = self.labelArray[i]
            if el != 0:
                yield el
                
    def getLastObject(self):
         return self.labelArray[ self.lastPatchNr ]
                    

class label_Grid(label_Patch):
    def __init__(self, size):
        label_Patch.__init__(self, size)
            
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
            blocksize *= self.size[i]
            
    def getPositionFromPatchNr(self, nr):
        pass
    
    def getPatchCount(self):
        cnt = self.size[0]
        for i in xrange(1,self.dims):
            cnt *= self.size[i]
        return cnt
            
            
            