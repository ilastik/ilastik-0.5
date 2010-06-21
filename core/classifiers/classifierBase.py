import vigra, numpy

class ClassifierBase(object):
    #human readable information
    name = "Base classifier" 
    description = "virtual base class" 
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    def __init__(self):
        pass

    def train(self, labels, features):
        pass

    def predict(self, features):
        pass

#    @static
#    def settings():
#        pass
#
#    @static
#    def setup():
#        pass