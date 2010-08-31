from PyQt4 import QtCore, QtGui
import overlayDialogBase

class SliderReceiver(QtCore.QObject):
    def __init__(self, dialog, index, oldValue):
        QtCore.QObject.__init__(self)
        self.dialog = dialog
        self.index = index
        self.oldValue = oldValue

    def sliderMoved(self, value):
        self.dialog.sliderMoved(self.index, value, self.oldValue)
        self.oldValue = value

class MultivariateThresholdDialog(overlayDialogBase.OverlayDialogBase, QtGui.QDialog):
    configuresClass = "ilastik.core.overlays.thresHoldOverlay.ThresHoldOverlay"
    

            
    
    def __init__(self, instance, volumeEditor):
        QtGui.QDialog.__init__(self)
        self.overlayItem = instance
        self.volumeEditor = volumeEditor
        self.hbox = QtGui.QHBoxLayout()
        self.setLayout(self.hbox)
        self.sliders = []
        self.sliderReceivers = []
        self.previousValues = []
        self.totalValue = 0
        
        for index, t in enumerate(self.overlayItem.foregrounds):
            l = QtGui.QVBoxLayout()
            self.sliderReceivers.append(SliderReceiver(self,index,self.overlayItem.thresholds[index] * 1000))
            
            w = QtGui.QSlider(QtCore.Qt.Vertical)
            w.setRange(0,999)
            w.setSingleStep(1)
            w.setValue(self.overlayItem.thresholds[index] * 1000)
            l.addWidget(w)
            label = QtGui.QLabel(t.name)
            l.addWidget(label)
            self.sliderReceivers[-1].connect(w, QtCore.SIGNAL('sliderMoved(int)'), self.sliderReceivers[-1].sliderMoved)
            self.sliders.append(w)
            
            self.hbox.addLayout(l)
            
        if len(self.overlayItem.backgrounds) > 0:
            l = QtGui.QVBoxLayout()
            self.sliderReceivers.append(SliderReceiver(self,len(self.sliders),self.overlayItem.thresholds[index] * 1000))
            
            w = QtGui.QSlider(QtCore.Qt.Vertical)
            w.setRange(0,1000)
            w.setSingleStep(1)
            w.setValue(self.overlayItem.thresholds[-1] * 1000)
            l.addWidget(w)
            label = QtGui.QLabel('Background')
            l.addWidget(label)
            self.sliderReceivers[-1].connect(w, QtCore.SIGNAL('sliderMoved(int)'), self.sliderReceivers[-1].valueChanged)
            self.sliders.append(w)
            
            self.hbox.addLayout(l)
            
    
    def sliderMoved(self, index, value, oldValue):
        self.sliders[index].setValue(value)
       
        thresholds = []
        for i,s in enumerate(self.sliders):
            if s.value() > 0:
                thresholds.append(s.value() / 1000.0)
            else:
                thresholds.append(-1 / 1000.0)
                    
        self.overlayItem.setThresholds(thresholds)
        self.volumeEditor.repaint()
        