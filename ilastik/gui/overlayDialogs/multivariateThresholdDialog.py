from PyQt4 import QtCore, QtGui
import overlayDialogBase
import ilastik.gui.overlaySelectionDlg
from ilastik.core.overlays.thresHoldOverlay import ThresHoldOverlay 

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
    

            
    
    def __init__(self, ilastik, instance = None):
        QtGui.QDialog.__init__(self)
        self.ilastik = ilastik
        if instance != None:
            self.overlayItem = instance
        else:
            ovm = self.ilastik.project.dataMgr[self.ilastik.activeImage].overlayMgr
            k = ovm.keys()[0]
            ov = ovm[k]
            self.overlayItem = ThresHoldOverlay([ov], [])

        self.volumeEditor = ilastik.labelWidget
        self.project = ilastik.project
        self.mainlayout = QtGui.QVBoxLayout()
        self.setLayout(self.mainlayout)
        self.mainwidget = QtGui.QWidget()
        self.mainlayout.addWidget(self.mainwidget)
        self.hbox = None
        
        self.buildDialog()
        
    def buildDialog(self):
        self.mainwidget.hide()
        self.mainlayout.removeWidget(self.mainwidget)
        self.mainwidget.close()
        del self.mainwidget
        self.mainwidget = QtGui.QWidget()
        self.mainlayout.addWidget(self.mainwidget)      
        self.hbox = QtGui.QHBoxLayout()
        self.mainwidget.setLayout(self.hbox)
        
        self.sliders = []
        self.sliderReceivers = []
        self.previousValues = []
        self.totalValue = 0
        
        for index, t in enumerate(self.overlayItem.foregrounds):
            l = QtGui.QVBoxLayout()
            print t.name
            print len(self.overlayItem.thresholds)
            print index
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
        w = QtGui.QPushButton("Select Forground")
        self.connect(w, QtCore.SIGNAL("clicked()"), self.selectForegrounds)
        l.addWidget(w)
        w = QtGui.QPushButton("Select Background")
        self.connect(w, QtCore.SIGNAL("clicked()"), self.selectBackgrounds)
        l.addWidget(w)
        self.hbox.addLayout(l)

        
    
    def selectForegrounds(self):
        d = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.project.dataMgr[self.ilastik.activeImage].overlayMgr, singleSelection = False)
        o = d.exec_()
        if len(o) > 0:
            self.overlayItem.setForegrounds(o)
        self.buildDialog()
    
    def selectBackgrounds(self):
        d = ilastik.gui.overlaySelectionDlg.OverlaySelectionDialog(self.project.dataMgr[self.ilastik.activeImage].overlayMgr, singleSelection = False)
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
        