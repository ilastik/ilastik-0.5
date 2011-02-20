import numpy, vigra
import overlayBase
import ilastik.core.overlayMgr as overlayMgr
from ilastik.core.volume import DataAccessor
import datetime

#*******************************************************************************
# M u l t i v a r i a t e T h r e s h o l d A c c e s s o r                    *
#*******************************************************************************

class MultivariateThresholdAccessor(object):
    def __init__(self, thresholdOverlay):

        self.thresholdOverlay = thresholdOverlay        
        self.shape = self.thresholdOverlay.dsets[0].shape
        #self.dtype = self.thresholdOverlay.dsets[0].dtype
        self.dtype = 'uint8'
        
        
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
        raise Exception('yeah sure', 'no setting of multivariathresholdaccessor _data')
        

#*******************************************************************************
# T h r e s h o l d O v e r l a y                                              *
#*******************************************************************************

class ThresholdOverlay(overlayBase.OverlayBase, overlayMgr.OverlayItem):
    def __init__(self, foregrounds, backgrounds, sigma = -1, autoAdd = True, autoVisible = True):
        overlayBase.OverlayBase.__init__(self)
        self._data = None
        if sigma<0:
            self.sigma = 1.5
            self.smoothing = False
        else:
            self.sigma = sigma
            self.smoothing = True
        
        self.dsets = []
        self.foregrounds = []
        self.backgrounds = []
        
        self.setForegrounds(foregrounds)
        self.setBackgrounds(backgrounds)
                      
        accessor = MultivariateThresholdAccessor(self)
        overlayMgr.OverlayItem.__init__(self, accessor, alpha = 1.0, autoAdd = autoAdd, autoVisible = autoVisible,  linkColorTable = True)
        self.linkColorTable = True
        self.color = None
        
    def getColorTab(self):
        colorTab = []
        for i in range(256):
            colorTab.append(long(0))

        for index,item in enumerate(self.foregrounds):
            if item.getColor() is not None:
                colorTab[index+1] = item.getColor()

        return colorTab
    
    def setForegrounds(self, foregrounds):
        b = min(len(self.backgrounds),1)
        
        back = None
        if b > 0:
            back = self.dsets[-1]
        
        dsets = []
        for i,f in enumerate(foregrounds):
            dsets.append(f._data)
        
        if back is not None:
            dsets.append(back)

        self.foregrounds = foregrounds
        self.calculateDsets(dsets, True)
        self.recalculateThresholds() 
        


    def setBackgrounds(self, backgrounds):
        dsets = []
        for index, d in enumerate(self.dsets):
                if index < len(self.foregrounds):
                    dsets.append(d)
                    
        if len(backgrounds)>0:
            background = numpy.zeros(backgrounds[0]._data.shape, backgrounds[0]._data.dtype)
            for b in backgrounds:
                background += b._data[:,:,:,:,:]
            dsets.append(background)
                          
        
        self.backgrounds = backgrounds
        self.calculateDsets(dsets, False)
        self.recalculateThresholds()

    def calculateDsets(self, dsets, new_fg = True):
        """
        eventually smooth the dataSets before doing the threshold. sad sad world.
        no point in re-smoothing the foreground, if only the background has changed
        """
        if self.smoothing is True:   
            dsets_new = []
            #smooth only the foreground!
            for index, d in enumerate(dsets):
                if index < len(self.foregrounds) and new_fg is True:
                    data = numpy.ndarray(d.shape, 'float32')
                    for t in range(d.shape[0]):
                        for c in range(d.shape[-1]):
                            if d.shape[1] > 1:
                                start_time = datetime.datetime.now()           
                                dRaw = numpy.asarray(d[t, :, :, :, c])
                                dRaw = dRaw.swapaxes(0, 2).view()
                                res = vigra.filters.gaussianSmoothing(dRaw, self.sigma)
                                res = res.swapaxes(0, 2).view()
                                data[t, :, :, :, c] = res                                          
                            else:
                                dRaw = d[t,0,:,:,c].astype('float32').view(vigra.ScalarImage)           
                                data[t,0,:,:,c] = vigra.filters.gaussianSmoothing(dRaw, self.sigma)
                    dataAcc = DataAccessor(data)
                    dsets_new.append(dataAcc)
                else:
                    dsets_new.append(d)            
            self.dsets = dsets_new
        else:
            self.dsets = dsets

        
    def setThresholds(self, thresholds):
        if (len(thresholds)==2):
            print "setting probability ratio threshold to: ", thresholds[0]/thresholds[1]
        self.thresholds = numpy.zeros((len(self.dsets)),'float32' )
        for index, t in enumerate(thresholds):
            self.thresholds[index] = t
            
    def recalculateThresholds(self):
        thres = []
        for i in range(len(self.dsets)):
            thres.append(1.0 / len(self.dsets))
        self.setThresholds(thres)
        
