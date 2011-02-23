import numpy
import vigra
import threading

#*******************************************************************************
# C l a s s i f i e r B a s e                                                  *
#*******************************************************************************

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
    printLock = threading.Lock()

    #If you want to provide a gui to the user, to set up additional parameter and stuff
    #implement the following settings classmethod in your derived class
    #
    # @classmethod
    #    def settings(cls):
    #        pass
    #
    #Using @classmethod and cls.your_member_variable, you make sure that the
    #change is applies to all current and future instances of the derived
    #class.

    workerNumber = None
    numWorkers = None

    def __init__(self):
        pass

    def setWorker(self, workerNumber, numWorkers):
        """ workerNumber in [0, numWorkers) gives the partition number of this
            particular part."""
        self.workerNumber = workerNumber
        self.numWorkers = numWorkers

    def train(self, labels, features, isInteractive):
        """ train the classifier with column vector of numeric labels and
            feature matrix features. If isInteractive is set, the learning
            should be faster, but is allowed to be less accurate.
            The learning is distributed to multiple threads.
            workerNumber in [0, numWorkers) gives the partition number of this
            particular part."""
             
        pass

    def predict(self, features):
        pass
     
    def serialize(self, h5grp):
        pass

    @classmethod
    def deserialize(cls, h5G):
        """Reimplement this method to load the classifier from the project file
        
           parameters:
           cls: Derived class
           h5G: Name of the group in which the classifier was serialized"""
           
        pass


