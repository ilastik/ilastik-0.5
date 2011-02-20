from PyQt4 import QtCore, QtGui

#*******************************************************************************
# E d i t C h a n n e l s D i a l o g                                          *
#*******************************************************************************

class EditChannelsDialog(QtGui.QDialog):
    def __init__(self, selectedChannels, numOfChannels, parent):
        QtGui.QWidget.__init__(self, parent=None)
        self.setWindowTitle("Edit Channels")
        
        self.selectedChannels = selectedChannels
        self.numOfChannels = numOfChannels
        
        self.mainLayout = QtGui.QVBoxLayout()
        self.channelListBox = QtGui.QGroupBox('Select Channel for feature computation')
        self.channelList = QtGui.QListWidget()
        
        self.tempLayout = QtGui.QVBoxLayout()
        self.tempLayout.addWidget(self.channelList)
        
        self.channelListBox.setLayout(self.tempLayout)
        
        for c_ind in range(self.numOfChannels):
            channelItem = QtGui.QListWidgetItem('Channel %d' % c_ind)
            sel = QtCore.Qt.Unchecked
            if c_ind in self.selectedChannels:
                sel = QtCore.Qt.Checked 
            channelItem.setCheckState(sel)
            self.channelList.addItem(channelItem)
            
        self.mainLayout.addWidget(self.channelListBox)
        
        confirmButtons = QtGui.QHBoxLayout()
        
        self.okay = QtGui.QPushButton('OK')
        self.cancel = QtGui.QPushButton('Cancel')
        
        self.connect(self.okay, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.cancel, QtCore.SIGNAL("clicked()"), self.reject)
        
        confirmButtons.addStretch()
        confirmButtons.addWidget(self.okay)
        confirmButtons.addWidget(self.cancel)
        
        
        self.mainLayout.addLayout(confirmButtons)
        
        self.setLayout(self.mainLayout)
        
        
    def exec_(self):
        if QtGui.QDialog.exec_(self) == QtGui.QDialog.Accepted:
            result = []        
            for c_ind in self.selectedChannels:
                channelItem = self.channelList.item(c_ind)
                if channelItem.checkState() == QtCore.Qt.Checked:
                    result.append(c_ind)
            self.selectedChannels = result
            return result
        else:
            return None