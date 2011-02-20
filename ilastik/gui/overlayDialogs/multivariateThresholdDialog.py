from PyQt4 import QtCore, QtGui
import overlayDialogBase
import ilastik.gui.overlaySelectionDlg
from ilastik.core.overlays.thresholdOverlay import ThresholdOverlay 

#*******************************************************************************
# S l i d e r R e c e i v e r                                                  *
#*******************************************************************************

class SliderReceiver(QtCore.QObject):
    def __init__(self, dialog, index, oldValue):
        QtCore.QObject.__init__(self)
        self.dialog = dialog
        self.index = index
        self.oldValue = oldValue

    def sliderMoved(self, value):
        self.dialog.sliderMoved(self.index, value, self.oldValue)
        self.oldValue = value

#*******************************************************************************
# M u l t i v a r i a t e T h r e s h o l d D i a l o g                        *
#*******************************************************************************

class MultivariateThresholdDialog(overlayDialogBase.OverlayDialogBase, QtGui.QDialog):
    configuresClass = "ilastik.core.overlays.thresholdOverlay.ThresholdOverlay"
    name = "Thresholding Overlay"
    author = "C. N. S."
    homepage = "hci"
    description = "lazy evaluation thresholding"    

            
    
    def __init__(self, ilastik, instance = None):
        QtGui.QDialog.__init__(self, ilastik)
        self.setWindowTitle("Multi-variate Thresholding")
        
        self.ilastik = ilastik
        if instance != None:
            self.overlayItem = instance
        else:
            ovm = self.ilastik.project.dataMgr[self.ilastik._activeImageNumber].overlayMgr
            k = ovm.keys()[0]
            ov = ovm[k]
            self.overlayItem = ThresholdOverlay([ov], [])

        self.volumeEditor = ilastik.labelWidget
        self.project = ilastik.project
        self.mainlayout = QtGui.QVBoxLayout()
        self.setLayout(self.mainlayout)
        self.mainwidget = QtGui.QWidget()
        self.mainlayout.addWidget(self.mainwidget)
        self.hbox = None
        
        self.buildDialog()
        
        self.acceptButton = QtGui.QPushButton("Ok")
        self.connect(self.acceptButton, QtCore.SIGNAL('clicked()'), self.okClicked)
        self.mainlayout.addWidget(self.acceptButton)
        
    def buildDialog(self):
        self.mainwidget.hide()
        self.mainlayout.removeWidget(self.mainwidget)
        self.mainwidget.close()
        del self.mainwidget
        self.mainwidget = QtGui.QWidget()
        self.mainlayout.insertWidget(0, self.mainwidget)      
        self.hbox = QtGui.QHBoxLayout()
        self.mainwidget.setLayout(self.hbox)
        
        self.sliders = []
        self.sliderReceivers = []
        self.previousValues = []
        self.totalValue = 0
        
        for index, t in enumerate(self.overlayItem.foregrounds):
            l = QtGui.QVBoxLayout()
            #print t.name
            #print len(self.overlayItem.thresholds)
            #print index
            self.sliderReceivers.append(SliderReceiver(self,index,self.overlayItem.thresholds[index] * 1000))
            
            w = QtGui.QSlider(QtCore.Qt.Vertical)
#*******************************************************************************
# p r o b a b i l i t y                                                        *
#*******************************************************************************

            w.setToolTip("Change the threshold for " + str(t.name) + "\n a low threshold compared to the other thresholds means a high class probability")
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
            self.sliderReceivers.append(SliderReceiver(self,len(self.sliders),self.overlayItem.thresholds[-1] * 1000))
            
            w = QtGui.QSlider(QtCore.Qt.Vertical)
            w.setRange(0,1000)
            w.setSingleStep(1)
            w.setValue(self.overlayItem.thresholds[-1] * 1000)
            l.addWidget(w)
            label = QtGui.QLabel('Background')
            l.addWidget(label)
            self.sliderReceivers[-1].connect(w, QtCore.SIGNAL('sliderMoved(int)'), self.sliderReceivers[-1].sliderMoved)
            self.sliders.append(w)
            
            self.hbox.addLayout(l)

        
        l = QtGui.QVBoxLayout()
        w = QtGui.QPushButton("Select Foreground")
        self.connect(w, QtCore.SIGNAL("clicked()"), self.selectForegrounds)
        l.addWidget(w)
        w = QtGui.QPushButton("Select Background")
        self.connect(w, QtCore.SIGNAL("clicked()"), self.selectBackgrounds)
        l.addWidget(w)
        
        l2 = QtGui.QHBoxLayout()
        self.smoothing = QtGui.QCheckBox("Smooth")
        self.smoothing.setToolTip("Smooth the input overlays with the specified pixel sigma using a gaussian\n Smoothing may take a while depending on the size of the data...")
        self.smoothing.setCheckState(self.overlayItem.smoothing * 2)
        self.connect(self.smoothing, QtCore.SIGNAL("stateChanged(int)"), self.smoothingChanged)
        self.sigma = QtGui.QLineEdit(str(self.overlayItem.sigma))
        self.sigma.setToolTip("sigma in pixels")
        l2.addWidget(self.smoothing)
        l2.addWidget(self.sigma)
        l.addLayout(l2)
    
        self.hbox.addLayout(l)
        self.setMinimumHeight(300)
        
    def smoothingChanged(self, state):
        sigma = self.overlayItem.sigma
        try:
            sigma = float(self.sigma.text())
        except:
            pass
        self.overlayItem.sigma = sigma
        if state == QtCore.Qt.Checked:
            self.overlayItem.smoothing = True
        else:
            self.overlayItem.smoothing = False
        self.overlayItem.setForegrounds(self.overlayItem.foregrounds)
        
        thresholds = []
        for i,s in enumerate(self.sliders):
            if s.value() > 0:
                thresholds.append(s.value() / 1000.0)
            else:
                thresholds.append(-1 / 1000.0)
                    
        self.overlayItem.setThresholds(thresholds)    
            
        self.volumeEditor.repaint()
        
    
    def selectForegrounds(self):
        d = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.ilastik, singleSelection = False)
        o = d.exec_()
        if len(o) > 0:
            self.overlayItem.setForegrounds(o)
        self.buildDialog()
    
    def selectBackgrounds(self):
        d = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.ilastik, singleSelection = False)
        o = d.exec_()
        self.overlayItem.setBackgrounds(o)
        self.buildDialog()

    
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
        
    
    def okClicked(self):
        if len(self.overlayItem.dsets) >= 2:
            self.accept()
        else:
            QtGui.QMessageBox.warning(self, "Error", "Please select more than one Overlay for thresholding - either more than one foreground overlays, or one foreground and one background overlay !")
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return self.overlayItem
        else:
            return None        
