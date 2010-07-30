import vigra, numpy

class ClassifierBase(object):
    #human readable information
    name = "Base classifier" 
    description = "virtual base class" 
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    #minimum required isotropic context
    #0 means pixel based classification
    #-1 means whole dataset
    minContext = 0

    #If you want to provide a gui to the user, to set up additional parameter and stuff
    #implement the following settings classmethod in your derived class

#    @classmethod
#    def settings(cls):
#        pass


    def __init__(self):
        pass

    def train(self, labels, features):
        pass

    def predict(self, features):
        pass
    
#    def serialize(self, h5grp):
#        pass
#
#    @classmethod
#    def deserialize(cls, h5grp):
#        pass


