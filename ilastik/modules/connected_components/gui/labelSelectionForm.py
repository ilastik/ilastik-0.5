from PyQt4 import QtCore, QtGui

#*******************************************************************************
# L a b e l S e l e c t i o n F o r m                                          *
#*******************************************************************************

class LabelSelectionForm(QtGui.QDialog):
    def __init__(self, parent = None, desc_names = None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Select the synapse label, used in prediction')
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.descList = QtGui.QListWidget()
        for i, d in enumerate(desc_names):
            self.descList.insertItem(i, d)
        self.layout.addWidget(self.descList)
        tempLayout = QtGui.QHBoxLayout()
        self.qiv = QtGui.QIntValidator(100, 1000000, self)
        self.minsize = QtGui.QLineEdit(QtCore.QString("1000"))
        self.minsize.setValidator(self.qiv)
        self.minsize.setToolTip("Minimal synapse size in pixels")
        tempLayout.addWidget(QtGui.QLabel("Min. size"))
        tempLayout.addWidget(self.minsize)
        self.maxsize = QtGui.QLineEdit(QtCore.QString("250000"))
        self.maxsize.setValidator(self.qiv)
        self.maxsize.setToolTip("Maximal synapse size in pixels")
        tempLayout.addWidget(QtGui.QLabel("Max. size"))
        tempLayout.addWidget(self.maxsize)
        self.layout.addLayout(tempLayout)
        tempLayout = QtGui.QHBoxLayout()
        self.ok_btn = QtGui.QPushButton("ok")
        self.connect(self.ok_btn, QtCore.SIGNAL('clicked()'), self.ok_btn_clicked)
        self.cancel_btn = QtGui.QPushButton("cancel")
        self.connect(self.cancel_btn, QtCore.SIGNAL('clicked()'), self.cancel_btn_clicked)
        tempLayout.addWidget(self.ok_btn)
        tempLayout.addWidget(self.cancel_btn)
        self.layout.addLayout(tempLayout)
    
    def ok_btn_clicked(self):
        self.accept()
    def cancel_btn_clicked(self):
        self.close()
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            chosen = self.descList.selectedItems()
            if chosen is not None:
                return chosen[0].text(), int(self.minsize.text()), int(self.maxsize.text())
            else:
                print "No label selected!"
                return None, None, None
        else:
            return None, None, None
        
        