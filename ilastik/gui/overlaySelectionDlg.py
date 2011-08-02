# -*- coding: utf-8 -*-
from PyQt4.QtGui import QVBoxLayout, QHBoxLayout, QDialog, QToolButton, QGroupBox, QSpinBox, QSpacerItem

from ilastik.modules.classification.gui import treeWidget
from ilastik.modules.classification.gui import preView


class OverlaySelectionDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.overlayTreeWidgetLayout = QHBoxLayout()
        self.overlayTreeWidget = treeWidget.OverlayTreeWidget()
        self.overlayTreeWidgetLayout.addWidget(self.overlayTreeWidget)
        self.overlayTreeWidget.itemSelectionChanged.connect(self.overlayTreeItemSelectionChanged)
        
        self.preViewAndSpinBoxLayout = QVBoxLayout()
        self.preView = preView.PreView()
        self.preViewAndSpinBoxLayout.addWidget(self.preView)
        
        self.spinBoxLayout = QHBoxLayout()
        self.channelSpinboxLabel = QLabel("Channel")
        self.channelSpinbox = QSpinBox(self)
        self.channelSpinbox.setEnabled(False)
#        self.connect(self.channelSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.channelSpinboxValueChanged)
        self.sliceSpinboxLabel = QLabel("Slice")
        self.sliceSpinbox = QSpinBox(self)
        self.sliceSpinbox.setEnabled(False)
#        self.connect(self.sliceSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.sliceSpinboxValueChanged)
        self.spinBoxLayout.addWidget(self.channelSpinboxLabel)
        self.spinBoxLayout.addWidget(self.channelSpinbox)
        self.spinBoxLayout.addStretch()
        self.spinBoxLayout.addWidget(self.sliceSpinboxLabel)
        self.spinBoxLayout.addWidget(self.sliceSpinbox)
        self.spinBoxLayout.addSpacerItem(QSpacerItem(10,0))
#        self.spinBoxLayout.addStretch()
        
        self.preViewAndSpinBoxLayout.addLayout(self.spinBoxLayout)
                
        self.buttonLayout = QHBoxLayout()
        self.add_selectedButoon = QToolButton()
        self.add_selectedButoon.setText("Add Selected")
        self.add_selectedButoon.clicked.connect(self.on_add_selectedClicked)
        self.cancelButton = QToolButton()
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self.on_cancelClicked)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.add_selectedButoon)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addSpacerItem(QSpacerItem(10,0))
        self.preViewAndSpinBoxLayout.addLayout(self.buttonLayout)
        self.preViewAndSpinBoxLayout.addSpacerItem(QSpacerItem(0,10))
        
        self.layout.addLayout(self.overlayTreeWidgetLayout)
        self.layout.addLayout(self.preViewAndSpinBoxLayout)
        self.layout.setContentsMargins(0,0,0,0)
        
    # methods
    # ------------------------------------------------
    
    def overlayTreeItemSelectionChanged(self):
        currentTreeItem = self.overlayTreeWidget.currentItem()
        if isinstance(currentTreeItem, treeWidget.OverlayTreeWidgetItem):
            self.channelSpinbox.setEnabled(True)
            self.sliceSpinbox.setEnabled(True)
            self._showOverlayImageInPreView(currentTreeItem)
        else:
            self.channelSpinbox.setEnabled(False)
            self.sliceSpinbox.setEnabled(False)
            
    def _showOverlayImageInPreView(self, currentTreeItem):
        print currentTreeItem.item.name
    
    def createOverlayTreeWidget(self, overlayDict, forbiddenOverlays, preSelectedOverlays):
        self.overlayTreeWidget.addOverlaysToTreeWidget(overlayDict, forbiddenOverlays, preSelectedOverlays)
        
    def on_add_selectedClicked(self):
        self.accept()
    
    def on_cancelClicked(self):
        self.reject()
    
    
    
    
class SimpleObject:
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    import sys

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
        
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    ex1 = OverlaySelectionDialog()
    a = SimpleObject("Labels")
    b = SimpleObject("Raw Data")
    ex1.createOverlayTreeWidget({"Classification/Labels/Channel A/xz": a, "Raw Data": b}, [], [])
    ex1.show()
    ex1.raise_()  
      
    
    app.exec_() 