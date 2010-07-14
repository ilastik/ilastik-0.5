
from PyQt4 import QtCore, QtGui, uic

import core.segmentors

class SegmentorSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastik):
        QtGui.QWidget.__init__(self, ilastik)
        self.ilastik = ilastik
        self.previousSegmentor = self.currentSegmentor = self.ilastik.project.segmentor


        uic.loadUi('gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, QtCore.SIGNAL('pressed()'), self.segmentorSettings)

        self.segmentors = core.segmentors.segmentorBase.SegmentorBase.__subclasses__()
        j = 0
        for i, c in enumerate(self.segmentors):
            #qli = QtGui.QListWidgetItem(c.name)
            self.listWidget.addItem(c.name)
            if c == self.currentSegmentor:
                j = i

        self.connect(self.listWidget, QtCore.SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        self.listWidget.setCurrentRow(j)

    def currentRowChanged(self, current):
        c = self.currentSegmentor = self.segmentors[current]
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


    def segmentorSettings(self):
        self.currentSegmentor.settings()


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return  self.currentSegmentor
        else:
            return self.previousSegmentor

def test():
    """Text editor demo"""
    import numpy
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = SegmentorSelectionDlg()
    print dialog.show()
    app.exec_()


if __name__ == "__main__":
    test()