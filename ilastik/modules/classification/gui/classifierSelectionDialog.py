

from PyQt4 import QtCore, QtGui, uic
import ilastik
from ilastik.modules.classification.core.classifiers import classifierBase

import os

#*******************************************************************************
# C l a s s i f i e r S e l e c t i o n D l g                                  *
#*******************************************************************************

class ClassifierSelectionDlg(QtGui.QDialog):
    def __init__(self, ilastikMain):
        QtGui.QWidget.__init__(self, ilastikMain)
        self.setWindowTitle("Select Classifier")
        self.ilastik = ilastikMain
        self.previousClassifier = self.currentClassifier = self.ilastik.project.dataMgr.module["Classification"].classifier

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/modules/classification/gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, QtCore.SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, QtCore.SIGNAL('rejected()'), self.reject)
        self.connect(self.settingsButton, QtCore.SIGNAL('pressed()'), self.classifierSettings)

        self.classifiers = classifierBase.ClassifierBase.__subclasses__()
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
        #check wether the plugin writer provided a settings method
        func = getattr(c, "settings", None)
        if callable(func):
            self.settingsButton.setVisible(True)
        else:
            self.settingsButton.setVisible(False)


    def classifierSettings(self):
        self.currentClassifier.settings()


    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            return self.currentClassifier
        else:
            return self.previousClassifier

def test():
    #from spyderlib.utils.qthelpers import qapplication
    app = QtGui.QApplication([""])

    dialog = ClassifierSelectionDlg()
    print dialog.show()
    app.exec_()


#*******************************************************************************
# i f   _ _ n a m e _ _   = =   " _ _ m a i n _ _ "                            *
#*******************************************************************************

if __name__ == "__main__":
    test()
    test()