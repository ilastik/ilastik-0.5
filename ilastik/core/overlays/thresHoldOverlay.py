import numpy
import overlayBase
import ilastik.core.overlayMgr as overlayMgr


class MultivariateThresholdAccessor(object):
    def __init__(self, thresholdOverlay):

        self.thresholdOverlay = thresholdOverlay        
        self.shape = self.thresholdOverlay.dsets[0].data.shape
        self.dtype = self.thresholdOverlay.dsets[0].data.dtype
        
        
    def __getitem__(self, key):
        """
        yep, this is ugly and index kung fu, but relatively fast 
        """
        self.probabilities = self.thresholdOverlay.dsets
        self.thresholds = self.thresholdOverlay.thresholds
        current_guess = numpy.where(1.0 * self.probabilities[0][key] / (self.probabilities[0][key]+self.probabilities[1][key]) >  (1.0 * self.thresholds[0]/(self.thresholds[0]+self.thresholds[1])), 0, 1)
        current_best = self.probabilities[0][key]
        current_best = numpy.where(current_guess < 1, current_best, self.probabilities[1][key])
        for i in range(2,len(self.probabilities)):
            next_guess = numpy.zeros(current_guess.shape, current_guess.dtype)
            next_guess[:] = i
            quota_k = current_best / (current_best+self.probabilities[i][key])
            quota_other = self.thresholds[current_guess]/(self.thresholds[current_guess]+self.thresholds[next_guess])
            current_guess = numpy.where( quota_k >  quota_other, current_guess, next_guess)
            current_best = numpy.where(current_guess < i, current_best, self.probabilities[i][key])
            
        answer = current_guess + 1
        return answer
    
    def __setitem__(self, key, data):
        raise Exception('yeah sure', 'no setting of multivariathresholdaccessor data')
        

class ThresHoldOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, foregrounds, backgrounds):
        overlayBase.OverlayBase.__init__(self)
        
        self.data = None
        
        self.dsets = []
        self.foregrounds = []
        self.backgrounds = []
        
        self.setForegrounds(foregrounds)
        self.setBackgrounds(backgrounds)
                      
        accessor = MultivariateThresholdAccessor(self)
        
        self.generateColorTab()
        
        overlayMgr.OverlayItem.__init__(self, accessor, alpha = 1.0, colorTable = self.colorTable, autoAdd = True, autoVisible = True,  linkColorTable = True)        

    def generateColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0))

        for index,item in enumerate(self.foregrounds):
            colorTab[index+1] = long(item.color.rgba())

        self.colorTable = colorTab
        

    
    def setForegrounds(self, foregrounds):
        b = min(len(self.backgrounds),1)
        
        back = None
        if b > 0:
            back = self.dsets[-1]
        
        dsets = []
        for i,f in enumerate(foregrounds):
            dsets.append(f.data)
        
        if back is not None:
            dsets.append(back)

        self.foregrounds = foregrounds
        self.calculateDsets(dsets)
        self.recalculateThresholds() 
        self.generateColorTab()     
            
    def setBackgrounds(self, backgrounds):
        dsets = []
        for i,f in enumerate(self.foregrounds):
            dsets.append(f.data)

        
        if len(backgrounds)>0:
            background = numpy.zeros(backgrounds[0].data.shape, backgrounds[0].data.dtype)
            for b in backgrounds:
                background += b.data[:,:,:,:,:]
            dsets.append(background)
                          
        
        self.backgrounds = backgrounds
        self.calculateDsets(dsets)
        self.recalculateThresholds()
        self.generateColorTab()     

    def calculateDsets(self, dsets):
        self.dsets = dsets


    def recalculateThresholds(self):
        thres = []
        for i in range(len(self.dsets)):
            thres.append(1.0 / len(self.dsets))
        self.setThresholds(thres)
        
        
    def setThresholds(self, thresholds):
        self.thresholds = numpy.zeros((len(self.dsets)),'float32' )
        for index, t in enumerate(thresholds):
            self.thresholds[index] = t
