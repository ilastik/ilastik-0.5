           
#*******************************************************************************
# R a n d o m S e e d                                                          *
#*******************************************************************************

class RandomSeed(object):
    
    randomSeed = None
                
    @classmethod
    def getRandomSeed(cls):
        return cls.randomSeed
    
    @classmethod
    def setRandomSeed(cls, seed):
        cls.randomSeed = seed