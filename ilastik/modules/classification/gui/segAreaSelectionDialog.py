from PyQt4 import QtGui, QtCore
import ilastik

class SegAreaSelectionDialog(QtGui.QDialog):
    def __init__(self, ilastikMain, desc_names):
        QtGui.QWidget.__init__(self, ilastikMain)
        self.setWindowTitle("Select Labels for the Table")
        self.ilastik = ilastikMain


        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.descList = QtGui.QListWidget()
        #allow multiple selections
        self.descList.setSelectionMode(2)
        for i, d in enumerate(desc_names):
            self.descList.insertItem(i, d)
        self.layout.addWidget(self.descList)
        
        self.relativeBox = QtGui.QCheckBox("Use only selected labels for total area")
        self.layout.addWidget(self.relativeBox)
        
        tempLayout = QtGui.QHBoxLayout()
        self.alsoSave = QtGui.QCheckBox("also save to Destination File:")
        self.connect(self.alsoSave, QtCore.SIGNAL("stateChanged(int)"), self.toggleAlsoSave)
        tempLayout.addWidget(self.alsoSave)
        self.layout.addLayout(tempLayout) 

        self.alsoSaveFrame = QtGui.QFrame()
        tempLayout = QtGui.QHBoxLayout()
        self.fileButton = QtGui.QPushButton("Select")
        self.connect(self.fileButton, QtCore.SIGNAL('clicked()'), self.slotFile)
        self.fileLine = QtGui.QLineEdit("")
        tempLayout.addWidget(self.fileLine)
        tempLayout.addWidget(self.fileButton)
        self.alsoSaveFrame.setLayout(tempLayout)
        self.alsoSaveFrame.setVisible(False)
        self.layout.addWidget(self.alsoSaveFrame)
        
        tempLayout = QtGui.QHBoxLayout()
        self.ok_btn = QtGui.QPushButton("ok")
        self.connect(self.ok_btn, QtCore.SIGNAL('clicked()'), self.ok_btn_clicked)
        self.cancel_btn = QtGui.QPushButton("cancel")
        self.connect(self.cancel_btn, QtCore.SIGNAL('clicked()'), self.cancel_btn_clicked)
        tempLayout.addWidget(self.ok_btn)
        tempLayout.addWidget(self.cancel_btn)
        self.layout.addLayout(tempLayout)
    
    def toggleAlsoSave(self):
        if self.alsoSave.checkState() == 0:
            self.alsoSaveFrame.setVisible(False)
        else:
            self.alsoSaveFrame.setVisible(True)
    
    def slotFile(self):
        filename= QtGui.QFileDialog.getSaveFileName(self, "Save to File", "*.txt")
        self.fileLine.setText(filename)
    
    def ok_btn_clicked(self):
        self.accept()
    def cancel_btn_clicked(self):
        self.close()
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            
            #chosen = [self.descList.selectedItems()
            chosen = [x.row() for x in self.descList.selectedIndexes()]
            if chosen is not None:
                return chosen, self.relativeBox.isChecked(), str(self.fileLine.text())
            else:
                print "No label selected!"
                return None, None, None
        else:
            return None, None, None
        