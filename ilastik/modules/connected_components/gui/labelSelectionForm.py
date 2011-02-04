from PyQt4 import QtCore, QtGui

class LabelSelectionForm(QtGui.QDialog):
    def __init__(self, parent = None, desc_names = None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Select the object label, used in prediction')
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.descList = QtGui.QListWidget()
        for i, d in enumerate(desc_names):
            self.descList.insertItem(i, d)
        self.layout.addWidget(self.descList)
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
            return chosen[0].text()
        else:
            return None
        
        