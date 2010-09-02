# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
import sys, os
from ilastik.core.overlayMgr import OverlayItem
import qimage2ndarray
from PyQt4.QtOpenGL import QGLWidget
from ilastik.gui.iconMgr import ilastikIcons
import ilastik.gui.overlayDialogs as overlayDialogs
import ilastik

class MyListWidgetItem(QListWidgetItem):
    def __init__(self, item):
        QListWidgetItem.__init__(self, item.name)
        self.origItem = item

class OverlayCreateSelectionDlg(QDialog):
    def __init__(self, ilastikMain):
        QWidget.__init__(self, ilastikMain)
        self.ilastik = ilastikMain

        #get the absolute path of the 'ilastik' module
        ilastikPath = os.path.dirname(ilastik.__file__)
        uic.loadUi(ilastikPath+'/gui/classifierSelectionDlg.ui', self)

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)
        #self.connect(self.settingsButton, SIGNAL('pressed()'), self.classifierSettings)

        self.overlayDialogs = overlayDialogs.overlayClassDialogs.values()
        
        self.currentOverlay = self.overlayDialogs[0]
        
        j = 0
        for i, o in enumerate(self.overlayDialogs):
            self.listWidget.addItem(MyListWidgetItem(o))
        self.listWidget.setCurrentRow(0)

        self.connect(self.listWidget, SIGNAL('currentRowChanged(int)'), self.currentRowChanged)
        
        
        self.settingsButton.setVisible(False)

    def currentRowChanged(self, current):
        o = self.currentOverlay = self.overlayDialogs[current]
        
        self.name.setText(o.name)
        self.homepage.setText(o.homepage)
        self.description.setText(o.description)
        self.author.setText(o.author)


    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return self.currentOverlay
        else:
            return None





class ExtendedQLabel(QLabel):

    def __init(self, parent):
        QLabel.__init__(self, parent)

    def mouseReleaseEvent(self, ev):
        self.emit(SIGNAL('clicked()'))

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
    def __init__(self, ilastik, forbiddenItems=[], singleSelection=True, selectedItems=[], parent=None):
        QWidget.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setMinimumWidth(600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layoutWidget = QWidget(self)
        self.selectedItemList = []
        self.ilastik = ilastik
        self.christophsDict = cdict = ilastik.project.dataMgr[ilastik.activeImage].overlayMgr 
        self.forbiddenItems = forbiddenItems
        self.selectedItems = selectedItems
        self.singleSelection = singleSelection
        
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
        self.checkAllButton = QPushButton("Create New")
        self.connect(self.checkAllButton, SIGNAL('clicked()'), self.checkAll)
        #self.uncheckAllButton = QPushButton("Uncheck All")
        #self.connect(self.uncheckAllButton, SIGNAL('clicked()'), self.uncheckAll)
        treeButtonsLayout.addWidget(self.expandAllButton)
        treeButtonsLayout.addWidget(self.checkAllButton)
        #treeButtonsLayout.addWidget(self.uncheckAllButton)
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
        self.grview = QGraphicsView()
        self.grview.setDragMode(QGraphicsView.ScrollHandDrag)
        self.grscene = QGraphicsScene()
        tempLayoutZoom = QHBoxLayout(self)
        self.min = ExtendedQLabel()
        self.min.setPixmap(QPixmap(ilastikIcons.ZoomOut))
        self.connect(self.min, SIGNAL('clicked()'), self.scaleDown)
        self.zoomScaleLabel = ExtendedQLabel("100%")
        self.connect(self.zoomScaleLabel, SIGNAL('clicked()'), self.clickOnLabel)
        self.max = ExtendedQLabel()
        self.max.setPixmap(QPixmap(ilastikIcons.ZoomIn))
        self.connect(self.max, SIGNAL('clicked()'), self.scaleUp)
        tempLayoutZoom.addStretch()
        tempLayoutZoom.addWidget(self.min)
        tempLayoutZoom.addWidget(self.zoomScaleLabel)
        tempLayoutZoom.addWidget(self.max)
        tempLayoutZoom.addStretch()
        tempLayout = QHBoxLayout(self)
        self.channelLabel = QLabel("Channel")
        self.channelSpinbox = QSpinBox(self)
        self.connect(self.channelSpinbox, SIGNAL('valueChanged(int)'), self.channelSpinboxValueChanged)
        self.sliceLabel = QLabel("Slice")
        self.sliceSpinbox = QSpinBox(self)
        self.sliceValue = 0
        self.connect(self.sliceSpinbox, SIGNAL('valueChanged(int)'), self.sliceSpinboxValueChanged)
        tempLayout.addWidget(self.channelLabel)
        tempLayout.addWidget(self.channelSpinbox)
        tempLayout.addStretch()
        tempLayout.addWidget(self.sliceLabel)
        tempLayout.addWidget(self.sliceSpinbox)
        descLabelLayout.addWidget(self.desc)
        descLabelLayout.addWidget(self.grview)
        descLabelLayout.addLayout(tempLayoutZoom)
        descLabelLayout.addLayout(tempLayout)
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
        
        if self.singleSelection == True:
            self.setWindowTitle("Overlay Singel Selection")
            self.desc.setText("Singel Selection Mode")
            self.checkAllButton.setEnabled(False)
            self.uncheckAllButton.setEnabled(False)
        else:
            self.setWindowTitle("Overlay Multi Selection")
            self.desc.setText("Multi Selection Mode")
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
                    self.treeWidget.addTopLevelItem(newItemsChild)                   
                    boolStat = False
                    if self.christophsDict[keys] in self.selectedItems:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
                elif i+1 == len(split) and len(split) > 1:
                    newItemsChild = MyTreeWidgetItem(self.christophsDict[keys])
                    testItem.addChild(newItemsChild)
                    if self.christophsDict[keys] in self.selectedItems:
                        newItemsChild.setCheckState(0, 2)
                    else:
                        newItemsChild.setCheckState(0, 0)
                    
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
        if self.singleSelection == True and currentItem.checkState(column) == 2:
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
                self.desc.setText(child.item.key)
                self.channelSpinbox.setMaximum(child.item.data.shape[-1]-1)
                self.sliceSpinbox.setMaximum(child.item.data.shape[1]-1)
                imageArray = child.item.data[0, self.sliceValue, :, :, child.item.channel]
                pixmapImage = QPixmap(qimage2ndarray.gray2qimage(imageArray))
                self.grscene.addPixmap(pixmapImage)
                self.grview.setScene(self.grscene)
                self.channelSpinbox.setValue(child.item.channel)
            else:
                self.desc.setText(child.item.key)
                self.channelSpinbox.setMaximum(child.item.data.shape[-1]-1)
                self.sliceSpinbox.setMaximum(child.item.data.shape[1]-1)
                imageArray = child.item.data[0, self.sliceValue, :, :, child.item.channel]
                pixmapImage = QPixmap(qimage2ndarray.gray2qimage(imageArray))
                self.grscene.addPixmap(pixmapImage)
                self.grview.setScene(self.grscene)
        else:
            self.desc.setText(self.treeWidget.currentItem().text(0))


    def scaleUp(self):
        self.grview.scale(1.5, 1.5)

    def clickOnLabel(self):
        pass
    

    def scaleDown(self):
        print self.grview.size()
        self.grview.scale(.5, .5)

    def channelSpinboxValueChanged(self, value):
        child = self.treeWidget.currentItem()
        imageArray = child.item.data[0, self.sliceValue, :, :, value]
        pixmapImage = QPixmap(qimage2ndarray.gray2qimage(imageArray))
        self.grscene.addPixmap(pixmapImage)
        self.grview.setScene(self.grscene)
        child.item.channel = value

    def sliceSpinboxValueChanged(self, value):
        child = self.treeWidget.currentItem()
        imageArray = child.item.data[0, self.sliceValue, :, :, child.item.channel]
        pixmapImage = QPixmap(qimage2ndarray.gray2qimage(imageArray))
        self.grscene.addPixmap(pixmapImage)
        self.grview.setScene(self.grscene)
        self.sliceValue = value

    def expandAll(self):
        it = MyQTreeWidgetIter(self.treeWidget, QTreeWidgetItemIterator.HasChildren)
        while (it.value()):
            it.value().setExpanded(True)
            it.next()


    def checkAll(self):
        dlg = OverlayCreateSelectionDlg(self.ilastik)
        answer = dlg.exec_()
        if answer is not None:
            dlg_creation = answer(self.ilastik)
            answer = dlg_creation.exec_()
            if answer is not None:
                name = QInputDialog.getText(self,"Edit Name", "Please Enter the name of the new Overlay:", text = "Custom Overlays/My Overlay" )
                name = str(name[0])
                self.ilastik.project.dataMgr[self.ilastik.activeImage].overlayMgr[name] = answer
                self.cancel()

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
