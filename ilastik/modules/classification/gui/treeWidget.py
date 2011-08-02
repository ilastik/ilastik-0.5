# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignal


class OverlayTreeWidgetIter(QtGui.QTreeWidgetItemIterator):
    def __init__(self, *args):
        QtGui.QTreeWidgetItemIterator.__init__(self, *args)
    def next(self):
        self.__iadd__(1)
        value = self.value()
        if value:
            return self.value()
        else:
            return False


class OverlayTreeWidgetItem(QtGui.QTreeWidgetItem):
    def __init__(self, item, overlayPathName):
        """
        item:            OverlayTreeWidgetItem
        overlayPathName: string
                         full name of the overlay, for example 'File Overlays/My Data'
        """
        self.overlayPathName = overlayPathName
        QtGui.QTreeWidgetItem.__init__(self, [item.name])
        self.item = item


class OverlayTreeWidget(QtGui.QTreeWidget):
    spacePressed = pyqtSignal()
    
    def __init__(self, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        
        self.singleOverlaySelection = True
        
        self.header().close()
        self.setSortingEnabled(True)
        self.installEventFilter(self)
        self.spacePressed.connect(self.spacePressedTreewidget)
        self.itemChanged.connect(self.treeItemChanged)


    def addOverlaysToTreeWidget(self, overlayDict, forbiddenOverlays, preSelectedOverlays):
        testItem = QtGui.QTreeWidgetItem("a")
        for keys in overlayDict.keys():
            if overlayDict[keys] in forbiddenOverlays:
                continue
            else:
                boolStat = False
                split = keys.split("/")
            for i in range(len(split)):
                if len(split) == 1:
                    newItemsChild = OverlayTreeWidgetItem(overlayDict[keys], keys)
                    self.addTopLevelItem(newItemsChild)                   
                    boolStat = False
                    if overlayDict[keys] in preSelectedOverlays:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
                elif i+1 == len(split) and len(split) > 1:
                    newItemsChild = OverlayTreeWidgetItem(overlayDict[keys], keys)
                    testItem.addChild(newItemsChild)
                    if overlayDict[keys] in preSelectedOverlays:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
                elif self.topLevelItemCount() == 0 and i+1 < len(split):
                    newItem = QtGui.QTreeWidgetItem([split[i]])
                    self.addTopLevelItem(newItem)
                    testItem = newItem
                    boolStat = True
                    
                elif self.topLevelItemCount() != 0 and i+1 < len(split):
                    if boolStat == False:
                        for n in range(self.topLevelItemCount()):
                            if self.topLevelItem(n).text(0) == split[i]:
                                testItem = self.topLevelItem(n)
                                boolStat = True
                                break
                            elif n+1 == self.topLevelItemCount():
                                newItem = QtGui.QTreeWidgetItem([split[i]])
                                self.addTopLevelItem(newItem)
                                testItem = newItem
                                boolStat = True
                        
                    elif testItem.childCount() == 0:
                        newItem = QtGui.QTreeWidgetItem([split[i]])
                        testItem.addChild(newItem)
                        testItem = newItem
                        boolStat = True
                    else:
                        for x in range(testItem.childCount()):
                            if testItem.child(x).text(0) == split[i]:
                                testItem = testItem.child(x)
                                boolStat = True
                                break
                            elif x+1 == testItem.childCount():
                                newItem = QtGui.QTreeWidgetItem([split[i]])
                                testItem.addChild(newItem)
                                testItem = newItem
                                boolStat = True
                                
    def treeItemChanged(self, item, column):
        print "itemChanged"
        currentItem = item
        it = OverlayTreeWidgetIter(self, QtGui.QTreeWidgetItemIterator.Checked)
        i = 0
        while (it.value()):
            if self.singleOverlaySelection == True and currentItem.checkState(column) == 2:
                if it.value() != currentItem:
                    it.value().setCheckState(0, 0)
            it.next()
            i += 1
        if i == 0:
#            self.addSelectedButton.setEnabled(False)
            pass
        else:
#            self.addSelectedButton.setEnabled(True)
            pass
                                
    def createSelectedItemList(self):
        selectedItemList = []
        it = OverlayTreeWidgetIter(self, QtGui.QTreeWidgetItemIterator.Checked)
        while (it.value()):
            selectedItemList.append(it.value().item)
            it.next()
        return selectedItemList


    def spacePressedTreewidget(self):
        for item in self.selectedItems():
            if item.childCount() == 0:
                if item.checkState(0) == 0:
                    item.setCheckState(0, 2)
                else: 
                    item.setCheckState(0, 0)
                    
    def event(self, event):
        if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==QtCore.Qt.Key_Space):
            self.emit(QtCore.SIGNAL("spacePressed"))
            return True
        return QtGui.QTreeWidget.event(self, event)

class SimpleObject:
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    import sys
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
        
    app = QApplication(sys.argv)
    app.setStyle("cleanlooks")
    
    ex1 = OverlayTreeWidget()
    a = SimpleObject("Labels")
    b = SimpleObject("Raw Data")
    ex1.addOverlaysToTreeWidget({"Classification/Labels": a, "Raw Data": b}, [], [])
    print ex1.createSelectedItemList()
    ex1.show()
    ex1.raise_()        
    
    app.exec_() 