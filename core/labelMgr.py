import numpy

class LabelBrushQueueEntry(object):
    """Label queue entry to get undo information and for online learning"""
    def __init__(self, NewLabel, ImageID):
        self.newLabel = NewLabel
        self.imageID = ImageID
        self.positions = []
        self.oldValues = []
        self.isUndo = False
        
    def finalize(self):
        self.positions = numpy.array(self.positions).astype(numpy.uint32)
        self.oldValues = numpy.array(self.oldValues).astype(numpy.uint32)
        

class label_Base:
    """ label structure
    convention for label values: 0 is unlabeled, first label is 1 and so on.
    """
    def __init__(self, size):
        self.classId = labelManagerID.IDlabel_Base
        self.size = size
        self.dims = size.__len__()
        self.rad = 1 # todo: hack.... add settings-class
        self.drawCallback = None
        
        self.undoDescriptions = []
    
    def __getstate__(self):
        self.drawCallback = None
        return self.__dict__
        
    def __setstate__(self, dict):
        self.__dict__.update(dict)
        
    def undoPush(self, undoPointDescription):
        self.undoDescriptions.append(undoPointDescription)
    
    def undo(self):
        pass
        
    def setDrawCallback(self, callback):
        self.drawCallback = callback
        
    def setPaintRad(self, rad):
        self.rad = rad
    
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
        if (self.drawCallback != None):
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
        self.classId = labelManagerID.IDlabel_Patch
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
        #self.lastPatchNr = self.getPatchNrFromPosition(pos)
        #self.labelArray[ self.lastPatchNr ] = label
        #label_Base.setLabel(self, pos, label)
        rad = self.rad # TODO: hack.... add settings-class
        t = rad**2
        for x in xrange(int(pos[0]-rad), int(pos[0]+rad)):
            for y in xrange(int(pos[1]-rad), int(pos[1]+rad)): 
                if (x-pos[0])**2 + (y-pos[1])**2 < t:
                    if x > -1 and y > -1 and x < self.size[0] and y < self.size[1]:
                        self.lastPatchNr = self.getPatchNrFromPosition([x,y])
                        oldLabel = self.labelArray[self.lastPatchNr]
                        self.labelArray[ self.lastPatchNr ] = label
                        label_Base.setLabel(self, [x,y], label)
                        
                        if oldLabel != self.currentBrushQueueEntry.newLabel:
                            self.currentBrushQueueEntry.positions.append(self.lastPatchNr)
                            self.currentBrushQueueEntry.oldValues.append(oldLabel)
            
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
        for x in range(int(x0), int(x1 + 1)): # TODO We add 1 to x1 so that the range includes x1
            if steep:
                self.setLabel((y, x), label)
            else:
                self.setLabel((x, y), label)
            error = error + deltay
            if error > 0:
                y = y + ystep
                error = error - deltax

        
    def getLabel(self, pos):
        #print "pos: ", pos, "patchNr: ", self.getPatchNrFromPosition(pos), "size: ", self.size, "shape: ", self.labelArray.shape
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
        self.classId = labelManagerID.IDlabel_Grid

class label_Pixel(label_Grid):
    def __init__(self, size):
        label_Patch.__init__(self, size)
        self.classId = labelManagerID.IDlabel_Pixel
        self.undoIndices = []
        self.undoValues = [] 
           
    def init_storage(self):
        #self.labelArray = numpy.ndarray(self.getPatchCount())
        self.labelArray = numpy.zeros(self.getPatchCount())
        self.undoLabelArray_lastState = self.labelArray.copy()
    
    
    # todo: move all undo-stuff one or two levels up to grid or patch
    def undo(self, step):
        # TODO: Move 2 Classes up
        self.labelArray[step.positions] = step.oldValues
        
#        if len(self.undoIndices)<1:
#            print "nothing to undo"
#            return
#        ind = self.undoIndices.pop()
#        values = self.undoValues.pop()
#        self.labelArray[ind]-=values
#        self.undoLabelArray_lastState = self.labelArray.copy()
    
    def undoPush(self, undoPointDescription):
        label_Base.undoPush(self, undoPointDescription)
        diff = self.labelArray - self.undoLabelArray_lastState
        ind = diff.nonzero()
        self.undoIndices.append(ind)
        self.undoValues.append( diff[ind] )
        self.undoLabelArray_lastState = self.labelArray.copy()
        
    def getPatchNrFromPosition(self, pos):
        nr = 0
        blocksize = 1
        for i in xrange(self.dims):
            #attrnr = ord("x")
            #if hasattr(pos, chr(attrnr)):
            #nr += blocksize * getattr(pos, chr(attrnr))
            nr += blocksize * pos[i]
            blocksize *= self.size[i]
        return nr
            
    def getPositionFromPatchNr(self, nr):
        pass
    
    def getPatchCount(self):
        cnt = self.size[0]
        for i in xrange(1,self.dims):
            cnt *= self.size[i]
        return cnt
    

class labelManagerID:
    IDlabel_Base = 0
    IDlabel_Patch = 1
    IDlabel_Grid = 2
    IDlabel_Pixel = 3
    labelManagerObject = {
        IDlabel_Base: label_Base,
        IDlabel_Patch: label_Patch,
        IDlabel_Grid: label_Grid,
        IDlabel_Pixel: label_Pixel
    }
# ---------------------------

class labelSettings_base:
    pass

class labelSettings_pixel:
    def __init__(self):
        self.brushSize = 1