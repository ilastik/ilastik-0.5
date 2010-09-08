import numpy, vigra
import overlayBase
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core.volume import DataAccessor

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
        current_guess = numpy.where(1.0 * self.probabilities[0][key] / (self.probabilities[0][key]+self.probabilities[1][key] + 1e-15) >  (1.0 * self.thresholds[0]/(self.thresholds[0]+self.thresholds[1]+ 1e-15)), 0, 1)
        current_best = self.probabilities[0][key]
        current_best = numpy.where(current_guess < 1, current_best, self.probabilities[1][key])
        for i in range(2,len(self.probabilities)):
            next_guess = numpy.zeros(current_guess.shape, current_guess.dtype)
            if len(next_guess.shape) != 0:
                next_guess[:] = i
                quota_k = 1.0 * current_best / (current_best+self.probabilities[i][key]+ 1e-15)
                quota_other = 1.0 * self.thresholds[current_guess]/(self.thresholds[current_guess]+self.thresholds[next_guess]+ 1e-15)
            else:
                next_guess = i
                quota_k = 1.0 * current_best / (current_best+self.probabilities[i][key]+ 1e-15)
                quota_other = 1.0 * self.thresholds[current_guess]/(self.thresholds[current_guess]+self.thresholds[next_guess]+ 1e-15)
            current_guess = numpy.where( quota_k >  quota_other, current_guess, next_guess)
            next_best = numpy.where(current_guess < i, current_best, self.probabilities[i][key])
            current_best = next_best
            
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
            if isinstance(item.color, int) or isinstance(item.color, long):
                colorTab[index+1] = item.color
            else:
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
        """
        smooth the dataSets before doing the threshold. sad sad world.
        """
        dsets_new = []
        for index, d in enumerate(dsets):
            data = numpy.ndarray(d.shape, 'float32')
            for t in range(d.shape[0]):
                for c in range(d.shape[-1]):
                    if d.shape[-1] > 1:                   
                        dRaw = d[t,:,:,:,c].astype('float32').view(vigra.ScalarVolume)           
                        data[t,:,:,:,c] = vigra.filters.gaussianSmoothing(dRaw, 2.0)
                    else:
                        dRaw = d[t,0,:,:,c].astype('float32').view(vigra.ScalarImage)           
                        data[t,0,:,:,c] = vigra.filters.gaussianSmoothing(dRaw, 2.0) 

            dataAcc = DataAccessor(data)
            dsets_new.append(dataAcc)
            
        self.dsets = dsets_new


    def recalculateThresholds(self):
        thres = []
        for i in range(len(self.dsets)):
            thres.append(1.0 / len(self.dsets))
        self.setThresholds(thres)
        
        
    def setThresholds(self, thresholds):
        self.thresholds = numpy.zeros((len(self.dsets)),'float32' )
        for index, t in enumerate(thresholds):
            self.thresholds[index] = t
