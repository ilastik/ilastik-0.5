from PyQt4 import QtCore, QtGui
import overlayDialogBase

class MultivariateThresholdDialog(overlayDialogBase.OverlayDialogBase):
    configuresClass = "ilastik.core.overlays.thresHoldOverlay.ThresHoldOverlay"
    
    def __init__(self):
        pass
    
    def exec_(self):
        pass