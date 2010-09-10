from PyQt4 import QtGui

class ShortcutManager():
    def __init__(self):
        self.shortcuts = dict()
        
    def register(self, shortcut, description):
        self.shortcuts[shortcut.key().toString()] = description
        
    def showDialog(self):
        dlg = ShortcutManagerDlg(self)

class ShortcutManagerDlg(QtGui.QDialog):
    def __init__(self, s):
        QtGui.QDialog.__init__(self)
        
        l = QtGui.QGridLayout(self)
    
        for i, sc in enumerate(s.shortcuts):
            desc = s.shortcuts[sc]
        
            l.addWidget(QtGui.QLabel(str(sc)), i,0)
            l.addWidget(QtGui.QLabel(desc), i,1)
            self.setLayout(l)
        self.exec_()

shortcutManager = ShortcutManager()