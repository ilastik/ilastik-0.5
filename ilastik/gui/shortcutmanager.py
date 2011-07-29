from PyQt4 import QtGui, QtCore

#*******************************************************************************
# s h o r t c u t M a n a g e r                                                *
#*******************************************************************************

class shortcutManager():
    def __init__(self):
        self.shortcuts = dict()
        
    def register(self, shortcut, group, description):
        if not group in self.shortcuts:
            self.shortcuts[group] = dict()
        self.shortcuts[group][shortcut.key().toString()] = description
        
    def showDialog(self, parent=None):
        dlg = shortcutManagerDlg(self, parent)

#*******************************************************************************
# s h o r t c u t M a n a g e r D l g                                          *
#*******************************************************************************

class shortcutManagerDlg(QtGui.QDialog):
    def __init__(self, s, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setModal(False)
        self.setWindowTitle("Shortcuts")
        self.setMinimumWidth(500)
        if len(s.shortcuts)>0:
            scrollArea = QtGui.QScrollArea(self)
            scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            
            mainWidget = QtGui.QWidget(self)
            
            scrollArea.setWidget(mainWidget)
            scrollArea.setWidgetResizable(True)
            
            tempLayout = QtGui.QVBoxLayout(mainWidget)
            
            mainWidget.setLayout(tempLayout)
            
            customShortcuts ={\
                               'Navigation': \
                                 {'MouseWheel' : 'Change slice', \
                                  'Alt+MouseWheel' : 'Change slice (fast)', \
                                  'Ctrl+MouseWheelUp' : "Zoom in", \
                                  'Ctrl+MouseWheelDown' : "Zoom out ", \
                                  'Ctrl+MouseLeftClick' : "Change slices by jumping to position", \
                                  }, \
                                'Labeling': \
                                { 'MouseLeftClick' : "Label pixels", \
                                  'Shift+MouseLeftClick' : "Erase labels", \
                                  'MouseRightClick on image' : 'Label context menu', \
                                }
                              } 
            
            
            
            for group in s.shortcuts.keys():
                grpBox = QtGui.QGroupBox(group)
                l = QtGui.QGridLayout(self)
                
                for i, sc in enumerate(s.shortcuts[group]):
                    desc = s.shortcuts[group][sc]
                    l.addWidget(QtGui.QLabel(str(sc)), i,0)
                    l.addWidget(QtGui.QLabel(desc), i,1)
                    
                if group in customShortcuts:
                    for j, sc in enumerate(customShortcuts[group]):
                        l.addWidget(QtGui.QLabel(str(sc)), i + j + 1, 0)
                        l.addWidget(QtGui.QLabel(customShortcuts[group][sc]), i + j + 1, 1)
                    
                grpBox.setLayout(l)
                tempLayout.addWidget(grpBox)
            
            mainLayout = QtGui.QVBoxLayout(self)
            mainLayout.addWidget(scrollArea)
            self.setLayout(mainLayout)
            self.show()
        else:
            l = QtGui.QVBoxLayout()
            l.addWidget(QtGui.QLabel("Load the data by pressing the \"New\" button in the project dialog"))
            self.setLayout(l)
            self.show()
            
shortcutManager = shortcutManager()