import numpy
import overlayBase
import ilastik.core.overlayMgr


class MultivariateThresholdAccessor(object):
    def __init__(self, probabilities, thresholds):
        self.probabilities = probabilities
        self.thresholds = thresholds
        self.shape = probabilities[0].shape
        self.dtype = probabilities[0].dtype
        
        
    def __getitem__(self, key):
        current_guess = numpy.where(self.probabilities[0][key] / (self.probabilities[0][key]+self.probabilities[1][key]) >  (self.thresholds[0]/(self.thresholds[0]+self.thresholds[1])), 0, 1)
        for i in range(2,len(self.probabilities)):
            next_guess = numpy.zeros(current_guess.shape, current_guess.dtype)
            next_guess[:] = i
            current_guess = numpy.where(self.probabilities[current_guess][key] / (self.probabilities[current_guess][key]+self.probabilities[next_guess][key]) >  (self.thresholds[current_guess]/(self.thresholds[current_guess]+self.thresholds[next_guess])), current_guess, next_guess)
        return current_guess+1

    def setThresholds(self, thresholds):
        self.thresholds = thresholds
    
    def __setitem__(self, key, data):
        raise Exception('lkahsdhsad', 'oiazsdihasdkhaskd')  
        

class ThreshHoldOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, foregrounds, backgrounds):
        overlayBase.OverlayBase.__init__(self)
        overlayMgr.OverlayItem.__init__(data)

        self.foregrounds = foregrounds
        self.backgrounds = backgrounds
        background = numpy.zeros(backgrounds[0].shape, backgrounds[0].dtype)
        for b in backgrounds:
            background += b[:]
        foregrounds.append(background)
        
        thresholds = numpy.zeros((len(foregrounds),),'float32' )
        thresholds[:] = 1.0 / len(foregrounds)
        
        accessor = MultivariateThresholdAccessor(foregrounds, thresholds)
        
        colorTab = []
        for i in range(256):
            colorTab.append(long(0))

        for index,item in enumerate(foregrounds):
            colorTab[index+1] = long(item.color)

        
        overlayMgr.OverlayItem.__init__(self, accessor, alpha = 1.0, colorTable = colorTab, autoAdd = True, autoVisible = True,  linkColorTable = True)
        
        
        