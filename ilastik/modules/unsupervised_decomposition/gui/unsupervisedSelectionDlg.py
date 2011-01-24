from PyQt4 import QtCore, QtGui, uic
import ilastik
from ilastik.modules.unsupervised_decomposition.core.algorithms import unsupervisedDecompositionBase

import os

class UnsupervisedSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastikMain):
        QtGui.QWidget.__init__(self, ilastikMain)
        self.setWindowTitle("Select Algorithm")
        self.ilastik = ilastikMain
        self.previousUnsupervisedDecomposer = self.currentUnsupervisedDecomposer = self.ilastik.project.dataMgr.module["Unsupervised_Decomposition"].unsupervisedMethod

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/modules/unsupervised_decomposition/gui/unsupervisedSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, QtCore.SIGNAL('pressed()'), self.unsupervisedSettings)

        self.unsupervisedDecomposers = unsupervisedDecompositionBase.UnsupervisedDecompositionBase.__subclasses__()
        j = 0
        for i, c in enumerate(self.unsupervisedDecomposers):
            self.listWidget.addItem(c.name)
            if c == self.currentUnsupervisedDecomposer:
                j = i

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(0)

    def currentRowChanged(self, current):
        c = self.currentUnsupervisedDecomposer = self.unsupervisedDecomposers[current]
        self.name.setText(c.name)
        self.homepage.setText(c.homepage)
        self.description.setText(c.description)
        self.author.setText(c.author)
        #check wether the plugin writer provided a settings method
        func = getattr(c, "settings", None)
        if callable(func):
            self.settingsButton.setVisible(True)
        else:
            self.settingsButton.setVisible(False)

    def unsupervisedSettings(self):
        self.currentUnsupervisedDecomposer.settings()

    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return self.currentUnsupervisedDecomposer
        else:
            return self.previousUnsupervisedDecomposer        

def test():
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = UnsupervisedSelectionDlg()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()
    test()