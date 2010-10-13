from PyQt4 import QtGui

class shortcutManager():
    def __init__(self):
        self.shortcuts = dict()
        
    def register(self, shortcut, description):
        self.shortcuts[shortcut.key().toString()] = description
        
    def showDialog(self, parent=None):
        dlg = shortcutManagerDlg(self, parent)

class shortcutManagerDlg(QtGui.QDialog):
    def __init__(self, s, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Shortcuts")
        if len(s.shortcuts)>0:
            l = QtGui.QGridLayout(self)
            
            for i, sc in enumerate(s.shortcuts):
                desc = s.shortcuts[sc]
                
                l.addWidget(QtGui.QLabel(str(sc)), i,0)
                l.addWidget(QtGui.QLabel(desc), i,1)
            self.setLayout(l)
            self.exec_()
        else:
            l = QtGui.QVBoxLayout()
            l.addWidget(QtGui.QLabel("Load the data by pressing the \"New\" button in the project dialog"))
            self.setLayout(l)
            self.exec_()
            
shortcutManager = shortcutManager()