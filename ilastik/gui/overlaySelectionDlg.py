from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
from ilastik.core.overlayMgr import OverlayItem

class MyTreeWidget(QTreeWidget):
    def __init__(self, *args):
        QTreeWidget.__init__(self, *args)
        
    def event(self, event):
        if (event.type()==QEvent.KeyPress) and (event.key()==Qt.Key_Space):
            self.emit(SIGNAL("spacePressed"))
            return True

        return QTreeWidget.event(self, event)


class MyQTreeWidgetIter(QTreeWidgetItemIterator):
    def __init__(self, *args):
        QTreeWidgetItemIterator.__init__(self, *args)
    def next(self):
        self.__iadd__(1)
        value = self.value()
        if value:
            return self.value()
        else:
            return False


class MyTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, item):
        QTreeWidgetItem.__init__(self, [item.name])
        self.item = item


class OverlaySelectionDialog(QDialog):
    def __init__(self, cdict, forbiddenItems=[], singelSelection=True, parent=None):
        QWidget.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setMinimumWidth(600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layoutWidget = QWidget(self)
        self.selectedItemList = []
        self.christophsDict = cdict
        self.forbiddenItems = forbiddenItems
        self.singelSelection = singelSelection
        
        # widgets and layouts
        # ------------------------------------------------
        
        GroupsLayout = QHBoxLayout()
        treeGroupBoxLayout = QGroupBox("Overlays")
        treeAndButtonsLayout = QVBoxLayout()
        self.treeWidget = MyTreeWidget()
        self.connect(self.treeWidget, SIGNAL('spacePressed'), self.spacePressedTreewidget)
        self.treeWidget.header().close()
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.itemClicked.connect(self.clickOnTreeItem)
        self.connect(self.treeWidget, SIGNAL('itemChanged(QTreeWidgetItem *,int)'), self.treeItemChanged)

        treeButtonsLayout = QHBoxLayout()
        self.expandAllButton = QPushButton("Expand All")
        self.connect(self.expandAllButton, SIGNAL('clicked()'), self.expandAll)
        self.checkAllButton = QPushButton("Check All")
        self.connect(self.checkAllButton, SIGNAL('clicked()'), self.checkAll)
        self.uncheckAllButton = QPushButton("Uncheck All")
        self.connect(self.uncheckAllButton, SIGNAL('clicked()'), self.uncheckAll)
        treeButtonsLayout.addWidget(self.expandAllButton)
        treeButtonsLayout.addWidget(self.checkAllButton)
        treeButtonsLayout.addWidget(self.uncheckAllButton)
        treeButtonsLayout.addStretch()
        treeAndButtonsLayout.addWidget(self.treeWidget)
        treeAndButtonsLayout.addLayout(treeButtonsLayout)
        treeGroupBoxLayout.setLayout(treeAndButtonsLayout)
        
        descLabelGroupBox = QGroupBox("Description")
        descLabelLayout = QVBoxLayout()
        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setAlignment(Qt.AlignTop)
        self.desc.setMinimumWidth(200)
        self.desc.setMaximumWidth(300)
        descLabelLayout.addWidget(self.desc)
        descLabelGroupBox.setLayout(descLabelLayout)
        GroupsLayout.addWidget(treeGroupBoxLayout)
        GroupsLayout.addWidget(descLabelGroupBox)
        
        tempLayout = QHBoxLayout()
        self.cancelButton = QPushButton("Cancel")
        self.connect(self.cancelButton, SIGNAL('clicked()'), self.cancel)
        self.addSelectedButton = QPushButton("Add Selected")
        self.connect(self.addSelectedButton, SIGNAL('clicked()'), self.addSelected)
        tempLayout.addStretch()
        tempLayout.addWidget(self.cancelButton)
        tempLayout.addWidget(self.addSelectedButton)
        
        if self.singelSelection == True:
            self.setWindowTitle("Overlay Singel Selection")
            self.desc.setText("<b>Singel Selection Mode</b> <br /><br />In singel selction mode it is possible to choose only one overlay.<br />For overlay-description select an overlay.<br />To (un)check an overlay please <br /> -click on a checkbox<br />-select overlay and press the spacebar")
            self.checkAllButton.setEnabled(False)
            self.uncheckAllButton.setEnabled(False)
        else:
            self.setWindowTitle("Overlay Multi Selection")
            self.desc.setText("<b>Multi Selection Mode</b> <br /><br />In multi selction mode it is possible to choose several overlays.<br />For overlay-description select an overlay.<br />To (un)ckeck overlays please<br />-click on a checkbox<br />-slect several overlays with ctrl + mouse and press then the spacebar<br />-select several overlays with shift + click and press then the spacebar<br />")
            self.treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.layout.addLayout(GroupsLayout)
        self.layout.addLayout(tempLayout)
        
        self.addItemsToTree()
        
    # methods
    # ------------------------------------------------
    def addItemsToTree(self):
        testItem = QTreeWidgetItem("a")
        for keys in self.christophsDict.keys():
            if self.christophsDict[keys] in self.forbiddenItems:
                continue
            else:
                boolStat = False
                split = keys.split("/")
            for i in range(len(split)):
                if len(split) == 1:
                    newItemsChild = MyTreeWidgetItem(self.christophsDict[keys])
                    newItemsChild.setCheckState(0, 0)
                    self.treeWidget.addTopLevelItem(newItem)                   
                    boolStat = False
                    
                elif i+1 == len(split) and len(split) > 1:
                    newItemsChild = MyTreeWidgetItem(self.christophsDict[keys])
                    newItemsChild.setCheckState(0, 0)
                    testItem.addChild(newItemsChild)
                    
                elif self.treeWidget.topLevelItemCount() == 0 and i+1 < len(split):
                    newItem = QTreeWidgetItem([split[i]])
                    self.treeWidget.addTopLevelItem(newItem)
                    testItem = newItem
                    boolStat = True
                    
                elif self.treeWidget.topLevelItemCount() != 0 and i+1 < len(split):
                    if boolStat == False:
                        for n in range(self.treeWidget.topLevelItemCount()):
                            if self.treeWidget.topLevelItem(n).text(0) == split[i]:
                                testItem = self.treeWidget.topLevelItem(n)
                                boolStat = True
                                break
                            elif n+1 == self.treeWidget.topLevelItemCount():
                                newItem = QTreeWidgetItem([split[i]])
                                self.treeWidget.addTopLevelItem(newItem)
                                testItem = newItem
                                boolStat = True
                        
                    elif testItem.childCount() == 0:
                        newItem = QTreeWidgetItem([split[i]])
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
                                newItem = QTreeWidgetItem([split[i]])
                                testItem.addChild(newItem)
                                testItem = newItem
                                boolStat = True


    def treeItemChanged(self, item, column):
        currentItem = item
        if self.singelSelection == True and currentItem.checkState(column) == 2:
            it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.Checked)
            while (it.value()):
                if it.value() != currentItem:
                    it.value().setCheckState(0, 0)
                it.next()

                                
    def clickOnTreeItem(self):
        if self.treeWidget.currentItem().childCount() == 0:
            child = self.treeWidget.currentItem()
            if child.parent():
                parent = child.parent() 
                self.desc.setText("<b>%s</b> <br /><br /> %s" % (parent.text(0), child.item.desc))
            else: 
                self.desc.setText("<b>%s</b> <br /><br /> %s" % ("No Group", child.item.desc))
        else:
            self.desc.setText(self.treeWidget.currentItem().text(0))


    def expandAll(self):
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.HasChildren)
        while (it.value()):
            it.value().setExpanded(True)
            it.next()


    def checkAll(self):
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.NoChildren)
        while (it.value()):
            it.value().setCheckState(0, 2)
            it.next()
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.HasChildren)
        while (it.value()):
            it.value().setExpanded(True)
            it.next()


    def uncheckAll(self):
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.Checked)
        while (it.value()):
            it.value().setCheckState(0, 0)
            it.next()

    def cancel(self):
        self.reject()

    def addSelected(self):
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.Checked)
        while (it.value()):
            self.selectedItemList.append(it.value().item)
            it.next()
        self.accept()

    def spacePressedTreewidget(self):
        for item in self.treeWidget.selectedItems():
            if item.childCount() == 0:
                if item.checkState(0) == 0:
                    item.setCheckState(0, 2)
                else: 
                    item.setCheckState(0, 0)
                    
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return  self.selectedItemList
        else:
            return []
