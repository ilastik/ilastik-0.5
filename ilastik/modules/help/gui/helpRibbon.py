# -*- coding: utf-8 -*-
from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase, TabButton

from PyQt4 import QtGui, QtCore

from ilastik.gui.iconMgr import ilastikIcons

from ilastik.gui.overlayWidget import OverlayWidget
from ilastik.gui.shortcutmanager import shortcutManager
from ilastik.gui import volumeeditor as ve
from ilastik.modules.help.gui.about import About

#*******************************************************************************
# H e l p T a b                                                                *
#*******************************************************************************

class HelpTab(IlastikTabBase, QtGui.QWidget):
    name = 'Help'
    position = 101
    moduleName = "Help"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        ovs = self.ilastik._activeImage.module[self.__class__.moduleName].getOverlayRefs()
        if len(ovs) == 0:
            raw = self.ilastik._activeImage.overlayMgr["Raw Data"]
            if raw is not None:
                ovs.append(raw.getRef())
                
        overlayWidget = OverlayWidget(self.ilastik.labelWidget, self.ilastik.project.dataMgr)
        overlayWidget.setVisible(False)
        self.ilastik.labelWidget.setOverlayWidget(overlayWidget)
        self.ilastik.labelWidget.setLabelWidget(ve.DummyLabelWidget())
               
    def on_deActivation(self):
        pass
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
        self.btnShortcuts = TabButton('Shortcuts', ilastikIcons.Help)
        self.btnAbout     = TabButton('About', ilastikIcons.Ilastik)
      
        self.btnShortcuts.setToolTip('Show a list of ilastik shortcuts')
        
        tl.addWidget(self.btnShortcuts)
        tl.addWidget(self.btnAbout)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        
    def _initConnects(self):
        self.connect(self.btnShortcuts, QtCore.SIGNAL('clicked()'), self.on_btnShortcuts_clicked)
        self.connect(self.btnAbout, QtCore.SIGNAL('clicked()'), self.on_btnAbout_clicked)
        
    def on_btnShortcuts_clicked(self):
        shortcutManager.showDialog(self.ilastik)

    def on_btnAbout_clicked(self):
        about = About(self.ilastik)
        about.show()