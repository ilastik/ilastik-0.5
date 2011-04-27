from ilastik.gui.ribbons.ilastikTabBase import IlastikTabBase

from PyQt4 import QtGui, QtCore

#*******************************************************************************
# H e l p T a b                                                                *
#*******************************************************************************

class HelpTab(IlastikTabBase, QtGui.QWidget):
    name = 'Example'  #the name of your ribbon
    position = 101    #the position in the tabbar
    moduleName = "Example"
    
    def __init__(self, parent=None):
        IlastikTabBase.__init__(self, parent)
        QtGui.QWidget.__init__(self, parent)
        
        self._initContent()
        self._initConnects()
        
    def on_activation(self):
        print 'Changed to Tab: ', self.__class__.name
        
        """
        you can create some default overlays here 
        or set up your own labelWidget for the VolumeEditor
        that can handle user given pixel labels in any
        way
        """
       
    def on_deActivation(self):
        print 'Left Tab ', self.__class__.name
        
    def _initContent(self):
        tl = QtGui.QHBoxLayout()
        tl.setMargin(0)
        
        self.btnExample = QtGui.QPushButton('Example')
      
        self.btnExample.setToolTip('Example button')
        
        tl.addWidget(self.btnShortcuts)
        tl.addStretch()
        
        self.setLayout(tl)
        #self.shortcutManager = shortcutManager()
        
    def _initConnects(self):
        self.connect(self.btnExample, QtCore.SIGNAL('clicked()'), self.on_btnExample_clicked)
        
    def on_btnShortcuts_clicked(self):
        """
        do some interesting things here
        """