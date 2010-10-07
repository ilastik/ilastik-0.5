import numpy
import overlayBase
import ilastik.core.overlayMgr as overlayMgr


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
        
        for index, num in enumerate(self.overlay.selectedNumbers):
            answer = numpy.where(input == num, num, answer)
            
        return answer
    
    def __setitem__(self, key, data):
        raise Exception('yeah sure', 'no setting of SelectionAccessor _data')
        

class SelectionOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, inputData, color):
        overlayBase.OverlayBase.__init__(self)
        
        self.color = color
        
        self._data = None

        self.inputData = inputData
        self.selectedNumbers = []
                      
        accessor = SelectionAccessor(self)
        
        self.generateColorTab()
        
        overlayMgr.OverlayItem.__init__(self, accessor, alpha = 1.0, color = self.color, colorTable = self.colorTable, autoAdd = True, autoVisible = True,  linkColorTable = True)        

    def generateColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0))

        for index,item in enumerate(self.selectedNumbers):
                colorTab[item % 256] = self.color

        self.colorTable = colorTab
        
        
    def setSelectedNumbers(self, numbers):
        self.selectedNumbers = numbers
        self.generateColorTab()
