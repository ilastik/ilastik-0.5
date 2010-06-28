
from PyQt4 import QtCore, QtGui, uic

import core.classifiers

class ClassifierSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastik):
        QtGui.QWidget.__init__(self, ilastik)
        self.ilastik = ilastik
        self.previousClassifier = self.currentClassifier = self.ilastik.project.classifier


        uic.loadUi('gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)

        self.classifiers = core.classifiers.classifierBase.ClassifierBase.__subclasses__()
        j = 0
        for i, c in enumerate(self.classifiers):
            #qli = QtGui.QListWidgetItem(c.name)
            self.listWidget.addItem(c.name)
            if c == self.currentClassifier:
                j = i

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(j)

    def currentRowChanged(self, current):
        c = self.currentClassifier = self.classifiers[current]
        self.name.setText(c.name)
        self.homepage.setText(c.homepage)
        self.description.setText(c.description)
        self.author.setText(c.author)

    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.currentClassifier
        else:
            return self.previousClassifier

def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = ClassifierSelectionDlg()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()