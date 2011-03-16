import numpy
import overlayBase
import ilastik.core.overlayMgr as overlayMgr


#*******************************************************************************
# S e l e c t i o n A c c e s s o r                                            *
#*******************************************************************************

class SelectionAccessor(object):
    def __init__(self, overlay):

        self.overlay = overlay
        self.inputData = self.overlay.inputData
        self.shape = self.inputData.shape
        self.dtype = self.inputData.dtype
        
        
    def __getitem__(self, key):
        input = self.inputData[key]
        
        if isinstance(input, numpy.ndarray):
            answer = numpy.zeros(input.shape, input.dtype)
        else:
            answer = 0
        
        #old version, faster for few selections
        #for index, num in enumerate(self.overlay.selectedNumbers):
        #    answer = numpy.where(input == num, num, answer)
        
        #new version, faster for many selections
        answer = numpy.where(numpy.vectorize(lambda x: x in self.overlay.selectedNumbersSet)(input), input, answer)
            
        return answer
    
    def __setitem__(self, key, data):
        raise Exception('yeah sure', 'no setting of SelectionAccessor _data')
        

#*******************************************************************************
# S e l e c t i o n O v e r l a y                                              *
#*******************************************************************************

class SelectionOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, inputData, color):
        overlayBase.OverlayBase.__init__(self)
        
        self.color = color
        
        self._data = None

        self.inputData = inputData
        self.selectedNumbers = []
        self.selectedNumbersSet = set([])
                      
        accessor = SelectionAccessor(self)
        
        self.generateColorTab()
        
        overlayMgr.OverlayItem.__init__(self, accessor, alpha = 1.0, color = self.color, colorTable = self.colorTable, autoAdd = True, autoVisible = True,  linkColorTable = True)        

    def generateColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0))

        for index,item in enumerate(self.selectedNumbers):
            colorTab[item % 256] = self.color
        colorTab[0]=long(0)
        self.colorTable = colorTab
        
        
    def setSelectedNumbers(self, numbers):
        self.selectedNumbers = numbers
        self.selectedNumbersSet = set(self.selectedNumbers)
        print "Total objects selected: ", len(numbers)
        self.generateColorTab()
