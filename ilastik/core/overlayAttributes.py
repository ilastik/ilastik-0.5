import h5py
import pickle

class OverlayAttributes(object):
    def __init__(self, overlayFile):
        f = h5py.File(overlayFile, 'r')
        dataset = f["volume/data"]
        
        self.prefix = ''
        self.key = "Unknown Key"
        self.color = 0xffff0000L #red
        self.colorTable = None
        self.min = None
        self.max = None
        self.autoVisible = True
        self.autoAdd = True
        self.alpha = 0.5
        
        if "overlayKey" in dataset.attrs.keys():
            self.key = dataset.attrs["overlayKey"]
        
        if "overlayColor" in dataset.attrs.keys():
            self.color = pickle.loads(dataset.attrs["overlayColor"])
            
        if "overlayColortable" in dataset.attrs.keys():
            self.colorTable = pickle.loads(dataset.attrs["overlayColortable"])
        
        if "overlayMin" in dataset.attrs.keys():
            self.min = pickle.loads(dataset.attrs["overlayMin"])
            
        if "overlayMax" in dataset.attrs.keys():
            self.max = pickle.loads(dataset.attrs["overlayMax"])
        
        if "overlayAutovisible" in dataset.attrs.keys():
            self.autoVisible = pickle.loads(dataset.attrs["overlayAutovisible"])
        
        if "overlayAdd" in dataset.attrs.keys():
            self.autoAdd = pickle.loads(dataset.attrs["overlayAdd"])
            
        if "overlayAlpha" in dataset.attrs.keys():
            self.alpha = pickle.loads(dataset.attrs["overlayAlpha"])
            
        f.close()